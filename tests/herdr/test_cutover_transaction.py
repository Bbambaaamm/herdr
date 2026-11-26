"""Isolated RC6/RC7 installer regression scenarios; no real service operations."""
import importlib.util
import json
import os
from pathlib import Path
import signal
import socket
from types import SimpleNamespace

import pytest

from deploy.herdr.cutover import cutover as current
from herdr.release import ReleaseError


# Run the same behavioral tests against the unmodified main controller to
# capture red-before-green evidence, without changing the test expectations.
if os.environ.get("CUTOVER_BASE_SOURCE"):
    spec = importlib.util.spec_from_file_location("cutover_baseline", os.environ["CUTOVER_BASE_SOURCE"])
    cutover = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cutover)
else:
    cutover = current


@pytest.fixture
def host(tmp_path, monkeypatch):
    c = cutover
    for name in ("RELEASES", "STATE_DIR", "CONSUMER_DIR", "UNIT_DIR"):
        path = tmp_path / name
        path.mkdir()
        monkeypatch.setattr(c, name, path)
    for name in ("CURRENT", "PUBLIC_STATE", "SNAPSHOT", "BRIDGE", "NGINX_ROUTE", "WEB_CONFIG"):
        monkeypatch.setattr(c, name, tmp_path / name, raising=False)
    previous = c.RELEASES / "rc6"
    candidate = c.RELEASES / "rc7"
    previous.mkdir()
    bundle = candidate / "deploy/agent_platform/production"
    bundle.mkdir(parents=True)
    (bundle / "nginx-maintenance.conf.in").write_bytes(b"maintenance")
    c.CURRENT.symlink_to(previous)
    c.PUBLIC_STATE.write_bytes(b"previous-marker")
    c.NGINX_ROUTE.write_bytes(b"active-route")
    c.SNAPSHOT.write_bytes(b"previous-snapshot")
    c.BRIDGE.write_bytes(b"previous-bridge")
    for name in c.UNITS:
        (c.UNIT_DIR / name).write_bytes(b"previous-unit")
    release = {"tag": "rc7", "commit": "b" * 40,
               "config_contract_sha256": "c" * 64, "payload_manifest_sha256": "d" * 64}
    states = {name: "active" for name in c.UNITS}
    states["agent-platform-export.service"] = "inactive"
    states["agent-platform-herdr.service"] = "inactive"
    report = dict(services=states.copy(), baseline_health="healthy", direct_health="401", public_health="401", public_root="200")
    events = []
    failure = {"candidate": False, "rollback": False, "interrupt": False}
    original_snapshot = c.snapshot_file
    # The test process is unprivileged. Emulate root file ownership only at
    # the OS boundary; preserve bytes/modes and exercise real controller I/O.
    monkeypatch.setattr(c.os, "geteuid", lambda: 0)
    monkeypatch.setattr(c.os, "chown", lambda *a, **k: None)
    monkeypatch.setattr(c, "pin_archive", lambda path: path)
    monkeypatch.setattr(c, "verify_archive", lambda path: release)
    monkeypatch.setattr(c, "preflight", lambda *a: report)
    monkeypatch.setattr(c, "install_candidate", lambda *a: candidate)
    def install_units(*a, **k):
        for name in c.UNITS:
            (c.UNIT_DIR / name).write_bytes(b"candidate-unit")
    monkeypatch.setattr(c, "install_units", install_units)
    monkeypatch.setattr(c, "install_consumers", lambda *a: release["config_contract_sha256"])
    monkeypatch.setattr(c, "expected_hashes", lambda *a, **k: {c.NGINX_ROUTE: c.sha256(b"active-route")})
    monkeypatch.setattr(c, "write_deployed", lambda doc: c.PUBLIC_STATE.write_bytes(c.canonical_json(doc)))
    monkeypatch.setattr(c, "assert_no_active_durable_worker", lambda: None)
    monkeypatch.setattr(c, "assert_hardening", lambda: None)
    monkeypatch.setattr(c, "watchdog_lock_available", lambda: True)
    # tmp_path parent is not a production root-only state parent.
    real_stat = Path.stat
    def owned_stat(path, *a, **k):
        info = real_stat(path, *a, **k)
        if path in (c.STATE_DIR, c.STATE_DIR.parent):
            return SimpleNamespace(st_uid=0, st_mode=0o40700)
        return info
    monkeypatch.setattr(Path, "stat", owned_stat)

    def run(*args, check=True):
        events.append(args)
        if args[:2] == ("/usr/bin/systemctl", "stop"):
            for unit in args[2:]:
                states[unit] = "inactive"
        if args[:2] == ("/usr/bin/systemctl", "start"):
            for unit in args[2:]:
                if unit == "agent-platform-export.service":
                    c.BRIDGE.write_bytes(b"candidate-bridge")
                    c.SNAPSHOT.write_bytes(b"candidate-snapshot")
                elif unit == "agent-platform-web.service" and c.CURRENT.resolve() == candidate and failure["candidate"]:
                    raise ReleaseError("injected_candidate_web_failure")
                elif unit == "agent-platform-web.service" and c.CURRENT.resolve() == previous and report["baseline_health"] == "degraded":
                    raise ReleaseError("known_RC6_web_failure")
                else:
                    states[unit] = "active"
        if args[:2] == ("/usr/bin/systemctl", "is-active"):
            return states[args[2]]
        if args[:2] == ("/usr/bin/systemctl", "show"):
            return "success"
        return ""
    monkeypatch.setattr(c, "run", run)
    monkeypatch.setattr(c, "http_status", lambda url: "200" if url.endswith("165/") else
                        "503" if c.NGINX_ROUTE.read_bytes() == b"maintenance" else "401")
    monkeypatch.setattr(c, "wait_http_status", lambda url, expected, **k: expected)

    def ready(target, document):
        events.append(("ready", target))
        if failure["interrupt"]:
            failure["interrupt"] = False
            os.kill(os.getpid(), signal.SIGTERM)
    monkeypatch.setattr(c, "assert_candidate_ready", ready, raising=False)
    monkeypatch.setattr(c, "start_watchdog_service", lambda: states.update({"agent-stack-watchdog.service": "active"}))
    real_restore = c.restore_units
    def restore(units):
        if failure["rollback"]:
            raise ReleaseError("injected_rollback_failure")
        real_restore(units)
    monkeypatch.setattr(c, "restore_units", restore)
    archive = tmp_path / "candidate.tar.gz"
    archive.write_bytes(b"verified-archive-fixture")
    def apply():
        return c.apply.__wrapped__(archive, "legacy", "rc7-" + "b" * 12)
    def degraded():
        states["agent-platform-web.service"] = "failed"
        report.update(baseline_health="degraded", direct_health="000")
        report["services"] = states.copy()
    return SimpleNamespace(c=c, previous=previous, candidate=candidate, report=report,
                           failure=failure, events=events, states=states, archive=archive,
                           apply=apply, degraded=degraded,
                           before={p: original_snapshot(p) for p in (c.PUBLIC_STATE, c.BRIDGE, c.SNAPSHOT)})


def test_T01_healthy_upgrade_exercises_previous(host):
    result = host.apply()
    assert result["status"] == "success" and result["rollback_exercised"]
    assert ("ready", host.previous) in host.events
    assert host.c.CURRENT.resolve() == host.candidate


def test_T02_degraded_upgrade_does_not_boot_broken_previous(host):
    host.degraded()
    result = host.apply()
    assert result["status"] == "success" and not result["rollback_exercised"]
    assert ("ready", host.previous) not in host.events
    assert result["baseline_health"] == "degraded"


@pytest.mark.parametrize("degraded", [False, True], ids=["T08_healthy", "T09_degraded"])
def test_T07_candidate_web_failure_restores_previous(host, degraded):
    if degraded:
        host.degraded()
    host.failure["candidate"] = True
    with pytest.raises(ReleaseError, match="rollback_degraded" if degraded else "rollback_healthy"):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous
    assert host.c.PUBLIC_STATE.read_bytes() == b"previous-marker"
    if degraded:
        for path, before in host.before.items():
            assert host.c.snapshot_file(path) == before
        assert host.states["agent-platform-web.service"] in {"inactive", "failed"}
    assert not (host.c.STATE_DIR / "transaction.json").exists()


def test_T10_rollback_failure_retains_reconciliation_evidence(host):
    host.degraded()
    host.failure.update(candidate=True, rollback=True)
    with pytest.raises(ReleaseError, match="rollback_incomplete"):
        host.apply()
    assert (host.c.STATE_DIR / "transaction.json").is_file()
    assert host.c.NGINX_ROUTE.read_bytes() == b"maintenance"
    assert host.states["agent-stack-watchdog.service"] == "inactive"


def test_T11_sigterm_restores_baseline(host):
    host.degraded()
    host.failure["interrupt"] = True
    with pytest.raises(ReleaseError, match="rollback_degraded"):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous
    assert not (host.c.STATE_DIR / "transaction.json").exists()


def test_T12_repeat_requires_full_coherence(host, monkeypatch):
    host.apply()
    calls = []
    monkeypatch.setattr(host.c, "assert_deployed_coherence", lambda *a: calls.append(a))
    host.archive.write_bytes(b"same-archive")
    assert host.apply()["status"] == "already_deployed"
    assert len(calls) == 1


def test_T13_real_lock_rejects_second_process(tmp_path, monkeypatch):
    import fcntl
    import subprocess
    lockdir = tmp_path / "runtime"
    lockdir.mkdir(mode=0o700)
    monkeypatch.setattr(current, "DEPLOYMENT_LOCK", lockdir / "cutover.lock")
    real_lstat, real_fstat = os.lstat, os.fstat
    def root_owned(info):
        values = list(info)
        values[4] = 0
        return os.stat_result(values)
    monkeypatch.setattr(current.os, "lstat", lambda p, **k: root_owned(real_lstat(p, **k)))
    monkeypatch.setattr(current.os, "fstat", lambda fd: root_owned(real_fstat(fd)))
    with current.deployment_lock():
        script = "import fcntl,sys; f=open(sys.argv[1],'r+'); fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)"
        result = subprocess.run([os.sys.executable, "-c", script, str(current.DEPLOYMENT_LOCK)], capture_output=True)
        assert result.returncode != 0 and b"BlockingIOError" in result.stderr


@pytest.fixture
def readiness(tmp_path, monkeypatch):
    from agent_platform_dashboard import production_contract as contract
    from agent_platform_dashboard import production_sources as sources
    from agent_platform_dashboard import production_web as web
    from agent_platform_dashboard import production_io as io
    from agent_platform_dashboard.observability import build
    c = cutover
    now = int(c.time.time())
    bridge = tmp_path / "herdr.json"
    snapshot = tmp_path / "snapshot.json"
    socketpath = tmp_path / "herdr.sock"
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    listener.bind(str(socketpath))
    listener.listen(16)
    monkeypatch.setattr(c, "BRIDGE", bridge, raising=False)
    monkeypatch.setattr(c, "SNAPSHOT", snapshot)
    monkeypatch.setattr(c, "HERDR_SOCKET", socketpath)
    monkeypatch.setattr(c, "pwd", SimpleNamespace(getpwnam=lambda _: SimpleNamespace(pw_uid=os.getuid())), raising=False)
    monkeypatch.setattr(c, "grp", SimpleNamespace(getgrnam=lambda _: SimpleNamespace(gr_gid=os.getgid())))
    document = dict(tag="v0.3.0-router-v5-p1d-rc7", commit="b" * 40, config_sha256="c" * 64, deployed_at=now)
    monkeypatch.setattr(c, "verify_tree", lambda _: {"commit": document["commit"]})
    monkeypatch.setattr(web, "load", lambda _: SimpleNamespace(snapshot_path=str(snapshot)))
    agents = [dict(agent=p + "-hermes", status="idle") for p in contract.PROFILES]
    bridge.write_text(json.dumps(dict(version=1, observed_at=now, profiles=list(contract.PROFILES), agents=agents)))
    bridge.chmod(0o640)
    model = contract.unavailable(now)
    for source in model["sources"]:
        if source["kind"] in {"herdr", "router", "release"}:
            rows = ([r for r in agents if r["agent"].startswith(source["profile"])] if source["kind"] == "herdr"
                    else [document.copy()] if source["kind"] == "release" else [])
            source.update(status="available", reason="ok", rows=rows, data_at=now)
    model["observability"] = build(model)
    snapshot.write_bytes(contract.encode(model))
    snapshot.chmod(0o640)
    def check():
        return c.assert_candidate_ready(tmp_path, document)
    yield SimpleNamespace(c=c, bridge=bridge, snapshot=snapshot, socket=socketpath, listener=listener,
                          model=model, document=document, check=check, contract=contract, build=build)
    listener.close()


def test_candidate_valid_data_is_ready(readiness):
    readiness.check()


@pytest.mark.parametrize("fault", ["missing_bridge", "unready_bridge", "missing_snapshot", "invalid_snapshot",
                                    "permissions", "metadata", "socket", "service_failed", "stale_bridge"],
                         ids=["T03", "T04", "T05", "T06", "T14", "T15", "T03_socket", "T04_result", "T04_stale"])
def test_readiness_blocks_invalid_dependencies_before_web(readiness, fault, monkeypatch):
    r = readiness
    if fault == "missing_bridge":
        r.bridge.unlink()
    elif fault == "unready_bridge":
        r.bridge.write_text('{}')
    elif fault == "missing_snapshot":
        r.snapshot.unlink()
    elif fault == "invalid_snapshot":
        r.snapshot.write_text('{}')
    elif fault == "permissions":
        r.snapshot.chmod(0o666)
    elif fault == "metadata":
        r.document["commit"] = "f" * 40
    elif fault == "socket":
        r.listener.close()
    elif fault == "stale_bridge":
        value = json.loads(r.bridge.read_text())
        value["observed_at"] = 0
        r.bridge.write_text(json.dumps(value))
    # Exercise switch_runtime, not merely the validator: no web start may occur.
    events = []
    def run(*args, **kwargs):
        events.append(args)
        return ("exit-code" if fault == "service_failed" else "success") if "show" in args else "active"
    monkeypatch.setattr(r.c, "run", run)
    monkeypatch.setattr(r.c, "atomic_symlink", lambda *a: None)
    monkeypatch.setattr(r.c, "write_deployed", lambda *a: None)
    monkeypatch.setattr(r.c, "assert_hardening", lambda: None)
    monkeypatch.setattr(r.c, "wait_http_status", lambda *a, **k: "401")
    with pytest.raises((ReleaseError, ValueError, OSError)):
        r.c.switch_runtime(Path("/verified-candidate"), r.document)
    assert not any(e[1:3] == ("start", "agent-platform-web.service") for e in events)


def test_unfinished_journal_blocks_before_archive(tmp_path, monkeypatch):
    monkeypatch.setattr(cutover, "STATE_DIR", tmp_path)
    monkeypatch.setattr(cutover, "immutable_preflight_controller", lambda: True)
    (tmp_path / "transaction.json").write_text('{}')
    with pytest.raises(ReleaseError, match="unfinished_deployment"):
        cutover.preflight(tmp_path / "must-not-open.tar.gz", "unused")


def test_RC6_bridge_unnamed_entry_reproduces_78_and_candidate_accepts(tmp_path):
    from agent_platform_dashboard import production_herdr as bridge
    bindings = {"quantlab-hermes": dict(profile="quantlab", pane_id="1")}
    payload = json.dumps({"id": "cli:agent:list", "result": {"type": "agent_list", "agents": [
        {"pane_id": "0", "agent_status": "idle"},
        {"name": "quantlab-hermes", "pane_id": "1", "agent_status": "idle"}]}}).encode()
    result = bridge.sanitize(payload, 100, bindings)
    assert result["agents"] == [{"agent": "quantlab-hermes", "status": "idle"}]


@pytest.mark.parametrize("web,marker_ok,expected", [
    ("active", True, "healthy"), ("failed", True, "degraded"),
    ("inactive", True, "degraded"), ("failed", False, "reject"),
], ids=["T01_preflight", "T02_preflight", "inactive_preflight", "T15_marker"])
def test_preflight_classifies_only_coherent_baseline(tmp_path, monkeypatch, web, marker_ok, expected):
    c = cutover
    root, legacy, releases, consumers, units = [tmp_path / n for n in ("root", "legacy", "releases", "consumers", "units")]
    for path in (root, legacy, releases, consumers, units):
        path.mkdir()
    release = dict(tag="v0.3.0-router-v5-p1d-rc7", commit="b" * 40,
                   config_contract_sha256="c" * 64, payload_manifest_sha256="d" * 64,
                   external_dependency=dict(size=6, sha256=c.sha256(b"binary")))
    old = dict(release, tag="v0.3.0-router-v5-p1d-rc6", commit="a" * 40)
    previous = releases / (old["tag"] + "-" + old["commit"][:12])
    bundle = previous / "deploy/agent_platform/production"
    bundle.mkdir(parents=True)
    (previous / "configs/consumers").mkdir(parents=True)
    for name in c.UNITS:
        (bundle / (name + ".in")).write_bytes(b"same-unit")
        (units / name).write_bytes(b"same-unit")
    for name in c.CONSUMERS:
        (previous / "configs/consumers" / (name + ".yaml")).write_bytes(b"same-consumer")
        (consumers / (name + ".yaml")).write_bytes(b"same-consumer")
    (root / "RELEASE.json").write_text('{}')
    (legacy / "DEPLOYED_GIT_SHA").write_text("legacy")
    (legacy / "herdr").write_bytes(b"binary")
    link, marker = tmp_path / "current", tmp_path / "marker.json"
    link.symlink_to(previous)
    document = c.deployed_document(old, old["config_contract_sha256"], 100)
    if not marker_ok:
        document["commit"] = "f" * 40
    marker.write_text(json.dumps(document))
    for name, value in dict(ROOT=root, LEGACY=legacy, RELEASES=releases, CURRENT=link,
                            PUBLIC_STATE=marker, CONSUMER_DIR=consumers, UNIT_DIR=units,
                            STATE_DIR=tmp_path / "state").items():
        monkeypatch.setattr(c, name, value)
    monkeypatch.setattr(c, "immutable_preflight_controller", lambda: True)
    monkeypatch.setattr(c, "verify_archive", lambda _: release)
    monkeypatch.setattr(c, "verify_tree", lambda path: old if path == previous else release)
    monkeypatch.setattr(c, "consumer_digest", lambda _: old["config_contract_sha256"])
    monkeypatch.setattr(c, "current_release_unit_hashes", lambda: {})
    monkeypatch.setattr(c, "expected_hashes", lambda *a, **k: {})
    monkeypatch.setattr(c, "extract_candidate", lambda *a: root)
    monkeypatch.setattr(c, "compare_trees", lambda *a: {})
    monkeypatch.setattr(c.socket, "gethostname", lambda: c.HOST)
    monkeypatch.setattr(c, "live_unix_socket", lambda _: True)
    monkeypatch.setattr(c, "assert_no_active_durable_worker", lambda: None)
    states = {name: "active" for name in c.UNITS}
    states["agent-platform-web.service"] = web
    monkeypatch.setattr(c, "run", lambda *a, **k: states[a[2]])
    monkeypatch.setattr(c, "http_status", lambda url: "000" if "127.0.0.1" in url and web != "active" else "401")
    if expected == "reject":
        with pytest.raises(ReleaseError, match="public_state_mismatch"):
            c.preflight(tmp_path / "archive", "legacy")
    else:
        assert c.preflight(tmp_path / "archive", "legacy")["baseline_health"] == expected


def test_T11_sigkill_retains_durable_journal(tmp_path):
    import subprocess
    import sys
    journal = tmp_path / "transaction.json"
    script = """import os,signal,sys
from pathlib import Path
from deploy.herdr.cutover import cutover as c
c.STATE_DIR=Path(sys.argv[1]).parent
def write(path,data,mode,*a):
    with path.open('wb') as f:
        f.write(data); f.flush(); os.fsync(f.fileno())
    path.chmod(mode)
c.atomic_write=write
c.begin_transaction(Path('/verified/rc6'),dict(services={},direct_health='000',public_health='401'),{}, {})
os.kill(os.getpid(),signal.SIGKILL)
"""
    result = subprocess.run([sys.executable, "-c", script, str(journal)])
    assert result.returncode == -signal.SIGKILL
    assert json.loads(journal.read_text())["previous"] == "/verified/rc6"
    assert journal.stat().st_mode & 0o777 == 0o600
