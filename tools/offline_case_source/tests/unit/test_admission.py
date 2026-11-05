"""Inert tests for the default root to canonical-host client."""
import json
import struct
import unittest
from pathlib import Path
import reference_support
from types import SimpleNamespace
from unittest.mock import patch

from offline_case import admission
from offline_case import driver
from offline_case import host_service
from offline_case.native import NativeHost
from offline_case.case import CASE, NONCE, HOST_PROFILE, BUDGET, Denied, canonical, sha
from offline_case.publication import existing_runtime, render_host_unit


BUILD = {"files": {"fixture": "a" * 64}}
POLICY = json.dumps(reference_support.runtime_policy()).encode()
APPROVED_RUNTIME = existing_runtime(json.loads(POLICY))
HOST_PYTHON = Path(APPROVED_RUNTIME["executable"])
HOST_UNIT_BYTES = render_host_unit(json.loads(POLICY))
SELECTOR = {
    "schema": 1, "nonce": NONCE, "case_unit": CASE,
    "socket": str(admission.SOCKET), "host_unit": admission.HOST_UNIT,
    "host_uid": 1001, "host_gid": 1001, "host_label": HOST_PROFILE,
    "host_executable": str(HOST_PYTHON), "host_executable_sha256": APPROVED_RUNTIME["executable_sha256"],
    "host_entry_sha256": sha(b"entry"),
    "host_script_sha256": sha(b"server"),
    "host_unit_fragment": "/etc/systemd/system/" + admission.HOST_UNIT,
    "host_unit_sha256": sha(HOST_UNIT_BYTES),
    "host_profile_source_sha256": sha(b"host source"),
    "host_compiled_sha256": sha(b"host compiled"),
    "host_policy_sha256": sha(POLICY), "build_sha256": sha(canonical(BUILD)),
    "task_id": "existing-task", "run_token": "existing-run", "fencing_token": 7,
}
BINDING = {"nonce": NONCE, "build_sha256": SELECTOR["build_sha256"]}
BUILD["core_files"] = {"agent-stack/bin/agent-herdr-host-entrypoint": SELECTOR["host_entry_sha256"]}
BUILD["files"].update({"offline_case/host_service.py": SELECTOR["host_script_sha256"],
                       "units/" + admission.HOST_UNIT: SELECTOR["host_unit_sha256"],
                       "overlays/host-profile.apparmor": SELECTOR["host_profile_source_sha256"]})
SELECTOR["build_sha256"] = sha(canonical(BUILD))
BINDING["build_sha256"] = SELECTOR["build_sha256"]


class FakeTransport:
    def __init__(self): self.calls = []
    def exchange(self, packet):
        self.calls.append(packet)
        return {"schema": 1, "request_sha256": packet["request_sha256"], "value": True}


class AdmissionClient(unittest.TestCase):
    def _construct(self, selector=None, transport=None):
        selector = SELECTOR if selector is None else selector
        def read(path, maximum=0, root_owned=False):
            self.assertTrue(root_owned)
            return canonical(selector) if path == admission.SELECTOR else POLICY
        with patch.object(admission, "pinned_bytes", side_effect=read):
            return admission.NativeAdmission.from_configuration(build=BUILD, transport=transport)

    def test_default_client_uses_exact_existing_task_and_bounded_operations(self):
        wire = FakeTransport()
        client = self._construct(transport=wire)
        self.assertTrue(client.admit({"approved": "host must still validate"}, BINDING))
        self.assertTrue(client.fence(BINDING))
        self.assertEqual([row["operation"] for row in wire.calls], ["admit", "fence"])
        self.assertEqual({row["task_id"] for row in wire.calls}, {"existing-task"})
        self.assertEqual({row["fencing_token"] for row in wire.calls}, {7})
        for row in wire.calls:
            digest = row.pop("request_sha256")
            self.assertEqual(digest, sha(canonical(row)))

    def test_missing_or_changed_selector_denies_before_transport(self):
        for changed in ({**SELECTOR, "host_uid": 0},
                        {**SELECTOR, "build_sha256": "b" * 64},
                        {**SELECTOR, "host_policy_sha256": "c" * 64},
                        {**SELECTOR, "host_label": "unconfined"},
                        {**SELECTOR, "host_profile_source_sha256": "0" * 64},
                        {**SELECTOR, "extra": True},
                        {**SELECTOR, "fencing_token": 0}):
            with self.subTest(changed=changed):
                with self.assertRaises(Denied): self._construct(changed)

    def test_retained_selector_must_match_future_authority_before_host_effects(self):
        client = self._construct()
        self.assertEqual(client.selector_sha256, sha(canonical(SELECTOR)))
        class InertKernel:
            def loaded_profile_sha256(self, profile): return "a" * 64
        host = NativeHost(InertKernel(), admission=client)
        with patch("offline_case.native.os.geteuid", return_value=0):
            with self.assertRaisesRegex(Denied, "retained host selector"):
                host.preflight({"host_selector_sha256": "0" * 64,
                                "operator_compiled_sha256": "a" * 64}, BUILD,
                               Path("/opt/agent-platform/herdr-offline-03414499dd0d1986"))

    def test_reply_is_bound_to_exact_request(self):
        class WrongWire:
            def exchange(self, packet):
                return {"schema": 1, "request_sha256": "0" * 64, "value": True}
        client = self._construct(transport=WrongWire())
        with self.assertRaises(Denied): client.fenced(BINDING)
        with self.assertRaises(Denied): client.fenced({**BINDING, "nonce": "other"})

    def test_child_seal_reply_rejects_old_or_changed_contract_before_ingress(self):
        for changed in ({"outcome": "SDK_INITIALIZATION_ONLY"},
                        {"binding": {**BINDING, "nonce": "foreign"}},
                        {"managed_children": 2}, {"extra": True}):
            with self.subTest(changed=changed):
                class Wire:
                    def __init__(self): self.phases = []
                    def exchange(self, packet):
                        phase = packet["arguments"]["phase"]
                        self.phases.append(phase)
                        values = {"root": {"kind": "CHILD_PANE_READY"},
                                  "child-ticket": {"effect": "child-ticket"},
                                  "child-seal": {"binding": BINDING,
                                      "outcome": "BOOTSTRAP_CONTINUATION_ONLY",
                                      "root": True, "managed_children": 1}}
                        if phase == "ingress": raise AssertionError("ingress after bad seal")
                        value = {**values[phase], **changed} if phase == "child-seal" else values[phase]
                        return {"schema": 1, "request_sha256": packet["request_sha256"], "value": value}
                wire = Wire()
                client = self._construct(transport=wire)
                with patch.object(client, "_pump", return_value=SimpleNamespace(
                        perform=lambda effect, binding: self.assertEqual(binding, BINDING))):
                    with self.assertRaisesRegex(Denied, "child bootstrap continuation"):
                        client.run(BINDING, BUDGET)
                self.assertEqual(wire.phases, ["root", "child-ticket", "child-seal"])

    def test_canonical_denial_cannot_be_returned_as_a_successful_effect(self):
        class DenyingWire:
            def exchange(self, packet):
                return {"schema": 1, "request_sha256": packet["request_sha256"],
                        "value": {"denied": "canonical fence refused"}}
        client = self._construct(transport=DenyingWire())
        with self.assertRaisesRegex(Denied, "canonical host denied"):
            client.fence(BINDING)

    def test_peer_requires_uid_label_cgroup_executable_and_stable_start(self):
        peer_selector = {**SELECTOR, "host_executable_sha256": sha(b"python"),
                         "host_unit_sha256": sha(b"unit")}
        transport = admission.UnixHostTransport(peer_selector)
        ticks = b"42 (host) S " + b"0 " * 18 + b"17 " + b"0\n"
        class Connection:
            def getsockopt(self, *_): return struct.pack("3i", 42, 1001, 1001)
        def process_read(path, maximum):
            if path.name == "stat": return ticks
            if path.name == "current": return (HOST_PROFILE + " (enforce)\n").encode()
            if path.name == "cgroup":
                return ("0::/system.slice/" + admission.HOST_UNIT + "\n").encode()
            if path.name == "cmdline":
                return (SELECTOR["host_executable"] + "\0-I\0-B\0" +
                        str(admission.HOST_ENTRY) + "\0" + admission.HOST_TARGET + "\0").encode()
            raise AssertionError(path)
        def source(path, maximum=0, root_owned=False):
            return (b"server" if path == admission.HOST_SCRIPT else
                    b"entry" if path == admission.HOST_ENTRY else
                    b"unit" if path == Path(SELECTOR["host_unit_fragment"]) else b"python")
        with patch.object(admission, "_process_read", side_effect=process_read), \
             patch.object(admission.os, "readlink", return_value=SELECTOR["host_executable"]), \
             patch.object(admission, "pinned_bytes", side_effect=source):
            transport._peer(Connection())
        with patch.object(admission, "_process_read", side_effect=process_read), \
             patch.object(admission.os, "readlink", return_value=SELECTOR["host_executable"]), \
             patch.object(admission, "pinned_bytes", return_value=b"changed"):
            with self.assertRaises(Denied): transport._peer(Connection())

    def test_host_service_rejects_foreign_request_before_dispatch(self):
        packet = {"schema": 1, "operation": "admit", "case": NONCE,
                  "task_id": SELECTOR["task_id"], "run_token": SELECTOR["run_token"],
                  "fencing_token": SELECTOR["fencing_token"], "binding": BINDING,
                  "arguments": {"authority": {}}}
        packet["request_sha256"] = sha(canonical(packet))
        host_service.check_request(packet, SELECTOR)
        with self.assertRaises(Denied):
            host_service.check_request({**packet, "operation": "run"}, SELECTOR)

    def test_server_transport_authenticates_before_canonical_dispatch(self):
        packet = {"schema": 1, "operation": "admit", "case": NONCE,
                  "task_id": SELECTOR["task_id"], "run_token": SELECTOR["run_token"],
                  "fencing_token": SELECTOR["fencing_token"], "binding": BINDING,
                  "arguments": {"authority": {"purpose": "fixture"}}}
        packet["request_sha256"] = sha(canonical(packet))
        class Connection:
            def __init__(self, value):
                raw = canonical(value)
                self.incoming = bytearray(struct.pack("!I", len(raw)) + raw)
                self.outgoing = bytearray()
            def settimeout(self, value): self.timeout = value
            def recv(self, amount):
                result = self.incoming[:amount]
                del self.incoming[:amount]
                return result
            def sendall(self, raw): self.outgoing.extend(raw)
        calls = []
        dispatch = lambda value: (calls.append(value), {"checked": True})[1]
        good = Connection(packet)
        host_service.exchange_one(good, SELECTOR, dispatch,
                                  peer_check=lambda _: (123, 17))
        answer = json.loads(good.outgoing[4:])
        self.assertEqual(answer["request_sha256"], packet["request_sha256"])
        self.assertEqual(answer["value"], {"checked": True})
        self.assertEqual(calls, [packet])
        bad = Connection({**packet, "run_token": "foreign"})
        with self.assertRaises(Denied):
            host_service.exchange_one(bad, SELECTOR, dispatch,
                                      peer_check=lambda _: (123, 17))
        self.assertEqual(calls, [packet])
        rejected = Connection(packet)
        host_service.exchange_one(rejected, SELECTOR,
            lambda _: (_ for _ in ()).throw(Denied("canonical fence refused")),
            peer_check=lambda _: (123, 17))
        self.assertEqual(json.loads(rejected.outgoing[4:])["value"],
                         {"denied": "canonical fence refused"})

    def test_canonical_component_constructor_uses_existing_uid_store_and_budget(self):
        calls = []
        task = {"attempt_state": "dispatching", "id": "existing-task",
                "run_token": "existing-run", "fencing_token": 7,
                "repo": "org/repo", "safety_profile": "fixed"}
        raw = {"host_uid": 1001, "task_store_root": "/canonical/tasks"}
        def work(root, selected, **kwargs):
            calls.append(("work", root, selected, kwargs))
            return SimpleNamespace(budget_authority=object())
        api = SimpleNamespace(HOST_POLICY_CONFIG=Path("/etc/herdr/host-policy.json"),
            _read_configuration=lambda _: raw,
            read_canonical_parent=lambda root, task_id, run: task,
            build_host_policy_factory=lambda **kw: calls.append(("factory", kw)),
            AdmissionControl=lambda **kw: calls.append(("control", kw)) or object(),
            AdmissionAuditLog=lambda path: ("audit", path), PlanBudget=lambda: "budget",
            policy_for_profile=lambda name: ("consumer", name),
            AdmissionRegistry=lambda **kw: calls.append(("registry", kw)) or object(),
            DEFAULT_ADMISSION_AUDIT=Path("/canonical/admission.jsonl"),
            DEFAULT_ADMISSION_REGISTRY=Path("/canonical/admission-registry.json"),
            build_root_work_factory=work,
            InvocationIdentity=lambda **kw: SimpleNamespace(**kw))
        with patch.object(host_service.os, "geteuid", return_value=1001):
            result = host_service.canonical_components("existing-task", "existing-run", api=api)
        self.assertEqual(result["identity"].fencing_token, 7)
        self.assertEqual([name for name, *_ in calls],
                         ["factory", "control", "registry", "work"])
        self.assertEqual(calls[2][1]["path"], api.DEFAULT_ADMISSION_REGISTRY)
        self.assertEqual(calls[3][3]["claimed_identity"], result["identity"])

    def test_default_cleanup_constructs_pinned_host_client(self):
        calls = []
        token = object()
        class Custody:
            def __init__(self, path): calls.append(("custody", path))
            def __enter__(self): return self
            def __exit__(self, *_): pass
        class Host:
            def __init__(self, *, build, admission):
                self.admission = admission
                calls.append(("host", build, admission))
        class Case:
            def __init__(self, custody, host, **kwargs):
                self.host = host
            def cleanup(self):
                calls.append(("cleanup", self.host.admission))
                return {"phase": "RETAINED_UNKNOWN"}
        with patch.object(driver, "pinned_bytes", return_value=canonical(BUILD)), \
             patch.object(driver, "validate_build"), \
             patch.object(driver.NativeAdmission, "from_configuration", return_value=token) as factory, \
             patch.object(driver, "NativeHost", Host), \
             patch.object(driver, "CaseDriver", Case), \
             patch("builtins.print"):
            self.assertEqual(driver.main(["--cleanup"], custody_type=Custody), 0)
        factory.assert_called_once_with(build=BUILD)
        self.assertIn(("host", BUILD, token), calls)
        self.assertIn(("cleanup", token), calls)


if __name__ == "__main__": unittest.main()
