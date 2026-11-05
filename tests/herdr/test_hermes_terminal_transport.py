"""Synthetic UI-loop faults plus one pinned SDK handler-only component.

No CLI startup, native binary, provider, HTTP, work authority, or allocation.
Portable fault cases use explicit handler doubles. If the audited SDK source is
installed, the final case executes only its three AST-selected buffer handlers.
"""
from __future__ import annotations

import ast
import hashlib
import json
import queue
import sys
import types
from dataclasses import replace
from pathlib import Path

import pytest
from prompt_toolkit.key_binding.key_processor import KeyPress, KeyPressEvent
from prompt_toolkit.keys import Keys

from herdr import hermes_terminal_transport as transport
from herdr import private_profile_namespace as private
from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
from herdr.security import (
    InvocationGuard, InvocationIdentity, NetworkAccess, PolicyDenied, ProcessPolicy,
    RuntimeAssurance, SecurityGrant,
)

SDK_SOURCE = Path("/opt/herdr/releases/p0-5035d92-test/hermes/hermes_cli/cli_tui_mixin.py")
SDK_SHA = "9cdbe471c0121ec08f76769108537f82d5a81094501ff4ba164302c7dff426a9"

# Transparent handler doubles for portable faults, NOT full Hermes acceptance.
_HANDLER_DOUBLE = """
def _tui_handle_paste(self, event):
    if event.data:
        event.current_buffer.insert_text(event.data)
def _tui_on_text_changed(self, buf):
    self._tui_last_text_change = time.monotonic()
def _tui_handle_enter(self, event):
    if self._tui_enter_overlay(event):
        return
    buf = event.app.current_buffer
    if time.monotonic() - self._tui_last_text_change < _RAPID_INPUT_ENTER_WINDOW_S:
        buf.insert_text("\\n")
        return
    text = buf.text.strip()
    if text:
        self._pending_input.put(text)
        buf.reset(append_to_history=True)
def _tui_build_key_bindings(self):
    return self._tui_handle_paste, self._tui_handle_enter
"""


class Clock:
    def __init__(self):
        self.now = 100.0

    def monotonic(self):
        return self.now

    def perf_counter(self):
        return self.now


class Timer:
    def __init__(self, callback):
        self.callback, self.cancelled = callback, False

    def cancel(self):
        self.cancelled = True


class Loop:
    def __init__(self, clock):
        self.clock, self.timers = clock, []
        self.running, self.closed = True, False

    def is_running(self):
        return self.running

    def is_closed(self):
        return self.closed

    def call_later(self, delay, callback):
        assert delay == 0.05
        timer = Timer(callback)
        self.timers.append(timer)
        return timer

    def flush(self, *, advance=0.051):
        self.clock.now += advance
        timers, self.timers = self.timers, []
        for timer in timers:
            if not timer.cancelled:
                timer.callback()


class Buffer:
    def __init__(self, owner):
        self.owner, self._text, self.cursor_position = owner, "", 0

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        self.cursor_position = min(self.cursor_position, len(value))
        self.owner._tui_on_text_changed(self)

    def insert_text(self, value):
        cursor = self.cursor_position
        self.text = self.text[:cursor] + value + self.text[cursor:]
        self.cursor_position = cursor + len(value)

    def reset(self, **kwargs):
        self.text = ""
        self.cursor_position = 0


def event(app, key, data=""):
    # Real event type, with a synthetic app; do not run prompt_toolkit Application.
    result = KeyPressEvent.__new__(KeyPressEvent)
    result._app, result._arg = app, None
    result.key_sequence = [KeyPress(key, data)]
    result.previous_key_sequence = []
    result.is_repeat = False
    return result


def guard_at(root):
    scope = CapabilityScope(
        providers=(), capabilities=("reasoning",), executors=("hermes-runtime",),
        tools=(), permissions=(), regions=("eu-central",),
        data_classes=(DataClass.PUBLIC,), input_modalities=("text",),
        output_modalities=("text",), max_cost_microusd=0, max_context_tokens=8192,
        max_egress=Egress.REGION_BOUND, max_retention=Retention.LIMITED,
        training=Training.EXCLUDED,
    )
    assurance = RuntimeAssurance(True, "a" * 64, NetworkAccess.NONE, (), True)
    identity = InvocationIdentity("github:example/repo", "agent", "parent", "parent-task",
                                  "task", "run", 1)
    grant = SecurityGrant(
        "synthetic", str(root), identity, scope, (), ProcessPolicy(False, (), NetworkAccess.NONE),
        assurance, (), (), (), (), "2026-01-01T00:00:00+00:00", "2030-01-01T00:00:00+00:00",
    )
    return InvocationGuard(grant)


def make_ui(monkeypatch, tmp_path, *, actual=False):
    clock, source_path = Clock(), Path(__file__)
    module = types.ModuleType(transport._SDK_MODULE)
    module.time, module._RAPID_INPUT_ENTER_WINDOW_S = clock, 0.05
    if actual:
        assert SDK_SOURCE.is_file()
        assert hashlib.sha256(SDK_SOURCE.read_bytes()).hexdigest() == SDK_SHA
        tree = ast.parse(SDK_SOURCE.read_bytes())
        cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "CLITuiMixin")
        names = {*transport._METHODS, "_tui_build_key_bindings"}
        functions = [n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name in names]
        assert len(functions) == 4
        code = compile(ast.Module(functions, type_ignores=[]), str(SDK_SOURCE), "exec")
    else:
        code = compile(_HANDLER_DOUBLE, str(source_path), "exec")
        monkeypatch.setattr(transport, "SDK_TUI_SHA256", hashlib.sha256(source_path.read_bytes()).hexdigest())
    exec(code, vars(module))
    monkeypatch.setitem(sys.modules, transport._SDK_MODULE, module)
    methods = {name: getattr(module, name) for name in (*transport._METHODS, "_tui_build_key_bindings")}
    methods["chat"] = lambda self, text: (_ for _ in ()).throw(AssertionError("chat must not be called"))
    methods["__module__"] = "cli"
    cli = type("HermesCLI", (), methods)()
    cli.config = {"display": {"cli_multiline_shortcuts": False}}
    cli._app = None
    cli._agent_running = False
    cli._attached_images = []
    cli._pending_input = queue.Queue()
    cli._tui_last_text_change = 0.0
    cli._tui_prev_text_len = cli._tui_prev_newline_count = 0
    cli._tui_paste_just_collapsed = cli._skip_paste_collapse = False
    cli._tui_multiline_shortcuts = False
    for key in transport._OVERLAYS:
        setattr(cli, key, None)
    cli._tui_enter_overlay = lambda ev: False
    cli._tui_enter_inline_command = lambda *args: False
    cli._inline_pastes = lambda *args: None
    cli._tui_paste_over_threshold = lambda *args: False
    if actual:
        fake_cli = types.ModuleType("cli")
        fake_cli._should_auto_attach_clipboard_image_on_paste = lambda text: False
        fake_cli._strip_leaked_bracketed_paste_wrappers = lambda text: text
        fake_cli._strip_leaked_terminal_responses_with_meta = lambda text: (text, False)
        fake_cli._apply_backslash_line_continuation = lambda text: text
        fake_cli._is_backslash_line_continuation = lambda text: False
        fake_cli._looks_like_slash_command = lambda text: text.startswith("/")
        fake_cli.logger = types.SimpleNamespace(warning=lambda *a: None)
        monkeypatch.setitem(sys.modules, "cli", fake_cli)
        sanitization = types.ModuleType("agent.message_sanitization")
        sanitization._sanitize_surrogates = lambda text: text
        monkeypatch.setitem(sys.modules, "agent.message_sanitization", sanitization)
    monkeypatch.setattr(private, "_HOME", tmp_path)
    config_path = tmp_path / ".hermes/profiles/native/config.yaml"
    config_path.parent.mkdir(parents=True)
    raw = json.dumps(cli.config).encode()
    config_path.write_bytes(raw)
    policy = private.PrivateSDKPolicy("native", "b" * 64, hashlib.sha256(raw).hexdigest())
    guard = guard_at(tmp_path)
    monkeypatch.setattr(transport, "time", clock)
    loop = Loop(clock)
    monkeypatch.setattr(transport.asyncio, "get_running_loop", lambda: loop)
    return types.SimpleNamespace(cli=cli, guard=guard, policy=policy, clock=clock,
                                 loop=loop, config_path=config_path, actual=actual)


def install(ui):
    handle = transport.install_native_cli_transport(
        ui.cli, ui.guard, private_sdk_policy=ui.policy)
    ui.buffer = Buffer(ui.cli)
    ui.app = types.SimpleNamespace(current_buffer=ui.buffer, is_running=True, is_done=False,
                                   loop=ui.loop, invalidate=lambda: None)
    ui.cli._app = ui.app
    ui.calls = []
    original = handle._originals["_tui_handle_enter"]

    def counted(ev):
        ui.calls.append(ev)
        return original(ev)

    handle._originals["_tui_handle_enter"] = counted
    ui.handle = handle
    return ui


@pytest.fixture
def ui(monkeypatch, tmp_path):
    return install(make_ui(monkeypatch, tmp_path))


def paste(ui, text="native prompt"):
    ui.cli._tui_handle_paste(event(ui.app, Keys.BracketedPaste, text))


def enter(ui):
    ui.cli._tui_handle_enter(event(ui.app, Keys.ControlJ, "\n"))


def test_bracketed_rapid_enter_is_one_original_evaluation_after_window(ui):
    chat = ui.cli.chat.__func__
    paste(ui)
    enter(ui)
    assert ui.calls == [] and ui.cli._pending_input.empty()
    assert ui.buffer.text == "native prompt"
    assert len(ui.loop.timers) == 1
    ui.loop.flush()
    assert len(ui.calls) == 1
    assert ui.cli._pending_input.get_nowait() == "native prompt"
    ui.loop.flush()
    assert ui.cli._pending_input.empty() and len(ui.calls) == 1
    assert ui.cli.chat.__func__ is chat


def test_unbracketed_rapid_input_keeps_original_newline_guard(ui):
    ui.buffer.insert_text("unbracketed")
    enter(ui)
    assert ui.buffer.text == "unbracketed\n"
    assert ui.cli._pending_input.empty() and len(ui.calls) == 1
    assert ui.loop.timers == []


def test_nonrapid_bracketed_enter_runs_original_immediately(ui):
    paste(ui)
    ui.clock.now += 0.1
    enter(ui)
    assert ui.cli._pending_input.get_nowait() == "native prompt"
    assert len(ui.calls) == 1 and ui.loop.timers == []


def test_direct_paste_call_without_bracketed_event_never_arms(ui):
    ui.cli._tui_handle_paste(event(ui.app, Keys.Any, "not bracketed"))
    enter(ui)
    assert ui.buffer.text.endswith("\n")
    assert ui.cli._pending_input.empty() and len(ui.calls) == 1
    assert ui.loop.timers == []


def test_duplicate_enter_cancels_pending_and_never_replays_it(ui):
    paste(ui)
    enter(ui)
    timer = ui.loop.timers[0]
    enter(ui)
    assert timer.cancelled and len(ui.calls) == 1
    assert ui.buffer.text.endswith("\n")
    ui.loop.flush()
    timer.callback()  # Stale delivery also cannot call original.
    assert len(ui.calls) == 1 and ui.cli._pending_input.empty()


@pytest.mark.parametrize("change", [
    "text", "edit_restore", "cursor", "buffer", "app", "stopped", "done",
    "overlay", "busy", "images", "generation", "profile", "grant",
])
def test_changed_snapshot_cancels_without_submit(ui, change):
    paste(ui)
    enter(ui)
    if change == "text":
        ui.buffer.insert_text("x")
    elif change == "edit_restore":
        original = ui.buffer.text
        ui.buffer.text = original + "x"
        ui.buffer.text = original
    elif change == "cursor":
        ui.buffer.cursor_position = 0
    elif change == "buffer":
        ui.app.current_buffer = Buffer(ui.cli)
    elif change == "app":
        ui.cli._app = types.SimpleNamespace()
    elif change == "stopped":
        ui.app.is_running = False
    elif change == "done":
        ui.app.is_done = True
    elif change == "overlay":
        ui.cli._secret_state = {"active": True}
    elif change == "busy":
        ui.cli._agent_running = True
    elif change == "images":
        ui.cli._attached_images.append(object())
    elif change == "generation":
        ui.handle._generation += 1
    elif change == "profile":
        ui.config_path.write_bytes(b'{"display":{"cli_multiline_shortcuts":true}}')
    elif change == "grant":
        ui.guard.grant = replace(ui.guard.grant, expires_at="2026-01-02T00:00:00+00:00")
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()


def test_second_paste_cancels_old_timer_and_requires_a_new_enter(ui):
    paste(ui, "one")
    enter(ui)
    paste(ui, "two")
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()
    enter(ui)
    assert ui.cli._pending_input.get_nowait() == "onetwo"
    assert len(ui.calls) == 1


def test_uninstall_before_timer_restores_methods_and_cancels(ui):
    originals = {name: ui.handle._originals[name] for name in transport._METHODS}
    paste(ui)
    enter(ui)
    ui.handle.uninstall()
    ui.handle.uninstall()
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()
    assert all(name not in vars(ui.cli) for name in transport._METHODS)
    assert ui.cli._tui_handle_paste.__func__ is originals["_tui_handle_paste"].__func__


def test_uninstall_does_not_overwrite_a_later_owner(ui):
    later = lambda ev: None
    ui.cli._tui_handle_enter = later
    ui.handle.uninstall()
    assert ui.cli._tui_handle_enter is later


@pytest.mark.parametrize("case", ["guard", "untyped_guard", "policy", "untyped_policy",
                                  "omitted", "true", "zero", "sealed_true", "started"])
def test_explicit_typed_guard_and_sealed_false_profile_required(monkeypatch, tmp_path, case):
    ui = make_ui(monkeypatch, tmp_path)
    guard, policy = ui.guard, ui.policy
    if case == "guard":
        guard = None
    elif case == "untyped_guard":
        guard = types.SimpleNamespace(grant=ui.guard.grant)
    elif case == "policy":
        policy = None
    elif case == "untyped_policy":
        policy = dict(profile_name="native")
    elif case == "omitted":
        ui.cli.config = {}
    elif case == "true":
        ui.cli.config["display"]["cli_multiline_shortcuts"] = True
    elif case == "zero":
        ui.cli.config["display"]["cli_multiline_shortcuts"] = 0
    elif case == "sealed_true":
        raw = b'{"display":{"cli_multiline_shortcuts":true}}'
        ui.config_path.write_bytes(raw)
        policy = replace(policy, config_sha256=hashlib.sha256(raw).hexdigest())
    elif case == "started":
        ui.cli._app = object()
    with pytest.raises(PolicyDenied):
        transport.install_native_cli_transport(ui.cli, guard, private_sdk_policy=policy)
    assert all(name not in vars(ui.cli) for name in transport._METHODS)


def test_sdk_source_or_window_mismatch_denies_before_install(monkeypatch, tmp_path):
    ui = make_ui(monkeypatch, tmp_path)
    monkeypatch.setattr(transport, "SDK_TUI_SHA256", "0" * 64)
    with pytest.raises(PolicyDenied, match="surface_changed"):
        transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)
    assert all(name not in vars(ui.cli) for name in transport._METHODS)


@pytest.mark.parametrize("case", ["other_loop", "closed", "not_running", "no_loop", "schedule_error"])
def test_ui_loop_failure_never_evaluates_original(ui, monkeypatch, case):
    paste(ui)
    if case == "other_loop":
        ui.app.loop = object()
    elif case == "closed":
        ui.loop.closed = True
    elif case == "not_running":
        ui.loop.running = False
    elif case == "no_loop":
        def fail():
            raise RuntimeError("no loop")
        monkeypatch.setattr(transport.asyncio, "get_running_loop", fail)
    else:
        def fail(*args):
            raise RuntimeError("schedule failed")
        monkeypatch.setattr(ui.loop, "call_later", fail)
    with pytest.raises((PolicyDenied, RuntimeError)):
        enter(ui)
    assert ui.calls == [] and ui.cli._pending_input.empty()
    assert ui.handle._pending is None


def test_early_timer_is_cancelled_without_rescheduling(ui):
    paste(ui)
    enter(ui)
    ui.loop.flush(advance=0.01)
    assert ui.calls == [] and ui.loop.timers == []
    ui.loop.flush(advance=1)
    assert ui.calls == [] and ui.cli._pending_input.empty()


def test_live_config_drift_cancels_timer(ui):
    paste(ui)
    enter(ui)
    ui.cli.config["display"]["cli_multiline_shortcuts"] = True
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()


def test_source_window_is_never_changed(ui):
    paste(ui)
    last = ui.cli._tui_last_text_change
    enter(ui)
    assert ui.cli._tui_last_text_change == last
    assert sys.modules[transport._SDK_MODULE]._RAPID_INPUT_ENTER_WINDOW_S == 0.05


def test_actual_pinned_sdk_buffer_handlers_only(monkeypatch, tmp_path):
    if not SDK_SOURCE.is_file():
        pytest.skip("audited external SDK source not installed; portable faults still run")
    ui = install(make_ui(monkeypatch, tmp_path, actual=True))
    paste(ui, "actual pinned handler")
    enter(ui)
    assert ui.buffer.text == "actual pinned handler" and ui.cli._pending_input.empty()
    ui.loop.flush()
    assert ui.cli._pending_input.get_nowait() == "actual pinned handler"
    assert len(ui.calls) == 1


def test_captured_bindings_pass_through_after_uninstall(ui):
    bound_paste, bound_enter = ui.cli._tui_build_key_bindings()
    ui.handle.uninstall()
    # Old key-binding references must not retain adapter policy or replay state.
    ui.cli.config = {}
    bound_paste(event(ui.app, Keys.BracketedPaste, "original"))
    bound_enter(event(ui.app, Keys.ControlJ, "\n"))
    assert ui.buffer.text == "original\n"
    assert len(ui.calls) == 1 and ui.cli._pending_input.empty()
    assert ui.loop.timers == []


def test_window_mismatch_denies_before_install(monkeypatch, tmp_path):
    ui = make_ui(monkeypatch, tmp_path)
    monkeypatch.setattr(sys.modules[transport._SDK_MODULE], "_RAPID_INPUT_ENTER_WINDOW_S", 0.025)
    with pytest.raises(PolicyDenied, match="surface_changed"):
        transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)


def test_expired_grant_denies_before_install(monkeypatch, tmp_path):
    ui = make_ui(monkeypatch, tmp_path)
    ui.guard.grant = replace(ui.guard.grant, expires_at="2026-01-02T00:00:00+00:00")
    with pytest.raises(PolicyDenied, match="grant_inactive"):
        transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)
    assert all(name not in vars(ui.cli) for name in transport._METHODS)


def test_uninstall_and_reinstall_before_run(monkeypatch, tmp_path):
    ui = make_ui(monkeypatch, tmp_path)
    chat = ui.cli.chat.__func__
    handle = transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)
    with pytest.raises(PolicyDenied, match="surface_changed"):
        transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)
    handle.uninstall()
    replacement = transport.install_native_cli_transport(ui.cli, ui.guard, private_sdk_policy=ui.policy)
    replacement.uninstall()
    assert ui.cli.chat.__func__ is chat


def test_actual_pinned_rapid_enter_baseline_keeps_newline(monkeypatch, tmp_path):
    if not SDK_SOURCE.is_file():
        pytest.skip("audited external SDK source not installed")
    ui = make_ui(monkeypatch, tmp_path, actual=True)
    ui.buffer = Buffer(ui.cli)
    ui.app = types.SimpleNamespace(current_buffer=ui.buffer, is_running=True, is_done=False,
                                   loop=ui.loop, invalidate=lambda: None)
    ui.cli._app = ui.app
    ui.cli._tui_handle_paste(event(ui.app, Keys.BracketedPaste, "native baseline"))
    ui.cli._tui_handle_enter(event(ui.app, Keys.ControlJ, "\n"))
    assert ui.buffer.text == "native baseline\n"
    assert ui.cli._pending_input.empty() and ui.loop.timers == []


def test_actual_pinned_collapse_remains_original_and_only_snapshot_is_deferred(monkeypatch, tmp_path):
    if not SDK_SOURCE.is_file():
        pytest.skip("audited external SDK source not installed")
    ui = install(make_ui(monkeypatch, tmp_path, actual=True))
    ui.cli._tui_paste_over_threshold = lambda *args: True
    collapsed = []

    def collapse(text, lines, *, fallback):
        collapsed.append((text, lines, fallback))
        ui.cli._tui_paste_just_collapsed = True
        return "[Pasted text #1: fixture]"

    ui.cli._tui_collapse_paste = collapse
    paste(ui, "many\nlines")
    enter(ui)
    assert collapsed == [("many\nlines", 1, False)]
    assert ui.buffer.text == "[Pasted text #1: fixture]"
    ui.loop.flush()
    assert ui.cli._pending_input.get_nowait() == "[Pasted text #1: fixture]"
    assert len(ui.calls) == 1


def test_independent_instances_do_not_share_pending_state(monkeypatch, tmp_path):
    first = install(make_ui(monkeypatch, tmp_path / "first"))
    second = install(make_ui(monkeypatch, tmp_path / "second"))
    # Last fixture selects the common synthetic clock/loop seam; use it for both
    # apps while keeping each handle's app/buffer/generation separate.
    first.handle._originals["_tui_handle_paste"].__func__.__globals__["time"] = second.clock
    first.app.loop = second.loop
    first.cli._tui_last_text_change = second.clock.now
    first.loop = second.loop
    paste(first, "one")
    # Its SDK handler has a distinct fixture clock, still at the same value.
    enter(first)
    paste(second, "two")
    second.buffer.insert_text("edited")
    second.loop.flush()
    assert first.cli._pending_input.get_nowait() == "one"
    assert second.cli._pending_input.empty()
    assert len(first.calls) == 1 and second.calls == []


@pytest.mark.parametrize("change", ["uninstall", "buffer", "app", "loop", "shortcuts"])
def test_snapshot_rechecked_after_sealed_profile_io(ui, monkeypatch, change):
    paste(ui)
    enter(ui)
    original_gate = ui.handle._gate

    def gate(*, sealed=False):
        original_gate(sealed=sealed)
        if not sealed:
            return
        if change == "uninstall":
            ui.handle.uninstall()
        elif change == "buffer":
            ui.buffer.insert_text("changed during profile read")
        elif change == "app":
            ui.cli._app = object()
        elif change == "loop":
            ui.app.loop = object()
        else:
            ui.cli._tui_multiline_shortcuts = True

    monkeypatch.setattr(ui.handle, "_gate", gate)
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()


@pytest.mark.parametrize("text", [
    "plain prompt", "  keep whitespace  ", "line one\nline two\tdata\n",
    "\n\t", "unicode: žluťoučký 😀", "literal [200~ and [201~ without ESC",
])
def test_encoder_exact_roundtrip_without_normalization(text):
    assert transport.validate_native_prompt(text) == text
    encoded = transport.encode_native_prompt(text)
    assert encoded == "\x1b[200~" + text + "\x1b[201~"
    assert encoded[6:-6] == text
    assert encoded.count("\x1b") == 2
    assert len(encoded.encode("utf-8")) <= transport.MAX_NATIVE_PROMPT_BYTES


@pytest.mark.parametrize("text", [None, b"text", 1, True, {}, [], ""])
def test_encoder_requires_nonempty_string(text):
    with pytest.raises(PolicyDenied, match="prompt_invalid"):
        transport.encode_native_prompt(text)


def test_encoder_rejects_every_cc_control_except_lf_tab():
    import unicodedata
    for number in range(256):
        char = chr(number)
        if unicodedata.category(char) != "Cc" or char in "\n\t":
            continue
        with pytest.raises(PolicyDenied, match="control_denied"):
            transport.encode_native_prompt("prefix" + char + "suffix")


@pytest.mark.parametrize("text", [
    "\x1b[201~\nmalicious", "\x1b[200~nested", "nul\x00tail",
    "delete\x7f", "csi\x9b201~", "carriage\rreturn",
    "\ud800", "before\udfffafter",
])
def test_encoder_denies_escape_injection_and_non_utf8(text):
    with pytest.raises(PolicyDenied):
        transport.encode_native_prompt(text)


def test_encoder_bounds_complete_utf8_bytes_not_characters():
    limit = transport.MAX_NATIVE_PROMPT_BYTES
    assert len(transport.encode_native_prompt("a" * (limit - 12)).encode()) == limit
    assert len(transport.encode_native_prompt("😀" * ((limit - 12) // 4)).encode()) == limit
    for text in ("a" * (limit - 11), "😀" * ((limit - 12) // 4 + 1)):
        with pytest.raises(PolicyDenied):
            transport.encode_native_prompt(text)


def constructor_fixture(monkeypatch, tmp_path, *, inherited=False, actual=False):
    ui = make_ui(monkeypatch, tmp_path, actual=actual)
    cli_type = type(ui.cli)
    prototype = dict(vars(ui.cli))
    ui.constructed = []

    def original(instance):
        ui.constructed.append(instance)
        vars(instance).update(prototype)

    if inherited:
        base = type("Base", (), {"__init__": original})
        methods = {k: v for k, v in vars(cli_type).items()
                   if k not in {"__dict__", "__weakref__", "__init__"}}
        cli_type = type("HermesCLI", (base,), methods)
    else:
        cli_type.__init__ = original
    return ui, cli_type, original


def attach_created(ui, instance):
    ui.cli = instance
    ui.handle = instance._tui_handle_enter.__self__
    ui.buffer = Buffer(instance)
    ui.app = types.SimpleNamespace(current_buffer=ui.buffer, is_running=True, is_done=False,
                                   loop=ui.loop, invalidate=lambda: None)
    instance._app = ui.app
    ui.calls = []
    original = ui.handle._originals["_tui_handle_enter"]

    def counted(ev):
        ui.calls.append(ev)
        return original(ev)

    ui.handle._originals["_tui_handle_enter"] = counted


@pytest.mark.parametrize("inherited", [False, True])
def test_factory_scopes_original_init_chat_and_all_pending_callbacks(monkeypatch, tmp_path, inherited):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path, inherited=inherited)
    chat = cli_type.chat
    own_init = vars(cli_type).get("__init__", transport._MISSING)
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        assert cli_type.__init__ is not original
        instance = cli_type()
        assert ui.constructed == [instance] and cli_type.chat is chat
        attach_created(ui, instance)
        paste(ui, "factory prompt")
        enter(ui)
        assert ui.calls == [] and len(ui.loop.timers) == 1
    assert vars(cli_type).get("__init__", transport._MISSING) is own_init
    assert cli_type.__init__ is original and cli_type.chat is chat
    assert all(name not in vars(instance) for name in transport._METHODS)
    ui.loop.flush()
    assert ui.calls == [] and instance._pending_input.empty()


def test_factory_constructor_to_original_enter_runs_once_inside_scope(monkeypatch, tmp_path):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        attach_created(ui, cli_type())
        paste(ui, "inside context")
        enter(ui)
        ui.loop.flush()
        assert ui.cli._pending_input.get_nowait() == "inside context"
        assert len(ui.calls) == 1
    assert cli_type.__init__ is original


def test_factory_nested_context_denies_without_clobbering_outer(monkeypatch, tmp_path):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        outer = cli_type.__init__
        with pytest.raises(PolicyDenied, match="already_active"):
            with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
                raise AssertionError("nested body must not run")
        assert cli_type.__init__ is outer
        assert isinstance(cli_type()._tui_handle_enter.__self__, transport.NativeCLITransport)
    assert cli_type.__init__ is original


def test_factory_double_install_denied_and_outer_restores(monkeypatch, tmp_path):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        instance = cli_type()
        with pytest.raises(PolicyDenied, match="surface_changed"):
            transport.install_native_cli_transport(instance, ui.guard, private_sdk_policy=ui.policy)
    assert cli_type.__init__ is original
    assert all(name not in vars(instance) for name in transport._METHODS)


def test_factory_original_constructor_failure_is_not_masked(monkeypatch, tmp_path):
    ui, cli_type, _ = constructor_fixture(monkeypatch, tmp_path)
    failure = ValueError("synthetic constructor failure")

    def original(instance):
        raise failure

    cli_type.__init__ = original
    with pytest.raises(ValueError) as caught:
        with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
            cli_type()
    assert caught.value is failure and cli_type.__init__ is original
    # The lock was released after a failure.
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        pass


def test_factory_foreign_thread_constructor_denies_before_original(monkeypatch, tmp_path):
    import threading
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    failures = []

    def construct():
        try:
            cli_type()
        except Exception as error:
            failures.append(error)

    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        thread = threading.Thread(target=construct)
        thread.start()
        thread.join(timeout=2)
        assert not thread.is_alive()
    assert len(failures) == 1 and isinstance(failures[0], PolicyDenied)
    assert ui.constructed == [] and cli_type.__init__ is original


def test_factory_expiry_before_construction_does_not_run_original(monkeypatch, tmp_path):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        ui.guard.grant = replace(ui.guard.grant, expires_at="2026-01-02T00:00:00+00:00")
        with pytest.raises(PolicyDenied, match="grant_inactive"):
            cli_type()
    assert ui.constructed == [] and cli_type.__init__ is original


@pytest.mark.parametrize("case", ["guard", "policy", "profile"])
def test_factory_entry_failure_never_changes_constructor(monkeypatch, tmp_path, case):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    guard, policy = ui.guard, ui.policy
    if case == "guard":
        guard = None
    elif case == "policy":
        policy = None
    else:
        raw = b'{"display":{"cli_multiline_shortcuts":true}}'
        ui.config_path.write_bytes(raw)
        policy = replace(policy, config_sha256=hashlib.sha256(raw).hexdigest())
    with pytest.raises(PolicyDenied):
        with transport.native_cli_transport_factory(cli_type, guard, private_sdk_policy=policy):
            raise AssertionError("invalid factory body")
    assert cli_type.__init__ is original and ui.constructed == []


def test_factory_cleans_every_instance_even_when_one_uninstall_fails(monkeypatch, tmp_path):
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    primary = ValueError("primary")
    with pytest.raises(ValueError) as caught:
        with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
            one, two = cli_type(), cli_type()
            one_handle = one._tui_handle_enter.__self__
            def fail():
                raise RuntimeError("synthetic cleanup")
            monkeypatch.setattr(two._tui_handle_enter.__self__, "uninstall", fail)
            raise primary
    assert caught.value is primary
    assert "native_cli_transport_cleanup_failed" in primary.__notes__
    assert one_handle._installed is False and cli_type.__init__ is original


def test_real_work_invocation_guard_per_instance_keeps_authority_unchanged(monkeypatch, tmp_path):
    from herdr.work_contract_host import WorkInvocationGuard
    ui = make_ui(monkeypatch, tmp_path)
    effects = []

    def authority(*args, **kwargs):
        effects.append((args, kwargs))

    ui.guard = WorkInvocationGuard(ui.guard.grant, work_authority=authority)
    authorize = ui.guard.authorize_tool_call.__func__
    install(ui)
    paste(ui, "work guard")
    enter(ui)
    ui.loop.flush()
    assert ui.cli._pending_input.get_nowait() == "work guard"
    assert len(ui.calls) == 1 and effects == []
    assert type(ui.handle._guard) is WorkInvocationGuard
    assert ui.guard.work_authority is authority
    assert ui.guard.authorize_tool_call.__func__ is authorize
    ui.handle.uninstall()


def test_real_work_guard_factory_runs_actual_pinned_original_enter(monkeypatch, tmp_path):
    from herdr.work_contract_host import WorkInvocationGuard
    if not SDK_SOURCE.is_file():
        pytest.skip("audited external SDK source not installed")
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path, actual=True)
    effects = []

    def authority(*args, **kwargs):
        effects.append((args, kwargs))

    ui.guard = WorkInvocationGuard(ui.guard.grant, work_authority=authority)
    chat = cli_type.chat
    with transport.native_cli_transport_factory(cli_type, ui.guard, private_sdk_policy=ui.policy):
        attach_created(ui, cli_type())
        paste(ui, "real work guard and original Enter")
        enter(ui)
        assert ui.cli._pending_input.empty() and ui.calls == []
        ui.loop.flush()
        assert ui.cli._pending_input.get_nowait() == "real work guard and original Enter"
        assert len(ui.calls) == 1
        assert ui.handle._originals["_tui_handle_paste"].__func__.__code__.co_filename == str(SDK_SOURCE)
        assert ui.guard.work_authority is authority
        assert cli_type.chat is chat and effects == []
    assert cli_type.__init__ is original and cli_type.chat is chat
    assert ui.handle._installed is False


@pytest.mark.parametrize("base", ["invocation", "work"])
@pytest.mark.parametrize("entry", ["install", "factory"])
def test_arbitrary_guard_subclasses_remain_denied(monkeypatch, tmp_path, base, entry):
    from herdr.work_contract_host import WorkInvocationGuard
    ui, cli_type, original = constructor_fixture(monkeypatch, tmp_path)
    if base == "invocation":
        class Derived(InvocationGuard):
            pass
        guard = Derived(ui.guard.grant)
    else:
        class Derived(WorkInvocationGuard):
            pass
        guard = Derived(ui.guard.grant, work_authority=lambda *a, **k: None)
    with pytest.raises(PolicyDenied, match="guard_required"):
        if entry == "install":
            transport.install_native_cli_transport(ui.cli, guard, private_sdk_policy=ui.policy)
        else:
            with transport.native_cli_transport_factory(cli_type, guard, private_sdk_policy=ui.policy):
                raise AssertionError("subclass must not enter")
    assert cli_type.__init__ is original
    assert all(name not in vars(ui.cli) for name in transport._METHODS)


@pytest.mark.parametrize("name", list(transport._METHODS))
def test_later_owner_wrapper_cancels_held_enter(ui, name):
    paste(ui)
    enter(ui)
    later = []
    setattr(ui.cli, name, lambda *args: later.append(args))
    ui.loop.flush()
    assert ui.calls == [] and ui.cli._pending_input.empty()
    assert later == []


def test_grant_changed_during_sealed_io_cancels_held_enter(ui, monkeypatch):
    paste(ui)
    enter(ui)
    original_gate = ui.handle._gate
    original_grant = ui.guard.grant

    def gate(*, sealed=False):
        original_gate(sealed=sealed)
        if sealed:
            ui.guard.grant = replace(original_grant, grant_id="different-active-grant")

    monkeypatch.setattr(ui.handle, "_gate", gate)
    ui.loop.flush()
    assert ui.guard.grant is not original_grant
    assert ui.calls == [] and ui.cli._pending_input.empty()


def test_same_original_grant_expiry_during_sealed_io_cancels(ui, monkeypatch):
    paste(ui)
    enter(ui)
    original_grant = ui.guard.grant
    alive = {"value": True}
    monkeypatch.setattr(SecurityGrant, "is_active", lambda self: alive["value"])
    original_gate = ui.handle._gate

    def gate(*, sealed=False):
        original_gate(sealed=sealed)
        if sealed:
            alive["value"] = False  # Clock crosses expiry without replacing the object.

    monkeypatch.setattr(ui.handle, "_gate", gate)
    ui.loop.flush()
    assert ui.guard.grant is original_grant and original_grant.is_active() is False
    assert ui.calls == [] and ui.cli._pending_input.empty()


@pytest.mark.parametrize("text", [
    "", "bad\x1b[201~command", "bad\0", "\r", "\x7f", "\u0085",
    "x" * 65525, "č" * 32763, "\ud800",
])
def test_native_api_validator_denies_unsafe_or_oversized_input(text):
    with pytest.raises(PolicyDenied):
        transport.validate_native_prompt(text)
