"""MCP conformance, policy, durable uncertainty and physical HTTP regressions."""
import json
import socket
import threading
import time
from contextlib import contextmanager
from dataclasses import replace
from datetime import UTC, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from herdr.capability import (CapabilityError, CapabilityRegistry, CapabilityScope, DataClass,
                             DataPolicy, Egress, Health, Modality, RegistrySnapshot, Retention,
                             RuntimeStateSnapshot, Training)
from herdr.mcp import (CallContext, CallLedger, ClientAdapter, DeliveryUncertain, GatewayError,
                       GatewayUnavailable, HTTPTransport, McpGateway, META, NodeToolset, PROTOCOL,
                       PolicyDenied, ServerAdapter, ServerBinding, TASKS, TaskIdentity, ToolBinding,
                       decode, encoded, hashed, header_value, request_message, schema_headers, validate_schema)

READ = {"name": "read", "description": "Read declared code",
        "inputSchema": {"type": "object", "properties": {"path": {"type": "string", "x-mcp-header": "Path"}},
                        "required": ["path"], "additionalProperties": False}}
WRITE = {"name": "write", "description": "Write declared output",
         "annotations": {"readOnlyHint": True},
         "inputSchema": {"type": "object", "properties": {"value": {"type": "string", "maxLength": 128}},
                         "required": ["value"], "additionalProperties": False}}
UNUSED = {"name": "database", "description": "unused schema must not enter code-only context",
          "inputSchema": {"type": "object"}}
ARGUMENT_POLICY = hashed({"version": "scoped_fixture_v1", "read_paths": ["source.py", "one.py", "two.py"]})
NOW = 1791075600.0


class Clock:
    def __init__(self):
        self.value = NOW
    def __call__(self):
        return self.value


class FakeTransport:
    def __init__(self):
        self.calls = []
        self.definitions = [READ, WRITE, UNUSED]
        self.fail = False
        self.task = False
        self.poll_status = "working"
        self.response = None
    def request(self, request, **kwargs):
        self.calls.append((request, kwargs))
        method = request["method"]
        if method == "tools/list":
            result = {"resultType": "complete", "tools": self.definitions, "ttlMs": 300000}
        elif self.fail:
            raise DeliveryUncertain("lost response with private-secret-must-not-be-logged")
        elif self.response is not None:
            result = self.response
        elif method == "resources/read":
            result = {"resultType": "complete", "contents": [{"uri": request["params"]["uri"], "text": "scoped data"}]}
        elif method == "tasks/get" or self.task:
            result = {"resultType": "complete" if method == "tasks/get" else "task",
                      "taskId": "remote-task-1", "status": self.poll_status,
                      "createdAt": "2026-10-03T20:00:00Z", "lastUpdatedAt": "2026-10-03T20:00:01Z",
                      "ttlMs": 60000, "pollIntervalMs": 1000}
            if self.poll_status == "completed":
                result["result"] = {"resultType": "complete", "content": [{"type": "text", "text": "observed output"}]}
            elif self.poll_status == "failed":
                result["error"] = {"code": -32603, "message": "remote failure"}
            elif self.poll_status == "input_required":
                result["inputRequests"] = {"question": {"method": "elicitation/create", "params": {}}}
        else:
            result = {"resultType": "complete", "content": [{"type": "text", "text": "untrusted output"}],
                      "structuredContent": {"grant": "root", "task_state": "done"}}
        return ({"jsonrpc": "2.0", "id": request["id"], "result": result},)


def fixture(tmp_path, *, tools=("code_read",), retries=1, max_calls=16, tasks=False, subscriptions=False, transport=None):
    clock = Clock()
    ledger = CallLedger(tmp_path / "protected", writable_roots=(tmp_path / "worker",))
    data = DataPolicy(("eu-west",), (DataClass.INTERNAL,), Egress.REGION_BOUND,
                      Retention.LIMITED, Training.EXCLUDED)
    bindings = (ToolBinding("read", "code_read", "CORE", ("repo:read",), True, hashed(READ)),
                ToolBinding("write", "code_write", "CONDITIONAL", ("repo:write",), False, hashed(WRITE)))
    server = ServerBinding("local", "quantlab-paper", "1", data, bindings,
                           (("herdr://docs/one", "docs_read"),), tasks, subscriptions)
    transport = transport or FakeTransport()
    client = ClientAdapter(server, transport, ledger, clock=clock)
    ids = tuple("mcp.local." + x for x in ("code_read", "code_write", "docs_read"))
    scope = CapabilityScope(("mcp.local",), ids, tuple(x + ".executor" for x in ids),
                            ("code_read", "code_write", "docs_read"),
                            ("repo:read", "repo:write", "resource:read"), ("eu-west",),
                            (DataClass.INTERNAL,), (Modality.TEXT,), (Modality.TEXT,), 100, 8192,
                            Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED)
    identity = TaskIdentity("quantlab-paper", "task-1", 1, 1, "a" * 64)
    bootstrap = CallContext(identity, NodeToolset("1", "code-only declared toolset", "0" * 64, tools, scope,
                                               ARGUMENT_POLICY, max_calls, retries), scope, scope)
    client.discover(bootstrap, clock())
    registry = CapabilityRegistry(client.registry_snapshot())
    context = replace(bootstrap, toolset=replace(bootstrap.toolset, registry_hash=registry.snapshot.hash))
    authority = {"active": True, "context_hash": context.hash}
    def states(req, provider):
        executor = next(x for x in registry.snapshot.executors if x.capability_id == req.capability_id)
        return (RuntimeStateSnapshot(executor.id, datetime.fromtimestamp(clock(), UTC).isoformat(),
                                     60, Health.HEALTHY, 32, 5, None, registry.snapshot.hash, req.hash),)
    gateway = McpGateway(ledger, registry, (client,),
                         authority=lambda ctx: authority["active"] and ctx.hash == authority["context_hash"],
                         runtime_states=states, argument_authority=lambda ctx, server, logical, args:
                         logical == "code_write" or logical == "code_read" and args.get("path") in {"source.py", "one.py", "two.py"},
                         argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    return gateway, context, transport, clock, client, authority


def semantic_calls(transport):
    return [x for x in transport.calls if x[0]["method"] != "tools/list"]


def test_discovery_maps_to_registry_and_omits_unused_schema_from_context(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    value = gateway.model_context(context)
    assert [x["name"] for x in value["tools"]] == ["local.read"]
    assert "database" not in json.dumps(value) and "local.write" not in json.dumps(value)
    assert len(gateway.registry.snapshot.capabilities) == 3
    assert all("mcp" in x.features for x in gateway.registry.snapshot.capabilities)
    assert transport.calls[0][0]["params"]["_meta"][META + "protocolVersion"] == PROTOCOL


@pytest.mark.parametrize("fault", ["unknown_provider", "omitted_conditional", "inactive_fence", "wrong_consumer", "missing_runtime"])
def test_runtime_and_alternative_calls_cannot_expand_minimal_toolset(tmp_path, fault):
    gateway, context, transport, clock, client, authority = fixture(tmp_path)
    server, tool, args = "local", "read", {"path": "source.py"}
    if fault == "unknown_provider":
        server = "alternative"
    elif fault == "omitted_conditional":
        tool, args = "write", {"value": "unexpected"}
    elif fault == "inactive_fence":
        authority["active"] = False
    elif fault == "wrong_consumer":
        context = replace(context, identity=replace(context.identity, consumer="another-consumer"))
    else:
        gateway.runtime_states = lambda *a: ()
    with pytest.raises(PolicyDenied):
        gateway.call(context, server, tool, args, "op-1")
    assert not semantic_calls(transport)


def test_parent_and_consumer_scope_remain_closed(tmp_path):
    gateway, context, *_ = fixture(tmp_path)
    restrictive = replace(context.parent_scope, permissions=("repo:read",))
    with pytest.raises(CapabilityError, match="escalates"):
        replace(context, parent_scope=restrictive)
    with pytest.raises(CapabilityError, match="escalates"):
        replace(context, consumer_scope=restrictive)


def test_remote_output_never_changes_grant_or_semantic_completion(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    before = context.hash
    result = gateway.call(context, "local", "read", {"path": "source.py"}, "op-1")
    assert result.state == "observed_complete"
    assert result.authority == "remote_observation"
    assert result.result["structuredContent"]["task_state"] == "done"
    assert context.hash == before
    assert gateway.model_context(context)["toolset_hash"] == context.toolset.hash
    assert gateway.ledger.get(hashed({"consumer": context.identity.consumer, "task_id": "task-1", "operation_key": "op-1"}))["state"] != "done"


def test_side_effect_hint_is_not_authority_and_lost_delivery_never_repeats(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path, tools=("code_write",))
    assert gateway.model_context(context)["tools"][0]["annotations"]["readOnlyHint"] is False
    transport.fail = True
    with pytest.raises(DeliveryUncertain):
        gateway.call(context, "local", "write", {"value": "economic output"}, "economic-op")
    with pytest.raises(DeliveryUncertain):
        gateway.call(context, "local", "write", {"value": "economic output"}, "economic-op")
    assert len(semantic_calls(transport)) == 1


def test_successful_restart_replay_returns_digest_without_reexecuting_or_logging_payload(tmp_path):
    gateway, context, transport, clock, client, authority = fixture(tmp_path, tools=("code_write",))
    secret = "private-secret-must-not-be-logged"
    first = gateway.call(context, "local", "write", {"value": secret}, "op")
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    client.ledger = ledger
    restored = McpGateway(ledger, gateway.registry, (client,), authority=gateway.authority,
                          runtime_states=gateway.runtime_states, argument_authority=gateway.argument_authority,
                          argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    replay = restored.call(context, "local", "write", {"value": secret}, "op")
    assert replay.replay and replay.result is None and replay.result_hash == first.result_hash
    assert len(semantic_calls(transport)) == 1
    audit = "\n".join(ledger.db.iterdump())
    assert secret not in audit and "untrusted output" not in audit
    assert ledger.db.execute("SELECT count(*) FROM contexts").fetchone()[0] >= 1


def test_crash_after_transmission_reservation_quarantines_side_effect(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tools=("code_write",))
    params = {"name": "write", "arguments": {"value": "result"}}
    key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id, "operation_key": "op"})
    request_hash = hashed({"server": "local", "method": "tools/call", "params": params})
    gateway.ledger.reserve(key, context, request_hash, "local", clock(), "tools/call", "write")
    gateway.ledger.sending(key, context, clock(), 5)
    with pytest.raises(DeliveryUncertain):
        gateway.call(context, "local", "write", params["arguments"], "op")
    assert not semantic_calls(transport)


def test_operation_key_conflict_cannot_change_payload_or_policy(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    gateway.call(context, "local", "read", {"path": "one.py"}, "op")
    with pytest.raises(PolicyDenied, match="reused"):
        gateway.call(context, "local", "read", {"path": "two.py"}, "op")
    assert len(semantic_calls(transport)) == 1


def test_readonly_retries_are_bounded_and_provider_circuit_survives_restart(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path, retries=2)
    transport.fail = True
    with pytest.raises(DeliveryUncertain, match="retry budget exhausted"):
        gateway.call(context, "local", "read", {"path": "one.py"}, "op")
    assert len(semantic_calls(transport)) == 3
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    assert not ledger.health("local", clock())
    assert ledger.health("independent-provider", clock())
    assert "private-secret-must-not-be-logged" not in "\n".join(ledger.db.iterdump())


def test_cumulative_task_budget_does_not_reset_with_new_operation_key(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path, max_calls=1)
    gateway.call(context, "local", "read", {"path": "one.py"}, "op1")
    with pytest.raises(PolicyDenied, match="cumulative"):
        gateway.call(context, "local", "read", {"path": "two.py"}, "op2")
    assert len(semantic_calls(transport)) == 1


def test_schema_change_invalidates_cache_without_widening_scope(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    clock.value += 301
    changed = json.loads(json.dumps(READ))
    changed["inputSchema"]["properties"]["path"]["type"] = "integer"
    transport.definitions = [changed, WRITE]
    with pytest.raises(PolicyDenied, match="definition changed"):
        gateway.model_context(context)
    assert not semantic_calls(transport)


def test_resources_require_exact_uri_node_permission_and_content_scope(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path, tools=("docs_read",))
    result = gateway.read_resource(context, "local", "herdr://docs/one", "resource")
    assert result.state == "observed_complete"
    with pytest.raises(PolicyDenied):
        gateway.read_resource(context, "local", "file:///private/credentials", "resource2")
    transport.response = {"resultType": "complete", "contents": [{"uri": "file:///private/credentials", "text": "untrusted"}]}
    with pytest.raises(PolicyDenied):
        gateway.read_resource(context, "local", "herdr://docs/one", "resource3")


def test_task_polling_is_durable_bound_and_observational(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    started = gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert started.state == "remote_running" and started.remote_task_id == "remote-task-1"
    with pytest.raises(GatewayUnavailable, match="interval"):
        gateway.poll(context, "op")
    clock.value += 2
    transport.poll_status = "input_required"
    pending = gateway.poll(context, "op")
    assert pending.state == "remote_running"
    clock.value += 2
    transport.poll_status = "completed"
    complete = gateway.poll(context, "op")
    assert complete.state == "observed_complete" and complete.authority == "remote_observation"
    assert len([x for x in semantic_calls(transport) if x[0]["method"] == "tools/call"]) == 1
    gateway.poll(context, "op")
    assert len([x for x in semantic_calls(transport) if x[0]["method"] == "tasks/get"]) == 2


def test_unnegotiated_tasks_and_remote_requests_are_rejected(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    transport.task = True
    with pytest.raises(GatewayError, match="unnegotiated"):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert gateway.call(context, "local", "read", {"path": "source.py"}, "op").state == "response_rejected"
    assert len(semantic_calls(transport)) == 1


def test_events_only_invalidate_observations_and_never_execute_remote_commands(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    gateway.observe_event(context, "local", {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
    assert client.expires_at == 0
    gateway.model_context(context)
    assert client.expires_at > clock()
    with pytest.raises(PolicyDenied):
        gateway.observe_event(context, "local", {"jsonrpc": "2.0", "method": "herdr/merge"})
    with pytest.raises(PolicyDenied):
        gateway.observe_event(context, "local", {"jsonrpc": "2.0", "method": "notifications/resources/updated",
                                               "params": {"uri": "file:///private"}})
    assert not semantic_calls(transport)


@pytest.mark.parametrize("schema", [
    {"$ref": "https://unapproved.example/schema"},
    {"type": "object", "properties": {"x": {"type": "number", "x-mcp-header": "X"}}},
    {"type": "array", "items": {"type": "string", "x-mcp-header": "X"}},
    {"type": "object", "properties": {"x": {"type": "string", "x-mcp-header": "bad\r\nHeader"}}},
])
def test_untrusted_schema_cannot_fetch_network_or_inject_headers(schema):
    with pytest.raises(GatewayError):
        validate_schema(schema, check_only=True)
        schema_headers(schema)


def test_full_json_schema_local_refs_and_conditional_validation():
    schema = {"type": "object", "$defs": {"value": {"type": "integer", "minimum": 1}},
              "properties": {"x": {"$ref": "#/$defs/value"}}, "required": ["x"], "additionalProperties": False}
    validate_schema(schema, {"x": 2})
    with pytest.raises(GatewayError):
        validate_schema(schema, {"x": 0})


def test_server_resolves_authentication_and_never_accepts_request_scope(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    adapter = ServerAdapter(gateway, lambda credential: context if credential == "trusted-session" else None,
                            origins=("https://approved.example",))
    message = request_message(context, "tools/list", {}, "1")
    status, raw = adapter.handle(encoded(message), authorization="trusted-session", origin="https://approved.example")
    assert status == 200 and decode(raw)["result"]["tools"][0]["name"] == "local.read"
    assert adapter.handle(encoded(message), authorization="invalid")[0] == 403
    assert adapter.handle(encoded(message), authorization="trusted-session", origin="https://attacker.example")[0] == 403
    message["params"]["_meta"]["org.herdr/task"]["fencing_token"] = 99
    assert adapter.handle(encoded(message), authorization="trusted-session")[0] == 403
    message = request_message(context, "herdr/merge", {}, "2")
    assert adapter.handle(encoded(message), authorization="trusted-session")[0] == 403
    assert not semantic_calls(transport)


@contextmanager
def provider_http(*, sse=False, lose_write=False, subscriptions=False, line_ending=b"\n") :
    observations = {"writes": 0, "requests": [], "bad_headers": False}
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass
        def do_POST(self):
            raw = self.rfile.read(int(self.headers["Content-Length"]))
            request = decode(raw)
            observations["requests"].append(request)
            method, params = request["method"], request["params"]
            expected_name = params.get("name", params.get("uri", params.get("taskId")))
            if (self.headers.get("MCP-Protocol-Version") != PROTOCOL
                    or self.headers.get("Mcp-Method") != method
                    or self.headers.get("Authorization") != "Bearer fixture-private-credential"
                    or expected_name is not None and self.headers.get("Mcp-Name") != header_value(expected_name)):
                observations["bad_headers"] = True
                self.send_error(400)
                return
            if method == "tools/list":
                result = {"resultType": "complete", "tools": [READ, WRITE], "ttlMs": 300000}
            else:
                if params.get("name") == "write":
                    observations["writes"] += 1
                    if lose_write:
                        self.close_connection = True
                        self.connection.shutdown(socket.SHUT_RDWR)
                        return
                result = {"resultType": "complete", "content": [{"type": "text", "text": "actual HTTP result"}]}
            response = {"jsonrpc": "2.0", "id": request["id"], "result": result}
            if method == "subscriptions/listen" and subscriptions:
                metadata = {META + "subscriptionId": request["id"]}
                ack = {"jsonrpc": "2.0", "method": "notifications/subscriptions/acknowledged",
                       "params": {"_meta": metadata, "notifications": params["notifications"]}}
                update = {"jsonrpc": "2.0", "method": "notifications/tools/list_changed",
                          "params": {"_meta": metadata}}
                response["result"] = {"resultType": "complete", "_meta": metadata}
                body = b"".join(b"data: " + encoded(item) + b"\n\n" for item in (ack, update, response))
            elif sse:
                progress = {"jsonrpc": "2.0", "method": "notifications/progress", "params": {"progress": 1}}
                body = b"data: " + encoded(progress) + b"\n\n" + b"data: " + encoded(response) + b"\n\n"
            else:
                body = encoded(response)
            if sse or method == "subscriptions/listen" and subscriptions:
                body = body.replace(b"\n", line_ending)
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream" if sse or method == "subscriptions/listen" and subscriptions else "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield HTTPTransport("http://127.0.0.1:" + str(server.server_port) + "/mcp",
                            lambda: "fixture-private-credential", allow_loopback=True), observations
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize("sse", [False, True])
def test_actual_http_and_sse_readonly_conformance(tmp_path, sse):
    with provider_http(sse=sse) as (transport, observations):
        gateway, context, *_ = fixture(tmp_path, transport=transport)
        result = gateway.call(context, "local", "read", {"path": "source.py"}, "op")
        assert result.state == "observed_complete"
        assert result.result["content"][0]["text"] == "actual HTTP result"
        assert not observations["bad_headers"]
        dump = "\n".join(gateway.ledger.db.iterdump())
        assert "fixture-private-credential" not in dump
        assert "actual HTTP result" not in dump


def test_actual_http_side_effect_loss_and_restart_never_duplicate(tmp_path):
    with provider_http(lose_write=True) as (transport, observations):
        gateway, context, *_ = fixture(tmp_path, tools=("code_write",), transport=transport)
        with pytest.raises(DeliveryUncertain):
            gateway.call(context, "local", "write", {"value": "economic output"}, "op")
        assert observations["writes"] == 1
        gateway.ledger.close()
        restored, same_context, *_ = fixture(tmp_path, tools=("code_write",), transport=transport)
        assert context.hash == same_context.hash
        with pytest.raises(DeliveryUncertain):
            restored.call(same_context, "local", "write", {"value": "economic output"}, "op")
        assert observations["writes"] == 1


def test_cumulative_cost_reservation_prevents_new_key_from_exceeding_scope(tmp_path):
    gateway, context, transport, clock, client, authority = fixture(tmp_path)
    scope = replace(context.toolset.scope, max_cost_microusd=5)
    context = replace(context, toolset=replace(context.toolset, scope=scope))
    authority["context_hash"] = context.hash
    gateway.call(context, "local", "read", {"path": "one.py"}, "op1")
    with pytest.raises(PolicyDenied, match="cost budget"):
        gateway.call(context, "local", "read", {"path": "two.py"}, "op2")
    assert len(semantic_calls(transport)) == 1
    assert gateway.ledger.db.execute("SELECT reserved_cost FROM calls WHERE deliveries=1").fetchone()[0] == 5


def test_admitted_tool_cannot_read_an_argument_target_outside_repo_policy(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    with pytest.raises(PolicyDenied, match="unapproved"):
        gateway.call(context, "local", "read", {"path": "../../private/credentials"}, "op")
    assert not semantic_calls(transport)


def test_changed_argument_policy_requires_a_versioned_node_replan(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    gateway.argument_policy_hash = "b" * 64
    with pytest.raises(PolicyDenied, match="policy changed"):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert not semantic_calls(transport)


def test_server_checks_routing_headers_before_tool_execution(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    adapter = ServerAdapter(gateway, lambda auth: context, origins=())
    message = request_message(context, "tools/call", {"name": "local.read", "arguments": {"path": "source.py"}}, "1")
    message["params"]["_meta"]["org.herdr/operation"] = "op"
    headers = {"MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/call", "Mcp-Name": "local.read"}
    assert adapter.handle(encoded(message), authorization="session", headers=headers)[0] == 400
    assert not semantic_calls(transport)
    headers["Mcp-Param-Path"] = "source.py"
    assert adapter.handle(encoded(message), authorization="session", headers=headers)[0] == 200
    assert len(semantic_calls(transport)) == 1


def test_server_lists_only_node_declared_resources(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path, tools=("docs_read",))
    adapter = ServerAdapter(gateway, lambda auth: context, origins=())
    message = request_message(context, "resources/list", {}, "1")
    status, response = adapter.handle(encoded(message), authorization="session")
    assert status == 200
    assert [x["uri"] for x in decode(response)["result"]["resources"]] == ["herdr://docs/one"]


def test_actual_http_subscription_is_bounded_correlated_and_observational(tmp_path):
    with provider_http(subscriptions=True) as (transport, observations):
        gateway, context, _, clock, client, _ = fixture(tmp_path, subscriptions=True, transport=transport)
        assert client.expires_at > clock()
        outcome = gateway.listen(context, "local", {"toolsListChanged": True}, "listen1")
        assert outcome.state == "observed_complete"
        assert outcome.authority == "remote_observation"
        assert outcome.result["closure"] == "graceful"
        assert outcome.result["events"][0]["code"] == "discovery_invalidated"
        assert client.expires_at == 0
        assert gateway.listen(context, "local", {"toolsListChanged": True}, "listen1").replay
        assert len([x for x in observations["requests"] if x["method"] == "subscriptions/listen"]) == 1
        assert not observations["bad_headers"]


@pytest.mark.parametrize("fault", ["unrequested", "wrong_identity", "before_ack"])
def test_subscription_cannot_expand_authority_or_skip_ack(tmp_path, fault):
    gateway, context, transport, _, _, _ = fixture(tmp_path, subscriptions=True)
    def stream(message, **kwargs):
        metadata = {META + "subscriptionId": message["id"]}
        ack = {"jsonrpc": "2.0", "method": "notifications/subscriptions/acknowledged",
               "params": {"_meta": metadata, "notifications": {"toolsListChanged": True}}}
        event = {"jsonrpc": "2.0", "method": "herdr/merge", "params": {"_meta": metadata}}
        if fault == "wrong_identity":
            ack["params"]["_meta"] = {META + "subscriptionId": "another"}
        if fault != "before_ack":
            yield ack
        yield event
    transport.stream = stream
    with pytest.raises(GatewayError):
        gateway.listen(context, "local", {"toolsListChanged": True}, "op")
    assert gateway.listen(context, "local", {"toolsListChanged": True}, "op").state == "response_rejected"


def test_subscription_requires_declared_resources_and_explicit_host_approval(tmp_path):
    gateway, context, *_ = fixture(tmp_path)
    with pytest.raises(PolicyDenied):
        gateway.listen(context, "local", {"toolsListChanged": True}, "op")
    gateway, context, *_ = fixture(tmp_path / "approved", subscriptions=True)
    with pytest.raises(PolicyDenied):
        gateway.listen(context, "local", {"resourceSubscriptions": ["herdr://docs/one"]}, "op")
    with pytest.raises(PolicyDenied):
        gateway.listen(context, "local", {"promptsListChanged": True}, "op")


def test_unused_provider_declarations_do_not_require_network_discovery(tmp_path):
    gateway, context, transport, _, client, _ = fixture(tmp_path)
    untouched = FakeTransport()
    inactive = ClientAdapter(replace(client.server, id="unused"), untouched, gateway.ledger)
    snapshot = inactive.registry_snapshot()
    assert snapshot.providers[0].id == "mcp.unused"
    assert not untouched.calls
    assert gateway.model_context(context)["tools"][0]["name"] == "local.read"
    assert not untouched.calls


def test_mutating_provider_endpoint_or_effect_policy_requires_replan(tmp_path):
    gateway, context, transport, _, client, _ = fixture(tmp_path)
    client.server = replace(client.server, tools=(replace(client.server.tools[0], read_only=False), client.server.tools[1]))
    with pytest.raises(PolicyDenied, match="execution policy changed"):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert not semantic_calls(transport)


def test_malformed_request_metadata_and_extensions_are_bounded_errors(tmp_path):
    gateway, context, transport, *_ = fixture(tmp_path)
    adapter = ServerAdapter(gateway, lambda _: context, origins=())
    for metadata in ([], {META + "protocolVersion": PROTOCOL, META + "clientCapabilities": {"extensions": []}},
                     {META + "protocolVersion": PROTOCOL, META + "clientCapabilities": {}}):
        message = request_message(context, "tools/list", {}, "op")
        message["params"]["_meta"] = metadata
        assert adapter.handle(encoded(message), authorization="host")[0] == 400
    assert not semantic_calls(transport)


def test_task_poll_cannot_continue_after_argument_policy_changes(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    clock.value += 2
    gateway.argument_policy_hash = "f" * 64
    with pytest.raises(PolicyDenied, match="argument policy changed"):
        gateway.poll(context, "op")


def test_custom_header_integers_are_limited_to_safe_protocol_range():
    assert header_value(2**53 - 1) == str(2**53 - 1)
    with pytest.raises(GatewayError):
        header_value(2**53)


def test_server_maps_remote_task_handle_to_exact_durable_attempt(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    adapter = ServerAdapter(gateway, lambda _: context, origins=())
    message = request_message(context, "tools/call", {"name": "local.read", "arguments": {"path": "source.py"}}, "create", tasks=True)
    message["params"]["_meta"]["org.herdr/operation"] = "economic-op"
    status, raw = adapter.handle(encoded(message), authorization="host")
    result = decode(raw)["result"]
    assert status == 200 and result["resultType"] == "task"
    handle = result["taskId"]
    assert handle != "remote-task-1" and len(handle) == 64
    clock.value += 2
    transport.poll_status = "completed"
    poll = request_message(context, "tasks/get", {"taskId": handle}, "poll", tasks=True)
    status, raw = adapter.handle(encoded(poll), authorization="host")
    result = decode(raw)["result"]
    assert status == 200 and result["taskId"] == handle and result["status"] == "completed"
    assert len([x for x in semantic_calls(transport) if x[0]["method"] == "tools/call"]) == 1
    poll["params"]["taskId"] = "f" * 64
    assert adapter.handle(encoded(poll), authorization="host")[0] == 403


@pytest.mark.parametrize("kind", ["read", "write", "resource", "subscription"])
def test_fresh_client_replays_offline_without_runtime_or_discovery(tmp_path, kind):
    tools = ("code_write",) if kind == "write" else ("docs_read",) if kind == "resource" else ("code_read",)
    gateway, context, transport, clock, client, _ = fixture(tmp_path, tools=tools, subscriptions=True)
    if kind == "subscription":
        def stream(message, **kwargs):
            metadata = {META + "subscriptionId": message["id"]}
            yield {"jsonrpc": "2.0", "method": "notifications/subscriptions/acknowledged",
                   "params": {"_meta": metadata, "notifications": {"toolsListChanged": True}}}
            yield {"jsonrpc": "2.0", "id": message["id"],
                   "result": {"resultType": "complete", "_meta": metadata}}
        transport.stream = stream
        first = gateway.listen(context, "local", {"toolsListChanged": True}, "op")
    elif kind == "resource":
        first = gateway.read_resource(context, "local", "herdr://docs/one", "op")
    else:
        first = gateway.call(context, "local", kind, {"value": "output"} if kind == "write" else {"path": "source.py"}, "op")
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    class Offline:
        def request(self, *args, **kwargs):
            pytest.fail("durable replay must not contact offline provider")
    fresh_client = ClientAdapter(client.server, Offline(), ledger, clock=clock)
    restored = McpGateway(ledger, gateway.registry, (fresh_client,), authority=gateway.authority,
        runtime_states=lambda *a: pytest.fail("durable replay must not require live runtime"),
        argument_authority=gateway.argument_authority, argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    assert fresh_client.definitions == {} and fresh_client.expires_at == 0
    if kind == "subscription":
        replay = restored.listen(context, "local", {"toolsListChanged": True}, "op")
    elif kind == "resource":
        replay = restored.read_resource(context, "local", "herdr://docs/one", "op")
    else:
        replay = restored.call(context, "local", kind, {"value": "output"} if kind == "write" else {"path": "source.py"}, "op")
    assert replay.replay and replay.result is None and replay.result_hash == first.result_hash
    ledger.close()


@pytest.mark.parametrize("status,state", [("completed", "observed_complete"), ("failed", "observed_error"),
                                         ("cancelled", "observed_error")])
def test_initial_terminal_remote_task_is_validated_without_poll(tmp_path, status, state):
    gateway, context, transport, _, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    transport.poll_status = status
    outcome = gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert outcome.state == state
    replay = gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert replay.state == state and replay.replay
    assert len(semantic_calls(transport)) == 1


@pytest.mark.parametrize("mutation", [False, True])
def test_initial_completed_task_cannot_bypass_result_validation(tmp_path, mutation):
    kind = "write" if mutation else "read"
    gateway, context, transport, _, *_ = fixture(tmp_path, tools=("code_write",) if mutation else ("code_read",), tasks=True)
    transport.response = {"resultType": "task", "taskId": "done", "status": "completed",
        "createdAt": "2026-10-03T20:00:00Z", "lastUpdatedAt": "2026-10-03T20:00:01Z", "ttlMs": 0}
    args = {"value": "output"} if mutation else {"path": "source.py"}
    with pytest.raises(DeliveryUncertain if mutation else GatewayError):
        gateway.call(context, "local", kind, args, "op")
    row = gateway.ledger.get(hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id, "operation_key": "op"}))
    assert row["state"] == ("delivery_uncertain" if mutation else "response_rejected")
    if mutation:
        with pytest.raises(DeliveryUncertain):
            gateway.call(context, "local", kind, args, "op")
    assert len(semantic_calls(transport)) == 1


def test_successful_task_poll_resets_persisted_failure_streak(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    clock.value += 2
    transport.fail = True
    for _ in range(2):
        with pytest.raises(DeliveryUncertain):
            gateway.poll(context, "op")
    transport.fail = False
    gateway.poll(context, "op")
    assert gateway.ledger.db.execute("SELECT * FROM health WHERE server='local'").fetchone() is None
    clock.value += 2
    transport.fail = True
    with pytest.raises(DeliveryUncertain):
        gateway.poll(context, "op")
    row = gateway.ledger.db.execute("SELECT failures,open_until FROM health WHERE server='local'").fetchone()
    assert row["failures"] == 1 and row["open_until"] == 0


def test_discovery_cannot_overwrite_concurrent_subscription_invalidation(tmp_path, monkeypatch):
    import herdr.mcp as module
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    original = module.validate_schema
    invalidated = False
    def validate(*args, **kwargs):
        nonlocal invalidated
        if not invalidated:
            invalidated = True
            gateway.observe_event(context, "local", {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"})
        return original(*args, **kwargs)
    monkeypatch.setattr(module, "validate_schema", validate)
    with pytest.raises(GatewayUnavailable, match="invalidated during"):
        client.discover(context, clock())
    assert client.expires_at == 0
    gateway.model_context(context)
    assert client.expires_at > clock()
    assert not semantic_calls(transport)


@pytest.mark.parametrize("value", [float(2**53), -float(2**53), 1.5])
def test_integral_float_routing_headers_cannot_bypass_safe_integer_range(value):
    with pytest.raises(GatewayError):
        header_value(value)
    assert header_value(1.0) == "1"


@pytest.mark.parametrize("bad", [{"resultType": "unknown"},
                               {"resultType": "complete", "content": "malformed"}])
def test_rejected_mutating_response_retains_uncertainty_and_never_resends(tmp_path, bad):
    gateway, context, transport, _, *_ = fixture(tmp_path, tools=("code_write",))
    transport.response = bad
    for _ in range(2):
        with pytest.raises(DeliveryUncertain):
            gateway.call(context, "local", "write", {"value": "actual side effect"}, "op")
    row = gateway.ledger.get(hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id, "operation_key": "op"}))
    assert row["state"] == "delivery_uncertain" and row["deliveries"] == 1
    assert len(semantic_calls(transport)) == 1


@pytest.mark.parametrize("mutation", [False, True])
@pytest.mark.parametrize("valid", [False, True])
def test_initial_completed_task_enforces_approved_output_schema(tmp_path, monkeypatch, mutation, valid):
    definition = WRITE if mutation else READ
    monkeypatch.setitem(definition, "outputSchema", {
        "type": "object", "properties": {"count": {"type": "integer"}},
        "required": ["count"], "additionalProperties": False})
    gateway, context, transport, _, *_ = fixture(
        tmp_path, tools=("code_write",) if mutation else ("code_read",), tasks=True)
    transport.response = {"resultType": "task", "taskId": "immediate", "status": "completed",
        "createdAt": "2026-10-03T20:00:00Z", "lastUpdatedAt": "2026-10-03T20:00:01Z", "ttlMs": 0,
        "result": {"resultType": "complete", "content": [{"type": "text", "text": "observed"}],
                   "structuredContent": {"count": 1 if valid else "invalid"}}}
    args = {"value": "output"} if mutation else {"path": "source.py"}
    if valid:
        assert gateway.call(context, "local", "write" if mutation else "read", args, "op").state == "observed_complete"
    else:
        with pytest.raises(DeliveryUncertain if mutation else GatewayError):
            gateway.call(context, "local", "write" if mutation else "read", args, "op")
        row = gateway.ledger.get(hashed({"consumer": context.identity.consumer,
            "task_id": context.identity.task_id, "operation_key": "op"}))
        assert row["state"] == ("delivery_uncertain" if mutation else "response_rejected")
    assert len(semantic_calls(transport)) == 1


@pytest.mark.parametrize("uri", [{}, [], 1, None, "", "x" * 4097])
def test_malformed_resource_uri_returns_bounded_protocol_error(tmp_path, uri):
    gateway, context, transport, *_ = fixture(tmp_path, tools=("docs_read",))
    adapter = ServerAdapter(gateway, lambda _: context, origins=())
    message = request_message(context, "resources/read", {"uri": uri}, "request")
    message["params"]["_meta"].update({"org.herdr/provider": "local", "org.herdr/operation": "resource"})
    status, raw = adapter.handle(encoded(message), authorization="trusted")
    assert status == 400 and decode(raw)["error"]["message"] == "invalid_request"
    assert not semantic_calls(transport)


@pytest.mark.parametrize("error,status,retryable,reconcile", [
    (PolicyDenied, 403, False, False), (GatewayUnavailable, 503, True, False),
    (DeliveryUncertain, 502, False, True)])
def test_server_distinguishes_policy_outage_and_uncertain_delivery(tmp_path, monkeypatch, error, status, retryable, reconcile):
    gateway, context, *_ = fixture(tmp_path)
    adapter = ServerAdapter(gateway, lambda _: context, origins=())
    def fail(*a):
        raise error("private detail must not be returned")
    monkeypatch.setattr(gateway, "call", fail)
    message = request_message(context, "tools/call", {"name": "local.read", "arguments": {"path": "source.py"}}, "request")
    message["params"]["_meta"]["org.herdr/operation"] = "op"
    actual, raw = adapter.handle(encoded(message), authorization="trusted")
    assert actual == status
    assert decode(raw)["error"]["data"] == {"retryable": retryable, "reconcileRequired": reconcile}
    assert b"private detail" not in raw


@pytest.mark.parametrize("ttl", [10**500, -1, True, 1.5])
def test_discovery_ttl_is_rejected_before_float_conversion(tmp_path, ttl):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    original = transport.request
    def request(message, **kwargs):
        result = original(message, **kwargs)
        if message["method"] == "tools/list":
            result[0]["result"]["ttlMs"] = ttl
        return result
    transport.request = request
    with pytest.raises(GatewayError, match="TTL"):
        client.discover(context, clock())


@pytest.mark.parametrize("line_ending", [b"\n", b"\r\n", b"\r"])
def test_actual_http_sse_supports_all_standard_line_endings(tmp_path, line_ending):
    with provider_http(sse=True, line_ending=line_ending) as (transport, observations):
        gateway, context, *_ = fixture(tmp_path, transport=transport)
        assert gateway.call(context, "local", "read", {"path": "source.py"}, "op").state == "observed_complete"
        assert len([x for x in observations["requests"] if x["method"] == "tools/call"]) == 1


def test_sse_crlf_split_between_reads_is_not_a_second_newline(tmp_path, monkeypatch):
    import herdr.mcp as module
    gateway, context, *_ = fixture(tmp_path)
    message = request_message(context, "tools/call", {"name": "read"}, "correlation")
    progress = {"jsonrpc": "2.0", "method": "notifications/progress", "params": {}}
    response = {"jsonrpc": "2.0", "id": "correlation",
                "result": {"resultType": "complete", "content": []}}
    chunks = iter([b"data: " + encoded(progress) + b"\r", b"\n\r",
                   b"\ndata: " + encoded(response) + b"\r", b"\n\r", b"\n", b""])
    class Response:
        status = 200
        def getheader(self, *a):
            return "text/event-stream"
        def read1(self, *a):
            return next(chunks)
        def isclosed(self):
            return False
    class Socket:
        def settimeout(self, *a):
            pass
    class Connection:
        sock = Socket()
        def connect(self):
            pass
        def request(self, *a, **k):
            pass
        def getresponse(self):
            return Response()
        def close(self):
            pass
    monkeypatch.setattr(module.http.client, "HTTPConnection", lambda *a, **k: Connection())
    transport = HTTPTransport("http://127.0.0.1:9/mcp", allow_loopback=True)
    assert transport.request(message, timeout=2) == (progress, response)


@pytest.mark.parametrize("restart", [False, True])
@pytest.mark.parametrize("valid", [False, True])
def test_terminal_poll_uses_durable_admitted_schema_without_discovery(tmp_path, monkeypatch, restart, valid):
    monkeypatch.setitem(READ, "outputSchema", {"type": "object", "properties": {"count": {"type": "integer"}},
        "required": ["count"], "additionalProperties": False})
    gateway, context, transport, clock, client, _ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    clock.value += 301
    original = transport.request
    def request(message, **kwargs):
        if message["method"] == "tools/list":
            pytest.fail("terminal poll must not refresh discovery")
        response = original(message, **kwargs)
        response[0]["result"]["result"]["structuredContent"] = {"count": 1 if valid else "invalid"}
        response[0]["result"]["ttlMs"] = 0
        return response
    transport.request = request
    transport.poll_status = "completed"
    if restart:
        gateway.ledger.close()
        ledger = CallLedger(tmp_path / "protected")
        fresh = ClientAdapter(client.server, transport, ledger, clock=clock)
        gateway = McpGateway(ledger, gateway.registry, (fresh,), authority=gateway.authority,
            runtime_states=gateway.runtime_states, argument_authority=gateway.argument_authority,
            argument_policy_hash=ARGUMENT_POLICY, clock=clock)
        assert fresh.definitions == {}
    if valid:
        assert gateway.poll(context, "op").state == "observed_complete"
        assert gateway.poll(context, "op").replay
    else:
        with pytest.raises(GatewayError):
            gateway.poll(context, "op")
    assert len([x for x in semantic_calls(transport) if x[0]["method"] == "tools/call"]) == 1


def test_missing_legacy_task_plan_fails_before_consuming_remote_result(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    gateway.ledger.db.execute("UPDATE calls SET validation_plan_json=NULL")
    clock.value += 2
    with pytest.raises(DeliveryUncertain, match="validation plan"):
        gateway.poll(context, "op")
    assert len(semantic_calls(transport)) == 1


def test_authenticated_header_replay_uses_pinned_plan_after_restart(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    class Offline:
        def request(self, *a, **k):
            pytest.fail("header replay must not contact provider")
    fresh = ClientAdapter(client.server, Offline(), ledger, clock=clock)
    restored = McpGateway(ledger, gateway.registry, (fresh,), authority=gateway.authority,
        runtime_states=lambda *a: pytest.fail("header replay must not require runtime"),
        argument_authority=gateway.argument_authority, argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    adapter = ServerAdapter(restored, lambda _: context, origins=())
    message = request_message(context, "tools/call", {"name": "local.read", "arguments": {"path": "source.py"}}, "request")
    message["params"]["_meta"]["org.herdr/operation"] = "op"
    headers = {"MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/call",
               "Mcp-Name": "local.read", "Mcp-Param-Path": "source.py"}
    status, raw = adapter.handle(encoded(message), authorization="trusted", headers=headers)
    assert status == 200 and decode(raw)["result"]["isError"] is True
    headers["Mcp-Param-Path"] = "foreign.py"
    assert adapter.handle(encoded(message), authorization="trusted", headers=headers)[0] == 400


@pytest.mark.parametrize("field,value", [("resultType", {}), ("resultType", []), ("status", []), ("status", {})])
def test_unhashable_provider_tags_raise_protocol_error_without_escaping(tmp_path, field, value):
    gateway, context, transport, *_ = fixture(tmp_path, tasks=True)
    transport.response = {"resultType": "task", "taskId": "remote", "status": "working",
        "createdAt": "2026-10-03T20:00:00Z", "lastUpdatedAt": "2026-10-03T20:00:01Z", "ttlMs": 0}
    transport.response[field] = value
    with pytest.raises(GatewayError):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")


def operation_key(context, operation="op"):
    return hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id,
                   "operation_key": operation})


def tool_request(context, tool="read", arguments=None, operation="op", *, tasks=False):
    message = request_message(context, "tools/call", {"name": "local." + tool,
        "arguments": {"path": "source.py"} if arguments is None else arguments}, "request", tasks=tasks)
    message["params"]["_meta"]["org.herdr/operation"] = operation
    return message


@pytest.mark.parametrize("failure", ["transport", "output_validation"])
def test_post_send_mutation_outage_requires_reconciliation_without_retry(tmp_path, monkeypatch, failure):
    import herdr.mcp as module
    if failure == "output_validation":
        monkeypatch.setitem(WRITE, "outputSchema", {"type": "object"})
    gateway, context, transport, *_ = fixture(tmp_path, tools=("code_write",))
    original_request = transport.request
    def request(message, **kwargs):
        if message["method"] == "tools/call" and failure == "transport":
            transport.calls.append((message, kwargs))
            raise GatewayUnavailable("deadline after provider accepted mutation")
        return original_request(message, **kwargs)
    transport.request = request
    original_validate = module.validate_schema
    def validate(schema, instance=None, **kwargs):
        if failure == "output_validation" and schema == WRITE["outputSchema"] and not kwargs.get("check_only"):
            raise GatewayUnavailable("bounded output validator timed out")
        return original_validate(schema, instance, **kwargs)
    monkeypatch.setattr(module, "validate_schema", validate)
    adapter = ServerAdapter(gateway, lambda _: context, origins=())
    message = tool_request(context, "write", {"value": "write once"})
    for _ in range(2):
        status, raw = adapter.handle(encoded(message), authorization="trusted")
        assert status == 502
        assert decode(raw)["error"]["data"] == {"retryable": False, "reconcileRequired": True}
    assert len(semantic_calls(transport)) == 1
    assert gateway.ledger.get(operation_key(context))["state"] == "delivery_uncertain"


@pytest.mark.parametrize("legacy_state,tool", [("prepared", "read"), ("prepared", "write"),
                                              ("delivery_uncertain", "read")])
@pytest.mark.parametrize("headers", [False, True])
def test_legacy_eligible_rows_persist_validation_plan_before_transmission(tmp_path, legacy_state, tool, headers):
    gateway, context, transport, clock, client, _ = fixture(tmp_path,
        tools=("code_read" if tool == "read" else "code_write",), tasks=True)
    args = {"path": "source.py"} if tool == "read" else {"value": "result"}
    params = {"name": tool, "arguments": args}
    key = operation_key(context)
    request_hash = hashed({"server": "local", "method": "tools/call", "params": params})
    gateway.ledger.reserve(key, context, request_hash, "local", clock(), "tools/call", tool)
    if legacy_state == "delivery_uncertain":
        gateway.ledger.sending(key, context, clock(), 5)
    assert gateway.ledger.get(key)["validation_plan_json"] is None
    # A real restart preserves the migrated NULL plan; no current-process cache is authority.
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    fresh = ClientAdapter(client.server, transport, ledger, clock=clock)
    gateway = McpGateway(ledger, gateway.registry, (fresh,), authority=gateway.authority,
        runtime_states=gateway.runtime_states, argument_authority=gateway.argument_authority,
        argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    original = transport.request
    def request(message, **kwargs):
        if message["method"] == "tools/call":
            plan = ledger.get(key)["validation_plan_json"]
            assert plan is not None
            assert decode(plan.encode())["definition_hash"] == hashed(READ if tool == "read" else WRITE)
        return original(message, **kwargs)
    transport.request = request
    transport.task = True
    message = tool_request(context, tool, args, tasks=True)
    routing = {"MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/call", "Mcp-Name": "local." + tool}
    if tool == "read":
        routing["Mcp-Param-Path"] = "source.py"
    status, raw = ServerAdapter(gateway, lambda _: context, origins=()).handle(
        encoded(message), authorization="trusted", headers=routing if headers else None)
    assert status == 200, decode(raw)
    assert ledger.get(key)["state"] == "remote_running"
    clock.value += 2
    transport.poll_status = "completed"
    assert gateway.poll(context, "op").state == "observed_complete"
    assert len([x for x in semantic_calls(transport) if x[0]["method"] == "tools/call"]) == 1


@pytest.mark.parametrize("args", [[], "path", None, 1, True])
@pytest.mark.parametrize("headers", [False, True])
def test_tool_arguments_are_objects_even_with_permissive_approved_schema(tmp_path, monkeypatch, args, headers):
    monkeypatch.setitem(READ, "inputSchema", {})
    gateway, context, transport, *_ = fixture(tmp_path)
    gateway.argument_authority = lambda *a: pytest.fail("non-object arguments must not reach host authorization")
    gateway.clients["local"].expires_at = 0
    transport.calls.clear()
    message = tool_request(context)
    message["params"]["arguments"] = args
    routing = {"MCP-Protocol-Version": PROTOCOL, "Mcp-Method": "tools/call", "Mcp-Name": "local.read"}
    status, raw = ServerAdapter(gateway, lambda _: context, origins=()).handle(
        encoded(message), authorization="trusted", headers=routing if headers else None)
    assert status == 400 and decode(raw)["error"]["message"] == "invalid_request"
    assert transport.calls == []


def test_removed_provider_task_poll_is_a_bounded_policy_denial_after_restart(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    restored = McpGateway(ledger, gateway.registry, (), authority=gateway.authority,
        runtime_states=gateway.runtime_states, argument_authority=gateway.argument_authority,
        argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    message = request_message(context, "tasks/get", {"taskId": operation_key(context)}, "poll", tasks=True)
    status, raw = ServerAdapter(restored, lambda _: context, origins=()).handle(encoded(message), authorization="trusted")
    assert status == 403 and decode(raw)["error"]["message"] == "policy_denied"
    assert len(semantic_calls(transport)) == 1


@pytest.mark.parametrize("number", [b"1e10000", b"-1e10000", b"NaN", b"Infinity"])
def test_nonfinite_json_rejected_in_ignored_metadata_before_dispatch(tmp_path, number):
    gateway, context, transport, *_ = fixture(tmp_path)
    message = request_message(context, "tools/list", {}, "request")
    message["params"]["_meta"]["overflow"] = 0
    raw = encoded(message).replace(b'"overflow":0', b'"overflow":' + number)
    status, response = ServerAdapter(gateway, lambda _: context, origins=()).handle(raw, authorization="trusted")
    assert status == 400 and decode(response)["error"]["message"] == "invalid_request"
    assert not semantic_calls(transport)
    with pytest.raises(GatewayError):
        decode(b'{"value":' + number + b'}')


def test_provider_uses_supported_data_values_in_node_scope(tmp_path):
    gateway, context, transport, clock, client, authority = fixture(tmp_path)
    data = replace(client.server.data_policy, regions=("eu-west", "us-east"),
                   data_classes=(DataClass.PUBLIC, DataClass.INTERNAL))
    client.server = replace(client.server, data_policy=data)
    gateway.registry.reload(client.registry_snapshot())
    scope = replace(context.toolset.scope, regions=("us-east",), data_classes=(DataClass.INTERNAL,))
    context = replace(context, toolset=replace(context.toolset, registry_hash=gateway.registry.snapshot.hash,
        scope=scope), parent_scope=scope, consumer_scope=scope)
    authority["context_hash"] = context.hash
    seen = []
    original = gateway.runtime_states
    def states(req, provider):
        seen.append((req.region, req.data_class))
        return original(req, provider)
    gateway = McpGateway(gateway.ledger, gateway.registry, (client,), authority=gateway.authority,
        runtime_states=states, argument_authority=gateway.argument_authority,
        argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    assert gateway.call(context, "local", "read", {"path": "source.py"}, "op").state == "observed_complete"
    assert seen and set(seen) == {("us-east", DataClass.INTERNAL)}


@pytest.mark.parametrize("annotations", [None, [], "invalid", {"readOnlyHint": 1}, {"title": []}])
def test_malformed_pinned_annotations_fail_during_discovery(tmp_path, monkeypatch, annotations):
    monkeypatch.setitem(READ, "annotations", annotations)
    with pytest.raises(GatewayError, match="annotation"):
        fixture(tmp_path)


@pytest.mark.parametrize("callback", ["runtime_observations", "argument_policy_before_send"])
def test_registry_reload_during_admission_cannot_send_under_stale_context(tmp_path, callback):
    gateway, context, transport, *_ = fixture(tmp_path)
    snapshot = gateway.registry.snapshot
    changed = replace(snapshot, providers=tuple(replace(x, version=x.version + "-changed") for x in snapshot.providers))
    if callback == "runtime_observations":
        original = gateway.runtime_states
        def states(*args):
            result = original(*args)
            gateway.registry.reload(changed)
            return result
        gateway.runtime_states = states
    else:
        original = gateway.argument_authority
        count = 0
        def arguments(*args):
            nonlocal count
            count += 1
            if count == 2:
                gateway.registry.reload(changed)
            return original(*args)
        gateway.argument_authority = arguments
    with pytest.raises(PolicyDenied, match="replan"):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert not semantic_calls(transport)
    row = gateway.ledger.get(operation_key(context))
    assert row is None or row["deliveries"] == 0


@pytest.mark.parametrize("restart", [False, True])
def test_exhausted_read_retry_reports_nonretryable_outcome_without_provider_contact(tmp_path, restart):
    gateway, context, transport, clock, client, _ = fixture(tmp_path, retries=0)
    transport.fail = True
    with pytest.raises(DeliveryUncertain, match="retry budget exhausted"):
        gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    assert len(semantic_calls(transport)) == 1
    if restart:
        gateway.ledger.close()
        ledger = CallLedger(tmp_path / "protected")
        client = ClientAdapter(client.server, transport, ledger, clock=clock)
        gateway = McpGateway(ledger, gateway.registry, (client,), authority=gateway.authority,
            runtime_states=lambda *a: pytest.fail("exhausted operation must not seek a new route"),
            argument_authority=gateway.argument_authority, argument_policy_hash=ARGUMENT_POLICY, clock=clock)
    transport.calls.clear()
    status, raw = ServerAdapter(gateway, lambda _: context, origins=()).handle(
        encoded(tool_request(context)), authorization="trusted")
    assert status == 502 and decode(raw)["error"]["message"] == "read_retry_exhausted"
    assert decode(raw)["error"]["data"] == {"retryable": False, "reconcileRequired": True}
    assert transport.calls == []


def test_discovery_failures_open_persisted_circuit_and_success_resets_streak(tmp_path):
    gateway, context, transport, clock, client, _ = fixture(tmp_path)
    original = transport.request
    def unavailable(message, **kwargs):
        transport.calls.append((message, kwargs))
        raise GatewayUnavailable("discovery transport deadline")
    transport.request = unavailable
    for _ in range(3):
        with pytest.raises(GatewayUnavailable):
            client.discover(context, clock())
    assert len(transport.calls) == 4  # fixture discovery + three failures
    gateway.ledger.close()
    ledger = CallLedger(tmp_path / "protected")
    fresh = ClientAdapter(client.server, transport, ledger, clock=clock)
    with pytest.raises(GatewayUnavailable, match="circuit"):
        fresh.discover(context, clock())
    assert len(transport.calls) == 4
    clock.value += 61
    transport.request = original
    fresh.discover(context, clock())
    assert ledger.db.execute("SELECT failures FROM health WHERE server='local'").fetchone() is None
    transport.request = unavailable
    for _ in range(2):
        with pytest.raises(GatewayUnavailable):
            fresh.discover(context, clock())
    assert ledger.health("local", clock())
    transport.request = original
    fresh.discover(context, clock())
    assert ledger.db.execute("SELECT failures FROM health WHERE server='local'").fetchone() is None


def test_schema_helper_respects_existing_lower_hard_limits():
    import subprocess
    import sys
    code = """import resource
resource.setrlimit(resource.RLIMIT_CPU, (1, 1))
resource.setrlimit(resource.RLIMIT_AS, (128_000_000, 128_000_000))
from herdr.mcp_schema import main
raise SystemExit(main())
"""
    result = subprocess.run([sys.executable, "-c", code], input=encoded(
        {"schema": {"type": "object"}, "instance": {}, "check_only": False}),
        capture_output=True, timeout=5)
    assert result.returncode == 0 and result.stdout == b"valid", result.stderr


@pytest.mark.parametrize("failure", [ValueError, OSError, MemoryError])
def test_schema_helper_setup_failure_is_availability_failure(monkeypatch, failure):
    import resource
    from herdr import mcp_schema
    def fail(*args):
        raise failure("runtime setup constraint")
    monkeypatch.setattr(resource, "setrlimit", fail)
    assert mcp_schema.main() == 78


@pytest.mark.parametrize("returncode", [-9, 78, 2])
def test_schema_helper_abnormal_exit_is_not_permanent_schema_rejection(monkeypatch, returncode):
    import subprocess
    import herdr.mcp as module
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **k:
        subprocess.CompletedProcess([], returncode, b"", b"bounded runtime constraint"))
    with pytest.raises(GatewayUnavailable):
        validate_schema({"type": "object"}, {})

def test_exhausted_remote_poll_budget_requires_reconciliation(tmp_path):
    gateway, context, transport, clock, *_ = fixture(tmp_path, tasks=True)
    transport.task = True
    gateway.call(context, "local", "read", {"path": "source.py"}, "op")
    gateway.ledger.db.execute("UPDATE calls SET polls=32")
    clock.value += 2
    message = request_message(context, "tasks/get", {"taskId": operation_key(context)}, "poll", tasks=True)
    status, raw = ServerAdapter(gateway, lambda _: context, origins=()).handle(encoded(message), authorization="trusted")
    assert status == 502 and decode(raw)["error"]["data"] == {"retryable": False, "reconcileRequired": True}
    assert len(semantic_calls(transport)) == 1
