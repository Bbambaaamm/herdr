"""Inert composition through the canonical Unix work port and fixed fixture."""
import hashlib
import json
import os
from dataclasses import asdict, replace
from pathlib import Path
import queue
import socket
import struct
import sys
import tempfile
import threading
import types
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT.parents[1] / ""), str(ROOT.parents[1] / "tests"),
                str(ROOT.parents[1] / "tests/herdr")]

from herdr import host_model_transport as transport
from herdr import work_authority
from herdr.bootstrap_authority import PeerProcess
from herdr.check_runner import CheckEnvironment
from herdr.capability import Egress
from herdr.evidence import canonical, digest
from herdr.work_budget import BudgetAllocation, BudgetLimits
from herdr.work_budget_configuration import bind_budget
from herdr.work_contract_host import HostWorkContractFactory
from herdr.work_cycle import WorkContractError
from herdr.security import PolicyDenied
from offline_case.case import NONCE


class MemoryEndpoint:
    """Byte stream with real framing semantics and zero kernel socket effects."""
    def __init__(self):
        self.incoming = queue.Queue()
        self.buffer = bytearray()
        self.peer = None
        self.timeout = 5
        self.closed = False
    def connect(self, path):
        self.path = path
    def settimeout(self, seconds):
        self.timeout = seconds
    def getsockopt(self, level, option, size):
        if (level, option, size) == (socket.SOL_SOCKET, socket.SO_PEERCRED, 12):
            return struct.pack("3i", os.getpid(), os.geteuid(), os.getegid())
        raise AssertionError("foreign socket option")
    def sendall(self, raw):
        if self.closed:
            raise OSError("closed memory stream")
        self.peer.incoming.put(bytes(raw))
    def recv(self, amount):
        while not self.buffer:
            item = self.incoming.get(timeout=self.timeout)
            if item is None:
                return b""
            self.buffer.extend(item)
        result = bytes(self.buffer[:amount])
        del self.buffer[:amount]
        return result
    def close(self):
        if not self.closed:
            self.closed = True
            self.peer.incoming.put(None)
    def __enter__(self): return self
    def __exit__(self, *args): self.close()


def pair():
    left, right = MemoryEndpoint(), MemoryEndpoint()
    left.peer = right; right.peer = left
    return left, right


def fixture_factory(tmp):
    """Reuse the original synthetic contract constructor, without pytest execution."""
    old = sys.modules.get("pytest")
    if old is None:
        stub = types.ModuleType("pytest")
        stub.mark = types.SimpleNamespace(parametrize=lambda *a, **k: lambda f: f)
        sys.modules["pytest"] = stub
    try:
        from tests.herdr import test_work_contract_host as module
        runtime = tmp / "synthetic-runtime"
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_bytes(b"inert synthetic executable bytes")
        environment = CheckEnvironment("inert-offline-1",
            ((str(runtime), hashlib.sha256(runtime.read_bytes()).hexdigest()),),
            (str(runtime),))
        with patch.object(module, "environment", return_value=environment):
            return module.factory_fixture(tmp)
    finally:
        if old is None:
            sys.modules.pop("pytest", None)


class OfflineFixtureComposed(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        self.storage = self.root / "protected-host"
        self.storage.mkdir(mode=0o700)

    def prepared(self, role):
        seed, workspace, original, grant, _ = fixture_factory(self.root / role)
        factory = HostWorkContractFactory(approve=seed.approve,
            environment=seed.environment, storage=self.storage / role / "checks",
            audit_log=seed.audit_log, git=seed.git)
        task_id = ("offline188-" + NONCE if role == "root" else
                   "offline188-" + NONCE + "-managed-child")
        identity = replace(grant.identity, consumer="github:Bbambaaamm/herdr",
            agent_id=role + "-agent", parent_agent_id=("coordinator" if role == "root" else "root-agent"),
            parent_task_id=("coordinator:coordinator" if role == "root" else "offline188-" + NONCE),
            task_id=task_id, run_token=(NONCE if role == "root" else "1" * 32),
            fencing_token=(1 if role == "root" else 2))
        route = replace(grant.provider_routes[0], provider="nous", base_url=transport.ENDPOINT,
            api_mode="chat_completions", max_egress=Egress.GLOBAL,
            credential_refs=("pool:nous:offline",))
        grant = replace(grant, identity=identity,
            scope=replace(grant.scope, providers=("nous",), max_egress=Egress.GLOBAL,
                          max_cost_microusd=0, max_context_tokens=65536),
            provider_routes=(route,), credential_refs=("pool:nous:offline",))
        limits = BudgetLimits(1000000, 1000000, 16, 100000, 0, 2, 1, 1, 1)
        allocation = BudgetAllocation(digest(role + "-allocation"), identity.consumer,
            digest(role + "-work"), digest("one-lineage"), digest("one-approval"), limits)
        quote = {"provider": "nous", "model": transport._FIXTURE_MODEL,
            "api_mode": "chat_completions", "base_url": transport.ENDPOINT,
            "max_request_bytes": 20000, "max_output_tokens": 100,
            "max_tokens": 20100, "max_cost_microusd": 0, "max_work_ms": 20000}
        plan = replace(original, identity=identity, grant_sha256=grant.hash,
                       budget_reference=allocation.hash,
                       baseline_policy="host-approved-omission",
                       baseline_omission_reason="inert composed transport fixture")
        factory.approve = lambda **kwargs: plan
        private = self.storage / role
        private.mkdir(mode=0o700)
        bind_budget(factory, {"version": 1, "allocation": asdict(allocation),
            "ancestors": [], "model_quotes": [quote]}, storage=private,
            writable_roots=(workspace,))
        factory.prepare(identity=identity, workspace=workspace, grant=grant,
                        spec_sha256=plan.spec_sha256)
        factory.host_task = {"id": task_id, "run_token": identity.run_token,
            "fencing_token": identity.fencing_token,
            "parent_agent_id": identity.parent_agent_id,
            "derived_parent_admission_sha256": "a" * 64}
        from tests.unit.test_offline_fixture import definition, payload
        work = definition()
        work["managed_children"]["children"][0]["worktree_identity"] = (
            str(workspace / ".managed-child/workspace") + "|1:2")
        factory.host_admission = {"definition": work}
        body = canonical({**payload(role, ({"role": "user", "content": "frozen arithmetic"},)),
                          "max_tokens": 50})
        request_id = "sdk:offline:" + role
        receipt = factory.budget_effect(identity, grant.hash, "start", {
            "request_id": request_id,
            **{k: quote[k] for k in ("provider", "model", "api_mode", "base_url")},
            "request_sha256": hashlib.sha256(body).hexdigest(),
            "request_bytes": len(body), "output_tokens": 50})
        owner = types.SimpleNamespace(
            work_budget=factory.budget_effect,
            work_authority=factory.authorize_invocation,
            launch=types.SimpleNamespace(grant=grant, identity=identity,
                private_profile_snapshot=object()))
        return factory, owner, receipt, json.loads(body), request_id

    def test_root_and_child_enter_real_work_port_once_without_http(self):
        for role in ("root", "child"):
            with self.subTest(role=role):
                factory, owner, receipt, payload, request_id = self.prepared(role)
                selector = {"nonce": NONCE,
                    "host_label": "herdr-offline-controller-03414499dd0d1986",
                    "task_id": "offline188-" + NONCE, "run_token": NONCE,
                    "fencing_token": 1}
                # The only replaced observations are host label, cgroup and
                # root configuration files. Original grant/budget/intent and
                # fixture decision functions execute unchanged.
                original_open = os.open
                def open_proc(path, flags, *args, **kwargs):
                    name = os.fspath(path)
                    if name in ("/proc/self/attr/current", "/proc/self/cgroup"):
                        source = self.root / ("label" if name.endswith("current") else "cgroup")
                        return original_open(source, flags)
                    return original_open(path, flags, *args, **kwargs)
                (self.root / "label").write_text(transport._OFFLINE_HOST_LABEL + "\n")
                (self.root / "cgroup").write_text(
                    "0::/system.slice/herdr-offline-host-03414499dd0d1986.service\n")
                config = lambda path: (selector if str(path).endswith("offline-case-host.json")
                    else {"storage": str(self.storage)})
                socket_path = self.root / (role + ".sock")
                failures = []
                observed = []
                peer = PeerProcess(os.getpid(), 7, 12345, 17, 19,
                                   ("synthetic-held-python",))
                owner.launch._published_bootstrap_receipt = types.SimpleNamespace(
                    peer_pid=peer.pid, process_start_ticks=peer.start_ticks,
                    python_device=peer.exe_device, python_inode=peer.exe_inode)
                owner.launch.mount = types.SimpleNamespace(
                    verify_mounted=lambda pid, sealed: observed.append((pid, sealed)))
                owner.launch.sealed = "original-sealed-fixture"
                threads = []
                def server(connection):
                    try:
                        work_authority.dispatch_work_connection(owner, connection)
                    except BaseException as exc:
                        failures.append(exc)
                    finally:
                        connection.close()
                def socket_factory(*args):
                    client, server_endpoint = pair()
                    thread = threading.Thread(target=server, args=(server_endpoint,), daemon=True)
                    threads.append(thread); thread.start()
                    return client
                actual_execute = transport.execute_host_model
                def checked_execute(*args, **kwargs):
                    try: return actual_execute(*args, **kwargs)
                    except BaseException as exc:
                        failures.append(exc)
                        raise
                with patch.object(work_authority, "SOCKET_PATH", socket_path), \
                     patch("herdr.host_configuration._read_configuration", side_effect=config), \
                     patch.object(transport.os, "open", side_effect=open_proc), \
                     patch.object(transport, "_perform_http", side_effect=AssertionError("external HTTP reached")), \
                     patch.object(transport, "execute_host_model", side_effect=checked_execute), \
                     patch.object(work_authority, "inspect_peer", return_value=peer), \
                     patch.object(work_authority.socket, "socket", side_effect=socket_factory):
                    client = work_authority.WorkAuthorityClient()
                    args = (owner.launch.identity, owner.launch.grant.hash, request_id,
                            {"operation_id": receipt["operation_id"], "max_work_ms": 20000}, payload)
                    try: first = client.model_transport(*args)
                    except BaseException as exc:
                        raise AssertionError(f"{role}: {failures!r}") from exc
                    second = client.model_transport(*args)
                    factory.budget_effect(owner.launch.identity, owner.launch.grant.hash,
                        "returned", {"operation_id": receipt["operation_id"]})
                    crash_id = request_id + ":crash"
                    quote = {"provider": "nous", "model": transport._FIXTURE_MODEL,
                        "api_mode": "chat_completions", "base_url": transport.ENDPOINT}
                    body = canonical(payload)
                    crash = factory.budget_effect(owner.launch.identity, owner.launch.grant.hash,
                        "start", {"request_id": crash_id, **quote,
                                  "request_sha256": hashlib.sha256(body).hexdigest(),
                                  "request_bytes": len(body), "output_tokens": 50})
                    crash_args = (owner.launch.identity, owner.launch.grant.hash, crash_id,
                        {"operation_id": crash["operation_id"], "max_work_ms": 20000}, payload)
                    with patch.object(transport, "_perform_fixture",
                                      side_effect=RuntimeError("injected fixture crash")):
                        with self.assertRaises(PolicyDenied):
                            client.model_transport(*crash_args)
                    with patch.object(transport, "_perform_fixture",
                                      side_effect=AssertionError("consumed operation resent")):
                        with self.assertRaises(PolicyDenied):
                            client.model_transport(*crash_args)
                for thread in threads:
                    thread.join(5)
                    self.assertFalse(thread.is_alive())
                self.assertEqual([type(exc) for exc in failures],
                                 [RuntimeError, WorkContractError])
                self.assertEqual(str(failures[0]), "injected fixture crash")
                self.assertIn("never resend", str(failures[1]))
                self.assertEqual(first, second)
                self.assertEqual(first["kind"], "http_response")
                self.assertEqual(len(observed), 6)
                self.assertTrue((factory.storage / "model-transport" /
                    (crash["operation_id"] + ".intent.json")).is_file())
                self.assertFalse((factory.storage / "model-transport" /
                    (crash["operation_id"] + ".response.json")).exists())
                self.assertEqual(len(list((self.storage / ("offline-fixture-" + NONCE)).glob("*.json"))),
                                 1 if role == "root" else 2)


if __name__ == "__main__": unittest.main()
