"""Disposable issuer tests; real IPC/FDs with explicit root/cgroup doubles.

These are regression evidence, not a privileged native deployment acceptance.
"""
from copy import deepcopy
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import array
import hashlib
import json
import os
from pathlib import Path
import socket
import stat
import struct
import subprocess
import sys
import threading
import time
from types import SimpleNamespace

import pytest

from herdr import host_configuration as host, launch_plan_publication as publication
from herdr import launch_plan_issuer as issuer, launch_plan_handoff as handoff
from herdr.policy_launch import FrozenTree, CODE_TARGET, BUNDLE_TARGET, RUNTIME_TARGETS, process_start_ticks, IDENTITY_ENV
from herdr.launch_environment import STARTUP_CONTROLS
from herdr.private_mount_plan import request_for
from herdr.security import SecurityError, ToolRule, RiskClass, canonical_json_bytes
from tests.herdr.test_launch_plan_handoff import live
from tests.herdr.test_private_host_composition import private_config


@pytest.mark.parametrize("directory", ["agent-stack/bin", "scripts"])
def test_host_wrapper_runs_approved_entrypoint_with_its_sibling_imports(tmp_path, directory):
    # Execute the actual wrapper in an isolated child, with explicit policy and
    # immutability doubles. This verifies imports/argv, not root admission.
    import shutil
    root = tmp_path / "release"
    wrapper = root / issuer.HOST_ENTRYPOINT
    wrapper.parent.mkdir(parents=True)
    repository = Path(__file__).resolve().parents[2]
    shutil.copyfile(repository / issuer.HOST_ENTRYPOINT, wrapper)
    (root / "hermes/venv/lib/python3.11/site-packages").mkdir(parents=True)
    target = root / directory / "probe.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("import json, sys\nfrom sibling_helper import value\nprint(json.dumps([value, sys.argv]))\n")
    (target.parent / "sibling_helper.py").write_text("value = 'approved-sibling'\n")
    program = r"""
import json, pathlib, runpy, sys
from types import SimpleNamespace
repository, root, entrypoint = sys.argv[1:]
sys.path.insert(0, repository)
from herdr import launch_plan_issuer, host_configuration, host_bootstrap
from herdr.host_bootstrap import PYTHON_TARGET
from herdr.policy_launch import RUNTIME_TARGETS
hermes_target = next(str(x) for x in RUNTIME_TARGETS if x != PYTHON_TARGET)
# Interpreter authority is doubled to the disposable test interpreter;
# production continues to pin its published bin/python3.11.
host_bootstrap.PYTHON_EXECUTABLE = "bin/" + pathlib.Path(sys.executable).name
launch_plan_issuer._policy = lambda: (
    {"entrypoints": [entrypoint]}, {"code": {"source": root}, "storage": root,
    "runtime": [{"target": str(PYTHON_TARGET), "source": str(pathlib.Path(sys.executable).parent.parent)},
                {"target": hermes_target, "source": str(pathlib.Path(root) / "hermes")}]})
host_configuration._tree = lambda *args, **kwargs: SimpleNamespace(
    freeze=lambda *args: SimpleNamespace(close=lambda: None))
wrapper = pathlib.Path(root) / launch_plan_issuer.HOST_ENTRYPOINT
sys.argv = [str(wrapper), entrypoint, "caller-argument"]
runpy.run_path(str(wrapper), run_name="__main__")
"""
    result = subprocess.run([sys.executable, "-I", "-B", "-c", program,
                             str(repository), str(root), f"{directory}/probe.py"],
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ["approved-sibling", [str(target), "caller-argument"]]


class RootOS:
    def __getattr__(self, key):
        return (lambda: 0) if key == "geteuid" else getattr(os, key)


def configure(live, monkeypatch):
    grant = live.launch.grant
    now = datetime.now(UTC)
    grant = replace(grant, issued_at=now.isoformat(), expires_at=(now + timedelta(minutes=5)).isoformat())
    parent = replace(grant, identity=replace(grant.identity, agent_id=grant.identity.parent_agent_id,
                     task_id=grant.identity.parent_task_id, parent_agent_id="host-authority", parent_task_id="host-task"),
                     expires_at=(now + timedelta(minutes=10)).isoformat(), parent_grant_hash=None)
    grant = replace(grant, parent_grant_hash=parent.hash)
    live.launch.grant = grant
    live.launch._parent = parent
    raw = {"host_uid": os.getuid(), "grant_ttl_seconds": 300, "templates": {grant.identity.consumer: parent.to_json()},
           "private_launch": {"profile": {"name": live.profile.name,
                              "source": f"/home/agentops/.hermes/profiles/{live.profile.name}",
                              "files": live.profile.identity["files"]},
                              "credential_approval": {"schema_version": "herdr-profile-credential-approval-1",
                              "profile_sha256": live.profile.identity["manifest_sha256"],
                              "valid_until": (now + timedelta(hours=2)).isoformat(), "minimum_ttl_seconds": 60},
                              "plan_handoff": {"proposal_directory": str(live.proposals),
                                               "timeout_seconds": 3, "automatic_issuer": True}}}
    authority = {"request_timeout_seconds": 3}
    approvals = live.proposals.parent / "approvals"; approvals.mkdir()
    monkeypatch.setattr(issuer, "os", RootOS())
    monkeypatch.setattr(publication, "os", RootOS())
    monkeypatch.setattr(issuer, "_policy", lambda: (deepcopy(authority), deepcopy(raw)))
    monkeypatch.setattr(issuer, "_peer", lambda connection, *args: (
        os.getpid(), os.getuid(), os.getgid(), process_start_ticks(os.getpid())))
    monkeypatch.setattr(issuer, "_verify_root_owned_ancestry", lambda path: None)
    monkeypatch.setattr(publication, "_verify_root_owned_ancestry", lambda path: None)
    monkeypatch.setattr(publication, "_root_owner", lambda info: None)
    monkeypatch.setattr(publication, "APPROVAL_ROOT", approvals)
    monkeypatch.setattr(publication, "AUTHORITY_ROOT", live.plans)
    # Only complete immutable-source policy is a double in the IPC fixture.
    # It is exercised separately against real FD/profile/result fixtures below.
    monkeypatch.setattr(issuer, "_physical", lambda *args: None)
    monkeypatch.setattr(handoff, "time", time)
    endpoint = live.proposals.parent / "s"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    listener.bind(str(endpoint)); listener.listen(2); listener.settimeout(3)
    def connect(timeout):
        connection = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
        connection.settimeout(timeout); connection.connect(str(endpoint)); return connection
    # Endpoint root ownership/SO_PEERCRED root UID are explicit doubles only.
    monkeypatch.setattr(issuer, "_connect_issuer", connect)
    live.launch.private_plan_handoff.automatic_issuer = issuer.AutomaticLaunchPlanClient(issuer._digest(raw), 3)
    return raw, authority, approvals, listener


def run_server(listener, faults=None):
    errors = []
    results = []
    def run():
        try:
            connection, _ = listener.accept()
            with connection:
                if faults: faults()
                try: result = issuer.issue_request(connection)
                except Exception as exc:
                    errors.append(exc); result = {"schema_version": issuer.VERSION, "error": "denied"}
                connection.send(canonical_json_bytes(result)); results.append(result)
        except Exception as exc: errors.append(exc)
    thread = threading.Thread(target=run); thread.start()
    return thread, errors, results


def test_automatic_issuer_releases_existing_handoff_without_operator_ticket(live, monkeypatch):
    raw, _, approvals, listener = configure(live, monkeypatch)
    thread, errors, results = run_server(listener)
    try:
        live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert not thread.is_alive() and errors == [] and results[0]["published"] is True
        ticket = next(approvals.glob("*.json"))
        plan = next(live.plans.glob("*.json"))
        assert stat.S_IMODE(ticket.stat().st_mode) == 0o400
        assert stat.S_IMODE(plan.stat().st_mode) == 0o444
        assert json.loads(plan.read_bytes()) == live.launch.mount.private_mount_request
        assert all(body not in ticket.read_bytes() for body in live.inputs.values())
        live.launch.verify_private_handoff()
    finally: listener.close(); thread.join(4)


@pytest.mark.parametrize("fault", ["grant", "policy", "peer", "profile", "proposal", "fd", "parent"])
def test_automatic_request_denies_drift_and_keeps_evidence(live, monkeypatch, fault):
    raw, _, approvals, listener = configure(live, monkeypatch)
    original = issuer._validate
    def validate(request, fds, peer, current):
        request = deepcopy(request)
        if fault == "grant": request["grant"]["grant_id"] = "wrong-grant"
        elif fault == "policy": request["policy_sha256"] = "0" * 64
        elif fault == "peer": request["proposal"]["owner_start_ticks"] += 1
        elif fault == "profile": request["proposal"]["approved_profile"]["manifest_sha256"] = "0" * 64
        elif fault == "proposal": request["proposal"]["argv"] += ["malicious"]
        elif fault == "fd": request["proposal"]["plan"]["descriptors"][0]["source"] = "/proc/1/fd/9"
        else: request["grant"]["parent_grant_hash"] = "a" * 64
        return original(request, fds, peer, current)
    monkeypatch.setattr(issuer, "_validate", validate)
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors and not list(approvals.glob("*.json")) and not list(live.plans.glob("*.json"))
        assert len(list(live.proposals.glob("*.json"))) == 1
    finally: listener.close(); thread.join(4)


@pytest.mark.parametrize("boundary", ["ticket", "plan"])
def test_late_withdrawal_denies_at_both_publication_boundaries(live, monkeypatch, boundary):
    raw, _, approvals, listener = configure(live, monkeypatch)
    original = issuer._validate
    calls = []
    def validate(*args):
        calls.append(1)
        if len(calls) == (3 if boundary == "ticket" else 4):
            raw["grant_ttl_seconds"] -= 1
        return original(*args)
    monkeypatch.setattr(issuer, "_validate", validate)
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors and not list(live.plans.glob("*.json"))
        assert len(list(approvals.glob("*.json"))) == (0 if boundary == "ticket" else 1)
    finally: listener.close(); thread.join(4)


def test_existing_identity_is_never_overwritten(live, monkeypatch):
    _, _, approvals, listener = configure(live, monkeypatch)
    name = issuer._digest(live.launch.identity.to_json()) + ".json"
    existing = approvals / name; existing.write_bytes(b"retained-operator-evidence")
    old = existing.stat().st_ino
    thread, errors, _ = run_server(listener)
    try:
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors and existing.read_bytes() == b"retained-operator-evidence" and existing.stat().st_ino == old
        assert not list(live.plans.glob("*.json"))
    finally: listener.close(); thread.join(4)


def test_lost_reply_preserves_one_published_identity_without_retry_or_pane(live, monkeypatch):
    _, _, approvals, listener = configure(live, monkeypatch)
    errors = []
    def server():
        try:
            connection, _ = listener.accept()
            with connection:
                assert issuer.issue_request(connection)["published"] is True
                # Simulate a transport failure after the committed publication.
        except Exception as exc: errors.append(exc)
    thread = threading.Thread(target=server); thread.start()
    try:
        live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors == [] and not thread.is_alive()
        assert len(list(approvals.glob("*.json"))) == len(list(live.plans.glob("*.json"))) == 1
        assert live.launch.mount.private_mount_plan is not None and live.launch.sealed is None
        live.launch.verify_private_handoff()
    finally: listener.close(); thread.join(4)


def test_actual_unprivileged_process_cannot_issue_or_serve():
    if os.geteuid() == 0: pytest.skip("ordinary-user refusal requires non-root")
    with pytest.raises(SecurityError, match="root plan authority"): issuer.issue_request(None)
    with pytest.raises(SecurityError, match="requires root"): issuer.serve()


@pytest.mark.parametrize("fault", [None, "uid", "dumpable", "namespace", "cgroup", "delegated",
                                   "argv", "interpreter", "python-env", "loader-env", "pid-reuse"])
def test_host_peer_requires_every_independent_authority_binding(tmp_path, monkeypatch, fault):
    from herdr import launch_environment
    from herdr.host_bootstrap import PYTHON_TARGET
    executable = tmp_path / "python/bin/python3.11"; executable.parent.mkdir(parents=True); executable.write_bytes(b"python")
    actual = executable.stat(); pid = 1234; uid = os.getuid()
    class Peer:
        def getsockopt(self, *args): return struct.pack("3i", pid, uid + (fault == "uid"), os.getgid())
    class ObservedPath(type(Path())):
        def stat(self, *args, **kwargs):
            if str(self) == f"/proc/{pid}/status":
                return SimpleNamespace(st_mode=stat.S_IFREG | 0o444, st_uid=uid + 1 if fault == "dumpable" else 0, st_gid=0)
            if str(self) == f"/proc/{pid}/exe":
                return SimpleNamespace(st_dev=actual.st_dev, st_ino=actual.st_ino + (fault == "interpreter"))
            return super().stat(*args, **kwargs)
        def lstat(self):
            if str(self).startswith('/sys/fs/cgroup/'):
                return SimpleNamespace(st_mode=stat.S_IFREG | (0o666 if fault == "delegated" else 0o644), st_uid=0)
            return super().lstat()
    group = "/system.slice/herdr-host.service"
    argv = [str(executable), "-I", "-B", str(tmp_path / issuer.HOST_ENTRYPOINT), "agent-stack/bin/agent-task-worker"]
    if fault == "argv": argv[3] = "/tmp/mutable-worker.py"
    def metadata(pid, name, limit):
        return (b"0::/user.slice/untrusted.service\n" if fault == "cgroup" else f"0::{group}\n".encode()) if name == "cgroup" else "\0".join(argv).encode()
    class ObservedOS:
        def __getattr__(self, key):
            if key == "readlink":
                return lambda path: path.rsplit('/', 1)[-1] + ("-sandbox" if fault == "namespace" and f"/{pid}/" in path else "-host")
            return getattr(os, key)
    ticks = []
    def starts(pid):
        ticks.append(1); return 10 + (fault == "pid-reuse" and len(ticks) > 1)
    monkeypatch.setattr(issuer, "Path", ObservedPath)
    monkeypatch.setattr(issuer, "os", ObservedOS())
    monkeypatch.setattr(issuer, "_proc_bytes", metadata)
    monkeypatch.setattr(issuer, "process_start_ticks", starts)
    ancestry = []
    monkeypatch.setattr(issuer, "_verify_root_owned_ancestry", lambda path: ancestry.append(str(path)))
    monkeypatch.setattr(launch_environment, "process_environment", lambda pid: (
        {"PYTHONPATH": "/tmp/inject"} if fault == "python-env" else {"LD_PRELOAD": "inject"} if fault == "loader-env" else {}))
    raw = {"host_uid": uid, "code": {"source": str(tmp_path)},
           "runtime": [{"target": str(PYTHON_TARGET), "source": str(executable.parent.parent)}]}
    policy = {"host_cgroups": [group], "entrypoints": [argv[4]]}
    if fault is None:
        assert issuer._peer(Peer(), policy, raw) == (pid, uid, os.getgid(), 10)
        assert ancestry == ["/sys/fs/cgroup" + group]
    else:
        with pytest.raises((SecurityError, ValueError)): issuer._peer(Peer(), policy, raw)


def test_same_uid_is_not_host_authority():
    connection, other = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    try:
        with pytest.raises(SecurityError): issuer._peer(connection, {"host_cgroups": []}, {"host_uid": os.getuid()})
    finally: connection.close(); other.close()


@pytest.mark.parametrize("fault", ["missing-fds", "wrong-credentials", "invalid-json", "oversized"])
def test_real_seqpacket_authentication_and_bounds_close_received_fds(tmp_path, fault):
    sender, receiver = socket.socketpair(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    receiver.setsockopt(socket.SOL_SOCKET, socket.SO_PASSCRED, 1)
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        before = len(os.listdir("/proc/self/fd"))
        body = b"{}" if fault != "invalid-json" else b"invalid"
        if fault == "oversized": body = b"x" * (issuer.MAX_REQUEST + 1)
        ancillary = [] if fault == "missing-fds" else [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [fd]))]
        sender.sendmsg([body], ancillary)
        peer = (os.getpid() + (fault == "wrong-credentials"), os.getuid(), os.getgid(), 1)
        with pytest.raises((SecurityError, ValueError)): issuer._receive(receiver, peer)
        assert len(os.listdir("/proc/self/fd")) == before
    finally: os.close(fd); sender.close(); receiver.close()


def test_host_composition_selects_automatic_client_only_by_root_policy(tmp_path, monkeypatch):
    raw, _, _, _ = private_config(tmp_path, monkeypatch)
    proposals = tmp_path / "proposals"; proposals.mkdir(mode=0o700)
    raw["private_launch"]["plan_handoff"] = {"proposal_directory": str(proposals), "timeout_seconds": 30,
                                             "automatic_issuer": True}
    protected = []
    monkeypatch.setattr(issuer, "_policy", lambda: ({"request_timeout_seconds": 30}, deepcopy(raw)))
    monkeypatch.setattr(issuer, "protect_host_process", lambda: protected.append(True))
    factory = host.build_host_policy_factory()
    client = factory.private_plan_handoff.automatic_issuer
    assert isinstance(client, issuer.AutomaticLaunchPlanClient) and client.policy_sha256 == issuer._digest(raw)
    assert protected == [True]
    raw["private_launch"]["plan_handoff"]["automatic_issuer"] = "worker-choice"
    with pytest.raises(SecurityError): host.build_host_policy_factory()


@pytest.fixture
def physical(live, monkeypatch):
    from tests.herdr.test_policy_launch import frozen
    from herdr.host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE
    trees = []
    code_fixture = live.proposals.parent / "code-fixture"; code_fixture.mkdir()
    _, code = frozen(code_fixture, files={
        "agent-stack/policy-bin/herdr": b"cli", SHIM_SOURCE: b"shim", STAGE1_SOURCE: b"stage1"})
    trees.append(code)
    for target in sorted(RUNTIME_TARGETS, key=str):
        directory = live.proposals.parent / ("runtime-" + str(len(trees))); directory.mkdir()
        _, tree = frozen(directory, target=target); trees.append(tree)
    raw, _, _, listener = configure(live, monkeypatch); listener.close()
    raw["storage"] = str(live.proposals.parent)
    raw["code"] = {"source": str(code.path), "target": str(code.target)}
    raw["runtime"] = [{"source": str(tree.path), "target": str(tree.target)} for tree in trees[1:]]
    def definition(value, **kwargs):
        tree = next(t for t in trees if str(t.target) == value["target"])
        def freeze(*args):
            tree.verify()
            return replace(tree, fd=os.dup(tree.fd))
        return SimpleNamespace(freeze=freeze)
    monkeypatch.setattr(host, "_tree", definition)  # Root protection only is doubled; byte/FD verification remains real.
    proof = {"schema_version": "herdr-policy-bootstrap-1", "authority": "herdr-host-frozen-tree",
             "identity": live.launch.identity.to_json(), "trees": {str(t.target): {"device": t.device,
             "inode": t.inode, "source_digest": t.source_digest, "snapshot_kind": "host-frozen-copy"} for t in trees}}
    source = live.proposals.parent / "bootstrap-fixture"; source.mkdir()
    _, bootstrap = frozen(source, target=Path("/run/herdr-bootstrap"), files={"hermes": b"shim",
                         "agent-hermes-policy-stage1": b"stage1", "immutable-trees.json": canonical_json_bytes(proof)})
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM); sock.bind(str(live.proposals.parent / "bootstrap.sock"))
    sockfd = os.open(live.proposals.parent / "bootstrap.sock", os.O_PATH | os.O_CLOEXEC)
    bundle = live.proposals.parent / "bundle"; bundle.touch(mode=0o600)
    bundlefd = os.open(bundle, os.O_RDONLY)
    clifd = os.open(code.path / "agent-stack/policy-bin/herdr", os.O_RDONLY)
    def entry(fd, target, kind):
        info = os.fstat(fd)
        return {"source": f"/proc/{os.getpid()}/fd/{fd}", "fd": fd, "device": info.st_dev,
                "inode": info.st_ino, "kind": kind, "target": str(target)}
    descriptors = [live.work.descriptor(), live.output.descriptor(), *live.profile.fd_descriptors(),
                   *[entry(t.fd, t.target, "directory") for t in trees],
                   entry(bootstrap.fd, bootstrap.target, "directory"),
                   entry(sockfd, "/run/herdr-policy/bootstrap-authority.sock", "socket"),
                   entry(bundlefd, BUNDLE_TARGET, "file"), entry(clifd, "/home/agentops/.local/bin/herdr", "file")]
    grant = live.launch.grant
    binding = live.output.reservation
    from herdr.result_submission import ResultSlot
    rule = ToolRule("herdr_submit_result", RiskClass.RESULT_SUBMISSION, ("status", "evidence", "summary"),
                    allowed_roots=(str(live.output.logical.parent),), requires_sandbox=True,
                    result_slot=ResultSlot.from_dict({k: v for k, v in binding.items() if k != "schema_version"}))
    grant = replace(grant, scope=replace(grant.scope, tools=(*grant.scope.tools, "herdr_submit_result")),
                    tool_rules=(*grant.tool_rules, rule))
    argv = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--unshare-pid", "--die-with-parent",
            "--tmpfs", "/tmp", "--tmpfs", "/home/agentops", "--proc", "/proc", "--chdir", grant.workspace_root,
            "--tmpfs", "/home/agentops/.config/herdr", "--tmpfs", "/opt/agent-platform", "--tmpfs", "/run"]
    for value in descriptors:
        op = "--ro-bind-data" if value["kind"] == "sealed-profile-data" else (
             "--bind-fd" if value["kind"] == "reserved-result" else "--ro-bind-fd")
        argv += [op, str(value["fd"]), value["target"]]
    argv += ["--setenv", "HOME", "/home/agentops", "--setenv", "PATH",
             "/run/herdr/policy-code/agent-stack/policy-bin:/usr/bin:/bin", "--setenv", "HERDR_DURABLE_SANDBOX", "1",
             "--remount-ro", "/home/agentops", "--", "/bin/bash", "--noprofile", "--norc", "-i"]
    # Undo the IPC fixture's physical double for these direct source checks.
    monkeypatch.setattr(issuer, "_physical", ORIGINAL_PHYSICAL)
    try:
        yield SimpleNamespace(plan=request_for(grant.identity, descriptors, argv), argv=argv, grant=grant,
                              profile=live.profile.identity, fds=[x["fd"] for x in descriptors], raw=raw,
                              live=live, bundle=bundle, bootstrap=bootstrap, trees=trees)
    finally:
        for fd in (sockfd, bundlefd, clifd): os.close(fd)
        sock.close(); bootstrap.close()
        for tree in trees: tree.close()


ORIGINAL_PHYSICAL = issuer._physical


def test_physical_policy_checks_real_profile_result_and_runtime_fds(physical):
    p = physical
    issuer._physical(p.plan, p.argv, p.grant, p.profile, p.fds, p.raw)


@pytest.mark.parametrize("fault", [None, "foreign-grant", "replacement", "hardlink",
                                   "public-write", "read-only", "mount-crossing", "control-path"])
def test_file_scoped_owned_write_mounts_keep_exact_source_and_grant(physical, monkeypatch, fault):
    from herdr.child_ownership import ChildOwnership, WriteScope
    from herdr.owned_write_mounts import OwnedWritePins
    from herdr import owned_write_mounts
    p = physical
    target = p.live.work.logical / "owned.py"
    target.write_text("owned"); target.chmod(0o600)
    contract = ChildOwnership((WriteScope("file", "owned.py"),), (), (), (), "parent", "artifact://handoff/child")
    with OwnedWritePins(contract, p.live.work) as owned:
        entry = owned.descriptors()[0]
        fd = owned.mounts[0].fd
        argv = list(p.argv)
        at = argv.index("--setenv")
        argv[at:at] = ["--bind-fd", str(fd), str(target)]
        roots = (str(target),) if fault != "foreign-grant" else (str(target.with_name("foreign.py")),)
        write = ToolRule("write_file", RiskClass.WORKSPACE_WRITE, ("path", "content"),
                         path_fields=("path",), allowed_roots=roots)
        grant = replace(p.grant, scope=replace(p.grant.scope, tools=(*p.grant.scope.tools, "write_file")),
                        tool_rules=(*p.grant.tool_rules, write))
        if fault == "replacement":
            target.rename(target.with_name("retained.py")); target.write_text("replacement")
        elif fault == "hardlink": os.link(target, target.with_name("alias.py"))
        elif fault == "public-write": target.chmod(0o666)
        elif fault == "read-only": argv[at] = "--ro-bind-fd"
        elif fault == "mount-crossing":
            actual = owned_write_mounts._mount_id
            monkeypatch.setattr(owned_write_mounts, "_mount_id", lambda value: actual(value) + (value == fd))
        elif fault == "control-path":
            new = target.with_name(".herdr-control")
            target.rename(new); entry["target"] = str(new); argv[at + 2] = str(new)
            grant = replace(grant, tool_rules=(*p.grant.tool_rules,
                replace(write, allowed_roots=(str(p.live.work.logical),))))
        entries = [*p.plan["descriptors"], entry]
        plan = request_for(grant.identity, entries, argv)
        args = (plan, argv, grant, p.profile, [*p.fds, fd], p.raw)
        if fault is None:
            issuer._physical(*args)
        else:
            with pytest.raises((SecurityError, OSError, ValueError)):
                issuer._physical(*args)


def test_root_and_child_grants_use_the_existing_consumer_ceiling(live, monkeypatch):
    raw, _, _, listener = configure(live, monkeypatch); listener.close()
    request = {"grant": live.launch.grant.to_json(), "parent_grant": live.launch._parent.to_json()}
    assert issuer._grant(request, raw, live.profile.identity) == live.launch.grant
    root = replace(live.launch.grant, identity=live.launch._parent.identity, parent_grant_hash=None)
    assert issuer._grant({"grant": root.to_json(), "parent_grant": None}, raw, live.profile.identity) == root
    foreign = replace(live.launch._parent, identity=replace(live.launch._parent.identity, agent_id="foreign-parent"))
    with pytest.raises(SecurityError): issuer._grant({**request, "parent_grant": foreign.to_json()}, raw, live.profile.identity)


@pytest.mark.parametrize("grant_write,mount_write,accepted", [(True,True,True), (False,False,True),
    (False,True,False), (True,False,True)])
def test_accepts_the_actual_native_builder_command(physical, monkeypatch, grant_write, mount_write, accepted):
    from tests.herdr.test_policy_launch import sandbox_module
    from herdr.policy_launch import PolicyMount, PreparedPolicyLaunch
    from herdr.security import stage_policy_bundle
    from herdr.host_bootstrap import HostBootstrap
    p = physical
    write = ToolRule("write_file", RiskClass.WORKSPACE_WRITE, ("path", "content"),
                     path_fields=("path",), allowed_roots=(p.grant.workspace_root,))
    root_grant = replace(p.grant, scope=replace(p.grant.scope, tools=(*p.grant.scope.tools, "write_file")),
                         tool_rules=(*p.grant.tool_rules, write))
    if not grant_write:
        root_grant = p.grant
    stage = stage_policy_bundle(p.bundle.parent / "builder-grant")
    mount = PolicyMount(stage, p.trees[0], p.trees[1:])
    mount.require_immutable_runtime = lambda: None  # Disposable roots cannot claim privileged immutability.
    mount.private_workspace_pin = p.live.work; mount.private_result_pin = p.live.output
    mount.private_identity = p.grant.identity
    broker = HostBootstrap.__new__(HostBootstrap)
    broker.tree = p.bootstrap; broker.socket_path = p.bundle.parent / "bootstrap.sock"
    broker.socket_fd = p.fds[-3]
    info = os.fstat(broker.socket_fd); broker.socket_identity = (info.st_dev, info.st_ino)
    mount.bootstrap = broker
    module = sandbox_module()
    if not (module.BWRAP.is_file() and Path("/home/agentops/.local/bin/herdr").is_file()
            and module.HERDR_CONFIG.is_dir()):
        pytest.skip("actual native host builder requires the agentops CLI/config and bwrap")
    # The generic live fixture predates the managed-child result naming contract.
    # This root builder fixture retains the same exact result FD/reservation.
    try:
        with pytest.raises(RuntimeError, match="durable_private_mount_plan_unapproved"):
            module.command(workspace=Path(p.grant.workspace_root), writable=(p.live.output.logical,),
                           real_binary=Path("/home/agentops/.local/bin/herdr"), policy_mount=mount,
                           admission_root=p.live.proposals.parent,
                           pinned_worktree=p.live.work,
                           hermes_profile=p.live.profile.name, private_profile_snapshot=p.live.profile,
                           root_workspace_writable=mount_write)
        plan, argv = mount.private_mount_request, mount.private_mount_argv
        operation = argv[argv.index(str(p.live.work.fd)) - 1]
        assert operation == ("--bind-fd" if mount_write else "--ro-bind-fd")
        assert p.live.output.logical.name == "result.json"  # Ordinary root slot, not a child result filename.
        args = (plan, argv, root_grant, p.profile, [entry["fd"] for entry in plan["descriptors"]], p.raw)
        if accepted:
            issuer._physical(*args)
        else:
            with pytest.raises(SecurityError, match="write mount exceeds host grant"):
                issuer._physical(*args)
    finally:
        for fd in mount.private_cli_pins.values(): os.close(fd)
        stage.close()


@pytest.mark.parametrize("fault", ["fd-reorder", "fd-number", "profile-hash", "writable-code", "late-root-bind", "late-home",
                                   "arbitrary-command", "result-intent", "result-bytes", "bootstrap-bytes", "bundle-bytes",
                                   "missing-runtime", "work-write", "literal-write", "namespace", "unknown-option",
                                   "missing-custody", "duplicate-custody"])
def test_physical_policy_rejects_source_and_command_attacks(physical, fault):
    p = physical; argv = list(p.argv); entries = deepcopy(p.plan["descriptors"]); fds = list(p.fds)
    extra = None
    if fault == "fd-reorder": fds[0], fds[1] = fds[1], fds[0]
    elif fault == "fd-number":
        extra = os.open(p.live.proposals, os.O_RDONLY | os.O_DIRECTORY)
        argv[argv.index(str(entries[0]["fd"]))] = str(extra)
        entries[0]["fd"] = extra; entries[0]["source"] = f"/proc/{os.getpid()}/fd/{extra}"
    elif fault == "profile-hash": next(x for x in entries if x["kind"] == "sealed-profile-data")["sha256"] = "0" * 64
    elif fault == "writable-code": argv[argv.index(str(CODE_TARGET)) - 2] = "--bind-fd"
    elif fault == "late-root-bind": argv[argv.index("--"):argv.index("--")] = ["--ro-bind", "/", "/"]
    elif fault == "late-home": argv[argv.index("--"):argv.index("--")] = ["--tmpfs", "/home/agentops"]
    elif fault == "arbitrary-command": argv[-4:] = ["/bin/bash", "-c", "malicious"]
    elif fault == "result-intent": os.setxattr(p.live.output.logical, "user.herdr.result_submission", b"uncertain")
    elif fault == "result-bytes": p.live.output.logical.write_bytes(b"already-delivered")
    elif fault == "bootstrap-bytes":
        file = p.bootstrap.path / "hermes"; file.chmod(0o600); file.write_bytes(b"different")
    elif fault == "bundle-bytes": p.bundle.write_bytes(b"presealed-or-forged")
    elif fault == "missing-runtime":
        target = str(p.trees[-1].target)
        at = next(i for i, entry in enumerate(entries) if entry["target"] == target)
        entries.pop(at); fds.pop(at)
        at = argv.index(target); del argv[at - 2:at + 1]
    elif fault == "work-write": argv[argv.index(str(p.live.work.fd)) - 1] = "--bind-fd"
    elif fault == "literal-write": argv[argv.index("--"):argv.index("--")] = ["--bind", "/tmp", "/tmp"]
    elif fault == "namespace": argv.remove("--unshare-pid")
    elif fault == "missing-custody": argv.remove("--die-with-parent")
    elif fault == "duplicate-custody": argv.insert(argv.index("--"), "--die-with-parent")
    else: argv[argv.index("--"):argv.index("--")] = ["--share-net"]
    plan = request_for(p.grant.identity, entries, argv)
    try:
        with pytest.raises((SecurityError, OSError, ValueError)):
            issuer._physical(plan, argv, p.grant, p.profile, fds, p.raw)
    finally:
        if extra is not None: os.close(extra)


@pytest.mark.parametrize("key", ["HOME", "PATH", "HERDR_DURABLE_SANDBOX"])
@pytest.mark.parametrize("position", ["before", "after"])
def test_required_public_environment_cannot_be_unset(physical, key, position):
    argv = list(physical.argv)
    index = argv.index("--setenv") if position == "before" else argv.index("--remount-ro")
    argv[index:index] = ["--unsetenv", key]
    plan = request_for(physical.grant.identity, physical.plan["descriptors"], argv)
    with pytest.raises(SecurityError, match="required public environment"):
        issuer._argv(plan, argv, physical.grant.workspace_root, physical.profile)


def test_client_uses_remaining_deadline_for_connect_send_and_reply(live, monkeypatch):
    plan, argv = handoff._build(live.launch, live.builder)
    published = live.launch.private_plan_handoff._publish_proposal(live.launch, plan, argv)
    clock = {"now": 0.0}
    monkeypatch.setattr(issuer, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    calls = []
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): calls.append(("io", value))
        def sendmsg(self, blocks, rights):
            assert json.loads(blocks[0])["deadline_monotonic_ns"] == 2_000_000_000
            clock["now"] += 0.25
            return len(blocks[0])
        def recv(self, maximum):
            return canonical_json_bytes({"schema_version": issuer.VERSION,
                "identity_sha256": issuer._digest(live.launch.identity.to_json()),
                "plan_sha256": issuer._digest(plan), "published": True})
    def connect(timeout):
        calls.append(("connect", timeout))
        clock["now"] += 0.5
        return Connection()
    monkeypatch.setattr(issuer, "_connect_issuer", connect)
    issuer.AutomaticLaunchPlanClient("a" * 64, 2).issue(live.launch, published, deadline=2.0)
    assert calls == [("connect", 2.0), ("io", 1.5), ("io", 1.25)]


@pytest.mark.parametrize("stage", ["before-connect", "after-connect"])
def test_client_exhausted_handoff_budget_cannot_send_a_request(live, monkeypatch, stage):
    plan, argv = handoff._build(live.launch, live.builder)
    published = live.launch.private_plan_handoff._publish_proposal(live.launch, plan, argv)
    clock = {"now": 2.0 if stage == "before-connect" else 0.0}
    monkeypatch.setattr(issuer, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    class Connection:
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def settimeout(self, value): pass
        def sendmsg(self, *args): pytest.fail("expired budget sent descriptors")
    def connect(timeout):
        assert stage == "after-connect", "expired budget contacted the issuer"
        clock["now"] = 2.0
        return Connection()
    monkeypatch.setattr(issuer, "_connect_issuer", connect)
    with pytest.raises(SecurityError, match="deadline"):
        issuer.AutomaticLaunchPlanClient("a" * 64, 2).issue(live.launch, published, deadline=2.0)
    assert not list(live.plans.iterdir())


@pytest.mark.parametrize("fault", ["missing", "bool", "text", "expired", "future", "queued",
                                   "first-validation", "ticket-stage", "plan-stage", "policy-read"])
def test_server_enforces_caller_deadline_before_each_publication(live, monkeypatch, fault):
    _, _, approvals, listener = configure(live, monkeypatch)
    clock = {"now": time.monotonic()}
    monkeypatch.setattr(issuer, "time", SimpleNamespace(monotonic=lambda: clock["now"]))
    original_receive = issuer._receive
    def receive(connection, peer):
        request, descriptors = original_receive(connection, peer)
        if fault == "missing": request.pop("deadline_monotonic_ns")
        elif fault == "bool": request["deadline_monotonic_ns"] = True
        elif fault == "text": request["deadline_monotonic_ns"] = "late"
        elif fault == "expired": request["deadline_monotonic_ns"] = int((clock["now"] - 1) * 1e9)
        elif fault == "future": request["deadline_monotonic_ns"] = int((clock["now"] + 10) * 1e9)
        elif fault == "queued": clock["now"] += 4
        return request, descriptors
    monkeypatch.setattr(issuer, "_receive", receive)
    physical_calls = []
    def physical(*args):
        physical_calls.append(True)
        boundary = {"first-validation": 1, "ticket-stage": 3, "plan-stage": 4}.get(fault)
        if boundary is not None and len(physical_calls) == boundary:
            clock["now"] += 4
    monkeypatch.setattr(issuer, "_physical", physical)
    original_policy = issuer._policy
    policy_calls = []
    def policy():
        policy_calls.append(True)
        if fault == "policy-read" and len(policy_calls) == 2: clock["now"] += 4
        return original_policy()
    monkeypatch.setattr(issuer, "_policy", policy)
    thread, errors, results = run_server(listener)
    try:
        with pytest.raises(SecurityError):
            live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert not thread.is_alive() and errors
        assert not list(live.plans.glob("*.json"))
        assert results[0].get("published") is not True
        if fault not in {"plan-stage"}:
            assert not list(approvals.glob("*.json"))
    finally:
        listener.close()
        thread.join(4)


@pytest.mark.parametrize("fault", ["eof", "timeout", "malformed"])
def test_committed_plan_is_reconciled_after_lost_reply_without_reissuance(live, monkeypatch, fault):
    _, _, _, listener = configure(live, monkeypatch)
    original_connect = issuer._connect_issuer
    contacts = []
    class LostReply:
        def __init__(self, connection): self.connection = connection
        def __enter__(self): return self
        def __exit__(self, *args): self.connection.close()
        def __getattr__(self, name): return getattr(self.connection, name)
        def recv(self, maximum):
            answer = self.connection.recv(maximum)
            assert json.loads(answer)["published"] is True
            if fault == "timeout": raise TimeoutError("reply lost after commit")
            return b"" if fault == "eof" else b"{"
    def connect(timeout):
        contacts.append(timeout)
        return LostReply(original_connect(timeout))
    monkeypatch.setattr(issuer, "_connect_issuer", connect)
    thread, errors, results = run_server(listener)
    try:
        live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert not thread.is_alive() and errors == []
        assert results[0]["published"] is True and len(contacts) == 1
        assert len(list(live.plans.glob("*.json"))) == len(list(live.proposals.glob("*.json"))) == 1
        assert json.loads(next(live.plans.glob("*.json")).read_bytes()) == live.launch.mount.private_mount_request
        live.launch.verify_private_handoff()
    finally:
        listener.close()
        thread.join(4)


def test_accepted_long_handoff_uses_shorter_issuer_budget(live, monkeypatch):
    _, _, _, listener = configure(live, monkeypatch)
    live.launch.private_plan_handoff.timeout_seconds = 60
    captured = []
    original_receive = issuer._receive
    def receive(connection, peer):
        request, descriptors = original_receive(connection, peer)
        captured.append(request["deadline_monotonic_ns"] / 1e9)
        assert time.monotonic() < captured[-1] <= time.monotonic() + 3
        return request, descriptors
    monkeypatch.setattr(issuer, "_receive", receive)
    thread, errors, results = run_server(listener)
    try:
        live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors == [] and results[0]["published"] is True and len(captured) == 1
    finally:
        listener.close()
        thread.join(4)


@pytest.mark.parametrize("fault", [None, "policy-drift", "authority-unavailable"])
def test_actual_host_factory_uses_protected_issuer_timeout(tmp_path, monkeypatch, fault):
    raw, _, _, _ = private_config(tmp_path, monkeypatch)
    proposals = tmp_path / "proposals"; proposals.mkdir(mode=0o700)
    raw["private_launch"]["plan_handoff"] = {
        "proposal_directory": str(proposals), "timeout_seconds": 60, "automatic_issuer": True}
    protected = []
    def policy():
        if fault == "authority-unavailable":
            raise SecurityError("protected issuer policy unavailable")
        current = deepcopy(raw)
        if fault == "policy-drift": current["host_uid"] += 1
        return {"request_timeout_seconds": 30}, current
    monkeypatch.setattr(issuer, "_policy", policy)
    monkeypatch.setattr(issuer, "protect_host_process", lambda: protected.append(True))
    if fault:
        with pytest.raises(SecurityError): host.build_host_policy_factory()
        assert protected == []
    else:
        factory = host.build_host_policy_factory()
        assert factory.private_plan_handoff.timeout_seconds == 60
        assert factory.private_plan_handoff.automatic_issuer.timeout_seconds == 30
        assert protected == [True]


def test_automatic_native_grammar_denies_private_network_namespace(physical):
    argv = list(physical.argv)
    argv.insert(argv.index("--"), "--unshare-net")
    plan = request_for(physical.grant.identity, physical.plan["descriptors"], argv)
    with pytest.raises(SecurityError, match="unsupported automatic mount operation"):
        issuer._argv(plan, argv, physical.grant.workspace_root, physical.profile)


@pytest.mark.parametrize("key", [
    *IDENTITY_ENV.values(),
    "HERDR_DURABLE_TASK_PANE", "HERDR_DURABLE_TASK_ID", "HERDR_DURABLE_RUN_TOKEN",
    "HERDR_DURABLE_TASK_FILE", "HERDR_DURABLE_AGENT", "HERDR_DURABLE_MARKER",
    "HERDR_DURABLE_BRIDGE_SOCKET", "HERDR_REAL_BINARY", "OTHER_INHERITED_KEY"])
def test_automatic_native_cleanup_cannot_unset_inherited_launch_context(physical, key):
    argv = list(physical.argv)
    argv[argv.index("--remount-ro"):argv.index("--remount-ro")] = ["--unsetenv", key]
    plan = request_for(physical.grant.identity, physical.plan["descriptors"], argv)
    with pytest.raises(SecurityError, match="approved startup cleanup"):
        issuer._argv(plan, argv, physical.grant.workspace_root, physical.profile)


@pytest.mark.parametrize("key", [
    *STARTUP_CONTROLS,
    "HERMES_HOME", "HERMES_PROFILE", "HERMES_CONFIG_DIR", "XDG_CONFIG_HOME",
    "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME", "LD_FUTURE_CONTROL"])
def test_automatic_native_cleanup_accepts_only_builder_cleanup_inventory(physical, key):
    argv = list(physical.argv)
    argv[argv.index("--remount-ro"):argv.index("--remount-ro")] = ["--unsetenv", key]
    plan = request_for(physical.grant.identity, physical.plan["descriptors"], argv)
    issuer._argv(plan, argv, physical.grant.workspace_root, physical.profile)


@pytest.mark.skipif(sys.platform != "linux" or os.geteuid() == 0,
                    reason="real non-root Linux proc ownership and protection required")
@pytest.mark.parametrize("dumpable", [0, 1])
def test_real_non_dumpable_peer_uses_proc_entry_not_process_directory(dumpable):
    # No proc/ownership/ptrace doubles. Test the production check against a
    # separate ordinary-user process and observe same-UID kernel protection.
    program = r"""
import ctypes,json,os,sys
from pathlib import Path
sys.path.insert(0,sys.argv[1])
from herdr import launch_plan_issuer as issuer
libc=ctypes.CDLL(None,use_errno=True)
mode=int(sys.argv[2])
assert libc.prctl(4,mode,0,0,0)==0 and libc.prctl(3,0,0,0,0)==mode
base=Path('/proc')/str(os.getpid())
status=(base/'status').stat()
print(json.dumps({'pid':os.getpid(),'directory_uid':base.stat().st_uid,
                  'status_uid':status.st_uid,'status_gid':status.st_gid}),flush=True)
sys.stdin.read(1)
"""
    repository = Path(__file__).resolve().parents[2]
    child = subprocess.Popen([sys.executable, "-I", "-B", "-c", program,
                              str(repository), str(dumpable)],
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, text=True)
    try:
        import select
        assert select.select([child.stdout], [], [], 10)[0], "native proc probe did not start"
        line = child.stdout.readline()
        assert line, child.stderr.read()
        observation = json.loads(line)
        assert observation["pid"] == child.pid
        assert observation["directory_uid"] == os.getuid()
        if dumpable == 0:
            assert observation["status_uid"] == observation["status_gid"] == 0
            issuer._require_non_dumpable(child.pid)
            with pytest.raises(PermissionError):
                fd = os.open(f"/proc/{child.pid}/environ", os.O_RDONLY)
                os.close(fd)
        else:
            assert observation["status_uid"] == os.getuid()
            with pytest.raises(SecurityError, match="must be non-dumpable"):
                issuer._require_non_dumpable(child.pid)
            # Do not read or print inherited environment bytes.
            fd = os.open(f"/proc/{child.pid}/environ", os.O_RDONLY)
            os.close(fd)
        child.communicate("x", timeout=10)
        assert child.returncode == 0
    finally:
        if child.poll() is None:
            child.kill(); child.communicate(timeout=5)


@pytest.mark.parametrize("fault", ["not-regular", "owner", "group"])
def test_non_dumpable_proc_marker_denies_wrong_type_owner_or_group(monkeypatch, fault):
    class ObservedPath(type(Path())):
        def stat(self):
            return SimpleNamespace(st_mode=(stat.S_IFDIR if fault == "not-regular" else stat.S_IFREG) | 0o444,
                                   st_uid=1 if fault == "owner" else 0,
                                   st_gid=1 if fault == "group" else 0)
    monkeypatch.setattr(issuer, "Path", ObservedPath)
    with pytest.raises(SecurityError, match="must be non-dumpable"):
        issuer._require_non_dumpable(1234)


@pytest.mark.parametrize("options", [
    {"root_workspace_writable": "yes", "private_profile_snapshot": object(), "policy_mount": object()},
    {"root_workspace_writable": True},
    {"root_workspace_writable": False, "child_workspace_writable": False,
     "private_profile_snapshot": object(), "policy_mount": object()},
])
def test_root_workspace_mode_cannot_bypass_private_or_child_admission(tmp_path, options):
    from tests.herdr.test_policy_launch import sandbox_module
    with pytest.raises(RuntimeError, match="private_root_workspace_mode_required"):
        sandbox_module().command(tmp_path, tmp_path / "absent", **options)
