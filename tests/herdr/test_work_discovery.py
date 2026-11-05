"""Targeted physical inspection without executable project imports or writes."""
import hashlib
from pathlib import Path
import pytest
from herdr.work_configuration import inspect_discovery
from herdr.work_cycle import WorkContractError

def snapshot(path,name):
    return {name:{"sha256":hashlib.sha256((path/name).read_bytes()).hexdigest(),"mode":0o644}}

def test_discovery_observes_symbols_imports_and_entry_guard_without_executing_source(tmp_path):
    source=tmp_path/"entry.py"
    source.write_text("import forbidden_side_effect\nfrom package import service\n"
                      "def run():\n    return service()\n"
                      "if __name__ == '__main__':\n    raise RuntimeError('must not execute')\n")
    original=source.read_bytes()
    result=inspect_discovery(tmp_path,["entry.py"],snapshot(tmp_path,"entry.py"))
    assert result["symbols"]=={"entry.py":["run"]}
    assert any("entry guard" in fact for fact in result["facts"])
    assert any("forbidden_side_effect" in fact and "package" in fact for fact in result["facts"])
    assert any("UNKNOWN" in value for value in result["unknowns"])
    assert source.read_bytes()==original and sorted(p.name for p in tmp_path.iterdir())==["entry.py"]

def test_changed_targeted_input_cannot_reuse_previous_observation(tmp_path):
    source=tmp_path/"entry.py";source.write_text("def run():\n    return 1\n")
    original=snapshot(tmp_path,"entry.py")
    source.write_text("def run():\n    return 2\n")
    with pytest.raises(WorkContractError,match="changed"):
        inspect_discovery(tmp_path,["entry.py"],original)

def test_discovery_cannot_follow_a_project_symlink(tmp_path):
    outside=tmp_path/"outside";outside.mkdir()
    (outside/"entry.py").write_text("def foreign():\n    return 1\n")
    root=tmp_path/"tree";root.mkdir();(root/"alias").symlink_to(outside,target_is_directory=True)
    declared={"alias/entry.py":{"sha256":hashlib.sha256((outside/"entry.py").read_bytes()).hexdigest(),"mode":0o644}}
    with pytest.raises((OSError,WorkContractError)):
        inspect_discovery(root,["alias/entry.py"],declared)

def test_targeted_discovery_has_cumulative_and_individual_input_bounds(tmp_path):
    for number in range(5):(tmp_path/f"input-{number}.txt").write_bytes(b"x"*262144)
    paths=[f"input-{number}.txt" for number in range(5)]
    declared={name:snapshot(tmp_path,name)[name] for name in paths}
    with pytest.raises(WorkContractError,match="exceeds bound"):
        inspect_discovery(tmp_path,paths,declared)
    (tmp_path/"too-big.txt").write_bytes(b"x"*262145)
    with pytest.raises(WorkContractError,match="bounded inspection"):
        inspect_discovery(tmp_path,["too-big.txt"],snapshot(tmp_path,"too-big.txt"))
