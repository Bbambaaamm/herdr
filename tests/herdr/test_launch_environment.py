import pytest
from herdr.launch_environment import sanitize_environment,require_clean_environment

def test_loader_controls_removed_before_native_process_creation(monkeypatch):
    import subprocess,sys
    monkeypatch.setenv("LD_PRELOAD","/worker/native.so")
    monkeypatch.setenv("LD_AUDIT","/worker/audit.so")
    monkeypatch.setenv("LD_LIBRARY_PATH","/worker")
    monkeypatch.setenv("LD_FUTURE_CONTROL","/worker/future.so")
    monkeypatch.setenv("GLIBC_TUNABLES","unsafe")
    original={"LD_PRELOAD":"/worker/native.so","LD_FUTURE_CONTROL":"unsafe",
              "GLIBC_TUNABLES":"unsafe","HERDR_POLICY_TASK_ID":"task"}
    selected=sanitize_environment(original)
    require_clean_environment(selected)
    result=subprocess.run([sys.executable,"-I","-S","-c",
        "import os;assert not any(v for k,v in os.environ.items() if k.startswith('LD_'));print(os.environ['HERDR_POLICY_TASK_ID'])"],
        env=selected,capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="task"
    assert sanitize_environment(original)=={"HERDR_POLICY_TASK_ID":"task"}
    with pytest.raises(ValueError): require_clean_environment(original)


def test_empty_loader_control_is_still_denied():
    import pytest
    with pytest.raises(ValueError,match="unsafe"):
        require_clean_environment({"LD_TRACE_LOADED_OBJECTS":""})
    assert sanitize_environment({"LD_TRACE_LOADED_OBJECTS":"","TASK":"safe"})=={"TASK":"safe"}

def test_live_spawn_source_has_no_loader_controls():
    import os
    from herdr.launch_environment import require_clean_spawn_source
    require_clean_spawn_source(os.getpid())


def test_unreadable_spawn_source_denies_before_creation():
    import pytest
    from herdr.launch_environment import require_clean_spawn_source
    with pytest.raises((ValueError,OSError)):
        require_clean_spawn_source(999999999)

def test_poisoned_spawn_parent_is_denied(monkeypatch):
    import pytest
    import herdr.launch_environment as module
    from pathlib import Path
    def status(pid,parent):
        values=["S",str(parent)]+["0"]*18
        values[19]="1234"
        return str(pid)+" (parent) "+" ".join(values)
    original=Path.read_text
    def read(self,*args,**kwargs):
        if str(self)=="/proc/120/stat":return status(120,121)
        if str(self)=="/proc/121/stat":return status(121,1)
        return original(self,*args,**kwargs)
    monkeypatch.setattr(Path,"read_text",read)
    monkeypatch.setattr(module,"process_environment",lambda pid:{"LD_TRACE_LOADED_OBJECTS":""})
    with pytest.raises(ValueError,match="unsafe"):
        module.require_clean_spawn_source(120)


def test_subprocess_runner_sanitizes_before_first_native_exec():
    import os,sys
    from herdr.runtime import SubprocessHerdrRunner
    inherited={**os.environ,"LD_TRACE_LOADED_OBJECTS":"","LD_PRELOAD":"/worker/native.so",
               "BASH_ENV":"/worker/startup","HERDR_SAFE_PROBE":"retained"}
    runner=SubprocessHerdrRunner(executable=sys.executable,env=inherited)
    result=runner.run(["-I","-S","-c",
        "import os;assert not any(k.startswith('LD_') for k in os.environ);assert 'BASH_ENV' not in os.environ;print(os.environ['HERDR_SAFE_PROBE'])"])
    assert result.returncode==0,result.stderr
    assert result.stdout.strip()=="retained"
