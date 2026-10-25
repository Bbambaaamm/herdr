"""Opt-in transport timing for the pinned Hermes interactive CLI.

Install only from an authenticated bootstrap consumer, before instance.run.
PrivateSDKPolicy is data from that consumer, not a new approval. This adapter
never sends input, invokes chat, or authorizes an effect. It defers one existing
Enter handler after an observed BracketedPaste. Unbracketed input retains the
SDK's rapid-input guard. Library callers are unaffected.
"""
from __future__ import annotations

import asyncio
import hashlib
import inspect
import json
import math
import os
import stat
import sys
import threading
import time
import unicodedata
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from .private_profile_namespace import PrivateSDKPolicy
from .security import InvocationGuard, PolicyDenied

SDK_TUI_SHA256 = "9cdbe471c0121ec08f76769108537f82d5a81094501ff4ba164302c7dff426a9"
_SDK_MODULE = "hermes_cli.cli_tui_mixin"
_METHODS = ("_tui_handle_paste", "_tui_handle_enter", "_tui_on_text_changed")
_OVERLAYS = (
    "_connection_state", "_sudo_state", "_secret_state", "_approval_state",
    "_slash_confirm_state", "_model_picker_state", "_command_palette_state",
    "_clarify_state",
)
_MISSING = object()
_FACTORY_LOCK = threading.Lock()
MAX_NATIVE_PROMPT_BYTES = 65536  # Complete UTF-8 envelope, not just its content.
_PASTE_START = "\x1b[200~"
_PASTE_END = "\x1b[201~"


def _need(ok, reason):
    if not ok:
        raise PolicyDenied(reason)



def encode_native_prompt(text):
    """Frame approved plain text for ONE native agent prompt, without sending it.

    Content cannot inject a terminator, terminal escape, or another input event.
    No stripping/newline normalization; only LF and TAB are allowed controls.
    Native API pass-through and real SDK submission require separate evidence.
    """
    _need(type(text) is str and 0 < len(text) <= MAX_NATIVE_PROMPT_BYTES - 12,
          "native_cli_prompt_invalid")
    _need(not any(unicodedata.category(char) == "Cc" and char not in "\n\t"
                  for char in text), "native_cli_prompt_control_denied")
    try:
        raw = text.encode("utf-8")
    except UnicodeError:
        raise PolicyDenied("native_cli_prompt_invalid") from None
    _need(len(raw) + 12 <= MAX_NATIVE_PROMPT_BYTES, "native_cli_prompt_too_large")
    return _PASTE_START + text + _PASTE_END



def _canonical_guard(guard):
    # WorkInvocationGuard is the canonical work entry, not arbitrary subclassing.
    if type(guard) is InvocationGuard:
        return True
    from .work_contract_host import WorkInvocationGuard
    return type(guard) is WorkInvocationGuard


def _false_shortcuts(config):
    return (type(config) is dict and type(config.get("display")) is dict
            and config["display"].get("cli_multiline_shortcuts") is False)


def _object(pairs):
    result = {}
    for key, value in pairs:
        _need(key not in result, "native_cli_profile_invalid")
        result[key] = value
    return result


def _sealed_config(policy):
    # Existing policy verifies the complete no-alias private-home path.
    path = policy.profile_home / "config.yaml"
    policy.verify_config_path(path)
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        before = os.fstat(fd)
        _need(stat.S_ISREG(before.st_mode) and 0 < before.st_size <= 131072,
              "native_cli_profile_invalid")
        raw = os.pread(fd, before.st_size + 1, 0)
        after = os.fstat(fd)
        fields = ("st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid",
                  "st_size", "st_mtime_ns", "st_ctime_ns")
        _need(all(getattr(before, name) == getattr(after, name) for name in fields)
              and len(raw) == before.st_size
              and hashlib.sha256(raw).hexdigest() == policy.config_sha256,
              "native_cli_profile_changed")
    finally:
        os.close(fd)
    try:
        config = json.loads(raw.decode("utf-8"), object_pairs_hook=_object,
                            parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError):
        raise PolicyDenied("native_cli_profile_invalid") from None
    _need(_false_shortcuts(config), "native_cli_shortcuts_not_explicitly_disabled")


def _surface(instance):
    _need(type(instance).__name__ == "HermesCLI" and type(instance).__module__ == "cli",
          "native_cli_instance_required")
    originals = {}
    for name in (*_METHODS, "_tui_build_key_bindings"):
        method = getattr(instance, name, None)
        _need(inspect.ismethod(method) and method.__self__ is instance,
              "native_cli_sdk_surface_changed")
        fn = method.__func__
        _need(fn.__module__ == _SDK_MODULE and fn.__name__ == name,
              "native_cli_sdk_surface_changed")
        path = inspect.getsourcefile(fn)
        _need(path is not None and Path(path).is_file()
              and hashlib.sha256(Path(path).read_bytes()).hexdigest() == SDK_TUI_SHA256,
              "native_cli_sdk_surface_changed")
        if name in _METHODS:
            originals[name] = method
    module = sys.modules.get(_SDK_MODULE)
    window = getattr(module, "_RAPID_INPUT_ENTER_WINDOW_S", None)
    _need(type(window) is float and window == 0.05, "native_cli_sdk_surface_changed")
    return originals, window


@dataclass(frozen=True)
class _Paste:
    app: object
    buffer: object
    text: str
    cursor: int
    generation: int
    changes: int
    thread: int


class NativeCLITransport:
    """Restorable per-instance handlers; uninstall also cancels a held Enter."""

    def __init__(self, instance, guard, policy, originals, window):
        self._instance = instance
        self._guard = guard
        self._grant = guard.grant
        self._policy = policy
        self._originals = originals
        self._window = window
        self._generation = 0
        self._changes = 0
        self._paste = None
        self._pending = None
        self._timer = None
        self._installed = True
        self._previous = {name: vars(instance).get(name, _MISSING) for name in _METHODS}
        self._wrappers = {
            "_tui_handle_paste": self._handle_paste,
            "_tui_handle_enter": self._handle_enter,
            "_tui_on_text_changed": self._text_changed,
        }

    def _gate(self, *, sealed=False):
        _need(self._guard.grant is self._grant and self._grant.is_active(),
              "native_cli_grant_inactive")
        _need(_false_shortcuts(getattr(self._instance, "config", None)),
              "native_cli_shortcuts_not_explicitly_disabled")
        if sealed:
            _sealed_config(self._policy)

    def _cancel(self):
        self._paste = None
        self._pending = None
        if self._timer is not None:
            self._timer.cancel()
            self._timer = None

    def _idle(self):
        return (getattr(self._instance, "_tui_multiline_shortcuts", None) is False
                and not getattr(self._instance, "_agent_running", False)
                and not getattr(self._instance, "_attached_images", ())
                and not any(getattr(self._instance, key, None) for key in _OVERLAYS))

    def _same(self, paste):
        app = paste.app
        return (self._installed and self._instance._app is app
                and all(vars(self._instance).get(name, _MISSING) is wrapper
                        for name, wrapper in self._wrappers.items())
                and app.current_buffer is paste.buffer
                and paste.buffer.text == paste.text
                and paste.buffer.cursor_position == paste.cursor
                and self._generation == paste.generation
                and self._changes == paste.changes
                and threading.get_ident() == paste.thread
                and app.is_running is True and app.is_done is False
                and self._idle())

    @staticmethod
    def _key(event, keys):
        from prompt_toolkit.key_binding.key_processor import KeyPressEvent
        return (type(event) is KeyPressEvent and len(event.key_sequence) == 1
                and event.key_sequence[0].key in keys
                and event.is_repeat is False and event.arg == 1)

    def _text_changed(self, buffer):
        if not self._installed:
            return self._originals["_tui_on_text_changed"](buffer)
        self._changes += 1
        self._cancel()
        return self._originals["_tui_on_text_changed"](buffer)

    def _handle_paste(self, event):
        if not self._installed:
            return self._originals["_tui_handle_paste"](event)
        from prompt_toolkit.keys import Keys
        self._generation += 1
        self._cancel()
        self._gate()
        before_changes = self._changes
        result = self._originals["_tui_handle_paste"](event)
        if (self._installed and self._key(event, {Keys.BracketedPaste})
                and type(event.data) is str and event.data
                and self._changes > before_changes and self._idle()
                and getattr(self._instance, "_app", None) is event.app):
            buffer = event.app.current_buffer
            self._paste = _Paste(event.app, buffer, buffer.text, buffer.cursor_position,
                                 self._generation, self._changes, threading.get_ident())
        return result

    def _handle_enter(self, event):
        if not self._installed:
            return self._originals["_tui_handle_enter"](event)
        from prompt_toolkit.keys import Keys
        self._gate()
        # Second Enter cancels the held one and takes the original SDK path.
        if self._pending is not None:
            self._cancel()
            return self._originals["_tui_handle_enter"](event)
        paste, self._paste = self._paste, None
        now = time.monotonic()
        changed = getattr(self._instance, "_tui_last_text_change", None)
        rapid = (type(changed) in (int, float) and math.isfinite(changed)
                 and 0 <= now - changed < self._window)
        if not (paste is not None and rapid and self._same(paste)
                and self._key(event, {Keys.ControlM, Keys.ControlJ})):
            return self._originals["_tui_handle_enter"](event)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            raise PolicyDenied("native_cli_ui_loop_required") from None
        _need(getattr(paste.app, "loop", None) is loop
              and loop.is_running() and not loop.is_closed(),
              "native_cli_ui_loop_required")
        token = object()
        self._pending = token

        def finish():
            if self._pending is not token:
                return
            self._pending = None
            self._timer = None
            # No retry/reschedule: changed identity/state cancels this gesture.
            if not self._same(paste):
                return
            try:
                self._gate(sealed=True)
                # Sealed-file IO may yield: recheck current identity/expiry afterward.
                self._gate(sealed=False)
            except (PolicyDenied, OSError, RuntimeError):
                return
            last = getattr(self._instance, "_tui_last_text_change", None)
            age = time.monotonic() - last if type(last) in (int, float) else -1
            if (not math.isfinite(age) or age < self._window or not self._same(paste)
                    or getattr(paste.app, "loop", None) is not loop
                    or not loop.is_running() or loop.is_closed()):
                return
            self._originals["_tui_handle_enter"](event)

        try:
            # Do not change the SDK's last-change clock or 50ms threshold.
            self._timer = loop.call_later(self._window, finish)
        except BaseException:
            self._cancel()
            raise

    def uninstall(self):
        if not self._installed:
            return
        self._installed = False
        self._cancel()
        for name, wrapper in self._wrappers.items():
            # Do not overwrite a later owner's replacement.
            if vars(self._instance).get(name, _MISSING) is not wrapper:
                continue
            previous = self._previous[name]
            if previous is _MISSING:
                delattr(self._instance, name)
            else:
                setattr(self._instance, name, previous)


def install_native_cli_transport(instance, guard=None, *, private_sdk_policy=None):
    """Explicit CLI-only opt-in, after verified bootstrap and before key binding.

    Both an active typed invocation guard and authenticated private-profile data
    are required. Sealed config AND this instance must explicitly set
    display.cli_multiline_shortcuts=false. This is not an effect authorization.
    Native senders not using actual BracketedPaste remain unsupported.
    """
    _need(_canonical_guard(guard), "native_cli_guard_required")
    _need(type(private_sdk_policy) is PrivateSDKPolicy, "native_cli_sealed_profile_required")
    _need(getattr(instance, "_app", None) is None, "native_cli_install_before_run_required")
    originals, window = _surface(instance)
    handle = NativeCLITransport(instance, guard, private_sdk_policy, originals, window)
    handle._gate(sealed=True)
    for name, wrapper in handle._wrappers.items():
        setattr(instance, name, wrapper)
    return handle


@contextmanager
def native_cli_transport_factory(cli_type, guard, *, private_sdk_policy):
    """Scope constructor wiring to one CLI entry; caller verifies cli_type origin.

    No implicit import or library installation. Nested/concurrent contexts and
    construction on a different thread deny. Legacy/no-policy callers must not
    enter this opt-in context. Every created instance is uninstalled on exit.
    """
    _need(isinstance(cli_type, type) and cli_type.__name__ == "HermesCLI"
          and cli_type.__module__ == "cli", "native_cli_instance_required")
    _need(_canonical_guard(guard) and guard.grant.is_active(),
          "native_cli_guard_required")
    _need(type(private_sdk_policy) is PrivateSDKPolicy,
          "native_cli_sealed_profile_required")
    _need(_FACTORY_LOCK.acquire(blocking=False), "native_cli_factory_already_active")
    handles = []
    factory_grant = guard.grant
    previous = vars(cli_type).get("__init__", _MISSING)
    original = cli_type.__init__
    owner_thread = threading.get_ident()
    active = False
    patched = False
    try:
        _sealed_config(private_sdk_policy)
        active = True
        constructing = False

        def initialize(instance, *args, **kwargs):
            nonlocal constructing
            _need(active and threading.get_ident() == owner_thread
                  and not constructing, "native_cli_factory_context_changed")
            constructing = True
            try:
                _need(guard.grant is factory_grant and factory_grant.is_active(),
                      "native_cli_grant_inactive")
                _sealed_config(private_sdk_policy)
                result = original(instance, *args, **kwargs)
                _need(result is None, "native_cli_constructor_invalid")
                _need(guard.grant is factory_grant and factory_grant.is_active(),
                      "native_cli_grant_inactive")
                handle = install_native_cli_transport(
                    instance, guard, private_sdk_policy=private_sdk_policy)
                handles.append(handle)
                return result
            finally:
                constructing = False

        cli_type.__init__ = initialize
        patched = True
        yield
    finally:
        primary = sys.exception()
        active = False
        cleanup_failed = False
        for handle in reversed(handles):
            try:
                handle.uninstall()
            except Exception:
                cleanup_failed = True
        if patched:
            cleanup_failed |= vars(cli_type).get("__init__") is not initialize
            if previous is _MISSING:
                delattr(cli_type, "__init__")
            else:
                cli_type.__init__ = previous
        _FACTORY_LOCK.release()
        if cleanup_failed:
            if primary is not None:
                primary.add_note("native_cli_transport_cleanup_failed")
            else:
                raise PolicyDenied("native_cli_transport_cleanup_failed")
