"""Pure effect-IO tests. No SDK import/init, socket, kernel, provider or service.

Real original typed admission/scheduler/work/budget/guard/Unix frame decisions
run against finite synthetic kernel observations and isolated disk journals.
This is not a physical confinement or complete observed-seal acceptance suite.
"""
import ast
from contextlib import contextmanager
from dataclasses import asdict, replace
from datetime import UTC, datetime
import copy
import hashlib
import importlib
import json
import os
from pathlib import Path, PurePosixPath
import reference_support
import queue
import stat
import struct
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor  # Cold standard-library import before IO adapters.

HERE = Path(__file__).resolve().parents[2]
CORE = HERE.parents[1] / ""
DELTA = HERE.parent / "reference/default-runtime-02/reference/delta"
OVERLAY = HERE
sys.path[:0] = [str(OVERLAY), str(CORE), str(CORE / "agent-stack/bin")]
if sys.platform == "win32":
    os.register_at_fork = lambda **kwargs: None  # No process/fork effects in this suite.
    fcntl = types.ModuleType("fcntl")
    fcntl.LOCK_EX, fcntl.LOCK_UN, fcntl.LOCK_NB = 1, 2, 4
    fcntl.flock = lambda *args: None  # Only inert sequential fixture filesystem IO.
    sys.modules["fcntl"] = fcntl
import importlib.util
spec = importlib.util.spec_from_file_location("herdr", CORE / "herdr/__init__.py",
    submodule_search_locations=[str(OVERLAY / "herdr"), str(CORE / "herdr")])
herdr = importlib.util.module_from_spec(spec)
sys.modules["herdr"] = herdr
spec.loader.exec_module(herdr)
import offline_case
offline_case.__path__.insert(0, str(OVERLAY / "offline_case"))
from herdr import security
from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
from herdr.security import InvocationIdentity, SecurityGrant, ProviderRoute, RuntimeAssurance, ProcessPolicy, NetworkAccess
from herdr.scheduler import AuditLog, DynamicChildScheduler, CanonicalParentAdmission, ChildProposal, DenyDecision
from herdr.taskgraph import TaskGraph
from herdr.admission import AdmissionControl, AuditLog as AdmissionAuditLog, AgentIdentity, TaskGraphSpec, ResourceUsage
from herdr.consumer_policies import policy_for_profile
from herdr.work_budget import BudgetAllocation, BudgetLimits, StopScope, BudgetBlocked
from herdr.work_contract_host import HostWorkContractFactory, WorkInvocationGuard
from herdr.work_cycle import WorkPlan, WorkCycle, WorkPhase, FileScope, ValidationCheck, CheckResult
from herdr.check_runner import CheckEnvironment
from herdr.evidence import canonical, digest
from herdr.canonical_case_runtime import CanonicalCaseRuntime, dispatch_with, LiveLaunch
from herdr.canonical_case_claim import claimed_root_identity, task_session_identity
from offline_case.case import NONCE, BUDGET, Denied, canonical as offline_canonical
from offline_case.root_effects import RootEffectPump, validate_effect
from offline_case.admission import NativeAdmission
from herdr.canonical_case_probe import probe_message, probe_response, verify_probe_receipt


class StatView:
    def __init__(self, value): self.value = value
    def __getattr__(self, name): return getattr(self.value, name)
    @property
    def st_uid(self): return 0  # Synthetic root-owned custody; no host ownership mutation.
    @property
    def st_mode(self): return stat.S_IFMT(self.value.st_mode) | (0o700 if stat.S_ISDIR(self.value.st_mode) else 0o600)


class PrivatePath(type(Path())):
    """Finite POSIX custody metadata for Windows-only inert filesystem tests."""
    def stat(self, **kwargs): return StatView(super().stat(**kwargs))
    def lstat(self): return self.stat(follow_symlinks=False)


class InertOS:
    def __init__(self): self.virtual = {}; self.counter = -10
    def __getattr__(self, name):
        if name in {"O_NOFOLLOW", "O_CLOEXEC", "O_DIRECTORY", "O_PATH", "O_NONBLOCK"}: return getattr(os, name, 0)
        if name in {"geteuid", "getuid", "getegid", "getgid"}: return lambda: 0
        return getattr(os, name)
    def open(self, name, flags, mode=0o777, **kwargs):
        spelling = str(name).replace("\\", "/")
        if spelling in {"/proc/self/attr/current", "/proc/self/cgroup"}:
            raw = (b"herdr-offline-controller-03414499dd0d1986 (enforce)" if spelling.endswith("current") else
                   b"0::/system.slice/herdr-offline-host-03414499dd0d1986.service\n")
            self.counter -= 1; self.virtual[self.counter] = raw; return self.counter
        if Path(name).is_dir():
            self.counter -= 1; self.virtual[self.counter] = b""; return self.counter
        return os.open(name, flags, mode, **kwargs)
    def read(self, fd, size):
        if fd in self.virtual:
            raw, self.virtual[fd] = self.virtual[fd][:size], self.virtual[fd][size:]
            return raw
        return os.read(fd, size)
    def close(self, fd):
        if fd in self.virtual: self.virtual.pop(fd); return
        return os.close(fd)
    def fsync(self, fd):
        if fd in self.virtual: return
        return os.fsync(fd)
    def fstat(self, fd): return StatView(os.fstat(fd))


class DiskAudit(AuditLog):
    """Only directory fsync is synthetic on Windows; events/replay are original."""
    def __init__(self, path): super().__init__(PrivatePath(path))
    def flush(self, **kwargs):
        with self._lock:
            events, self._buffer = self._buffer, []
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf8") as handle:
                for event in events: handle.write(json.dumps(event, sort_keys=True) + "\n")
                handle.flush(); os.fsync(handle.fileno())


class DiskJournal:
    """Finite original-attempt receipt filesystem boundary, never an authority."""
    def __init__(self, root): self.root = Path(root); self.root.mkdir(parents=True, exist_ok=True)
    def publish_once(self, event, value):
        path = self.root / (digest(event) + ".json")
        with path.open("xb") as handle:
            handle.write(canonical({"event": event, "value": value})); handle.flush(); os.fsync(handle.fileno())
    def read_once(self, event):
        value = json.loads((self.root / (digest(event) + ".json")).read_bytes())
        if value["event"] != event: raise ValueError("foreign fixture receipt")
        return value["value"]


def graph_for(identity):
    return TaskGraph.parse_planner_output({"envelope": {"issue": "Bbambaaamm/herdr#0", "spec_hash": "a" * 64,
        "graph_version": "1.1.0", "created_at": "2026-11-04T00:00:00+00:00", "planner": "inert-fixture",
        "max_nodes": 2, "max_depth": 2, "max_fanout": 1, "policy_profile": "herdr-core"}, "nodes": [{
        "id": identity.task_id, "parent_id": None, "type": "task", "role": "reader", "objective": "Inert composed case",
        "inputs": [{"artifact_ref": "fixture"}], "expected_outputs": [{"kind": "result"}], "dependencies": [],
        "priority": 1, "resource_class": "small", "model_policy": {"model": "meituan/longcat-2.0:free", "fallback_model": None},
        "tools": ["read_file"], "permissions": ["repo:read"], "timeout_seconds": 300, "max_attempts": 1}]})


def canonical_scheduler(directory, identity):
    scheduler = DynamicChildScheduler(audit_log=DiskAudit(directory / "scheduler.jsonl"), clock=lambda: 100)
    graph = graph_for(identity)
    scheduler.submit(graph, repo="Bbambaaamm/herdr", issue="0")
    parent = CanonicalParentAdmission(graph, graph.graph_hash(), identity, "root-idempotency", "Bbambaaamm/herdr", "0", "root-pane", "root-marker")
    scheduler.register_external_parent_attempt(task_id=identity.task_id, run_token=identity.run_token,
        idempotency_key=parent.idempotency_key, agent_name=identity.agent_id, pane_id=parent.pane_id,
        marker=parent.marker, repo=parent.repo, issue=parent.issue, role="reader", tools=("read_file",),
        permissions=("repo:read",), policy_profile="herdr-core", canonical_parent=parent)
    proposal = ChildProposal("reader", ("read_file",), "reader", ("read_file",), "One inert child",
        "meituan/longcat-2.0:free", None, ("repo:read",), ("repo:read",))
    child = scheduler.spawn_child(identity.task_id, proposal, delegation_key="only-child", parent_run_token=identity.run_token)
    if isinstance(child, DenyDecision): raise AssertionError(child)
    lease, = scheduler.dispatch(task_ids={child.id}, managed_start=True)
    rec = scheduler.record_for(child.id)
    from herdr.child_evidence import child_identity
    return scheduler, child_identity(rec), lease


class Wire:
    """In-memory AF_UNIX stream effects; no actual socket is constructed."""
    def __init__(self): self.incoming = queue.Queue(); self.outgoing = None; self.buffer = b""; self.closed = False
    def connect(self, _path): pass
    def settimeout(self, _seconds): pass
    def getsockopt(self, *args): return struct.pack("3i", 501, 0, 0)
    def sendall(self, raw): self.outgoing.put(bytes(raw))
    def recv(self, maximum, *args):
        peek = bool(args)
        while not self.buffer:
            self.buffer = self.incoming.get(timeout=3)
            if self.buffer is None: return b""
        raw = self.buffer[:maximum]
        if not peek: self.buffer = self.buffer[len(raw):]
        return raw
    def close(self): self.closed = True
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


class Fabric:
    def __init__(self, owner): self.owner = owner; self.threads = []; self.errors = []; self.exchanges = 0
    def socket(self, *args):
        left, right = Wire(), Wire()
        left.outgoing, right.outgoing = right.incoming, left.incoming
        self.exchanges += 1
        from herdr.work_authority import dispatch_work_connection
        def serve():
            try: dispatch_work_connection(self.owner, right)
            except BaseException as error: self.errors.append(error); left.incoming.put(None)
        thread = threading.Thread(target=serve); thread.start(); self.threads.append(thread)
        return left
    def check(self):
        for thread in self.threads: thread.join(3)
        assert all(not thread.is_alive() for thread in self.threads), "inert framing deadlock"
        assert not self.errors, self.errors


class ComposedTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="canonical-runtime-inert-")
        self.root = PrivatePath(self.temp.name)
        self.os = InertOS()
        import herdr.work_budget as budget
        import herdr.host_model_transport as transport
        import herdr.work_budget_configuration as bc
        import herdr.work_configuration as config
        import herdr.work_authority as wa
        import herdr.check_runner as cr
        self.stack = []
        def adapt(target, name, value):
            context = patch.object(target, name, value); context.start(); self.stack.append(context)
        for module in (budget, transport, wa): adapt(module, "os", self.os)
        adapt(transport, "Path", PrivatePath)
        adapt(bc, "Path", PrivatePath)
        adapt(cr, "Path", PurePosixPath)  # Pure path-schema validation only.
        adapt(config, "_private_directory", lambda value, **kwargs: PrivatePath(value).mkdir(parents=True, exist_ok=True))
        adapt(config, "_audit", lambda value: DiskAudit(value))
        from herdr.bootstrap_authority import PeerProcess
        adapt(wa, "inspect_peer", lambda pid: PeerProcess(pid, 500, 9001, 11, 22, ("/proc/self/fd/17", "-I", "-S", "/proc/self/fd/18")))
        adapt(transport, "_credential", lambda *args: (_ for _ in ()).throw(AssertionError("credential read forbidden")))
        adapt(transport, "_perform_http", lambda *args: (_ for _ in ()).throw(AssertionError("HTTP forbidden")))
        self.adapt = adapt
        self.identity = InvocationIdentity("github:Bbambaaamm/herdr", "root-agent", "operator", "coordinator:operator", "root-" + NONCE, "root-run", 7)
        self.scheduler, self.child_identity, self.lease = canonical_scheduler(self.root, self.identity)

    def tearDown(self):
        for context in reversed(self.stack): context.stop()
        self.temp.cleanup()

    def work(self, identity, role, parent_allocation=None):
        from herdr.work_budget_configuration import bind_budget
        from herdr import host_model_transport as transport
        workspace = self.root / role / "workspace"; workspace.mkdir(parents=True)
        scope = CapabilityScope(providers=("nous",), capabilities=(), executors=("hermes-runtime",), tools=(),
            permissions=("repo:read",), regions=("fixture",), data_classes=(DataClass.INTERNAL,),
            input_modalities=("text",), output_modalities=("text",), max_cost_microusd=0, max_context_tokens=65536,
            max_egress=Egress.NONE, max_retention=Retention.ZERO, training=Training.EXCLUDED)
        route = ProviderRoute("nous", transport.ENDPOINT, "chat_completions", ("fixture",),
            (DataClass.INTERNAL,), Egress.NONE, Retention.ZERO, Training.EXCLUDED, ("pool:nous:fixture",))
        grant = SecurityGrant(workspace_root=str(workspace), grant_id="inert-" + role, identity=identity, scope=scope,
            process=ProcessPolicy(False, (), NetworkAccess.NONE),
            runtime_assurance=RuntimeAssurance(True, "a" * 64, NetworkAccess.NONE, (), True),
            tool_rules=(), provider_routes=(route,), credential_refs=("pool:nous:fixture",), approvals=(), approval_required_for=(),
            issued_at="2026-01-01T00:00:00+00:00", expires_at="2030-01-01T00:00:00+00:00")
        environment = CheckEnvironment("inert-io-1", (("/usr/bin/python3", "d" * 64),), ("/usr/bin/python3",))
        limits = BudgetLimits(1000000, 1000000, 16, 1000000, 0, 2, 0, 1, 1)
        allocation = BudgetAllocation(digest(role), identity.consumer, digest(role + "-work"), digest("lineage"),
            digest("protected-fixture-authorization"), limits, None if parent_allocation is None else parent_allocation.allocation_id)
        quote = {"provider": "nous", "model": transport._FIXTURE_MODEL, "api_mode": "chat_completions",
            "base_url": transport.ENDPOINT, "max_request_bytes": 4096, "max_output_tokens": 100,
            "max_tokens": 5000, "max_cost_microusd": 0, "max_work_ms": 30000}
        plan = WorkPlan(identity, "spec-1", "a" * 64, "policy-1", "b" * 40, (FileScope("result.py"),),
            ("behavior",), (ValidationCheck("tests", (sys.executable, "result.py"), ("behavior",)),),
            grant_sha256=grant.hash, environment_sha256=environment.hash, budget_reference=allocation.hash)
        log = DiskAudit(self.root / "private" / role / "host" / "events.jsonl")
        factory = object.__new__(HostWorkContractFactory)
        factory.environment, factory.storage, factory.audit_log = environment, self.root / "private" / role / "host", log
        factory.check_storage = factory.storage; factory.commit_runtime_storage = None; factory._runtime_scratch = ()
        factory._lock = threading.RLock(); factory.cycles = {}; factory.allocations = {}; factory.handoffs = {}
        def git(args):
            if args == ["rev-parse", "HEAD"]: return plan.base_sha
            if args == ["status", "--porcelain", "-z"]: return ""
            raise AssertionError("unlisted inert Git observation")
        factory.git = git
        factory.local_commit_policy = None
        ancestors = [] if parent_allocation is None else [asdict(parent_allocation)]
        raw = {"version": 1, "allocation": asdict(allocation), "ancestors": ancestors, "model_quotes": [quote]}
        bind_budget(factory, raw, storage=self.root / "private")
        cycle = WorkCycle(plan, workspace, log, git=git, budget_authority=factory.budget_authority)
        cycle._snapshot = lambda: {"result.py": {"sha256": "c" * 64, "mode": "100644"}}
        def checked(check, _root, selected, tree):
            return CheckResult(check.id, selected.hash, selected.environment_sha256, tree, 0, "e" * 64, False, 1, "f" * 64)
        cycle.start(checked)
        factory.cycles[digest(identity.to_json())] = (cycle, None)
        factory.allocations[digest(identity.to_json())] = allocation
        definition = {"spec_version": "offline-arithmetic-1", "policy_version": "offline-clean-1",
            "criteria": ["arithmetic"], "discovery_files": ["arithmetic.py", "check_arithmetic.py"],
            "files": [{"path": "arithmetic.py", "subtree": False, "symbols": []}]}
        factory.host_task = {"id": identity.task_id, "run_token": identity.run_token, "fencing_token": identity.fencing_token,
            "parent_agent_id": identity.parent_agent_id, "derived_parent_admission_sha256": "9" * 64}
        factory.host_admission = {"definition": definition}
        class Mounted:
            def verify_mounted(self, pid, sealed):
                if pid != 501 or sealed != "inert-original-bundle": raise ValueError("wrong observed mount binding")
        from herdr.bootstrap_authority import BootstrapContinuation
        continuation = BootstrapContinuation(identity.to_json(), 501, 9001, "1" * 64, "2" * 64,
            "3" * 64, "4" * 64, "5" * 64, 11, 22)
        launch = types.SimpleNamespace(identity=identity, grant=grant, _published_bootstrap_receipt=continuation,
            sealed="inert-original-bundle", mount=Mounted(), private_profile_snapshot=None)
        owner = types.SimpleNamespace(launch=launch, work_authority=factory.authorize_invocation,
            work_verify=factory.verify_request, work_budget=factory.budget_effect, work_observe=factory.observe_sdk)
        launch.mount.bootstrap = owner
        selector = {"nonce": NONCE, "host_label": "herdr-offline-controller-03414499dd0d1986",
            "task_id": self.identity.task_id, "run_token": self.identity.run_token, "fencing_token": self.identity.fencing_token}
        import herdr.host_configuration as hc
        def read_config(path):
            return {"storage": str(self.root / "private")} if Path(path).name == "host-policy.json" else copy.deepcopy(selector)
        self.adapt(hc, "_read_configuration", read_config)
        return factory, launch, owner, allocation, quote

    def ingress(self, identity, role, parent=None):
        import herdr.work_authority as wa
        from herdr.security import ProviderRequest
        factory, launch, owner, allocation, quote = self.work(identity, role, parent)
        self.assertTrue(factory.authorize_invocation(identity, launch.grant.hash, kind="provider"))
        fabric = Fabric(owner)
        socket_effects = types.SimpleNamespace(socket=fabric.socket, AF_UNIX=1, SOCK_STREAM=1,
            SOL_SOCKET=1, SO_PEERCRED=17, MSG_PEEK=2)
        self.adapt(wa, "socket", socket_effects)
        original_denial = wa._observe_authenticated_denial
        def capture_denial(*args):
            fabric.errors.append(args[-1])
            return original_denial(*args)
        self.adapt(wa, "_observe_authenticated_denial", capture_denial)
        client = wa.WorkAuthorityClient()
        guard = WorkInvocationGuard(launch.grant, work_authority=client)
        guard.authorize_provider(ProviderRequest("nous", "fixture", DataClass.INTERNAL, Egress.NONE, Retention.ZERO, Training.EXCLUDED, "pool:nous:fixture"))
        payload = {"model": quote["model"], "messages": [{"role": "user", "content": probe_message(identity, launch.grant.hash, role)}], "max_tokens": 50}
        body = canonical(payload); request_id = role + ":sdk:1"
        receipt = client.effect(identity, launch.grant.hash, "start", {"request_id": request_id,
            **{k: quote[k] for k in ("provider", "model", "api_mode", "base_url")},
            "request_sha256": hashlib.sha256(body).hexdigest(), "request_bytes": len(body), "output_tokens": 50})
        try: answer = client.model_transport(identity, launch.grant.hash, request_id, receipt, payload)
        except BaseException:
            fabric.check()
            raise
        self.assertEqual(answer["body"]["choices"][0]["message"]["content"], "guarded-ingress-ok")
        # Replay same exact consumed operation returns original response, no new fixture counter.
        self.assertEqual(client.model_transport(identity, launch.grant.hash, request_id, receipt, payload), answer)
        client.effect(identity, launch.grant.hash, "returned", {"operation_id": receipt["operation_id"]})
        fabric.check()
        proof = verify_probe_receipt(factory, launch, role=role)
        self.assertEqual(proof["budget_unknown_measurements"], ["work_ms", "tokens", "cost_microusd"])
        self.assertEqual(factory.budget_authority.snapshot(allocation.allocation_id)["inflight"], 0)
        return factory, launch, allocation, proof

    def test_actual_root_and_canonical_child_guarded_unix_ingress_share_original_lineage(self):
        root, _, allocation, root_proof = self.ingress(self.identity, "root")
        child, _, _, child_proof = self.ingress(self.child_identity, "child", allocation)
        self.assertNotEqual(root_proof["identity"], child_proof["identity"])
        self.assertNotEqual(self.identity.run_token, self.child_identity.run_token)
        self.assertNotEqual(self.identity.fencing_token, self.child_identity.fencing_token)
        self.assertEqual(len(list((self.root / "private" / ("offline-fixture-" + NONCE)).glob("*.json"))), 2)
        self.assertEqual(root_proof["external_http"], child_proof["external_http"])

    def test_operator_run_consumes_actual_root_child_reply_then_guarded_fixture(self):
        """Wire the real run phase replies into the operator and original work port."""
        runtime, parts, journal, effects_io, binding = self.runtime()
        journal.publish_once("root-prepared", {"binding": binding, "sdk_imported": False,
            "setup_fds_closed": True, "setup_paths_hidden": True})
        journal.publish_once("case-cgroup", {"binding": binding, "identity": [11, 22]})
        self.identity = parts["identity"]
        _, child_identity, _ = canonical_scheduler(self.root / "contract-child", parts["identity"])
        root = LiveLaunch("root", parts["identity"], object(), "root-pane", "root-marker",
                          self.root, self.root / "root-result", self.root / "root-policy")
        child = LiveLaunch("child", child_identity, object(), "child-pane", "child-marker",
                           self.root, self.root / "child-result", self.root / "child-policy")
        runtime.live["root"] = root
        state = {"started": [], "sealed": [], "proofs": [], "parent": None}
        def start(entry): state["started"].append(entry.role)
        def exercise(entry):
            factory, _, allocation, proof = self.ingress(entry.identity, entry.role, state["parent"])
            if entry.role == "root": state["parent"] = allocation
            state["proofs"].append(proof)
        runtime._start_sdk = start
        runtime._prepare_child = lambda _: child
        runtime._ticket = lambda _: {"effect": "child-ticket"}
        runtime._seal = lambda entry: state["sealed"].append(entry.role)
        runtime._exercise_ingress = exercise
        effects_io.pane_pid = lambda pane: 501
        effects_io.host_reference = lambda entry: entry.identity.run_token
        effects_io.child_parent_source_request = lambda entry, bound: {
            "kind": "VERIFY_NATIVE_SOURCE", "role": entry.role, "binding": bound,
            "identity": entry.identity.to_json()}
        class RuntimeWire:
            def __init__(self): self.phases = []
            def exchange(self, packet):
                self.phases.append(packet["arguments"]["phase"])
                value = runtime.run(packet["arguments"]["budget"], packet["arguments"]["phase"])
                return {"schema": 1, "request_sha256": packet["request_sha256"], "value": value}
        wire = RuntimeWire()
        client = NativeAdmission({"build_sha256": binding["build_sha256"],
            "task_id": parts["identity"].task_id, "run_token": parts["identity"].run_token,
            "fencing_token": parts["identity"].fencing_token}, wire)
        effects = []
        with patch.object(client, "_pump", return_value=types.SimpleNamespace(
                perform=lambda effect, bound: effects.append((effect, bound)))):
            result = client.run(binding, BUDGET)
        self.assertEqual(wire.phases, ["root", "child-ticket", "child-seal", "ingress"])
        self.assertEqual(state["started"], ["root", "child"])
        self.assertEqual(state["sealed"], ["child"])
        self.assertEqual(len(effects), 2)
        self.assertEqual(effects[0][0]["request"]["kind"], "VERIFY_NATIVE_SOURCE")
        self.assertEqual(result["outcome"], "SDK_GUARDED_FIXTURE_INGRESS_ONLY")
        self.assertEqual(journal.read_once("case-finished"), result)
        self.assertEqual(journal.read_once("case-run-intent"), {"binding": binding})
        self.assertEqual([proof["identity"] for proof in state["proofs"]],
                         [parts["identity"].to_json(), child_identity.to_json()])
        self.assertEqual(len(list((self.root / "private" / ("offline-fixture-" + NONCE)).glob("*.json"))), 2)
        self.assertEqual(state["proofs"][0]["external_http"], 0)
        self.assertEqual(state["proofs"][1]["external_http"], 0)
        for proof in state["proofs"]:
            self.assertEqual(proof["synthetic_responses"], 1)
            self.assertEqual(proof["external_model"], 0)
            self.assertEqual(proof["external_cost"], 0)
            self.assertEqual(len(proof["settlement_sha256"]), 64)

    def test_actual_admission_and_named_consumer_deny_foreign_tools_and_pressure(self):
        control = AdmissionControl(audit_log=AdmissionAuditLog(self.root / "admission.jsonl"),
            consumer_policy_hook=policy_for_profile("herdr-core"))
        who = AgentIdentity("reader", "Bbambaaamm/herdr", "0")
        usage = ResourceUsage(cpu=.1, ram=.25, logical_cpus=8, total_ram_bytes=16 * 1024**3, mem_available_bytes=12 * 1024**3)
        self.assertTrue(control.check(who, TaskGraphSpec(1, 1, 0), usage, ("read_file",)))
        self.assertFalse(control.check(who, TaskGraphSpec(1, 1, 0), usage, ("write_file",)))
        self.assertFalse(control.check(who, TaskGraphSpec(1, 1, 0), replace(usage, cpu=1), ("read_file",)))

    def test_original_scoped_budget_stop_blocks_root_and_excludes_other_task(self):
        factory, launch, _, allocation, _ = self.work(self.identity, "root")
        authority = factory.budget_authority
        authority.stop(stop_id=digest("case-stop"), scope=StopScope.TASK, target=self.identity.task_id,
            source="canonical-offline-case", reason_code="offline-case-fenced", resume_condition="no-resume-single-attempt")
        with self.assertRaises(BudgetBlocked): authority.require_active(allocation.allocation_id, self.identity)
        authority.require_active(allocation.allocation_id, replace(self.identity, task_id="unrelated-task"))
        cold = type(authority)(audit_log=DiskAudit(authority.audit_log._path), authorize=authority.authorize)
        with self.assertRaises(BudgetBlocked): cold.require_active(allocation.allocation_id, self.identity)

    def test_actual_child_slot_registry_requires_original_lease_and_exact_fence_on_release(self):
        import herdr.runtime as native_runtime
        self.adapt(native_runtime, "os", self.os)
        registry = native_runtime.AdmissionRegistry(path=self.root / "slots.json")
        control = AdmissionControl(audit_log=AdmissionAuditLog(self.root / "slot-admission.jsonl"),
            consumer_policy_hook=policy_for_profile("herdr-core"))
        who = AgentIdentity("reader", "Bbambaaamm/herdr", "0", "reader", frozenset({"read_file"}))
        usage = ResourceUsage(cpu=.1, ram=.25, logical_cpus=8, total_ram_bytes=16 * 1024**3, mem_available_bytes=12 * 1024**3)
        _, _, lease = canonical_scheduler(self.root / "ordinary", replace(self.identity, task_id="ordinary-parent"))
        registry.reserve(control, who, TaskGraphSpec(2, 2, 1, "ordinary-parent"), usage, ("read_file",), lease, now=100)
        self.assertEqual(registry._read()[0]["fencing_token"], lease.fencing_token)
        registry.release(lease.agent_id, task_id=lease.task_id, fencing_token=lease.fencing_token + 1, now=100)
        self.assertEqual(len(registry._read()), 1)
        registry.release(lease.agent_id, task_id=lease.task_id, fencing_token=lease.fencing_token, now=100)
        self.assertEqual(registry._read(), [])

    def test_generic_case_admission_release_cannot_clear_slot_without_root_closure(self):
        import herdr.runtime as native_runtime
        self.adapt(native_runtime, "os", self.os)
        registry = native_runtime.AdmissionRegistry(path=self.root / "case-slots.json")
        control = AdmissionControl(audit_log=AdmissionAuditLog(self.root / "case-slot-admission.jsonl"),
            consumer_policy_hook=policy_for_profile("herdr-core"))
        who = AgentIdentity("reader", "Bbambaaamm/herdr", "0", "reader", frozenset({"read_file"}))
        usage = ResourceUsage(cpu=.1, ram=.25, logical_cpus=8, total_ram_bytes=16 * 1024**3, mem_available_bytes=12 * 1024**3)
        registry.reserve(control, who, TaskGraphSpec(2, 2, 1, self.identity.task_id), usage, ("read_file",), self.lease, now=100)
        with self.assertRaises(Exception):
            registry.release(self.lease.agent_id, task_id=self.lease.task_id, fencing_token=self.lease.fencing_token, now=100)
        self.assertEqual(len(registry._read()), 1)

    def test_torn_original_model_intent_is_retained_without_second_fixture_or_http(self):
        import herdr.work_authority as wa
        import herdr.host_model_transport as transport
        factory, launch, owner, allocation, quote = self.work(self.identity, "torn")
        fabric = Fabric(owner)
        self.adapt(wa, "socket", types.SimpleNamespace(socket=fabric.socket, AF_UNIX=1, SOCK_STREAM=1,
            SOL_SOCKET=1, SO_PEERCRED=17))
        client = wa.WorkAuthorityClient()
        payload = {"model": quote["model"], "messages": [{"role": "user",
            "content": probe_message(self.identity, launch.grant.hash, "root")}], "max_tokens": 50}
        body = canonical(payload)
        request = {"request_id": "torn:sdk:1", **{key: quote[key] for key in ("provider", "model", "api_mode", "base_url")},
            "request_sha256": hashlib.sha256(body).hexdigest(), "request_bytes": len(body), "output_tokens": 50}
        receipt = client.effect(self.identity, launch.grant.hash, "start", request)
        effects = []
        def crash(*args): effects.append(True); raise OSError("inert crash after original intent")
        self.adapt(transport, "_perform_fixture", crash)
        with self.assertRaises(security.PolicyDenied):
            client.model_transport(self.identity, launch.grant.hash, request["request_id"], receipt, payload)
        with self.assertRaises(security.PolicyDenied):
            client.model_transport(self.identity, launch.grant.hash, request["request_id"], receipt, payload)
        fabric.check()
        self.assertEqual(effects, [True])
        self.assertEqual(factory.budget_authority.snapshot(allocation.allocation_id)["inflight"], 1)
        with self.assertRaises(security.PolicyDenied):
            client.effect(self.identity, launch.grant.hash, "start", {**request, "request_id": "renamed:attempt"})
        fabric.check()

    def test_probe_is_bound_to_exact_role_identity_grant_and_cannot_emit_tools(self):
        _, launch, _, _, quote = self.work(self.identity, "probe")
        payload = {"model": quote["model"], "messages": [{"role": "user",
            "content": probe_message(self.identity, launch.grant.hash, "root")}]}
        self.assertEqual(probe_response(payload, self.identity, launch.grant, "root", 1)["body"]["id"], "offline-guarded-root")
        self.assertIsNone(probe_response(payload, self.identity, launch.grant, "child", 1))
        self.assertIsNone(probe_response(payload, replace(self.identity, run_token="foreign"), launch.grant, "root", 1))
        self.assertIsNone(probe_response(payload, self.identity, replace(launch.grant, grant_id="foreign"), "root", 1))
        with self.assertRaises(Exception): probe_response({**payload, "tools": [{}]}, self.identity, launch.grant, "root", 1)
        with self.assertRaises(Exception): probe_response(payload, self.identity, launch.grant, "root", 2)

    def test_root_effect_digest_sequence_and_no_resend_after_torn_effect(self):
        binding = {"nonce": NONCE, "boot_id": "inert", "challenge": "1" * 64,
                   "authority_sha256": "2" * 64, "build_sha256": "3" * 64}
        request = {"kind": "OBSERVE_CASE_UNIT", "role": "case", "binding": binding, "claim": {"unit": "fixed"}}
        packet = {"schema": "canonical-case-root-effect-1", "sequence": 1, "previous_sha256": "0" * 64,
                  "binding": binding, "request": request}
        packet["request_sha256"] = digest(packet)
        class Pump(RootEffectPump):
            def __init__(self): self.rows = {}; self.effects = 0
            def _read(self, name): return copy.deepcopy(self.rows.get(name))
            def _write(self, name, value):
                if name in self.rows: raise FileExistsError()
                self.rows[name] = copy.deepcopy(value)
            def _case_unit(self, value): self.effects += 1; raise OSError("lost root effect outcome")
        pump = Pump()
        with patch("offline_case.root_effects.os.geteuid", lambda: 0, create=True):
            with self.assertRaises(OSError): pump.perform(packet, binding)
            with self.assertRaises(Denied): pump.perform(packet, binding)
        self.assertEqual(pump.effects, 1)
        for field, value in (("sequence", 2), ("previous_sha256", "9" * 64), ("binding", {})):
            altered = {**packet, field: value}
            with self.assertRaises(Denied): validate_effect(altered, binding, previous="0" * 64, sequence=1)

    def test_original_worker_identity_extraction_is_byte_semantically_equivalent(self):
        source = (CORE / "agent-stack/bin/agent-task-worker").read_text(encoding="utf8")
        tree = ast.parse(source)
        functions = [node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name in {"_task_session_identity", "_claimed_root_identity"}]
        namespace = {"hashlib": hashlib}
        exec(compile(ast.Module(body=functions, type_ignores=[]), "original-worker-extract", "exec"), namespace)
        task = {"id": "root-" + NONCE, "run_token": "actual-claim", "repo": "Bbambaaamm/herdr", "fencing_token": 7,
                "routing": {"selected_agent": "quantlab-hermes"}}
        self.assertEqual(task_session_identity(task), namespace["_task_session_identity"](task))
        self.assertEqual(claimed_root_identity(task), namespace["_claimed_root_identity"](task))

    def test_all_twelve_default_operation_bodies_and_exact_callbacks_are_present(self):
        tree = ast.parse((OVERLAY / "overlays/herdr/canonical_case_runtime.py").read_text(encoding="utf8"))
        cls = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "CanonicalCaseRuntime")
        names = {node.name for node in cls.body if isinstance(node, ast.FunctionDef)}
        self.assertTrue({"admit", "prepare", "claim_unit", "bind_cgroup", "run", "fence", "fenced", "started", "cgroup_identity", "observe_all", "retire", "retired"} <= names)
        factory, launch, owner, _, _ = self.work(self.identity, "root")
        runtime = object.__new__(CanonicalCaseRuntime)
        runtime._births = lambda: (_ for _ in ()).throw(Denied("durable case fence"))
        entry = LiveLaunch("root", self.identity, launch, "pane", "marker", self.root, self.root / "result", self.root / "policy", work=factory)
        runtime._guard_work_callbacks(entry)
        self.assertIs(owner.work_budget.__func__, HostWorkContractFactory.budget_effect)
        self.assertIs(owner.work_authority.__func__, HostWorkContractFactory.authorize_invocation)
        with self.assertRaises(Denied): owner.case_live_guard()
        owner.work_budget = lambda *args: None
        with self.assertRaises((Denied, AttributeError)): runtime._guard_work_callbacks(entry)

    def runtime(self):
        from herdr.policy_launch import HostPolicyLaunchFactory
        from herdr.runtime import AdmissionRegistry
        task = {"id": "root-" + NONCE, "run_token": "original-root-run", "fencing_token": 7,
            "repo": "Bbambaaamm/herdr", "routing": {"selected_agent": "operator"},
            "max_attempts": 1, "attempt_state": "accepted",
            "ownership_epoch": {"version": 1, "run_token": "original-root-run", "fencing_token": 7}}
        identity = claimed_root_identity(task)
        work, launch, _, allocation, _ = self.work(identity, "runtime")
        factory = object.__new__(HostPolicyLaunchFactory)
        factory.storage = self.root / "private"
        binding = {"nonce": NONCE, "boot_id": "inert-boot", "challenge": "1" * 64,
                   "authority_sha256": "2" * 64, "build_sha256": "3" * 64}
        journal = DiskJournal(self.root / "original-attempt")
        journal.publish_once("single-case-root-admit", {"binding": binding, "task_id": identity.task_id,
            "run_token": identity.run_token, "fencing_token": identity.fencing_token})
        owner = self
        class Effects:
            def __init__(self): self.complete = True; self.cleanup_calls = []
            def current_task(self, _parts, *, historical): return copy.deepcopy(task)
            def boot_id(self): return binding["boot_id"]
            def require_live_case(self, selected):
                if selected != binding: raise Denied("foreign case")
            def validate_authority(self, authority, selected):
                if authority != {"binding": selected}: raise Denied("foreign authority")
            def unit_source(self, unit):
                if unit != offline_case.case.CASE: raise Denied("foreign unit")
                return "4" * 64
            def root_unit_receipt(self, selected, claim):
                if selected != binding or claim["source_sha256"] != "4" * 64: raise Denied("foreign unit source")
                return {"cgroup": [11, 22], "unit": offline_case.case.CASE, "invocation_id": "5" * 32,
                    "main_pid": 500, "main_start_ticks": 9000, "source_sha256": "4" * 64}
            def historical_closure(self, selected, roster):
                if selected != binding: raise Denied("foreign historic case")
                return {"fenced": True, "case_cgroup_empty": True, "descendants": [], "fds": [], "maps": [],
                    "profile_holders": [], "complete": self.complete, "boot_id": binding["boot_id"]}
            def require_historical_namespace_closed(self, selected, row, proof):
                if selected != binding or proof is not None: raise Denied("namespace observation unknown")
            def verify_releases(self, parts, scheduler, roster):
                for row in roster:
                    if row["role"] == "child":
                        rec = scheduler.record_for(row["identity"]["task_id"])
                        owner.assertTrue(rec.cleanup_complete)
                        owner.assertEqual(rec.attempt_state, "terminal")
                        owner.assertIsNone(rec.lease)
        effects = Effects()
        parts = {"root": self.root, "identity": identity, "task": task, "factory": factory,
            "work_factory": work, "admission_control": AdmissionControl(audit_log=AdmissionAuditLog(self.root / "runtime-admission.jsonl"),
                consumer_policy_hook=policy_for_profile("herdr-core")),
            "admission_registry": AdmissionRegistry(path=self.root / "registry.json")}
        runtime = CanonicalCaseRuntime(parts=parts, journal=journal, effects=effects, binding=binding)
        return runtime, parts, journal, effects, binding

    def test_cold_default_fence_observe_retire_replays_original_task_budget_without_launch(self):
        runtime, parts, journal, effects, binding = self.runtime()
        self.assertFalse(runtime.started())
        with self.assertRaises(Denied): runtime.observe_all()
        runtime.fence()
        self.assertTrue(runtime.fenced())
        cold = CanonicalCaseRuntime(parts=parts, journal=DiskJournal(journal.root), effects=effects, binding=binding, recovery=True)
        with self.assertRaises(Denied): cold.prepare({"binding": binding}, "begin")
        with self.assertRaises(Denied): cold.run(BUDGET, "root")
        effects.complete = False
        with self.assertRaises(Denied): cold.observe_all()
        self.assertFalse(cold.retired())
        effects.complete = True
        observed = cold.observe_all()
        self.assertTrue(cold.retire(observed))
        self.assertTrue(CanonicalCaseRuntime(parts=parts, journal=DiskJournal(journal.root), effects=effects,
            binding=binding, recovery=True).retired())
        self.assertEqual(parts["work_factory"].budget_authority.snapshot(
            parts["work_factory"].budget_definition["allocation"]["allocation_id"])["implementation_attempts"], 0)

    def test_prepare_intent_is_consumed_before_native_source_failure_and_never_retried(self):
        runtime, parts, journal, effects, binding = self.runtime()
        observed = []
        def unavailable(*args): observed.append(True); raise OSError("inert low-level preparation loss")
        effects.early_root_pane = unavailable
        with self.assertRaises(OSError): runtime.prepare({"binding": binding}, "begin")
        with self.assertRaises(Denied): runtime.prepare({"binding": binding}, "begin")
        self.assertEqual(observed, [True])
        self.assertIsNotNone(journal.read_once("root-prepare-intent"))

    def test_unit_claim_remains_unknown_until_root_observed_binding_and_rejects_substitution(self):
        runtime, parts, journal, effects, binding = self.runtime()
        journal.publish_once("root-prepared", {"binding": binding, "sdk_imported": False,
            "setup_fds_closed": True, "setup_paths_hidden": True})
        effect = runtime.claim_unit(offline_case.case.CASE)
        self.assertEqual(effect["request"]["kind"], "OBSERVE_CASE_UNIT")
        with self.assertRaises(Denied): runtime.started()
        with self.assertRaises(Denied): runtime.bind_cgroup([999, 22])
        self.assertIsNone(runtime.cgroup_identity())
        self.assertEqual(runtime.bind_cgroup([11, 22]), [11, 22])
        self.assertTrue(runtime.started())
        self.assertEqual(runtime.cgroup_identity(), [11, 22])
        runtime.fence()
        with self.assertRaises(Denied): runtime.claim_unit(offline_case.case.CASE)

    def test_closed_twelve_operation_dispatch_rejects_arguments_and_foreign_binding(self):
        runtime, parts, journal, effects, binding = self.runtime()
        packet = {"operation": "fenced", "arguments": {}, "binding": binding,
                  **{key: getattr(parts["identity"], key) for key in ("task_id", "run_token", "fencing_token")}}
        import herdr.canonical_case_claim as claims
        @contextmanager
        def lock(_parts): yield  # Only original worker lock IO is synthetic.
        with patch.object(claims, "operation_guard", lock):
            self.assertFalse(dispatch_with(runtime, packet))
            with self.assertRaises(Denied): dispatch_with(runtime, {**packet, "arguments": {"arbitrary": "command"}})
            with self.assertRaises(Denied): dispatch_with(runtime, {**packet, "binding": {**binding, "nonce": "foreign"}})

    def test_historical_scan_reads_own_enumeration_fd_while_alive_and_retains_foreign_loss(self):
        import offline_case.historical_holders as holders
        binding = {"boot_id": "inert-boot"}
        class Kernel:
            def __init__(self): self.alive = False; self.foreign_loss = False
            def exists(self, _path): return False
            def read(self, value, _maximum):
                value = str(value).replace("\\", "/")
                if value.endswith("/boot_id"): return b"inert-boot"
                if value.endswith("/cgroup"): return b"0::/system.slice/root-operator.service\n"
                if value.endswith("/attr/current"): return b"root-observer (enforce)"
                if value.endswith(("/maps", "/mountinfo")): return b""
                raise AssertionError(value)
            def process_start_ticks(self, _pid): return 9001
            def scandir(self, value):
                kernel = self
                class Entries:
                    def __enter__(self): kernel.alive = True; return self
                    def __exit__(self, *args): kernel.alive = False
                    def __iter__(self):
                        if str(value).replace("\\", "/") == "/proc":
                            yield types.SimpleNamespace(name="501")
                        else:
                            yield types.SimpleNamespace(name="99", path="/proc/501/fd/99")
                return Entries()
            def readlink(self, value):
                value = str(value).replace("\\", "/")
                if value.endswith("/ns/pid"): return "pid:[777]"
                if not self.alive or self.foreign_loss: raise FileNotFoundError("transient descriptor")
                return "/proc/501/fd"
        kernel = Kernel()
        with patch.object(holders.os, "scandir", kernel.scandir), patch.object(holders.os, "readlink", kernel.readlink), \
                patch.object(holders.os, "stat", lambda value: types.SimpleNamespace(st_mode=stat.S_IFDIR)):
            result = holders.observe_closed(binding, [], {"root": None, "child": None}, kernel, lambda _name: None)
            self.assertTrue(result["observation"]["complete"])
            kernel.foreign_loss = True
            with self.assertRaises(FileNotFoundError):
                holders.observe_closed(binding, [], {"root": None, "child": None}, kernel, lambda _name: None)

    def test_existing_approved_runtime_renders_exact_unit_and_missing_inventory_denies(self):
        from offline_case.publication import existing_runtime, render_host_unit
        policy = {"schema_version": 2, "host_uid": 1001, "runtime": [{"source": "/opt/reviewed/cp311", "target":
            "/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu",
            "files": {"bin/python3.11": "a" * 64}, "executable_files": ["bin/python3.11"],
            "max_bytes": 1000000, "max_file_bytes": 1000000}, {"target": "sdk"}]}
        selected = existing_runtime(policy)
        unit = render_host_unit(policy)
        self.assertIn(b"ExecStart=/opt/reviewed/cp311/bin/python3.11 -I -B ", unit)
        self.assertIn(b"AppArmorProfile=herdr-offline-controller-03414499dd0d1986", unit)
        self.assertNotIn(b"03414499dd0d1986/runtime/python", unit)
        changed = copy.deepcopy(policy); changed["runtime"][0]["files"] = {}
        with self.assertRaises(Denied): existing_runtime(changed)

    def test_generic_retirement_proof_rechecks_root_closure_fence_roster_and_actual_budget_stops(self):
        from herdr.canonical_case_recovery import require_root_release
        import herdr.canonical_case_claim as claims
        import herdr.work_configuration as work_config
        runtime, parts, journal, effects, binding = self.runtime()
        parent = parts["identity"]
        scheduler, child, _ = canonical_scheduler(self.root / "release-check", parent)
        rec = scheduler.record_for(child.task_id)
        rec.namespace_lifetime = {"version": 3, "pid": 501, "start_ticks": 9001}
        identities = [parent.to_json(), child.to_json()]
        journal.publish_once("case-fence-intent", {"binding": binding, "root": parent.to_json()})
        journal.publish_once("case-fenced", {"binding": binding, "identities": identities})
        rows = [{"identity": identity, "role": role} for identity, role in zip(identities, ("root", "child"))]
        for row in rows: journal.publish_once(row["role"] + "-launch-sdk-ready", row)
        closure = {"roster_sha256": digest(rows), "namespaces": {"child": rec.namespace_lifetime},
            "observation": {"fenced": True, "case_cgroup_empty": True, "descendants": [], "fds": [],
                "maps": [], "profile_holders": [], "complete": True, "boot_id": binding["boot_id"]}}
        authority = parts["work_factory"].budget_authority
        for identity in (parent, child):
            authority.stop(stop_id=digest({"binding": binding, "identity": identity.to_json()}), scope=StopScope.TASK,
                target=identity.task_id, source="canonical-offline-case", reason_code="offline-case-fenced",
                resume_condition="no-resume-single-attempt")
        event = {"identity": child.to_json(), "binding": binding, "idempotency_key": rec.idempotency_key,
                 "closure_sha256": digest(closure)}
        def restore(root, task, **kwargs):
            self.assertEqual(root, parts["root"]); self.assertEqual(task, parts["task"])
            self.assertEqual(kwargs, {"recovery": True})
            return parts["work_factory"]
        current = [closure]
        def metadata(kind, selected):
            self.assertEqual(kind, "closure"); self.assertEqual(selected, binding)
            if current[0] is None: raise FileNotFoundError("missing immutable root closure")
            return copy.deepcopy(current[0])
        with patch.object(claims, "read_held_task", lambda *args: claims.HeldTask(parts["task"])), \
                patch.object(claims, "attempt_journal", lambda *args: journal), patch.object(claims, "root_metadata", metadata), \
                patch.object(work_config, "build_root_work_factory", restore):
            self.assertEqual(require_root_release(parts["root"], parent, rec, event), closure)
            with self.assertRaises(Exception): require_root_release(parts["root"], parent, rec, {**event, "closure_sha256": "9" * 64})
            current[0] = {**closure, "observation": {**closure["observation"], "complete": False}}
            with self.assertRaises(Exception): require_root_release(parts["root"], parent, rec, event)
            current[0] = None
            with self.assertRaises(FileNotFoundError): require_root_release(parts["root"], parent, rec, event)
        source = (OVERLAY / "overlays/herdr/ownership_release.py").read_text(encoding="utf8")
        self.assertLess(source.index("require_root_release(self.root, parent, rec"), source.index("if rec.namespace_lifetime is not None:"))



    def test_operator_policy_has_exact_reciprocal_metadata_peers_and_complete_source_inventory(self):
        from offline_case.publication import render_operator_profile, render_operator_unit, render_host_unit
        selection = json.loads(json.dumps(reference_support.runtime_policy()).encode())
        rendered = render_operator_profile(selection)
        self.assertEqual(rendered, (OVERLAY / "overlays/operator-profile.apparmor").read_bytes())
        self.assertIn(b"/composed-core/** r,", rendered)
        self.assertNotIn(b"/herdr-offline-03414499dd0d1986/**", rendered)
        self.assertNotIn(b"runtime/core", rendered)
        for name in ("worker-profile.apparmor", "host-profile.apparmor", "observer-profile.apparmor", "trusted-preparation.apparmor"):
            text = (OVERLAY / "overlays" / name).read_text()
            self.assertIn("ptrace (readby) peer=herdr-offline-operator-03414499dd0d1986,", text)
            self.assertNotIn("runtime/core", text)
            self.assertIn("audit deny ptrace", text)
        for cleanup in (False, True):
            name = "herdr-offline-" + ("cleanup" if cleanup else "operator") + "-03414499dd0d1986.service"
            self.assertEqual(render_operator_unit(cleanup=cleanup), (OVERLAY / "units" / name).read_bytes())
        self.assertEqual(render_host_unit(selection), (OVERLAY / "units/herdr-offline-host-03414499dd0d1986.service").read_bytes())

    def test_host_peer_requires_kernel_label_and_exact_root_owned_caller_projection(self):
        from offline_case import host_service as host
        raw_script, raw_unit, raw_exe = b"driver", b"unit", b"python"
        build = {"files": {"offline_case/driver.py": hashlib.sha256(raw_script).hexdigest(),
            "units/" + host.OPERATOR_UNIT: hashlib.sha256(raw_unit).hexdigest()}}
        pid, ticks = 700, 12
        command = b"\0".join(host.DRIVER_COMMAND) + b"\0"
        cgroup = "0::/system.slice/" + host.OPERATOR_UNIT
        procstat = b"700 (root driver) S " + b"0 " * 18 + b"12 0\n"
        caller = {"schema": "canonical-case-root-caller-1", "pid": pid, "start_ticks": ticks,
            "boot_id": "boot", "label": host.OPERATOR_LABEL, "exe": "/usr/bin/python3.14",
            "exe_sha256": hashlib.sha256(raw_exe).hexdigest(),
            "command": [x.decode() for x in host.DRIVER_COMMAND], "cgroup": cgroup,
            "unit_sha256": hashlib.sha256(raw_unit).hexdigest(),
            "build_sha256": hashlib.sha256(offline_canonical(build)).hexdigest()}
        class Conn:
            label = host.OPERATOR_LABEL.encode()
            def getsockopt(self, level, option, size):
                return struct.pack("3i", pid, 0, 0) if option == 17 else self.label
        conn = Conn()
        def readproc(p, maximum):
            return {"stat": procstat, "cgroup": (cgroup + "\n").encode(),
                "cmdline": command, "boot_id": b"boot\n"}[p.name]
        def pinned(p, **kwargs):
            self.assertTrue(kwargs.get("root_owned"))
            if p.name.startswith("caller-"): return offline_canonical(caller)
            return {"driver.py": raw_script, host.OPERATOR_UNIT: raw_unit, "python3.14": raw_exe}[p.name]
        with patch.object(host.socket, "SO_PEERCRED", 17, create=True), \
             patch.object(host.socket, "SO_PEERSEC", 31, create=True), \
             patch.object(host, "_process_read", readproc), patch.object(host, "pinned_bytes", pinned):
            self.assertEqual(host.check_peer(conn, build), (pid, ticks))
            conn.label = b"herdr-offline-observer-03414499dd0d1986 (enforce)"
            with self.assertRaises(Denied): host.check_peer(conn, build)
            conn.label = host.OPERATOR_LABEL.encode()
            caller["start_ticks"] += 1
            with self.assertRaises(Denied): host.check_peer(conn, build)



    def test_default_host_loss_cleanup_reconstructs_root_history_without_execution_grant(self):
        from offline_case import historical_holders
        binding = {"nonce": NONCE, "boot_id": "boot"}
        pump = RootEffectPump.__new__(RootEffectPump)
        pump._read = lambda name: {"used": binding, "state": {"phase": "FENCE_INTENT"}} if name == "case-phase" else None
        pump._metadata = lambda kind, actual, value: value
        pump.io = types.SimpleNamespace(read=lambda p, n: b"boot\n", exists=lambda p: False)
        @contextmanager
        def empty_proc(path): yield iter(())
        with patch.object(historical_holders.os, "scandir", empty_proc):
            receipt = pump.observe_historical(binding)
        self.assertTrue(receipt["observation"]["complete"])
        self.assertFalse(receipt["observation"]["fenced"])
        self.assertEqual(receipt["outcome"], "ROOT_HOLDER_SCAN_ONLY_CANONICAL_FENCE_UNCONFIRMED")
        source = (OVERLAY / "offline_case/case.py").read_text()
        self.assertIn("self.host.observe_historical(binding)", source)
        self.assertIn('"RETAINED_UNKNOWN"', source)
        with self.assertRaises(Denied):
            pump._read = lambda name: {"used": binding, "state": {"phase": "START_INTENT"}}
            pump.observe_historical(binding)





    def test_actual_host_bridge_checks_complete_current_package_and_rejects_stale_or_changed_source(self):
        import shutil, runpy
        entry = OVERLAY / "overlays/agent-stack/bin/offline-case-host-entry"
        namespace = {"__file__": str(entry), "__name__": "inert_exact_bridge"}
        exec(compile(entry.read_bytes(), str(entry), "exec"), namespace)
        target = self.root / "bridge-package"
        for name in namespace["EXPECTED_PACKAGE"]:
            destination = target / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(OVERLAY / name, destination)
        class BridgeStatView(StatView):
            @property
            def st_ctime_ns(self): return self.value.st_mtime_ns  # Windows creation-time vs POSIX ctime IO model.
        class BridgePath(PrivatePath):
            def stat(self, *args, **kwargs): return BridgeStatView(Path.stat(self, *args, **kwargs))
        original_check = namespace["checked_bytes"]
        def checked(path, digest):
            try: return original_check(path, digest)
            except RuntimeError as exc: raise RuntimeError(str(path)) from exc
        namespace["checked_bytes"] = checked
        namespace["ROOT"] = BridgePath(target)
        namespace["Path"] = BridgePath
        calls = []
        original_fstat, original_open = os.fstat, os.open
        with patch.object(os, "open", lambda name, flags, *args, **kwargs: original_open(name, flags | getattr(os, "O_BINARY", 0), *args, **kwargs)), \
             patch.object(os, "O_NOFOLLOW", getattr(os, "O_NOFOLLOW", 0), create=True), \
             patch.object(os, "O_CLOEXEC", getattr(os, "O_CLOEXEC", 0), create=True), \
             patch.object(os, "fstat", lambda fd: BridgeStatView(original_fstat(fd))), \
             patch.object(sys, "argv", [str(entry.resolve())]), patch.object(sys, "path", list(sys.path)), \
             patch.object(runpy, "run_path", lambda path, **kwargs: calls.append((path, kwargs))):
            namespace["main"]()
            self.assertEqual(len(calls), 1)
            self.assertEqual(Path(calls[0][0]), target / "offline_case/host_service.py")
            self.assertGreaterEqual(len(namespace["EXPECTED_PACKAGE"]), 30)
            (target / "offline_case/admission.py").write_bytes(b"changed source")
            sys.argv = [str(entry.resolve())]
            with self.assertRaises(RuntimeError): namespace["main"]()
            self.assertEqual(len(calls), 1)



    def test_typed_root_startup_observation_preserves_original_method_and_rejects_changed_pid_challenge(self):
        import herdr.canonical_startup_observation as observed
        import herdr.case_roster as rosters
        import herdr.policy_launch as launches
        import herdr.host_configuration as config
        import herdr.canonical_case_effects as effects
        import offline_case.admission as admission
        import offline_case.native_source as native
        _, launch, _, _, _ = self.work(self.identity, "startup")
        class LogicalPosixPath(PurePosixPath):
            def resolve(self, **kwargs): return self
        with patch.object(security,"Path",LogicalPosixPath):
            grant = replace(launch.grant, workspace_root="/home/agentops/tmp/hermes-inert/workspace")
        authority = {"not_before": 0, "deadline": 2000000000}
        binding = {"nonce": NONCE, "challenge": "b"*64, "boot_id": "boot",
            "authority_sha256": hashlib.sha256(offline_canonical(authority)).hexdigest(), "build_sha256": "c"*64}
        helper = lambda profile: {"profile": profile, "source_sha256": "d"*64, "loaded_sha256": "e"*64,
            "entrypoint": "/opt/agent-platform/herdr-offline-03414499dd0d1986/helper.py",
            "files": {"helper.py":"f"*64}, "python":"/opt/python/bin/python3.11", "python_sha256":"a"*64}
        stdio = {str(n):{"path":"/dev/pts/7","device":1,"inode":2,"rdev":3} for n in range(3)}
        doc = {"schema":rosters.VERSION,"nonce":NONCE,"case_binding":binding,"not_before":1,"deadline":1801,
            "host_policy_sha256":"a"*64,"worker_source_sha256":rosters.WORKER_SOURCE,
            "controller":{"uid":1001,"gid":1001,"pid":os.getpid(),"start_ticks":10,"exe_sha256":"b"*64,
                "cgroup":"/system.slice/herdr-offline-host-03414499dd0d1986.service","profile":rosters.CONTROLLER_LABEL,
                "source_sha256":"c"*64,"loaded_sha256":"d"*64},
            "observer":helper(rosters.OBSERVER_LABEL),"preparer":helper(rosters.PREP_LABEL),
            "slots":{"root":{"identity":self.identity.to_json(),"workspace":grant.workspace_root,
                "unit":"herdr-offline-root-03414499dd0d1986.service","stdio":stdio,"marker":"inert-root"}}}
        roster = rosters.Roster.parse(offline_canonical(doc), InvocationIdentity)
        digest_native = hashlib.sha256(b"inert-native").hexdigest()
        value = {"identity":self.identity.to_json(),"pane_id":"pane-1","shell_pid":700,"shell_start_ticks":20,
            "controller_pid":os.getpid(),"controller_start_ticks":10,"roster_sha256":roster.sha256,
            "native_sha256":digest_native,"challenge":"9"*64,"root_grant_sha256":None,"plan_sha256":None,
            "root_context_sha256":None}
        row = {"schema":"canonical-case-root-metadata-1","kind":"root-startup-source","binding":binding,"value":value}
        row["projection_sha256"] = hashlib.sha256(offline_canonical(row)).hexdigest()
        phase={"schema":"canonical-case-phase-projection-1","state":{"phase":"ADMITTED","binding":binding},
            "authority":authority,"used":binding,"revision":1}
        phase["projection_sha256"]=hashlib.sha256(offline_canonical(phase)).hexdigest()
        def read_config(path):
            if path.name == "scope-fenced.json": raise FileNotFoundError(path)
            if path.name == "case-phase.json": return phase
            raise AssertionError(path)
        root_context = {"identity": self.identity.to_json(), "plan_sha256": "6"*64}
        def pinned(path, **kwargs):
            if path.name == "herdr": return b"inert-native"
            return offline_canonical(root_context if path.name == "root.json" else row)
        prepared=object.__new__(launches.PreparedPolicyLaunch);prepared.grant=grant
        observation=observed.AuthenticatedStartupObservation("root-startup-source","9"*64)
        stat_reads=[]
        def native_stat(path,maximum):
            self.assertEqual(maximum,8192)
            self.assertEqual(path.parent.parent,Path('/proc'))
            self.assertEqual(path.name,'stat')
            pid=int(path.parent.name);self.assertIn(pid,(700,os.getpid()))
            stat_reads.append(pid)
            return (str(pid)+' (native pane) '+' '.join(['S','1']+['0']*17+[str(10 if pid==os.getpid() else 20),'0'])).encode()
        with patch.object(rosters,"load_roster",lambda *args:roster), patch.object(config,"_read_configuration",read_config), \
             patch.object(admission,"_process_read",native_stat), \
             patch.object(observed,"pinned_bytes",pinned), patch.object(native,"NATIVE_SHA256",digest_native), \
             patch.object(effects.CanonicalHostEffects,"boot_id",lambda self:"boot"):
            prepared.verify_spawn_source(lambda:700,observation=observation)
            self.assertIn(700,stat_reads);self.assertIn(os.getpid(),stat_reads)
            with self.assertRaises(Denied): prepared.verify_spawn_source(lambda:701,observation=observation)
            with self.assertRaises(Denied): prepared.verify_spawn_source(lambda:700,
                observation=observed.AuthenticatedStartupObservation("root-startup-source","8"*64))
            with self.assertRaises(security.SecurityError): prepared.verify_spawn_source(lambda:700,observation=True)
            with patch.object(security,"Path",LogicalPosixPath):
                child_grant = replace(grant, identity=self.child_identity, parent_grant_hash=grant.hash, grant_id="inert-child-source")
            row["kind"] = "child-parent-startup-source"
            value.update(challenge="7"*64, root_grant_sha256=grant.hash, plan_sha256="6"*64,
                root_context_sha256=hashlib.sha256(offline_canonical(root_context)).hexdigest())
            row["projection_sha256"] = hashlib.sha256(offline_canonical({k:v for k,v in row.items() if k!="projection_sha256"})).hexdigest()
            prepared.grant = child_grant
            child_observation = observed.AuthenticatedStartupObservation("child-parent-startup-source","7"*64)
            prepared.verify_spawn_source(lambda:700, observation=child_observation)
            with patch.object(security,"Path",LogicalPosixPath):
                prepared.grant = replace(child_grant, parent_grant_hash="0"*64)
            with self.assertRaises(Denied): prepared.verify_spawn_source(lambda:700, observation=child_observation)

    def test_retained_parent_birth_denied_by_outer_fence_before_journal_and_after_cleanup_failure(self):
        import herdr.canonical_case_claim as claim
        import herdr.host_configuration as config
        task={'id':'offline-03414499dd0d1986968b2393d44275d0',
              'run_token':'inert-run','fencing_token':1,'repo':'example'}
        identity=claim.claimed_root_identity(task)
        calls=[]
        class Journal:
            def read_once(self,name):
                calls.append(name)
                if name=='single-case-root-admit':return {'task_id':identity.task_id,'run_token':identity.run_token}
                raise FileNotFoundError(name)
        def missing(path):
            calls.append('scope-read');raise FileNotFoundError(path)
        with patch.object(claim,'attempt_journal',lambda _:Journal()),patch.object(config,'_read_configuration',missing):
            claim.require_case_births('/inert',task)
        self.assertEqual(calls,['scope-read','single-case-root-admit','case-fence-intent'])
        for fence in ({'kind':'scope-fenced'},None):
            calls.clear()
            def present(path):
                calls.append('scope-read')
                if fence is None:raise Denied('malformed root fence')
                return fence
            with patch.object(claim,'attempt_journal',lambda _:Journal()),patch.object(config,'_read_configuration',present):
                with self.assertRaises((security.SecurityError,Denied)):
                    claim.require_case_births('/inert',task)
            self.assertEqual(calls,['scope-read'])
        calls.clear()
        with patch.object(config,'_read_configuration',lambda p:calls.append('foreign-read')):
            claim.require_case_births('/inert',{**task,'id':'unrelated-parent'})
        self.assertEqual(calls,[])

    def test_original_factory_preflight_occurs_after_actual_root_base_continuation(self):
        import herdr.policy_launch as policy
        import herdr.launch_ownership as ownership
        runtime, parts, journal, effects, binding = self.runtime()
        _, launch, _, _, _ = self.work(parts["identity"], "factory-order")
        grant=launch.grant
        ready={"value":False};events=[]
        class ReachedOriginalFreeze(Exception): pass
        class Frozen:
            def cleanup_after_pane_closed(self): pass
        class Tree:
            def freeze(self,*args): events.append("original-tree-freeze");return Frozen()
        class Profile:
            name="inert"
            def freeze(self):
                if not ready["value"]: raise AssertionError("factory reached before ROOT observer")
                events.append("original-profile-freeze");raise ReachedOriginalFreeze()
        factory=object.__new__(policy.HostPolicyLaunchFactory)
        for key,value in {"authorize":lambda **kwargs:grant,"parent_grant":None,"code":Tree(),"runtime":(),
            "storage":self.root,"writable_roots":(),"approved_profile":Profile(),
            "profile_preflight":lambda name:ready["value"]}.items():setattr(factory,key,value)
        owner=types.SimpleNamespace(directory=self.root,cleanup_after_pane_closed=lambda:None)
        # Crypto is not used before the original profile freeze; this import-only
        # adapter traps generation if a future edit crosses this bounded seam.
        crypto=types.ModuleType("cryptography.hazmat.primitives.asymmetric.ed25519")
        crypto.Ed25519PrivateKey=types.SimpleNamespace(generate=lambda:(_ for _ in ()).throw(AssertionError("unexpected key generation")))
        modules={name:types.ModuleType(name) for name in ("cryptography","cryptography.hazmat","cryptography.hazmat.primitives","cryptography.hazmat.primitives.asymmetric")}
        modules[crypto.__name__]=crypto
        def actual_prepare():return factory.prepare(identity=parts["identity"],workspace=Path(grant.workspace_root),tools=grant.scope.tools,permissions=grant.scope.permissions)
        effects.early_root_pane=lambda task:("pane-1","marker")
        effects.root_base_request=lambda actual,bound,pane:{"kind":"PUBLISH_ROOT_ROSTER","role":"root","binding":bound,
            "identity":actual["identity"].to_json(),"workspace":grant.workspace_root,"marker":pane[1],"pane_id":pane[0],
            "shell_pid":700,"controller_pid":os.getpid(),"controller_start_ticks":10}
        runtime._prepare_root=actual_prepare
        with patch.dict(sys.modules,modules),patch.object(ownership.LaunchOwnership,"create",lambda *args:owner):
            with self.assertRaises(security.SecurityError): actual_prepare()
            packet=runtime.prepare({"binding":binding},"begin")
            self.assertEqual(packet["request"]["kind"],"PUBLISH_ROOT_ROSTER")
            self.assertNotIn("plan_sha256",packet["request"])
            self.assertNotIn("grant_sha256",packet["request"])
            ready["value"]=True  # Synthetic root producer/socket readiness effect only.
            with self.assertRaises(ReachedOriginalFreeze): runtime.prepare({"binding":binding},"ticket")
            self.assertIn("original-profile-freeze",events)



    def test_root_effect_runs_actual_original_environment_guard_without_raw_environment_return(self):
        import io
        import herdr.observed_proc as proc
        import herdr.prep_entry as prep
        parents={700:800,800:900,900:1};ticks={700:20,800:30,900:40}
        def procstat(pid):return (str(pid)+" (owned native) "+" ".join(["S",str(parents[pid])]+["0"]*17+[str(ticks[pid]),"0"])).encode()
        env={800:b"HOME=/home/agentops\0PATH=/usr/bin:/bin\0",900:b"HOME=/home/agentops\0PATH=/usr/bin:/bin\0"}
        class ProcPath:
            def __init__(self,path):self.parts=str(path).replace("\\","/").split("/")
            def read_text(self):return procstat(int(self.parts[-2])).decode()
            def open(self,mode):return io.BytesIO(env[int(self.parts[-2])])
        pump=RootEffectPump.__new__(RootEffectPump)
        pump.io=types.SimpleNamespace(process_start_ticks=lambda pid:ticks[pid],
            read=lambda path,bound:procstat(int(str(path).replace("\\","/").split("/")[-2])))
        with patch.object(proc,"Path",ProcPath), patch.object(proc._os,"geteuid",lambda:0,create=True), \
             patch.object(prep,"protected_json",lambda path:{"controller":{"pid":os.getpid()}}):
            self.assertFalse(proc.native_scope_enabled())
            self.assertEqual(pump._guard_native_ancestry(700,900,40),(900,20))
            env[800]+=b"LD_PRELOAD=forbidden\0"
            with self.assertRaises(ValueError):pump._guard_native_ancestry(700,900,40)
            env[800]=b"HOME=/home/agentops\0"
            with self.assertRaises(Denied):pump._guard_native_ancestry(700,900,41)



    def test_supported_startup_config_proposal_rehashes_original_profile_and_projection_without_approval(self):
        from herdr.policy_launch import ApprovedProfile
        from offline_case.publication import propose_sdk_profile_inputs
        raw = offline_canonical({"model":{"provider":"nous","default":"fixture:free"},
            "fallback_providers":[],"fallback_model":[],"updates":{"check":True},"display":{"interface":"classic"}})
        policy = offline_canonical({"schema_version":1,"managed_scope":"none","fallback_chain":"empty"})
        files={"config.yaml":hashlib.sha256(raw).hexdigest(),".env":hashlib.sha256(b"").hexdigest(),
               "herdr-sdk-policy.json":hashlib.sha256(policy).hexdigest()}
        approved=ApprovedProfile("inert-source-profile",self.root/"inert-source-profile",files)
        result=propose_sdk_profile_inputs(approved,raw,policy)
        new_config=json.loads(result["config.yaml"])
        self.assertFalse(new_config["updates"]["check"])
        self.assertEqual(new_config["display"]["interface"],"classic")
        self.assertNotEqual(result["previous_profile"]["manifest_sha256"],result["proposed_profile"]["manifest_sha256"])
        self.assertEqual(result["proposed_profile"]["files"]["config.yaml"],hashlib.sha256(result["config.yaml"]).hexdigest())
        self.assertIsNone(result["private_sdk_projection"]["auth_sha256"])
        self.assertEqual(dict(approved.files),files)
        self.assertTrue(result["approval_required"]);self.assertFalse(result["installed_SDK_changed"])
        with self.assertRaises(Denied):propose_sdk_profile_inputs(approved,b"changed",policy)


if __name__ == "__main__": unittest.main(verbosity=2)
