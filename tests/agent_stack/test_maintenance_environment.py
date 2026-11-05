import importlib.machinery
import importlib.util
import os
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack/bin/hermes-maintenance"


def load_module(monkeypatch, tmp_path):
    loader = importlib.machinery.SourceFileLoader("maintenance_environment_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    with monkeypatch.context() as isolated:
        isolated.setattr(Path, "mkdir", lambda *args, **kwargs: None)
        isolated.setattr(os, "chmod", lambda *args, **kwargs: None)
        isolated.setattr(os, "umask", lambda *args, **kwargs: None)
        loader.exec_module(module)
    module.STATE = tmp_path
    module.BIN = tmp_path / "bin"
    module.log = lambda _: None
    return module


def test_queue_maintenance_launches_all_jobs_without_loader_controls(monkeypatch, tmp_path):
    from herdr.launch_environment import require_clean_environment
    module = load_module(monkeypatch, tmp_path)
    module.ENV.update(LD_PRELOAD="/unapproved/lib.so", LD_FUTURE_CONTROL="", BASH_ENV="/unapproved/startup")
    original = dict(module.ENV)
    calls = []
    def native(args, **kwargs):
        require_clean_environment(kwargs["env"])
        calls.append((args, dict(kwargs["env"])))
        return module.subprocess.CompletedProcess(args, 0, stdout="", stderr="")
    monkeypatch.setattr(module.subprocess, "run", native)
    module.agent_task_maintenance()
    assert [Path(args[0]).name for args, _ in calls] == [
        "agent-github-intake", "agent-task-dispatcher", "agent-task-export", "agent-swarm-export"]
    assert all(env["HOME"] == original["HOME"] and env["PATH"] == original["PATH"] for _, env in calls)
    assert module.ENV == original
    assert (tmp_path / "task-maintenance-heartbeat").exists()


def test_other_maintenance_keeps_its_browser_environment(monkeypatch, tmp_path):
    module = load_module(monkeypatch, tmp_path)
    seen = []
    def browser(args, **kwargs):
        seen.append(dict(kwargs["env"]))
        return module.subprocess.CompletedProcess(args, 0, stdout="ok", stderr="")
    monkeypatch.setattr(module.subprocess, "run", browser)
    assert module.run(["browser"]) == (0, "ok")
    assert seen == [module.ENV]
    assert "LD_LIBRARY_PATH" in seen[0]
