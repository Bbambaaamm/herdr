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
        {"tag": "v1.2.3", "commit": "a" * 40, "config_contract_sha256": "b" * 64},
        "b" * 64, 100)
    assert json.dumps(value, sort_keys=True) == json.dumps({
        "version": 1, "tag": "v1.2.3", "commit": "a" * 40,
        "config_sha256": "b" * 64, "deployed_at": 100}, sort_keys=True)
    with pytest.raises(release.ReleaseError, match="deployment_config_mismatch"):
        cutover.deployed_document(
            {"tag": "v1.2.3", "commit": "a" * 40, "config_contract_sha256": "b" * 64},
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
    }

    public_state.write_text(
        json.dumps(
            {
                "version": 1,
                "tag": release_doc["tag"],
                "commit": release_doc["commit"],
                "config_sha256": digest,
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
