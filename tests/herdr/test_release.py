"""Offline release/cutover contract tests; no privileged or live operations."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import tarfile

import pytest

from deploy.herdr.cutover import cutover
from herdr import release


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def consumer(name: str) -> bytes:
    return (f"schema_version: 1\nconsumer: {name}\nrepository: Example/{name}\n"
            f"policy_profile: {name}-safe\nhard_invariants:\n  - safe_only\n"
            "inheritance:\n  child_may_expand_parent_permissions: false\n"
            "routing:\n  capability_aware: true\n  cost_aware: true\n").encode()


def minimal_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, str]:
    repo = tmp_path / "repo"
    (repo / "configs" / "consumers").mkdir(parents=True)
    (repo / "provenance").mkdir()
    for name in release.CONSUMERS:
        (repo / "configs" / "consumers" / f"{name}.yaml").write_bytes(consumer(name))
    (repo / "provenance" / "external-runtime-dependency.txt").write_text(
        "herdr 0.9.1\nhome=https://herdr.dev\nbinary_sha256=" + "a" * 64
        + "\nbinary_size=42\nbinary_path=/external/herdr\n"
        "note=External binary dependency is pinned.\n", encoding="utf-8")
    payload = repo / "payload.txt"
    payload.write_text("bounded payload\n", encoding="utf-8")
    payload.chmod(0o755)
    git(repo, "init", "-q")
    git(repo, "add", ".")
    git(repo, "update-index", "--chmod=+x", "payload.txt")
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@localhost",
        "commit", "-qm", "release fixture")
    commit = subprocess.check_output(["git", "-C", str(repo), "rev-parse", "HEAD"], text=True).strip()
    git(repo, "-c", "user.name=Test", "-c", "user.email=test@localhost",
        "tag", "-a", "v1.2.3-rc.1", "-m", "fixture")
    monkeypatch.setattr(release, "PAYLOAD_PATHS", (
        "configs/consumers", "provenance/external-runtime-dependency.txt", "payload.txt"))
    return repo, commit


def test_release_consumer_contract_includes_herdr():
    assert "herdr" in release.CONSUMERS


def test_consumer_contract_is_closed_and_permission_monotonic():
    files = {f"{name}.yaml": consumer(name) for name in release.CONSUMERS}
    assert len(release.consumer_digest(files)) == 64
    unsafe = consumer("quantlab").replace(b"false", b"true")
    with pytest.raises(release.ReleaseError, match="permission_inheritance_not_fail_closed"):
        release.parse_consumer(unsafe, "quantlab")


def test_release_build_is_deterministic_and_tamper_evident(tmp_path, monkeypatch):
    repo, commit = minimal_repo(tmp_path, monkeypatch)
    git(repo, "config", "core.autocrlf", "true")
    first, second = tmp_path / "first.tar.gz", tmp_path / "second.tar.gz"
    one = release.build_release(repo, "v1.2.3-rc.1", commit, first)
    two = release.build_release(repo, "v1.2.3-rc.1", commit, second)
    assert first.read_bytes() == second.read_bytes()
    assert one["archive_sha256"] == two["archive_sha256"]
    assert one["config_contract_sha256"] == release.consumer_digest(
        {f"{name}.yaml": consumer(name) for name in release.CONSUMERS})
    assert release.verify_archive(first)["commit"] == commit
    with tarfile.open(first, "r:gz") as archive:
        members = archive.getmembers()
        assert [member.name for member in members[1:]] == sorted(
            member.name for member in members[1:])
        modes = {member.name: member.mode for member in members}
        prefix = f"v1.2.3-rc.1-{commit[:12]}"
        manifest = archive.extractfile(f"{prefix}/MANIFEST.sha256").read().decode().splitlines()
        manifest_paths = [line.split("  ", 1)[1] for line in manifest]
        assert manifest_paths == sorted(manifest_paths)
        assert modes[f"{prefix}/payload.txt"] == 0o555
        assert modes[f"{prefix}/configs/consumers/heating.yaml"] == 0o444
    damaged = tmp_path / "damaged.tar.gz"
    data = bytearray(first.read_bytes())
    data[len(data) // 2] ^= 1
    damaged.write_bytes(data)
    with pytest.raises((release.ReleaseError, tarfile.TarError, OSError, EOFError)):
        release.verify_archive(damaged)


def test_safe_extract_rejects_traversal_and_links(tmp_path):
    for name, kind in (("../escape", "file"), ("release/link", "link")):
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as archive:
            info = tarfile.TarInfo(name)
            if kind == "link":
                info.type = tarfile.SYMTYPE
                info.linkname = "/etc/passwd"
                archive.addfile(info)
            else:
                payload = b"x"
                info.size = len(payload)
                archive.addfile(info, io.BytesIO(payload))
        stream.seek(0)
        with tarfile.open(fileobj=stream, mode="r:") as archive:
            with pytest.raises(release.ReleaseError):
                release.safe_extract(archive, tmp_path / kind)


def test_cutover_helpers_are_atomic_and_never_drop_legacy_files(tmp_path):
    legacy, candidate = tmp_path / "legacy", tmp_path / "candidate"
    for root in (legacy, candidate):
        (root / "agent_platform_dashboard").mkdir(parents=True)
        (root / "deploy" / "agent_platform" / "production").mkdir(parents=True)
        (root / "agent_platform_dashboard" / "production_web.py").write_text("old")
        (root / "deploy" / "agent_platform" / "production" / "launch.py").write_text("same")
    (candidate / "agent_platform_dashboard" / "production_web.py").write_text("new")
    (candidate / "agent_platform_dashboard" / "production_release.py").write_text("added")
    result = cutover.compare_trees(candidate, legacy)
    assert result == {"unchanged": 1, "changed": 1, "added": 1, "removed": 0,
                      "candidate_files": 3, "legacy_files": 2}
    (candidate / "deploy" / "agent_platform" / "production" / "launch.py").unlink()
    with pytest.raises(release.ReleaseError, match="candidate_drops"):
        cutover.compare_trees(candidate, legacy)

    if os.name != "nt":
        links = tmp_path / "links"
        links.mkdir()
        first, second = tmp_path / "first", tmp_path / "second"
        first.mkdir(); second.mkdir()
        cutover.atomic_symlink(first, links / "current")
        assert (links / "current").resolve() == first
        cutover.atomic_symlink(second, links / "current")
        assert (links / "current").resolve() == second


def test_http_status_waits_for_reload_convergence(monkeypatch):
    statuses = iter(("401", "401", "503"))
    sleeps = []
    monkeypatch.setattr(cutover, "http_status", lambda _url: next(statuses))
    monkeypatch.setattr(cutover.time, "sleep", sleeps.append)

    assert cutover.wait_http_status("https://example.test/health", "503",
                                    attempts=3, delay=0.25) == "503"
    assert sleeps == [0.25, 0.25]


def test_http_status_wait_is_bounded_and_reports_last_status(monkeypatch):
    monkeypatch.setattr(cutover, "http_status", lambda _url: "401")
    monkeypatch.setattr(cutover.time, "sleep", lambda _delay: None)

    with pytest.raises(release.ReleaseError, match="http_status_timeout:503:401"):
        cutover.wait_http_status("https://example.test/health", "503",
                                 attempts=2, delay=0)


def test_runtime_units_use_only_atomic_current_symlink():
    for name in cutover.UNITS:
        template = Path("deploy/agent_platform/production") / f"{name}.in"
        text = template.read_text(encoding="utf-8")
        if name.endswith(".service"):
            assert "/opt/herdr/current" in text
            assert "/opt/agent-platform/release" not in text


def test_deployed_document_is_closed_and_binds_config():
    value = cutover.deployed_document(
        {
            "tag": "v1.2.3",
            "commit": "a" * 40,
            "config_contract_sha256": "b" * 64,
            "payload_manifest_sha256": "d" * 64,
        },
        "b" * 64, 100)
    assert json.dumps(value, sort_keys=True) == json.dumps({
        "version": 1, "tag": "v1.2.3", "commit": "a" * 40,
        "config_sha256": "b" * 64,
        "payload_manifest_sha256": "d" * 64,
        "deployed_at": 100}, sort_keys=True)
    with pytest.raises(release.ReleaseError, match="deployment_config_mismatch"):
        cutover.deployed_document(
            {
                "tag": "v1.2.3",
                "commit": "a" * 40,
                "config_contract_sha256": "b" * 64,
                "payload_manifest_sha256": "d" * 64,
            },
            "c" * 64, 100)



def test_watchdog_unit_is_versioned_and_cutover_managed():
    source = Path("agent-stack/systemd/agent-stack-watchdog.service").read_text(
        encoding="utf-8"
    )
    template = Path(
        "deploy/agent_platform/production/agent-stack-watchdog.service.in"
    ).read_text(encoding="utf-8")

    assert source == template
    assert "agent-stack-watchdog.service" in cutover.UNITS
    assert (
        "ExecStart=/opt/herdr/current/agent-stack/bin/agent-stack-watchdog"
        in source
    )
    assert (
        "/home/agentops/.local/bin/agent-stack-watchdog"
        not in source
    )

    expected = cutover.expected_hashes(
        Path(
            "deploy/herdr/cutover/"
            "legacy-quantlab-staging-01.sha256"
        )
    )
    assert (
        cutover.UNIT_DIR / "agent-stack-watchdog.service"
        in expected
    )


def _versioned_current_release_fixture(monkeypatch, tmp_path):
    releases = tmp_path / "releases"
    releases.mkdir()
    legacy = tmp_path / "legacy"
    legacy.mkdir()
    unit_dir = tmp_path / "units"
    unit_dir.mkdir()
    public_state = tmp_path / "deployed-release.json"

    commit = "a" * 40
    tag = "v0.3.0-rc.8"
    current_release = releases / f"{tag}-{commit[:12]}"
    bundle = current_release / "deploy" / "agent_platform" / "production"
    bundle.mkdir(parents=True)

    manifest_lines = []
    expected = {}
    for name in cutover.UNITS:
        data = f"previous-release:{name}\n".encode()
        source = bundle / f"{name}.in"
        source.write_bytes(data)
        relative = f"deploy/agent_platform/production/{name}.in"
        digest = release.sha256(data)
        manifest_lines.append(f"{digest}  {relative}\n")
        expected[unit_dir / name] = digest
        (unit_dir / name).write_bytes(data)

    manifest = "".join(manifest_lines).encode()
    document = {
        "schema_version": 1,
        "tag": tag,
        "commit": commit,
        "commit_time": 1,
        "config_contract_sha256": "b" * 64,
        "external_dependency": {
            "name": "herdr",
            "version": "0.9.1",
            "sha256": "c" * 64,
            "size": 1,
        },
        "payload_manifest_sha256": release.sha256(manifest),
    }
    (current_release / "RELEASE.json").write_bytes(
        release.canonical_json(document)
    )
    (current_release / "MANIFEST.sha256").write_bytes(manifest)

    current = tmp_path / "current"
    current.symlink_to(current_release)
    public_state.write_text(
        json.dumps({
            "version": 1,
            "tag": tag,
            "commit": commit,
            "config_sha256": document["config_contract_sha256"],
            "payload_manifest_sha256": document["payload_manifest_sha256"],
            "deployed_at": 1,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(cutover, "RELEASES", releases)
    monkeypatch.setattr(cutover, "LEGACY", legacy)
    monkeypatch.setattr(cutover, "CURRENT", current)
    monkeypatch.setattr(cutover, "UNIT_DIR", unit_dir)
    monkeypatch.setattr(cutover, "PUBLIC_STATE", public_state)
    monkeypatch.setattr(cutover, "root_owned_readonly", lambda _path: True)
    return current_release, expected


def test_versioned_upgrade_accepts_manifest_bound_previous_release_units(
    monkeypatch,
    tmp_path,
):
    _current, expected = _versioned_current_release_fixture(
        monkeypatch,
        tmp_path,
    )
    assert cutover.current_release_unit_hashes() == expected


def test_versioned_upgrade_rejects_tampered_previous_release_unit(
    monkeypatch,
    tmp_path,
):
    current, _expected = _versioned_current_release_fixture(
        monkeypatch,
        tmp_path,
    )
    source = (
        current
        / "deploy"
        / "agent_platform"
        / "production"
        / f"{cutover.UNITS[0]}.in"
    )
    source.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(
        release.ReleaseError,
        match="current_release_unit_manifest_mismatch",
    ):
        cutover.current_release_unit_hashes()


def test_versioned_upgrade_rejects_public_marker_identity_mismatch(
    monkeypatch,
    tmp_path,
):
    _current, _expected = _versioned_current_release_fixture(
        monkeypatch,
        tmp_path,
    )
    marker = json.loads(
        cutover.PUBLIC_STATE.read_text(encoding="utf-8")
    )
    marker["commit"] = "d" * 40
    cutover.PUBLIC_STATE.write_text(
        json.dumps(marker),
        encoding="utf-8",
    )

    with pytest.raises(
        release.ReleaseError,
        match="current_release_public_state_mismatch",
    ):
        cutover.current_release_unit_hashes()


def test_rc8_bootstrap_accepts_only_explicit_reviewed_unit_hashes(
    monkeypatch,
    tmp_path,
):
    current, expected = _versioned_current_release_fixture(
        monkeypatch,
        tmp_path,
    )
    document = json.loads(
        (current / "RELEASE.json").read_text(encoding="utf-8")
    )
    # Bootstrap must work even when the unprivileged preflight operator cannot
    # access the legacy RC8 deployed marker.
    cutover.PUBLIC_STATE.unlink()
    identity = (document["tag"], document["commit"])
    reviewed = {
        name: expected[cutover.UNIT_DIR / name]
        for name in cutover.UNITS
    }
    monkeypatch.setattr(
        cutover,
        "BOOTSTRAP_VERSIONED_UNIT_HASHES",
        {identity: reviewed},
    )
    assert cutover.current_release_unit_hashes() == expected

    monkeypatch.setattr(
        cutover,
        "BOOTSTRAP_VERSIONED_UNIT_HASHES",
        {},
    )
    with pytest.raises(
        release.ReleaseError,
        match="current_release_public_state_missing",
    ):
        cutover.current_release_unit_hashes()


def test_rc8_bootstrap_rejects_installed_unit_not_matching_baseline(
    monkeypatch,
    tmp_path,
):
    current, expected = _versioned_current_release_fixture(
        monkeypatch,
        tmp_path,
    )
    document = json.loads(
        (current / "RELEASE.json").read_text(encoding="utf-8")
    )
    cutover.PUBLIC_STATE.unlink()
    identity = (document["tag"], document["commit"])
    reviewed = {
        name: expected[cutover.UNIT_DIR / name]
        for name in cutover.UNITS
    }
    monkeypatch.setattr(
        cutover,
        "BOOTSTRAP_VERSIONED_UNIT_HASHES",
        {identity: reviewed},
    )

    active = cutover.UNIT_DIR / cutover.UNITS[0]
    active.write_text("runtime drift\n", encoding="utf-8")

    with pytest.raises(
        release.ReleaseError,
        match="runtime_unit_bootstrap_mismatch",
    ):
        cutover.current_release_unit_hashes()


def test_rc8_router_recovery_evidence_is_exact_and_fail_closed(
    monkeypatch,
    tmp_path,
):
    releases = tmp_path / "releases"
    releases.mkdir()
    previous = releases / (
        f"{cutover.RECOVERY_RC8_TAG}-"
        f"{cutover.RECOVERY_RC8_COMMIT[:12]}"
    )
    previous.mkdir()

    class CurrentLink:
        @staticmethod
        def is_symlink():
            return True

        @staticmethod
        def resolve(*, strict):
            assert strict
            return previous

    snapshot = tmp_path / "snapshot.json"
    now = int(cutover.time.time())
    sources = []
    for profile in ("majak", "quantlab"):
        sources.append({
            "profile": profile,
            "kind": "router",
            "status": "unavailable",
            "reason": "source_failed",
            "rows": [],
        })
        sources.append({
            "profile": profile,
            "kind": "herdr",
            "status": "available",
            "reason": "ok",
            "rows": [{"agent": f"{profile}-hermes", "status": "idle"}],
        })
    sources.append({
        "profile": "quantlab",
        "kind": "release",
        "status": "available",
        "reason": "ok",
        "rows": [{
            "tag": cutover.RECOVERY_RC8_TAG,
            "commit": cutover.RECOVERY_RC8_COMMIT,
        }],
    })
    snapshot.write_text(
        json.dumps({
            "version": 1,
            "generated_at": now,
            "sources": sources,
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(cutover, "RELEASES", releases)
    monkeypatch.setattr(cutover, "CURRENT", CurrentLink())
    monkeypatch.setattr(cutover, "SNAPSHOT", snapshot)
    live_socket = {"value": True}
    monkeypatch.setattr(
        cutover,
        "live_unix_socket",
        lambda path: live_socket["value"],
    )
    counts = {"majak": 51, "quantlab": 51}
    monkeypatch.setattr(
        cutover,
        "recovery_router_group_counts",
        lambda: dict(counts),
    )

    statuses = {
        "agent-platform-web.service": "failed",
        "agent-platform-export.timer": "active",
        "agent-platform-herdr.timer": "active",
        "agent-stack-watchdog.service": "inactive",
    }

    assert cutover.rc8_router_recovery_evidence(statuses)
    bad = dict(statuses)
    bad["agent-stack-watchdog.service"] = "active"
    assert not cutover.rc8_router_recovery_evidence(bad)

    counts["majak"] = 50
    assert not cutover.rc8_router_recovery_evidence(statuses)
    counts["majak"] = 51

    document = json.loads(snapshot.read_text(encoding="utf-8"))
    document["sources"][0]["reason"] = "stale"
    snapshot.write_text(json.dumps(document), encoding="utf-8")
    assert not cutover.rc8_router_recovery_evidence(statuses)

    document["sources"][0]["reason"] = "source_failed"
    snapshot.write_text(json.dumps(document), encoding="utf-8")
    live_socket["value"] = False
    assert not cutover.rc8_router_recovery_evidence(statuses)


def test_live_unix_socket_requires_live_listener(tmp_path):
    import socket as socket_module

    if not hasattr(socket_module, "AF_UNIX"):
        pytest.skip("Unix sockets are unavailable on this platform")
    socket_path = tmp_path / "herdr.sock"
    listener = socket_module.socket(
        socket_module.AF_UNIX,
        socket_module.SOCK_STREAM,
    )
    listener.bind(str(socket_path))
    listener.listen(1)
    try:
        assert cutover.live_unix_socket(socket_path)
    finally:
        listener.close()

    assert not cutover.live_unix_socket(socket_path)


def test_recovery_router_group_query_is_bounded_at_overflow():
    import sqlite3

    database = sqlite3.connect(":memory:")
    database.execute(
        "CREATE TABLE requests ("
        "id INTEGER, task_id TEXT, actual_model TEXT, provider TEXT)"
    )
    database.executemany(
        "INSERT INTO requests VALUES (?, ?, ?, ?)",
        [
            (index, f"task-{index}", "model", "provider")
            for index in range(1, 53)
        ],
    )
    try:
        count = database.execute(
            cutover.RECOVERY_ROUTER_GROUP_COUNT_SQL
        ).fetchone()[0]
    finally:
        database.close()

    assert count == 51


def test_recovery_target_is_exact_reviewed_rc12(monkeypatch, tmp_path):
    archive = tmp_path / "rc12.tar.gz"
    archive.write_bytes(b"reviewed rc12 archive")
    monkeypatch.setattr(
        cutover,
        "RECOVERY_TARGET_ARCHIVE_SHA256",
        cutover.digest_file(archive),
    )
    document = {
        "tag": cutover.RECOVERY_TARGET_TAG,
        "commit": cutover.RECOVERY_TARGET_COMMIT,
        "config_contract_sha256": cutover.RECOVERY_TARGET_CONFIG_SHA256,
        "payload_manifest_sha256": (
            cutover.RECOVERY_TARGET_PAYLOAD_MANIFEST_SHA256
        ),
    }

    cutover.verify_recovery_target(archive, document)

    for field in (
        "tag",
        "commit",
        "config_contract_sha256",
        "payload_manifest_sha256",
    ):
        changed = dict(document)
        changed[field] = "unexpected"
        with pytest.raises(
            release.ReleaseError,
            match="recovery_target_identity_mismatch",
        ):
            cutover.verify_recovery_target(archive, changed)

    archive.write_bytes(b"different archive")
    with pytest.raises(
        release.ReleaseError,
        match="recovery_target_archive_mismatch",
    ):
        cutover.verify_recovery_target(archive, document)


def test_recovery_unit_quiescence_is_verified(monkeypatch):
    states = {
        "agent-platform-export.timer": "inactive",
        "agent-platform-herdr.timer": "inactive",
        "agent-stack-watchdog.service": "inactive",
    }
    calls = []

    def fake_run(*args, check=True):
        calls.append((args, check))
        if args[:2] == ("/usr/bin/systemctl", "is-active"):
            return states[args[2]]
        return ""

    monkeypatch.setattr(cutover, "run", fake_run)
    cutover.stop_recovery_units()
    assert calls[0] == ((
        "/usr/bin/systemctl",
        "stop",
        "agent-platform-export.timer",
        "agent-platform-herdr.timer",
        "agent-stack-watchdog.service",
    ), True)

    states["agent-platform-herdr.timer"] = "active"
    with pytest.raises(
        release.ReleaseError,
        match="recovery_timer_not_stopped:agent-platform-herdr.timer",
    ):
        cutover.stop_recovery_units()


def test_recovery_watchdog_stop_is_verified(monkeypatch):
    state = {"value": "inactive"}

    def fake_run(*args, check=True):
        if args[:2] == ("/usr/bin/systemctl", "is-active"):
            return state["value"]
        return ""

    monkeypatch.setattr(cutover, "run", fake_run)
    cutover.stop_watchdog_service()

    state["value"] = "active"
    with pytest.raises(
        release.ReleaseError,
        match="watchdog_not_stopped",
    ):
        cutover.stop_watchdog_service()


def test_recovery_apply_is_explicit_and_never_claims_rollback_exercise():
    source = Path("deploy/herdr/cutover/cutover.py").read_text(
        encoding="utf-8"
    )
    recovery = source.split("def recovery_apply(", 1)[1].split(
        "def main()",
        1,
    )[0]

    assert '"rollback_exercised": False' in recovery
    assert '"rollback_mode": "skipped_known_degraded_previous"' in recovery
    assert '"recovery_mode": "rc8_router_overflow"' in recovery
    assert '"fail_closed_route"' in recovery
    success, rollback = recovery.split("except BaseException as original_error:", 1)
    public_probe = (
        'wait_http_status(\n            "https://2.28.67.165/agent-platform/health",\n            "401",'
    )
    assert "stop_recovery_units()" in success
    assert success.index(public_probe) < success.index(
        "atomic_write(state_path, canonical_json(state), 0o600)"
    )
    assert success.index(
        "atomic_write(state_path, canonical_json(state), 0o600)"
    ) < success.index("start_watchdog_service()")
    assert '("stop_watchdog", stop_watchdog_service)' in rollback
    assert '"remove_success_state"' in rollback
    assert "start_telemetry_timers" in rollback
    assert "recovery_rollback_watchdog_active" in rollback


def test_agent_stack_runtime_chain_is_release_relative():
    dispatcher = Path(
        "agent-stack/bin/agent-task-dispatcher"
    ).read_text(encoding="utf-8")
    assert "BIN = Path(__file__).resolve().parent" in dispatcher
    assert 'WORKER = BIN / "agent-task-worker"' in dispatcher
    assert ".local/bin/agent-task-worker" not in dispatcher

    watchdog = Path(
        "agent-stack/bin/agent-stack-watchdog"
    ).read_text(encoding="utf-8")
    assert 'BIN_DIR="' in watchdog
    assert '$BIN_DIR/agent-stack-ensure' in watchdog
    assert '$BIN_DIR/agent-stack-recovery' in watchdog
    assert '$BIN_DIR/hermes-maintenance' in watchdog
    assert "/home/agentops/.local/bin/agent-stack-" not in watchdog

    maintenance = Path(
        "agent-stack/bin/hermes-maintenance"
    ).read_text(encoding="utf-8")
    assert "BIN = Path(__file__).resolve().parent" in maintenance
    for name in (
        "agent-codex-usage-export",
        "hermes-offsite-prepare",
        "hermes-offsite-sync",
    ):
        assert f'BIN / "{name}"' in maintenance
    assert "wrapper = BIN / profile" in maintenance
    assert 'script = BIN / name' in maintenance


def test_switch_runtime_keeps_watchdog_quiescent(
    monkeypatch,
    tmp_path,
):
    events = []

    def fake_run(*args, check=True):
        events.append(("run", *args))
        if (
            len(args) >= 3
            and args[0] == "/usr/bin/systemctl"
            and args[1] == "is-active"
        ):
            return "active"
        return ""

    monkeypatch.setattr(cutover, "run", fake_run)
    monkeypatch.setattr(
        cutover,
        "atomic_symlink",
        lambda target, link: events.append(
            ("symlink", str(target), str(link))
        ),
    )
    monkeypatch.setattr(
        cutover,
        "wait_http_status",
        lambda *_args, **_kwargs: "401",
    )
    monkeypatch.setattr(
        cutover,
        "assert_hardening",
        lambda: None,
    )

    target = tmp_path / "release"
    target.mkdir()

    cutover.switch_runtime(
        target,
        None,
    )

    stop = (
        "run",
        "/usr/bin/systemctl",
        "stop",
        "agent-stack-watchdog.service",
        "agent-platform-web.service",
    )
    link = (
        "symlink",
        str(target),
        str(cutover.CURRENT),
    )

    assert stop in events
    assert link in events
    assert events.index(stop) < events.index(link)

    assert not any(
        event[:4]
        == (
            "run",
            "/usr/bin/systemctl",
            "start",
            "agent-stack-watchdog.service",
        )
        for event in events
    )



def test_switch_runtime_resets_rate_limit_and_starts_herdr_once_via_export(
    monkeypatch,
    tmp_path,
):
    events = []

    def fake_run(*args, check=True):
        events.append(("run", *args))

        if args[:2] == (
            "/usr/bin/systemctl",
            "is-active",
        ):
            return "active"

        return ""

    monkeypatch.setattr(
        cutover,
        "run",
        fake_run,
    )

    monkeypatch.setattr(
        cutover,
        "atomic_symlink",
        lambda target, link: None,
    )

    monkeypatch.setattr(
        cutover,
        "wait_http_status",
        lambda *_args, **_kwargs: "401",
    )

    monkeypatch.setattr(
        cutover,
        "assert_hardening",
        lambda: None,
    )

    target = tmp_path / "release"
    target.mkdir()

    cutover.switch_runtime(
        target,
        None,
    )

    assert (
        "run",
        "/usr/bin/systemctl",
        "reset-failed",
        "agent-platform-herdr.service",
        "agent-platform-export.service",
        "agent-platform-web.service",
    ) in events

    assert (
        "run",
        "/usr/bin/systemctl",
        "start",
        "agent-platform-export.service",
    ) in events

    assert not any(
        event
        == (
            "run",
            "/usr/bin/systemctl",
            "start",
            "agent-platform-herdr.service",
        )
        for event in events
    )


def test_rollback_steps_continue_after_individual_failure():
    events = []

    def first():
        events.append("first")

    def broken():
        events.append("broken")
        raise RuntimeError("boom")

    def last():
        events.append("last")

    errors = cutover.run_rollback_steps(
        [
            ("first", first),
            ("broken", broken),
            ("last", last),
        ]
    )

    assert events == [
        "first",
        "broken",
        "last",
    ]

    assert len(errors) == 1
    assert errors[0].startswith(
        "broken:RuntimeError:boom"
    )



def test_watchdog_start_is_explicit(monkeypatch):
    events = []

    def fake_run(*args, check=True):
        events.append(("run", *args))
        if args[:3] == (
            "/usr/bin/systemctl",
            "is-active",
            "agent-stack-watchdog.service",
        ):
            return "active"
        return ""

    monkeypatch.setattr(cutover, "run", fake_run)

    cutover.start_watchdog_service()

    assert (
        "run",
        "/usr/bin/systemctl",
        "start",
        "agent-stack-watchdog.service",
    ) in events


def test_active_worker_blocks_control_plane_promotion(monkeypatch):
    monkeypatch.setattr(
        cutover,
        "run",
        lambda *args, **kwargs:
            "123 python3 /opt/herdr/current/agent-stack/bin/agent-task-worker task.json"
    )

    with pytest.raises(
        release.ReleaseError,
        match="durable_worker_active",
    ):
        cutover.assert_no_active_durable_worker()


def test_apply_keeps_watchdog_quiescent_during_rollback_exercise():
    source = Path(
        "deploy/herdr/cutover/cutover.py"
    ).read_text(encoding="utf-8")

    apply_source = source.split(
        "def apply(",
        1,
    )[1]

    assert "assert_no_active_durable_worker()" in apply_source
    assert "unit_snapshots = snapshot_units()" in apply_source
    assert "restore_units(unit_snapshots)" in apply_source
    assert "public_state_snapshot = snapshot_file(PUBLIC_STATE)" in apply_source
    assert "restore_file(" in apply_source
    assert "run_rollback_steps(" in apply_source
    assert "rollback_incomplete:" in apply_source
    assert "fail_closed_route" in apply_source
    assert '"restore_current"' in apply_source

    # switch_runtime itself never restarts durable dispatch.
    switch_source = source.split(
        "def switch_runtime(",
        1,
    )[1].split(
        "def start_watchdog_service",
        1,
    )[0]
    assert '"start",\n            "agent-stack-watchdog.service"' not in switch_source

    # Success path starts watchdog only after public health proof.
    assert apply_source.index(
        'wait_http_status(\n            "https://2.28.67.165/agent-platform/health",\n            "401",'
    ) < apply_source.index(
        "start_watchdog_service()"
    )


def test_legacy_watchdog_installer_is_release_relative():
    text = Path(
        "agent-stack/install-agent-stack-service.sh"
    ).read_text(encoding="utf-8")

    assert 'SCRIPT_DIR="' in text
    assert "$SCRIPT_DIR/systemd/agent-stack-watchdog.service" in text
    assert "/home/agentops/.local/share/agent-stack" not in text


def test_offsite_backup_captures_immutable_release_control_plane():
    text = Path(
        "agent-stack/bin/hermes-offsite-prepare"
    ).read_text(encoding="utf-8")

    assert "RELEASE_ROOT=" in text
    assert "CURRENT_RELEASE=" in text

    assert "RELEASE.json" in text
    assert "MANIFEST.sha256" in text
    assert '-C "$RELEASE_ROOT"' in text
    assert "COMPLETE immutable Herdr release" in text

    assert ".local/bin/agent-stack-watchdog" not in text
    assert ".local/bin/agent-stack-recovery" not in text
    assert ".local/bin/agent-task-dispatcher" not in text



def test_snapshot_restore_contract_is_exact(monkeypatch, tmp_path):
    path = tmp_path / "unit.service"
    path.write_bytes(b"before\n")
    path.chmod(0o640)

    snapshot = cutover.snapshot_file(path)

    assert snapshot is not None
    assert snapshot[0] == b"before\n"
    assert snapshot[1] == 0o640

    writes = []

    monkeypatch.setattr(
        cutover,
        "atomic_write",
        lambda target, data, mode, uid=0, gid=0:
            writes.append((target, data, mode, uid, gid)),
    )

    cutover.restore_file(path, snapshot)

    assert writes
    assert writes[0][0] == path
    assert writes[0][1] == b"before\n"
    assert writes[0][2] == 0o640



def test_already_deployed_requires_full_coherence(
    monkeypatch,
    tmp_path,
):
    candidate = tmp_path / "release"
    unit_dir = tmp_path / "units"
    consumer_dir = tmp_path / "consumers"
    public_state = tmp_path / "deployed-release.json"

    bundle = (
        candidate
        / "deploy"
        / "agent_platform"
        / "production"
    )
    bundle.mkdir(parents=True)
    unit_dir.mkdir()
    consumer_dir.mkdir()

    for name in cutover.UNITS:
        data = f"unit={name}\n".encode()
        (bundle / f"{name}.in").write_bytes(data)
        (unit_dir / name).write_bytes(data)

    consumer_files = {}

    for name in release.CONSUMERS:
        data = consumer(name)
        (
            candidate
            / "configs"
            / "consumers"
        ).mkdir(
            parents=True,
            exist_ok=True,
        )
        (
            candidate
            / "configs"
            / "consumers"
            / f"{name}.yaml"
        ).write_bytes(data)
        (
            consumer_dir
            / f"{name}.yaml"
        ).write_bytes(data)
        consumer_files[f"{name}.yaml"] = data

    digest = release.consumer_digest(consumer_files)

    release_doc = {
        "tag": "v1.2.3-rc.7",
        "commit": "a" * 40,
        "config_contract_sha256": digest,
        "payload_manifest_sha256": "d" * 64,
    }

    public_state.write_text(
        json.dumps(
            {
                "version": 1,
                "tag": release_doc["tag"],
                "commit": release_doc["commit"],
                "config_sha256": digest,
                "payload_manifest_sha256": release_doc["payload_manifest_sha256"],
                "deployed_at": 123456789,
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        cutover,
        "UNIT_DIR",
        unit_dir,
    )
    monkeypatch.setattr(
        cutover,
        "CONSUMER_DIR",
        consumer_dir,
    )
    monkeypatch.setattr(
        cutover,
        "PUBLIC_STATE",
        public_state,
    )

    cutover.assert_deployed_coherence(
        candidate,
        release_doc,
    )

    # A matching release symlink with stale units must fail closed.
    (unit_dir / cutover.UNITS[0]).write_text(
        "stale\n",
        encoding="utf-8",
    )

    with pytest.raises(
        release.ReleaseError,
        match="already_deployed_unit_mismatch",
    ):
        cutover.assert_deployed_coherence(
            candidate,
            release_doc,
        )

    # Restore the unit and prove a stale marker also fails closed.
    source = bundle / f"{cutover.UNITS[0]}.in"
    (unit_dir / cutover.UNITS[0]).write_bytes(
        source.read_bytes()
    )

    marker = json.loads(
        public_state.read_text(encoding="utf-8")
    )
    marker["commit"] = "b" * 40

    public_state.write_text(
        json.dumps(marker),
        encoding="utf-8",
    )

    with pytest.raises(
        release.ReleaseError,
        match="already_deployed_public_state_mismatch",
    ):
        cutover.assert_deployed_coherence(
            candidate,
            release_doc,
        )
