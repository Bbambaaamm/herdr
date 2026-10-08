"""RC26 marker bootstrap is explicitly privileged and narrowly scoped."""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "deploy" / "herdr" / "cutover" / "bootstrap_operator_marker.py"


def marker_module():
    spec = importlib.util.spec_from_file_location("test_marker_bootstrap", SOURCE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ACL = "user::rwx\nuser:quantadmin:--x\ngroup::r-x\nmask::r-x\nother::---\n"


def test_acl_contract_never_allows_listing_or_other_users():
    mod = marker_module()
    assert mod.safe_acl_rows(ACL)
    assert not mod.safe_acl_rows(ACL.replace("user:quantadmin:--x",
                                             "user:quantadmin:r-x"))
    assert not mod.safe_acl_rows(ACL.replace("other::---", "other::r-x"))
    assert not mod.safe_acl_rows(ACL + "user:attacker:r-x\n")


def test_root_is_required_before_any_mutation(monkeypatch):
    mod = marker_module()
    monkeypatch.setattr(mod.os, "geteuid", lambda: 1001)
    with pytest.raises(mod.cutover.ReleaseError, match="marker_bootstrap_root_required"):
        mod.bootstrap()


def test_unrelated_release_identity_fails_before_mutation(tmp_path, monkeypatch):
    mod = marker_module()
    current = tmp_path / "current"
    current.mkdir()
    (current / "RELEASE.json").write_text(json.dumps({
        "tag": "v0.3.0-rc.27", "commit": "f" * 40,
    }))
    monkeypatch.setattr(mod.cutover, "CURRENT", current)
    monkeypatch.setattr(mod.cutover, "deployment_lock", nullcontext)
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setattr(mod, "_require_frozen_source", lambda: None)
    def forbidden(*args, **kwargs):
        raise AssertionError("no state or permission mutations allowed")
    monkeypatch.setattr(mod, "_checked_command", forbidden)
    with pytest.raises(mod.cutover.ReleaseError,
                       match="marker_bootstrap_current_identity_mismatch"):
        mod.bootstrap()


def test_approved_rc26_bootstrap_checks_acl_marker_and_operator(tmp_path, monkeypatch):
    mod = marker_module()
    current = tmp_path / "current"
    current.mkdir()
    (current / "RELEASE.json").write_text(json.dumps({
        "tag": mod.PINNED_CURRENT[0], "commit": mod.PINNED_CURRENT[1],
        "config_contract_sha256": "a" * 64,
        "payload_manifest_sha256": "b" * 64,
    }))
    state = tmp_path / "private-state"
    state.mkdir()
    state.chmod(0o750)
    marker = state / "deployed-release.json"
    marker.write_text(json.dumps({
        "version": 1,
        "tag": mod.PINNED_CURRENT[0], "commit": mod.PINNED_CURRENT[1],
        "config_sha256": "a" * 64, "payload_manifest_sha256": "b" * 64,
        "deployed_at": 1,
    }) + "\n")
    marker.chmod(0o640)
    original = marker.read_bytes()
    commands = []
    bound_hashes = []

    monkeypatch.setattr(mod.cutover, "CURRENT", current)
    monkeypatch.setattr(mod.cutover, "PUBLIC_STATE", marker)
    monkeypatch.setattr(mod.cutover, "deployment_lock", nullcontext)
    def validated_units():
        bound_hashes.append("verified")
        return {}
    monkeypatch.setattr(mod.cutover, "current_release_unit_hashes", validated_units)
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setattr(mod, "_require_frozen_source", lambda: None)
    monkeypatch.setattr(mod.pwd, "getpwnam",
                        lambda name: SimpleNamespace(pw_uid=os.getuid(), pw_gid=os.getgid()))
    monkeypatch.setattr(mod.grp, "getgrnam",
                        lambda name: SimpleNamespace(gr_gid=os.getgid()))
    true_lstat = os.lstat

    def fake_lstat(path):
        info = true_lstat(path)
        if Path(path) == marker:
            return SimpleNamespace(st_mode=info.st_mode, st_uid=0,
                                   st_gid=info.st_gid, st_size=info.st_size)
        return info

    monkeypatch.setattr(mod.os, "lstat", fake_lstat)
    def checked(argv, error, *, input_text=None):
        commands.append((argv, error, input_text))
        return ACL if argv[0] == "/usr/bin/getfacl" else ""
    monkeypatch.setattr(mod, "_checked_command", checked)

    outcome = mod.bootstrap()
    assert outcome["status"] == "marker_operator_read_ok"
    assert outcome["marker_sha256"] == hashlib.sha256(original).hexdigest()
    assert bound_hashes == ["verified"]
    assert len(commands) == 4
    assert commands[0][0][0] == "/usr/bin/getfacl"
    assert commands[1][0][:3] == ["/usr/bin/setfacl", "-m", "u:quantadmin:--x"]
    assert commands[2][0][0] == "/usr/bin/getfacl"
    assert commands[3][0][:5] == [
        "/usr/sbin/runuser", "-u", "quantadmin", "--", "/usr/bin/python3"
    ]
    assert marker.read_bytes() == original
    assert marker.stat().st_mode & 0o777 == 0o644


def test_future_marker_writes_are_root_owned_and_readable(monkeypatch):
    mod = marker_module()
    writes = []
    monkeypatch.setattr(mod.cutover.grp, "getgrnam",
                        lambda name: SimpleNamespace(gr_gid=871))
    monkeypatch.setattr(
        mod.cutover, "atomic_write",
        lambda path, content, mode, uid, gid:
            writes.append((path, content, mode, uid, gid)),
    )
    marker = {"version": 1, "tag": mod.PINNED_CURRENT[0],
              "commit": mod.PINNED_CURRENT[1],
              "config_sha256": "a" * 64,
              "payload_manifest_sha256": "b" * 64,
              "deployed_at": 1}
    mod.cutover.write_deployed(marker)
    assert len(writes) == 1
    path, body, mode, uid, gid = writes[0]
    assert path == mod.cutover.PUBLIC_STATE
    assert json.loads(body) == marker
    assert (mode, uid, gid) == (0o644, 0, 871)



def bootstrap_fixture(tmp_path, monkeypatch, *, extra_marker=None, private_mode=0o640):
    """Disposable, unprivileged state; only OS uid *checks* are stubbed."""
    mod = marker_module()
    current = tmp_path / "current"
    current.mkdir()
    (current / "RELEASE.json").write_text(json.dumps({
        "tag": mod.PINNED_CURRENT[0], "commit": mod.PINNED_CURRENT[1],
        "config_contract_sha256": "a" * 64,
        "payload_manifest_sha256": "b" * 64,
    }))
    state = tmp_path / "private-state"
    state.mkdir()
    state.chmod(0o750)
    marker = state / "deployed-release.json"
    document = {
        "version": 1, "tag": mod.PINNED_CURRENT[0],
        "commit": mod.PINNED_CURRENT[1],
        "config_sha256": "a" * 64,
        "payload_manifest_sha256": "b" * 64,
        "deployed_at": 1,
    }
    if extra_marker:
        document.update(extra_marker)
    marker.write_text(json.dumps(document) + "\n")
    marker.chmod(0o640)
    queue = state / "queue.json"
    queue.write_text('{"private":"fixture"}\n')
    queue.chmod(private_mode)

    monkeypatch.setattr(mod.cutover, "CURRENT", current)
    monkeypatch.setattr(mod.cutover, "PUBLIC_STATE", marker)
    monkeypatch.setattr(mod.cutover, "deployment_lock", nullcontext)
    monkeypatch.setattr(mod.cutover, "current_release_unit_hashes", lambda: {})
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setattr(mod, "_require_frozen_source", lambda: None)
    true_lstat = os.lstat
    def stat_as_root(path):
        info = true_lstat(path)
        if Path(path) == marker:
            return SimpleNamespace(st_mode=info.st_mode, st_uid=0,
                                   st_gid=info.st_gid, st_size=info.st_size)
        return info
    monkeypatch.setattr(mod.os, "lstat", stat_as_root)
    monkeypatch.setattr(
        mod.grp, "getgrnam",
        lambda name: SimpleNamespace(gr_gid=os.getgid()),
    )
    return mod, state, marker, queue


acl_tools = pytest.mark.skipif(
    not all(shutil.which(command) for command in ("setfacl", "getfacl")),
    reason="POSIX ACL command tools unavailable",
)


@acl_tools
def test_probe_failure_restores_real_posix_acl_and_marker_mode(tmp_path, monkeypatch):
    import subprocess
    mod, state, marker, queue = bootstrap_fixture(tmp_path, monkeypatch)
    before_acl = subprocess.check_output(["/usr/bin/getfacl", "-cp", str(state)],
                                         text=True)
    before = marker.read_bytes()
    real_command = mod._checked_command
    def simulated_probe_failure(argv, error, *, input_text=None):
        if argv[0] == "/usr/sbin/runuser":
            raise mod.cutover.ReleaseError("simulated_operator_probe_failed")
        return real_command(argv, error, input_text=input_text)
    monkeypatch.setattr(mod, "_checked_command", simulated_probe_failure)
    with pytest.raises(mod.cutover.ReleaseError, match="simulated_operator_probe_failed"):
        mod.bootstrap()
    after_acl = subprocess.check_output(["/usr/bin/getfacl", "-cp", str(state)],
                                        text=True)
    assert after_acl == before_acl
    assert marker.read_bytes() == before
    assert marker.stat().st_mode & 0o777 == 0o640


@acl_tools
def test_world_readable_private_entry_prevents_acl_change(tmp_path, monkeypatch):
    import subprocess
    mod, state, marker, queue = bootstrap_fixture(
        tmp_path, monkeypatch, private_mode=0o644,
    )
    original = subprocess.check_output(["/usr/bin/getfacl", "-cp", str(state)],
                                       text=True)
    with pytest.raises(mod.cutover.ReleaseError,
                       match="marker_bootstrap_private_entry_unprotected"):
        mod.bootstrap()
    assert subprocess.check_output(["/usr/bin/getfacl", "-cp", str(state)],
                                   text=True) == original
    assert marker.stat().st_mode & 0o777 == 0o640


@acl_tools
def test_preexisting_private_acl_for_operator_is_denied(tmp_path, monkeypatch):
    import subprocess
    mod, state, marker, queue = bootstrap_fixture(tmp_path, monkeypatch)
    subprocess.run(["/usr/bin/setfacl", "-m", "u:quantadmin:r--", str(queue)],
                   check=True)
    with pytest.raises(mod.cutover.ReleaseError,
                       match="marker_bootstrap_private_acl_unprotected"):
        mod.bootstrap()
    assert marker.stat().st_mode & 0o777 == 0o640


def test_marker_with_unexpected_extra_field_is_denied(tmp_path, monkeypatch):
    mod, state, marker, queue = bootstrap_fixture(
        tmp_path, monkeypatch, extra_marker={"leaked_secret": "forbidden"},
    )
    with pytest.raises(mod.cutover.ReleaseError,
                       match="marker_bootstrap_public_document_invalid"):
        mod.bootstrap()
    assert marker.stat().st_mode & 0o777 == 0o640


def test_drifted_installed_unit_prevents_permission_change(tmp_path, monkeypatch):
    mod, state, marker, queue = bootstrap_fixture(tmp_path, monkeypatch)
    installed = tmp_path / "unit.service"
    installed.write_text("changed")
    monkeypatch.setattr(mod.cutover, "current_release_unit_hashes",
                        lambda: {installed: "0" * 64})
    with pytest.raises(mod.cutover.ReleaseError,
                       match="marker_bootstrap_installed_unit_drift"):
        mod.bootstrap()
    assert marker.stat().st_mode & 0o777 == 0o640


def test_privileged_entry_rejects_non_root_owned_worktree(tmp_path, monkeypatch):
    mod = marker_module()
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    with pytest.raises(SystemExit, match="marker_bootstrap_untrusted_entry"):
        mod.bootstrap()
