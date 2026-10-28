"""One-shot native prompt validation at the actual worker delivery boundary."""
import subprocess
import pytest
from herdr.security import PolicyDenied
from tests.agent_stack.test_worker_handshake import (
    worker, base_task, configure_paths, _modern_root_session,
)
from tests.herdr.test_work_cycle import setup, runner


def admitted(tmp_path, monkeypatch):
    configure_paths(tmp_path / "queue")
    task = base_task()
    session = _modern_root_session(task)
    cycle, root, plan, log = setup(tmp_path / "contract")
    cycle.start(runner)
    task.update(work_contract_version=1, work_contract={"plan_sha256": plan.hash})
    monkeypatch.setattr(worker, "HOST_WORK_CYCLES", {(task["id"], task["run_token"]): cycle})
    return task, session


def capture(monkeypatch):
    events = []
    monkeypatch.setattr(worker, "persist_execution_session",
        lambda task, **kw: events.append(("intent", task["execution_session"]["economic_delivery_attempted"])))
    def native(argv, **kw):
        events.append(("native", argv, kw))
        return subprocess.CompletedProcess(argv, 0, "ok", "")
    monkeypatch.setattr(worker.subprocess, "run", native)
    return events


@pytest.mark.parametrize("text", ["ordinary task", "line one\nline two\tČeský text", "x" * 60000], ids=["plain", "multiline-utf8", "large"])
def test_modern_prompt_uses_native_framing_and_intent_precedes_native(tmp_path, monkeypatch, text):
    task, session = admitted(tmp_path, monkeypatch)
    monkeypatch.setattr(worker, "prompt_text", lambda task: text)
    events = capture(monkeypatch)
    assert worker.run_prompt(task) == (0, "ok")
    assert events[0] == ("intent", True) and len(events) == 2
    _, argv, options = events[1]
    assert argv[:4] == [str(worker.HERDR), "agent", "prompt", session["agent_name"]]
    # The real native API contributes the paste frame (physically verified with
    # the installed binary). Parse that wire input with prompt_toolkit itself:
    # one paste with unchanged content, then one Enter, never nested escapes.
    from prompt_toolkit.input.vt100_parser import Vt100Parser
    from prompt_toolkit.keys import Keys
    keys = []
    parser = Vt100Parser(keys.append)
    parser.feed("\x1b[200~" + argv[4] + "\x1b[201~\r")
    parser.flush()
    assert len(keys) == 2
    assert keys[0].key == Keys.BracketedPaste and keys[0].data == text
    assert keys[1].key == Keys.ControlM
    assert argv[5:7] == ["--wait", "--timeout"] and options["text"] is True
    with pytest.raises(RuntimeError, match="already_started"):
        worker.run_prompt(task)
    assert len(events) == 2


@pytest.mark.parametrize("text", ["bad\x1b[201~command", "bad\0", "\r", "\x7f", "\u0085",
                                  "x" * 65525, "č" * 32763, "\ud800", ""], ids=["escape", "nul", "cr", "del", "c1", "ascii-limit", "utf8-limit", "surrogate", "empty"])
def test_invalid_framing_denies_before_intent_or_native(tmp_path, monkeypatch, text):
    task, session = admitted(tmp_path, monkeypatch)
    monkeypatch.setattr(worker, "prompt_text", lambda task: text)
    events = capture(monkeypatch)
    with pytest.raises(PolicyDenied):
        worker.run_prompt(task)
    assert session["economic_delivery_attempted"] is False and events == []


def test_native_timeout_retains_original_intent_without_resending(tmp_path, monkeypatch):
    task, session = admitted(tmp_path, monkeypatch)
    monkeypatch.setattr(worker, "prompt_text", lambda task: "approved one-shot work")
    events = capture(monkeypatch)
    def timeout(argv, **kw):
        events.append(("timeout", argv))
        raise subprocess.TimeoutExpired(argv, 1)
    monkeypatch.setattr(worker.subprocess, "run", timeout)
    with pytest.raises(subprocess.TimeoutExpired):
        worker.run_prompt(task)
    assert session["economic_delivery_attempted"] is True
    with pytest.raises(RuntimeError, match="already_started"):
        worker.run_prompt(task)
    assert len(events) == 2


def test_failed_intent_persistence_never_sends_prompt(tmp_path, monkeypatch):
    task, session = admitted(tmp_path, monkeypatch)
    monkeypatch.setattr(worker, "prompt_text", lambda task: "bounded work")
    monkeypatch.setattr(worker.subprocess, "run", lambda *a, **kw: pytest.fail("no send after failed fsync"))
    def failed_persistence(*a, **kw):
        raise OSError("fixture disk failure")
    monkeypatch.setattr(worker, "persist_execution_session", failed_persistence)
    with pytest.raises(OSError, match="fixture disk failure"):
        worker.run_prompt(task)
    assert session["economic_delivery_attempted"] is True


def test_legacy_prompt_text_and_delivery_are_preserved(tmp_path, monkeypatch):
    configure_paths(tmp_path)
    task = base_task()
    session = _modern_root_session(task)
    monkeypatch.setattr(worker, "prompt_text", lambda task: "legacy plain text")
    events = capture(monkeypatch)
    assert worker.run_prompt(task) == (0, "ok")
    assert events[1][1][4] == "legacy plain text"
