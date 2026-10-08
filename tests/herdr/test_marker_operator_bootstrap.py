"""RC26 marker bootstrap is explicitly privileged and narrowly scoped."""
from __future__ import annotations

from contextlib import nullcontext
import hashlib
import importlib.util
import json
import os
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
    }))
    state = tmp_path / "private-state"
    state.mkdir()
    state.chmod(0o750)
    marker = state / "deployed-release.json"
    marker.write_text('{"release":"reviewed"}\n')
    marker.chmod(0o640)
    original = marker.read_bytes()
    commands = []
    bound_hashes = []

    monkeypatch.setattr(mod.cutover, "CURRENT", current)
    monkeypatch.setattr(mod.cutover, "PUBLIC_STATE", marker)
    monkeypatch.setattr(mod.cutover, "deployment_lock", nullcontext)
    monkeypatch.setattr(mod.cutover, "current_release_unit_hashes",
                        lambda: bound_hashes.append("verified"))
    monkeypatch.setattr(mod.os, "geteuid", lambda: 0)
    monkeypatch.setattr(mod.pwd, "getpwnam",
                        lambda name: SimpleNamespace(pw_uid=os.getuid()))
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
    def checked(argv, error):
        commands.append((argv, error))
        return ACL if argv[0] == "/usr/bin/getfacl" else ""
    monkeypatch.setattr(mod, "_checked_command", checked)

    outcome = mod.bootstrap()
    assert outcome["status"] == "marker_operator_read_ok"
    assert outcome["marker_sha256"] == hashlib.sha256(original).hexdigest()
    assert bound_hashes == ["verified"]
    assert len(commands) == 3
    assert commands[0][0][:3] == ["/usr/bin/setfacl", "-m", "u:quantadmin:--x"]
    assert commands[1][0][0] == "/usr/bin/getfacl"
    assert commands[2][0][:5] == [
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
