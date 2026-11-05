"""Inert source tests. Never instantiate LinuxOps, SDK, services or namespaces."""
from contextlib import contextmanager
from dataclasses import replace
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import reference_support
import stat
import sys
import types
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE))
import trusted_prepare as prep
import native_preparation as ticket_source
import core_bridge as bridge

ORIGINAL = reference_support.accepted_root() / "proposed/core"
# Only the actual original pure identity/canonical value objects are imported.
# No SDK, issuer, broker, bootstrap factory or Linux implementation is started.
sys.path.insert(0, str(ORIGINAL))
from herdr.security import InvocationIdentity, canonical_json_bytes


def actual_plan_api():
    """Execute unchanged AST definitions from the public source reference.

    ApprovedPrivateMountPlan is the actual accepted class, including all read,
    identity, inode and byte-binding checks. Only its protected filesystem
    boundary is injected; no all-true replacement for authorize/read is used.
    """
    source = (ORIGINAL / "herdr/private_mount_plan.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    keep = {"ApprovedPrivateMountPlan", "request_for", "require"}
    body = [ast.ImportFrom(module="__future__", names=[ast.alias(name="annotations")], level=0)]
    body += [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and node.name in keep]
    module = ast.fix_missing_locations(ast.Module(body=body, type_ignores=[]))
    namespace = {"__name__": "herdr.actual_accepted_private_plan", "__package__": "herdr", "Path": Path,
        "stat": stat, "os": __import__("os"), "hashlib": hashlib,
        "dataclass": __import__("dataclasses").dataclass,
        "InvocationIdentity": InvocationIdentity, "canonical_json_bytes": canonical_json_bytes,
        "SecurityError": RuntimeError, "AUTHORITY_ROOT": Path("/etc/herdr/launch-plans"),
        "VERSION": "herdr-private-mount-plan-1"}
    synthetic_module = types.ModuleType(namespace["__name__"])
    synthetic_module.__dict__.update(namespace)
    sys.modules[synthetic_module.__name__] = synthetic_module
    exec(compile(module, "accepted_private_mount_plan.reference", "exec"), synthetic_module.__dict__)
    return synthetic_module


class Executed(Exception): pass


class FakeOps:
    """Every low-level effect is captured. A stray real OS call fails tests."""
    def __init__(self, *, fail=None, label="herdr-offline-prep-03414499dd0d1986 (enforce)"):
        self.calls = []; self.fail = fail; self.current_label = label
    def record(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        if self.fail == name: raise OSError("synthetic low-level failure")
    def euid(self): self.record("euid"); return 0
    def threads(self): self.record("threads"); return 1
    def label(self): self.record("label"); return self.current_label
    def fstat(self, fd):
        self.record("fstat", fd)
        return types.SimpleNamespace(st_mode=stat.S_IFDIR | 0o755 if fd == 4 else stat.S_IFREG | 0o444,
                                     st_dev=1, st_ino=fd)
    def __getattr__(self, name):
        allowed = {"unshare", "mount", "fork_namespace_init", "create_private_root", "target",
            "private_devices", "copy_sealed_file", "pivot_to", "chdir", "close_except", "setgroups",
            "map_worker_userns", "parent_fence_begin", "parent_fence_finish", "verify_parent_fence", "verify_stdio",
            "replace_resolver", "drop_bounding_capabilities", "setresgid", "setresuid", "clear_capabilities",
            "change_profile", "no_new_privileges", "install_filter", "verify_worker_identity"}
        if name not in allowed: raise AssertionError("Unexpected effect boundary: " + name)
        if name == "parent_fence_begin": return lambda: (self.record(name), 7)[1]
        return lambda *a, **k: self.record(name, *a, **k)
    def execve(self, *args): self.record("execve", *args); raise Executed()


def simple_recipe():
    return prep.Recipe((prep.Mount("/", None, False, "tmpfs"),
        prep.Mount("/run/herdr/policy-code", 4, True, "directory", 1, 4),
        prep.Mount("/home/agentops/.hermes/profiles/fixture/config.yaml", 5, True, "sealed-profile-data", 1, 5),
        prep.Mount("/proc", None, False, "proc"), prep.Mount("/dev", None, False, "dev"),
        prep.Mount("/tmp", None, False, "tmpfs")), (), ("/",),
        "/home/agentops/tmp/hermes-fixture/workspace", {"HOME": "/home/agentops"},
        ("/bin/bash", "--noprofile", "--norc", "-i"), "a" * 64)


def execute(ops, recipe=None, **extra):
    program = b"inert fixed BPF bytes; never installed"
    arguments = dict(root="/run/herdr-offline-private-root-fixture",
        identity_environment={"HERDR_POLICY_TASK_ID": "fixture"}, safe_environment={},
        filter_program=program, filter_sha256=hashlib.sha256(program).hexdigest(),
        prep_profile="herdr-offline-prep-03414499dd0d1986")
    arguments.update(extra)
    with patch.object(prep, "LinuxOps", side_effect=AssertionError("real LinuxOps forbidden")):
        return prep.prepare_and_exec(recipe or simple_recipe(), ops, **arguments)


class NativeBridgeTests(unittest.TestCase):
    def test_bridge_prepares_typed_root_then_distinct_retained_child(self):
        events = []
        class Identity:
            def __init__(self, task):
                self.task_id = task
                self.agent_id = task
                self.run_token = "run-" + task
                self.fencing_token = 1
                self.parent_task_id = "root" if task == "child" else "operator"
                self.parent_agent_id = "root" if task == "child" else "operator"
            def to_json(self): return {"task_id": self.task_id}
        class Prepared:
            def __init__(self, identity, parent_hash=None):
                self.identity = identity
                self.grant = types.SimpleNamespace(hash="grant-" + identity.task_id,
                    parent_hash=parent_hash)
                self.sealed = None
                self.private_profile_snapshot = types.SimpleNamespace(name="quantlab",
                    identity={"manifest_sha256": identity.task_id})
                self.mount = types.SimpleNamespace(private_workspace_pin="pin-" + identity.task_id)
            def bind_result_slot(self, *args): events.append((self.identity.task_id, "bind"))
            def prepare_private_command(self, builder):
                builder(); events.append((self.identity.task_id, "private_command"))
            def verify_bootstrap(self): events.append((self.identity.task_id, "verify_bootstrap"))
        class Factory:
            def __init__(self, parent_hash=None): self.parent_hash = parent_hash
            def prepare(self, *, identity, workspace, tools, permissions):
                events.append((identity.task_id, "factory_prepare"))
                return Prepared(identity, self.parent_hash)
            def prepare_child(self, *, identity, workspace, tools, permissions):
                events.append((identity.task_id, "factory_prepare_child"))
                return self.prepare(identity=identity, workspace=workspace, tools=tools,
                                    permissions=permissions)
        class Registry: pass
        class OwnershipRegistry:
            root = Path('/var/lib/herdr')
        class Scheduler:
            ownership_registry = OwnershipRegistry()
            def __init__(self):
                self._tasks = {task: types.SimpleNamespace(agent_id=task,
                    run_token="run-" + task, fencing_token=1,
                    parent_task_id="root" if task == "child" else None,
                    parent_agent_id="root" if task == "child" else None,
                    node=types.SimpleNamespace(tools=(), permissions=()))
                    for task in ("root", "child")}
        class Admission: pass
        class Journal:
            def publish_once(self, *args): events.append(("journal", args[0]))
        api = types.SimpleNamespace(HostPolicyLaunchFactory=Factory,
            AdmissionRegistry=Registry, AdmissionControl=Admission,
            OwnershipRegistry=OwnershipRegistry, DynamicChildScheduler=Scheduler,
            PreparedPolicyLaunch=Prepared, InvocationIdentity=Identity,
            HOST_POLICY_CONFIG=Path('/etc/herdr/host-policy.json'),
            build_host_policy_factory=lambda **kw: Factory(kw['parent_grant'].hash),
            reserve_empty_result=lambda *args: events.append((args[1].task_id, "reserve_result")),
            sandbox=types.SimpleNamespace(POLICY=Path('/approved-policy'),
                command=lambda *args, **kw: events.append(("sandbox", kw))))
        bridge_host = bridge.NativeHerdrHost(api=api, factory=Factory(), registry=Registry(),
            admission=Admission(), scheduler=Scheduler(),
            runner=object(), prep=object(), journal=Journal())
        def spec(task):
            return bridge.LaunchSpec(Identity(task), Path('/workspace'), Path('/result'),
                'idem-' + task, (), (), Path('/bin/bash'), 'marker-' + task, 'pane-' + task)
        root_spec, child_spec = spec('root'), spec('child')
        root = bridge_host.prepare(root_spec)
        self.assertEqual(events[:4], [('journal', 'prepare-intent-root'),
                                      ('root', 'factory_prepare'), ('root', 'reserve_result'),
                                      ('root', 'bind')])
        root.sealed = {"observed": True}
        child = bridge_host.prepare(child_spec, parent=root,
            retained_parent_verify=lambda: (root.grant, root.private_profile_snapshot.identity))
        self.assertEqual(child.grant.parent_hash, root.grant.hash)
        self.assertNotEqual(root.grant.hash, child.grant.hash)
        self.assertIn(('child', 'factory_prepare_child'), events)
        self.assertIn(('child', 'private_command'), events)
        self.assertEqual([kw["admission_root"] for name, kw in events if name == "sandbox"],
                         [Path('/var/lib/herdr'), Path('/var/lib/herdr')])

    def test_native_runner_sends_only_literal_accepted_commands(self):
        calls = []
        class IO:
            def run(self, arguments, *, timeout):
                calls.append((arguments, timeout))
                return types.SimpleNamespace(returncode=0,
                    stdout=b'{"result":{"pane":{"pane_id":"owned"}}}', stderr=b'')
        runner = bridge.NativeHerdrRunner('/opt/herdr/pinned/bin/herdr', IO())
        self.assertEqual(runner.invoke(['pane', 'get', 'owned'], timeout_seconds=4)
                         ['result']['pane']['pane_id'], 'owned')
        self.assertEqual(calls, [(['/opt/herdr/pinned/bin/herdr', 'pane', 'get', 'owned'], 4)])
        with self.assertRaises(bridge.Denied):
            runner.invoke(['pane', 'close', 'foreign'], timeout_seconds=4)
        self.assertEqual(len(calls), 1)

    def test_accepted_prompt_helper_uses_bounded_wait_output(self):
        # Execute the accepted pure helper body with a synthetic command IO.
        # This checks the actual callback grammar, including the challenge
        # response that the former runner rejected before SDK bootstrap.
        import re
        import secrets
        import time
        source = (ORIGINAL / "agent-stack/bin/agent_durable_sandbox.py").read_text()
        definition = next(node for node in ast.parse(source).body
                          if isinstance(node, ast.FunctionDef) and node.name == "verify_pane_prompt")
        module = ast.fix_missing_locations(ast.Module(body=[definition], type_ignores=[]))
        namespace = {"time": time, "secrets": secrets, "re": re,
                     "_pane_shell_instance": lambda *_: (42, 17)}
        exec(compile(module, "accepted_prompt_helper", "exec"), namespace)
        calls = []
        class IO:
            def run(self, arguments, *, timeout):
                calls.append((arguments, timeout))
                op = arguments[1:3]
                if op == ["pane", "process-info"]:
                    result = {"result": {"process_info": {"shell_pid": 42}}}
                elif op == ["pane", "run"]:
                    return types.SimpleNamespace(returncode=0, stdout=b"", stderr=b"")
                elif op == ["pane", "wait-output"]:
                    nonce = arguments[5][1:-1]
                    result = {"result": {"type": "output_matched", "pane_id": "owned",
                        "matched_line": nonce, "read": {"pane_id": "owned", "text": nonce + "\n"},
                        "revision": 1}}
                else:
                    raise AssertionError(op)
                return types.SimpleNamespace(returncode=0, stdout=json.dumps(result).encode(), stderr=b"")
        runner = bridge.NativeHerdrRunner("/opt/herdr/pinned/bin/herdr", IO())
        namespace["verify_pane_prompt"](runner.invoke, "owned", "marker",
                                          _instance_reader=lambda *_: (42, 17))
        self.assertEqual([args[1:3] for args, _ in calls],
                         [["pane", "process-info"], ["pane", "run"],
                          ["pane", "wait-output"], ["pane", "process-info"]])
        with self.assertRaises(bridge.Denied):
            runner.invoke(["pane", "wait-output", "owned", "--regex", ".*",
                           "--source", "recent-unwrapped", "--lines", "20",
                           "--timeout", "1000"], timeout_seconds=5)

    def test_preparation_custody_permissions_are_declared(self):
        profile = (HERE / "overlays/trusted-preparation.apparmor").read_text()
        unit = (HERE / "units/herdr-offline-03414499dd0d1986.service").read_text()
        operator = (HERE / "units/herdr-offline-operator-03414499dd0d1986.service").read_text()
        base = "/var/lib/herdr-offline-03414499dd0d1986"
        self.assertIn(f"{base}/{{authority.json,state.json,used-*.json}} r,", profile)
        self.assertIn(f"{base}/native-prep-intent-*.json rw,", profile)
        self.assertIn("ReadWritePaths=" + base, operator)
        self.assertIn("AppArmorProfile=herdr-offline-observer-03414499dd0d1986", unit)

    def test_preparation_entry_matches_case_start_phase_and_owned_cgroup(self):
        import prep_entry
        from offline_case.case import NONCE, canonical, sha
        import time
        authority = {"deadline": int(time.time()) + 100}
        binding = {"nonce": NONCE, "authority_sha256": sha(canonical(authority))}
        marker = dict(binding)
        record = {"case_binding": binding}
        state = {"binding": binding, "phase": "START_INTENT"}
        values = {prep_entry.CUSTODY / "authority.json": authority,
            prep_entry.CUSTODY / ("used-" + NONCE + ".json"): marker,
            prep_entry.CUSTODY / "state.json": state}
        with patch.object(prep_entry, "protected_json", side_effect=lambda path: values[path]):
            prep_entry.consumed_case(record)
            for phase in ("PLAN_INTENT", "PLAN_READY", "PREPARED"):
                values[prep_entry.CUSTODY / "state.json"] = {**state, "phase": phase}
                with self.assertRaises(RuntimeError): prep_entry.consumed_case(record)
        source = (HERE / "prep_entry.py").read_text()
        transport = (HERE / "native_preparation_transport.py").read_text()
        unit = (HERE / "units/herdr-offline-03414499dd0d1986.service").read_text()
        self.assertIn('state["phase"] == "START_INTENT"', source)
        self.assertIn('PREP_CGROUP = "/system.slice/herdr-offline-" + NONCE + ".service"', transport)
        self.assertIn('AppArmorProfile=herdr-offline-observer-03414499dd0d1986', unit)
        self.assertIn('from offline_case.case_anchor import main; main()', unit)

    def test_actual_native_unit_entry_accepts_only_role_phase_and_consumed_child(self):
        """Reach the unit's native/prep_entry.py, never the top-level shim."""
        spec = importlib.util.spec_from_file_location("inert_native_unit_entry", HERE / "native/prep_entry.py")
        entry = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(entry)
        from offline_case.case import NONCE, canonical, sha
        authority = {"deadline": 1793810588}
        binding = {"nonce": NONCE, "authority_sha256": sha(canonical(authority))}
        roster_path = Path("/etc/herdr/offline-03414499dd0d1986/roster.json")
        roster = {"preparer": {"entrypoint": str((HERE / "native/prep_entry.py").absolute()),
            "files": {name: sha(name.encode()) for name in
                ("prep_entry.py", "prep_entry_v2.py", "trusted_prepare.py",
                 "case_roster.py", "preparation_contract.py")}},
            "case_binding": binding, "deadline": authority["deadline"]}
        values = {roster_path: roster, entry.CUSTODY / "authority.json": authority,
            entry.CUSTODY / ("used-" + NONCE + ".json"): dict(binding),
            entry.CUSTODY / "state.json": {"binding": binding, "phase": "START_INTENT"}}
        calls = []
        shim = types.ModuleType("prep_entry_v2")
        shim.run = lambda role, *_args, **kwargs: calls.append((role, kwargs)) or 0
        child = ["--execute", "child", "--identity-sha256", "a" * 64]
        original_path = list(sys.path)
        try:
            with patch.object(entry, "protected_json", side_effect=lambda path: values[path]), \
                 patch.object(entry, "protected_bytes", side_effect=lambda path: Path(path).name.encode()), \
                 patch.object(entry.os, "geteuid", return_value=0), \
                 patch.dict(sys.modules, {"prep_entry_v2": shim}), \
                 patch("time.time", return_value=authority["deadline"] - 1):
                self.assertEqual(entry.main(child), 0)
                self.assertEqual(calls, [("child", {"identity_sha256": "a" * 64})])
                for phase in ("ADMITTED", "PREPARED", "FINISHED", "CONSUMED"):
                    values[entry.CUSTODY / "state.json"] = {"binding": binding, "phase": phase}
                    with self.assertRaises(RuntimeError): entry.main(child)
                values[entry.CUSTODY / "state.json"] = {"binding": binding, "phase": "START_INTENT"}
                with self.assertRaises(RuntimeError): entry.main(["--execute", "root"])
                for phase in ("ADMITTED", "PREPARED"):
                    values[entry.CUSTODY / "state.json"] = {"binding": binding, "phase": phase}
                    self.assertEqual(entry.main(["--execute", "root"]), 0)
                self.assertEqual(len(calls), 3)
                values[entry.CUSTODY / "state.json"] = {"binding": binding, "phase": "START_INTENT"}
                values[entry.CUSTODY / ("used-" + NONCE + ".json")] = {**binding, "challenge": "replayed"}
                with self.assertRaises(RuntimeError): entry.main(child)
                values[entry.CUSTODY / ("used-" + NONCE + ".json")] = dict(binding)
                with patch("time.time", return_value=authority["deadline"]):
                    with self.assertRaises(RuntimeError): entry.main(child)
                roster["preparer"]["files"]["prep_entry_v2.py"] = "0" * 64
                with self.assertRaises(RuntimeError): entry.main(child)
                self.assertEqual(len(calls), 3)
        finally:
            sys.path[:] = original_path

    def test_setup_precedes_fixed_worker_transition_and_sdk_exec(self):
        ops = FakeOps()
        with self.assertRaises(Executed): execute(ops)
        names = [row[0] for row in ops.calls]
        pos = lambda x: names.index(x)
        self.assertLess(pos("unshare"), pos("mount"))
        self.assertLess(pos("mount"), pos("pivot_to"))
        self.assertLess(pos("pivot_to"), pos("close_except"))
        self.assertLess(pos("close_except"), pos("setresuid"))
        self.assertLess(pos("clear_capabilities"), pos("change_profile"))
        self.assertLess(pos("change_profile"), pos("install_filter"))
        self.assertLess(pos("verify_worker_identity"), pos("execve"))
        transition = pos("change_profile")
        self.assertFalse({"mount", "unshare", "pivot_to", "write_self", "setresuid", "setresgid"}
                         & set(names[transition + 1:]))
        self.assertIn(("change_profile", (prep.PROFILE,), {}), ops.calls)
        self.assertIn(("close_except", ({0, 1, 2},), {}), ops.calls)
        self.assertIn(("map_worker_userns", (1001, 1001), {}), ops.calls)
        self.assertIn(("parent_fence_finish", (7,), {}), ops.calls)
        self.assertIn(("verify_stdio", (), {}), ops.calls)
        self.assertEqual(ops.calls[-1][1][0], "/bin/bash")

    def test_parent_mapping_and_death_fence_follow_private_pivot(self):
        ops = FakeOps()
        with self.assertRaises(Executed): execute(ops)
        names = [row[0] for row in ops.calls]
        self.assertLess(names.index("pivot_to"), names.index("map_worker_userns"))
        self.assertLess(names.index("map_worker_userns"), names.index("parent_fence_begin"))
        self.assertLess(names.index("setresuid"), names.index("parent_fence_finish"))
        self.assertLess(names.index("parent_fence_finish"), names.index("change_profile"))
        self.assertLess(names.index("change_profile"), names.index("verify_parent_fence"))
        self.assertLess(names.index("verify_parent_fence"), names.index("install_filter"))
        self.assertLess(names.index("verify_stdio"), names.index("unshare"))
        self.assertNotIn("write_self", names)

    def test_sealed_resolver_may_cover_only_its_approved_literal(self):
        identity = object()
        class Plan:
            sha256 = "a" * 64
            def __init__(self): self.identity = identity
            def authorize(self, descriptors, argv):
                return {"authority_sha256": self.sha256}
        desc = [{"fd": 5, "target": "/etc/resolv.conf", "kind": "sealed-resolver-data",
                 "device": 1, "inode": 5}]
        argv = ["/usr/bin/bwrap", "--tmpfs", "/", "--ro-bind", "/etc/resolv.conf",
                "/etc/resolv.conf", "--ro-bind-data", "5", "/etc/resolv.conf",
                "--unshare-pid", "--die-with-parent", "--disable-userns", "--cap-drop", "ALL",
                "--setenv", "HOME", "/home/agentops",
                "--chdir", "/work", "--remount-ro", "/", "--", "/bin/bash",
                "--noprofile", "--norc", "-i"]
        api = types.SimpleNamespace(ApprovedPrivateMountPlan=Plan,
            SYSTEM_RUNTIME_FILES={"/etc/resolv.conf"}, RESOLVER_TARGETS={"/etc/resolv.conf"},
            approved_system_files={"/etc/resolv.conf": "b" * 64}, fd_sha256=lambda fd: "b" * 64)
        held = {"/etc/resolv.conf": {"fd": 6, "device": 1, "inode": 6, "sha256": "b" * 64}}
        recipe = prep.recipe_from_approved(Plan(), desc, argv, identity=identity,
                                           api=api, system_fds=held)
        self.assertEqual([m.kind for m in recipe.mounts], ["tmpfs", "file", "sealed-resolver-data"])
        ops = FakeOps()
        with self.assertRaises(Executed): execute(ops, recipe)
        names = [row[0] for row in ops.calls]
        self.assertLess(names.index("replace_resolver"), names.index("copy_sealed_file"))
        swapped = argv[:]
        swapped[4:10] = ["--ro-bind-data", "5", "/etc/resolv.conf",
                         "--ro-bind", "/etc/resolv.conf", "/etc/resolv.conf"]
        with self.assertRaises(prep.Denied):
            prep.recipe_from_approved(Plan(), desc, swapped, identity=identity,
                                      api=api, system_fds=held)

    def test_stdio_boundary_rejects_arbitrary_targets(self):
        import os
        view = object.__new__(prep.LinuxOps)
        null = types.SimpleNamespace(st_mode=stat.S_IFCHR | 0o666, st_rdev=os.makedev(1, 3))
        modes = {0: os.O_RDONLY, 1: os.O_WRONLY, 2: os.O_WRONLY}
        with patch.object(prep.os, "fstat", return_value=null), patch.object(
                prep.fcntl, "fcntl", side_effect=lambda fd, _: modes[fd]):
            view.verify_stdio()
        foreign = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o600, st_rdev=0)
        with patch.object(prep.os, "fstat", return_value=foreign), patch.object(
                prep.fcntl, "fcntl", side_effect=lambda fd, _: modes[fd]):
            with self.assertRaises(prep.Denied): view.verify_stdio()

    def test_worker_domain_cannot_be_used_for_setup(self):
        ops = FakeOps(label=prep.PROFILE + " (enforce)")
        with self.assertRaisesRegex(prep.Denied, "exact_trusted_prep"): execute(ops)
        self.assertNotIn("mount", [x[0] for x in ops.calls])

    def test_unknown_or_unconfined_setup_domain_is_not_allowed(self):
        for label in ("unconfined", "herdr-offline-prep-foreign (enforce)", "x (complain)"):
            with self.subTest(label=label):
                ops = FakeOps(label=label)
                with self.assertRaises(prep.Denied): execute(ops)
                self.assertNotIn("unshare", [x[0] for x in ops.calls])

    def test_every_preparation_failure_stops_before_worker_exec(self):
        for fail in ("unshare", "mount", "fork_namespace_init", "create_private_root", "target",
                     "copy_sealed_file", "private_devices", "pivot_to", "chdir", "close_except",
                     "setgroups", "map_worker_userns", "parent_fence_finish", "verify_stdio", "drop_bounding_capabilities", "setresgid",
                     "setresuid", "clear_capabilities", "change_profile", "no_new_privileges",
                     "install_filter", "verify_worker_identity"):
            with self.subTest(fail=fail):
                ops = FakeOps(fail=fail)
                with self.assertRaises(OSError): execute(ops)
                self.assertNotIn("execve", [x[0] for x in ops.calls])

    def test_filter_tamper_and_inode_change_deny_before_namespace(self):
        ops = FakeOps()
        with self.assertRaisesRegex(prep.Denied, "filter_binding"): execute(ops, filter_sha256="0" * 64)
        self.assertEqual(ops.calls, [])
        ops = FakeOps(); recipe = simple_recipe()
        recipe = replace(recipe, mounts=(recipe.mounts[0], replace(recipe.mounts[1], inode=999), *recipe.mounts[2:]))
        with self.assertRaisesRegex(prep.Denied, "source_changed"): execute(ops, recipe)
        self.assertNotIn("unshare", [x[0] for x in ops.calls])

    def test_no_host_root_bind_or_direct_stage2_exec_in_syscall_sequence(self):
        ops = FakeOps()
        with self.assertRaises(Executed): execute(ops)
        mounts = [x[1] for x in ops.calls if x[0] == "mount"]
        self.assertFalse(any(x[0] == "/" and x[3] & prep.MS_BIND for x in mounts))
        self.assertTrue(all(x[0] is None or x[0] in {"tmpfs", "proc"} or x[0].startswith("/proc/self/fd/")
                            or x[0].startswith("/run/herdr-offline-private-root-fixture/") for x in mounts))
        self.assertFalse(any("agent-hermes-policy-run" in str(x) for x in ops.calls))

    def test_actual_typed_plan_binding_not_all_true_guard_fixture(self):
        api = actual_plan_api()
        identity = InvocationIdentity("fixture", "root", "operator", "case", "root-task", "run", 7)
        descriptors = [{"source": "/proc/222/fd/4", "fd": 4, "device": 1, "inode": 4,
                        "kind": "directory", "target": "/run/herdr/policy-code"}]
        argv = ["/usr/bin/bwrap", "--tmpfs", "/", "--ro-bind-fd", "4", "/run/herdr/policy-code",
                "--unshare-pid", "--die-with-parent", "--disable-userns", "--cap-drop", "ALL", "--chdir", "/work",
                "--remount-ro", "/", "--", "/bin/bash", "--noprofile", "--norc", "-i"]
        record = api.request_for(identity, descriptors, argv)
        conf = types.ModuleType("herdr.host_configuration")
        conf._read_configuration = lambda name: json.loads(json.dumps(record))
        inode = types.SimpleNamespace(st_dev=1, st_ino=3, st_size=1000)
        with patch.dict(sys.modules, {"herdr.host_configuration": conf}), patch.object(Path, "lstat", return_value=inode):
            name = hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json"
            plan = api.ApprovedPrivateMountPlan.read(Path("/etc/herdr/launch-plans") / name, identity)
            fixture_api = types.SimpleNamespace(ApprovedPrivateMountPlan=api.ApprovedPrivateMountPlan,
                SYSTEM_RUNTIME_FILES=frozenset(), approved_system_files={})
            recipe = prep.recipe_from_approved(plan, descriptors, argv, identity=identity,
                                              api=fixture_api, system_fds={})
            self.assertEqual(recipe.plan_sha256, plan.sha256)
            for tampered in ({**descriptors[0], "inode": 99}, {**descriptors[0], "target": "/mnt/alias"}):
                with self.assertRaises(RuntimeError):
                    prep.recipe_from_approved(plan, [tampered], argv, identity=identity, api=fixture_api, system_fds={})
            changed = [*argv[:-1], "bad"]
            with self.assertRaises(RuntimeError):
                prep.recipe_from_approved(plan, descriptors, changed, identity=identity, api=fixture_api, system_fds={})
            record["writable_targets"] = ["/run/herdr/policy-code"]
            with self.assertRaises(RuntimeError): plan.authorize(descriptors, argv)

    def test_untyped_or_self_minted_preparation_is_denied(self):
        api = types.SimpleNamespace(PreparedPolicyLaunch=type("Prepared", (), {}))
        with self.assertRaisesRegex(RuntimeError, "prepared_unsealed"):
            ticket_source.NativePreparationTicket.admit(object(), case_binding={}, native_argv=[], api=api)
        with self.assertRaisesRegex(RuntimeError, "host_admitted"):
            ticket_source.NativePreparationTicket(None, None, (), (), {}, "a" * 64, object())

    def test_actual_bootstrap_entry_order_is_wired_without_private_stage2(self):
        # No execution of SDK or accepted bootstrap: inspect the actual adapter
        # and assert its concrete call order, not duplicated boolean receipts.
        source = ast.parse((HERE / "core_bridge.py").read_bytes())
        native = next(n for n in source.body if isinstance(n, ast.ClassDef) and n.name == "NativeHerdrHost")
        method = next(n for n in native.body if isinstance(n, ast.FunctionDef) and n.name == "start_sdk")
        attributes = [(n.lineno, n.func.attr) for n in ast.walk(method) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)]
        lines = dict((name, line) for line, name in attributes)
        self.assertLess(lines["arm_bootstrap"], lines["start_sandbox_agent"])
        self.assertLess(lines["start_sandbox_agent"], lines["confirm_bootstrap"])
        self.assertLess(lines["confirm_bootstrap"], lines["verify_bootstrap"])
        self.assertNotIn("execve", lines)

    def test_no_import_time_linux_sdk_service_or_profile_effect(self):
        for name in ("trusted_prepare.py", "native_preparation.py", "core_bridge.py"):
            tree = ast.parse((HERE / name).read_bytes())
            for statement in tree.body:
                self.assertIsInstance(statement, (ast.Import, ast.ImportFrom, ast.FunctionDef,
                    ast.ClassDef, ast.Assign, ast.AnnAssign, ast.Expr))
                if isinstance(statement, ast.Expr): self.assertIsInstance(statement.value, ast.Constant)
        self.assertNotIn("subprocess", (HERE / "trusted_prepare.py").read_text())

    def test_worker_profile_delta_and_consumer_pin_are_exact(self):
        baseline = (ORIGINAL / "herdr/credential_isolation.py").read_bytes()
        self.assertEqual(hashlib.sha256(baseline).hexdigest(),
                         "2803a4330bac85223cef1887eaea9afbb6680938788d41d325a1312dade91b47")
        candidate = (HERE / "overlays/herdr/credential_isolation.py").read_bytes()
        profile = (HERE / "overlays/worker-profile.apparmor").read_bytes()
        old = b"66ad58859e0f5c141ddf7943c9ee369e37c0ba2d33115eb17ad872555778c226"
        new = hashlib.sha256(profile).hexdigest().encode()
        self.assertIn(b'WORKER_PROFILE_SOURCE_SHA256 = "' + new + b'"', candidate)
        self.assertIn(b"def _capture_own_fd_links", candidate)
        self.assertEqual((HERE.parents[1] / "herdr/credential_isolation.py").read_bytes(), candidate)
        self.assertIn(b"audit deny ptrace (read, trace, tracedby)", profile)
        self.assertIn(b"ptrace (readby) peer=herdr-offline-observer-03414499dd0d1986", profile)
        self.assertIn(b"audit deny capability,", profile)
        self.assertIn(b"audit deny change_profile,", profile)
        observer = (HERE / "overlays/observer-profile.apparmor").read_bytes()
        self.assertIn(b"ptrace (read) peer=herdr189-reference-lifetime", observer)
        self.assertIn(b"audit deny ptrace (trace, tracedby)", observer)
        self.assertIn(b"ptrace (readby) peer=herdr-offline-operator-03414499dd0d1986", observer)
        self.assertIn(b"audit deny capability sys_admin", observer)


if __name__ == "__main__": unittest.main(verbosity=2)
