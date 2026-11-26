"""Closed effective systemd validation against isolated files and manager replies."""
import json
import os
from pathlib import Path
import shutil
from types import SimpleNamespace

import pytest

from deploy.herdr.cutover import systemd_authority as s
from deploy.herdr.cutover import cutover as c
from herdr.release import canonical_json, ReleaseError


@pytest.fixture
def manager(tmp_path, monkeypatch):
    units = tmp_path / "units"
    units.mkdir()
    source = Path(c.__file__).parents[2] / "agent_platform/production"
    loaded = {}
    real_facts = s.facts
    bad_owner = set()
    def root_facts(path):
        row = real_facts(path)
        row.update(uid=1001 if path in bad_owner else 0, gid=0)
        return row
    monkeypatch.setattr(s, "facts", root_facts)
    # Only the unprivileged test directory's ancestors stand in for host roots.
    monkeypatch.setattr(s, "safe_ancestors", lambda path: None)
    for unit in c.UNITS:
        path = units / unit
        shutil.copyfile(source / (unit + ".in"), path)
        path.chmod(0o644)
        d = s.unit_directives(path)
        row = dict(FragmentPath=str(path), LoadState="loaded", Transient="no",
                   NeedDaemonReload="no", DropInPaths="", Environment=" ".join(d.get("Environment", [])))
        row.update({k: "".join(d.get(k, [])) for k in ("User", "Group", "WorkingDirectory")})
        for key in s.COMMANDS:
            row[key] = " ".join("{ path=" + line.split()[0] + " ; argv[]=" + line
                                + " ; ignore_errors=no ; start_time=[n/a] ; }" for line in d.get(key, []))
        if unit in s.SOURCE_DROPINS:
            folder = units / (unit + ".d")
            folder.mkdir()
            text = "[Service]\n"
            if "export" in unit:
                for profile in ("majak", "quantlab"):
                    text += f"BindReadOnlyPaths=/home/agentops/.hermes/profiles/{profile}/model-router:/sources/{profile}-router\n"
                for profile in ("majak", "quantlab"):
                    text += f"BindReadOnlyPaths=/home/agentops/.hermes/profiles/{profile}/search-router:/sources/{profile}-search\n"
            else:
                text += "BindReadOnlyPaths=/home/agentops/.config/herdr/herdr.sock:/sources/herdr.sock\n"
            (folder / "sources.conf").write_text(text)
            row["DropInPaths"] = str(folder / "sources.conf")
        loaded[unit] = row
    policy = tmp_path / "policy.json"
    policy.write_text('{"schema_version":1}')
    original_facts = s.facts
    monkeypatch.setattr(s, "facts", lambda path: original_facts(policy if str(path) == "/etc/herdr/host-policy.json" else path))
    api = dict(UNITS=c.UNITS, UNIT_DIR=units, ROOT=tmp_path, CURRENT=tmp_path,
               STATE_DIR=tmp_path, verify_tree=lambda _: {"commit": s.RC6},
               watchdog_fence_path=lambda: units / (s.WATCHDOG + ".d") / "264-cutover-transaction.conf",
               watchdog_fence_bytes=lambda: b"fence", watchdog_permit_path=lambda: tmp_path / "permit")
    api["run"] = lambda *args: "\n".join(k + "=" + v for k, v in loaded[args[2]].items())
    authority = s.SystemdAuthority(api)
    external_dir = tmp_path / "deploy/herdr/cutover"
    external_dir.mkdir(parents=True)
    (external_dir / "external-runtime-authority.json").write_text("{}")
    def capacity():
        authority.dropin.parent.mkdir(exist_ok=True)
        authority.dropin.write_text("[Service]\nExecStart=\nExecStart=" + s.CAPACITY_EXEC + "\n")
        loaded[s.WATCHDOG]["DropInPaths"] = str(authority.dropin)
        loaded[s.WATCHDOG]["ExecStart"] = "{ path=" + s.CAPACITY_EXEC + " ; argv[]=" + s.CAPACITY_EXEC + " ; ignore_errors=no ; }"
        descriptor = {"files": {str(authority.dropin): s.facts(authority.dropin)}, "trees": {}}
        directory = tmp_path / "deploy/herdr/cutover"
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "capacity-repair-authority.json").write_bytes(canonical_json(descriptor))
    return SimpleNamespace(authority=authority, loaded=loaded, capacity=capacity,
                           units=units, tmp=tmp_path, bad_owner=bad_owner, api=api)


def test_W01_standard_baseline(manager):
    assert manager.authority.capture()["mode"] == "standard"


def test_W02_approved_capacity_baseline(manager):
    manager.capacity()
    assert manager.authority.capture()["mode"] == "capacity_rc6"


@pytest.mark.parametrize("unit", c.UNITS, ids=lambda u: "W25_" + u)
def test_W03_W25_unknown_loaded_or_disk_override(manager, unit):
    directory = manager.units / (unit + ".d")
    directory.mkdir(exist_ok=True)
    (directory / "unknown.conf").write_text("[Service]\nEnvironment=EVIL=1\n")
    with pytest.raises(ReleaseError, match="unknown_disk_dropin"):
        manager.authority.capture()


def test_W04_changed_capacity_override(manager):
    manager.capacity()
    manager.authority.dropin.write_text("changed")
    with pytest.raises(ReleaseError, match="capacity_dependency_drift"):
        manager.authority.capture()


@pytest.mark.parametrize("failure", ["owner", "mode"], ids=["W05_owner", "W05_mode"])
def test_invalid_authority_metadata(manager, failure):
    path = manager.units / "agent-platform-export.service.d/sources.conf"
    if failure == "owner":
        manager.bad_owner.add(path)
    else:
        path.chmod(0o666)
    with pytest.raises(ReleaseError, match="source_dropin_drift"):
        manager.authority.capture()


def test_W06_source_symlink(manager):
    path = manager.units / "agent-platform-herdr.service.d/sources.conf"
    data = path.read_bytes()
    path.unlink()
    other = manager.tmp / "other"
    other.write_bytes(data)
    path.symlink_to(other)
    with pytest.raises(ReleaseError, match="source_dropin_drift"):
        manager.authority.capture()


@pytest.mark.parametrize("property,value", [
    ("Environment", "UNAPPROVED=1"), ("EnvironmentFiles", "/tmp/evil"),
    ("WorkingDirectory", "/tmp"), ("Transient", "yes"),
    ("NeedDaemonReload", "yes"), ("ExecStart", "{ path=/evil ; argv[]=/evil ; ignore_errors=no ; }"),
], ids=lambda x: "W07_" + x)
def test_W07_effective_config_change(manager, property, value):
    original = manager.authority.capture()
    manager.loaded[s.WATCHDOG][property] = value
    with pytest.raises(ReleaseError):
        manager.authority.verify(original)


def test_W20_orphan_permit_rejected(manager):
    (manager.tmp / "permit").write_text("stale")
    with pytest.raises(ReleaseError, match="orphan_watchdog_start_permit"):
        manager.authority.capture()


def test_inactive_backup_is_not_an_override(manager):
    (manager.units / "agent-platform-export.service.d/sources.conf.tmp").write_text("backup")
    assert manager.authority.capture()["mode"] == "standard"


def test_W25_pending_global_override(manager):
    folder = manager.units / "service.d"
    folder.mkdir()
    (folder / "injection.conf").write_text("[Service]\nEnvironment=EVIL=1")
    with pytest.raises(ReleaseError, match="unknown_disk_dropin"):
        manager.authority.capture()


def test_W06_inventory_detects_added_import_during_hash(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "safe.py").write_text("safe")
    monkeypatch.setattr(s, "safe_ancestors", lambda _: None)
    real = s.facts
    def race(path):
        value = real(path)
        if path.name == "safe.py":
            (root / "shadow.so").write_bytes(b"evil")
        return value
    monkeypatch.setattr(s, "facts", race)
    with pytest.raises(ReleaseError, match="runtime_inventory_changed"):
        s.inventory(root)


def test_W06_inventory_detects_rewrite_of_previously_hashed_file(tmp_path, monkeypatch):
    root = tmp_path / "tree"
    root.mkdir()
    (root / "first.py").write_text("approved")
    (root / "second.py").write_text("approved")
    monkeypatch.setattr(s, "safe_ancestors", lambda _: None)
    real = s.facts
    hashed = []
    def race(path):
        row = real(path)
        if path.is_file():
            if hashed:
                hashed[0].write_text("tampered")
            hashed.append(path)
        return row
    monkeypatch.setattr(s, "facts", race)
    with pytest.raises(ReleaseError, match="runtime_inventory_changed"):
        s.inventory(root)
