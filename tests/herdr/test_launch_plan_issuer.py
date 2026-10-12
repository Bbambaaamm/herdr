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
import threading
import time
from types import SimpleNamespace

import pytest

from herdr import host_configuration as host, launch_plan_publication as publication
from herdr import launch_plan_issuer as issuer, launch_plan_handoff as handoff
from herdr.policy_launch import FrozenTree, CODE_TARGET, BUNDLE_TARGET, RUNTIME_TARGETS, process_start_ticks
from herdr.private_mount_plan import request_for
from herdr.security import SecurityError, ToolRule, RiskClass, canonical_json_bytes
from tests.herdr.test_launch_plan_handoff import live
from tests.herdr.test_private_host_composition import private_config


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
        with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
        thread.join(4)
        assert errors == [] and not thread.is_alive()
        assert len(list(approvals.glob("*.json"))) == len(list(live.plans.glob("*.json"))) == 1
        assert live.launch.mount.private_mount_plan is None and live.launch.sealed is None
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
            if str(self) == f"/proc/{pid}": return SimpleNamespace(st_uid=uid if fault == "dumpable" else 0)
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
    argv = ["/usr/bin/bwrap", "--ro-bind", "/", "/", "--dev", "/dev", "--unshare-pid",
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


def test_root_and_child_grants_use_the_existing_consumer_ceiling(live, monkeypatch):
    raw, _, _, listener = configure(live, monkeypatch); listener.close()
    request = {"grant": live.launch.grant.to_json(), "parent_grant": live.launch._parent.to_json()}
    assert issuer._grant(request, raw, live.profile.identity) == live.launch.grant
    root = replace(live.launch.grant, identity=live.launch._parent.identity, parent_grant_hash=None)
    assert issuer._grant({"grant": root.to_json(), "parent_grant": None}, raw, live.profile.identity) == root
    foreign = replace(live.launch._parent, identity=replace(live.launch._parent.identity, agent_id="foreign-parent"))
    with pytest.raises(SecurityError): issuer._grant({**request, "parent_grant": foreign.to_json()}, raw, live.profile.identity)


def test_accepts_the_actual_native_builder_command(physical, monkeypatch):
    from tests.herdr.test_policy_launch import sandbox_module
    from herdr.policy_launch import PolicyMount, PreparedPolicyLaunch
    from herdr.security import stage_policy_bundle
    from herdr.host_bootstrap import HostBootstrap
    p = physical
    write = ToolRule("write_file", RiskClass.WORKSPACE_WRITE, ("path", "content"),
                     path_fields=("path",), allowed_roots=(p.grant.workspace_root,))
    root_grant = replace(p.grant, scope=replace(p.grant.scope, tools=(*p.grant.scope.tools, "write_file")),
                         tool_rules=(*p.grant.tool_rules, write))
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
                           pinned_worktree=p.live.work,
                           hermes_profile=p.live.profile.name, private_profile_snapshot=p.live.profile)
        plan, argv = mount.private_mount_request, mount.private_mount_argv
        issuer._physical(plan, argv, root_grant, p.profile, [entry["fd"] for entry in plan["descriptors"]], p.raw)
    finally:
        for fd in mount.private_cli_pins.values(): os.close(fd)
        stage.close()


@pytest.mark.parametrize("fault", ["fd-reorder", "fd-number", "profile-hash", "writable-code", "late-root-bind", "late-home",
                                   "arbitrary-command", "result-intent", "result-bytes", "bootstrap-bytes", "bundle-bytes",
                                   "missing-runtime", "work-write", "literal-write", "namespace", "unknown-option"])
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
    else: argv[argv.index("--"):argv.index("--")] = ["--share-net"]
    plan = request_for(p.grant.identity, entries, argv)
    try:
        with pytest.raises((SecurityError, OSError, ValueError)):
            issuer._physical(plan, argv, p.grant, p.profile, fds, p.raw)
    finally:
        if extra is not None: os.close(extra)

