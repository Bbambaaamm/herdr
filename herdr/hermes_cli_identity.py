"""Host-owned CLI/session correlation; never an invocation approval.

The authenticated stage2 owns the factory scope. SDK task/session arguments stay
unchanged; only Herdr's authorization boundary receives the signed task identity.
"""
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
import functools
import inspect
import sys
import threading
import weakref

from .security import InvocationGuard, PolicyDenied

_FACTORY_LOCK = threading.Lock()
_MISSING = object()


def _need(ok, reason):
    if not ok:
        raise PolicyDenied(reason)


def _session(value):
    return (type(value) is str and 0 < len(value.encode("utf-8")) <= 512
            and all(ord(char) >= 32 and ord(char) != 127 for char in value))


@dataclass(eq=False, frozen=True)
class _Turn:
    binding: object
    cli: object
    agent: object
    session: str


class CLIInvocationBinding:
    """One trusted CLI entry, same signed grant; no model-selected aliases."""
    def __init__(self, guard):
        from .work_contract_host import WorkInvocationGuard
        _need(type(guard) in (InvocationGuard, WorkInvocationGuard),
              "cli_binding_guard_required")
        self.guard = guard
        self._grant = guard.grant
        self._identity = guard.grant.identity
        self._hash = guard.grant.hash
        self._lock = threading.RLock()
        self._tool = ContextVar("herdr_cli_bound_tool", default=None)
        self._current_turn = ContextVar("herdr_cli_bound_turn", default=None)
        self._owners = []
        self._turns = {}
        self._active = False
        self._closed = False
        self._agent_type = None
        self._check_grant()

    def _check_grant(self):
        _need(not self._closed and self.guard.grant is self._grant
              and self._grant.identity == self._identity
              and self._grant.hash == self._hash and self._grant.is_active(),
              "cli_binding_grant_changed")

    def _register(self, cli):
        self._check_grant()
        _need(self._active and _session(getattr(cli, "session_id", None)),
              "cli_binding_session_required")
        self._owners.append(weakref.ref(cli))

    def _validate(self, turn):
        self._check_grant()
        _need(self._active and turn.binding is self
              and self._turns.get(id(turn.agent)) is turn
              and type(turn.agent) is self._agent_type
              and getattr(turn.cli, "agent", None) is turn.agent
              and getattr(turn.cli, "session_id", None) == turn.session
              and getattr(turn.agent, "session_id", None) == turn.session,
              "cli_binding_turn_changed")

    @contextmanager
    def turn(self, agent, task_id):
        with self._lock:
            self._check_grant()
            owners = [ref() for ref in self._owners]
            owners = [cli for cli in owners if cli is not None and getattr(cli, "agent", None) is agent]
            _need(self._active and type(agent) is self._agent_type and len(owners) == 1,
                  "cli_binding_agent_unbound")
            cli = owners[0]
            session = getattr(cli, "session_id", None)
            _need(_session(session) and task_id == session
                  and getattr(agent, "session_id", None) == session,
                  "cli_binding_task_mismatch")
            _need(not self._turns and self._current_turn.get() is None,
                  "cli_binding_turn_overlap")
            turn = _Turn(self, cli, agent, session)
            self._turns[id(agent)] = turn
            token = self._current_turn.set(turn)
        try:
            yield
        finally:
            with self._lock:
                if self._turns.get(id(agent)) is turn:
                    del self._turns[id(agent)]
            self._current_turn.reset(token)

    def begin_tool(self, agent, task_id):
        # SDK tool workers need not inherit the turn thread's ContextVars.
        # The exact agent has a live host-bound turn in the shared locked table.
        with self._lock:
            turn = self._turns.get(id(agent))
            _need(turn is not None and turn.agent is agent
                  and self._current_turn.get() is turn,
                  "cli_binding_tool_outside_turn")
            self._validate(turn)
            _need(task_id == turn.session, "cli_binding_task_mismatch")
            previous = self._tool.get()
            _need(previous is None or previous is turn, "cli_binding_cross_turn")
            return self._tool.set(turn)

    def end_tool(self, token):
        self._tool.reset(token)

    def caller_task_id(self, task_id):
        with self._lock:
            turn = self._tool.get()
            _need(turn is not None, "cli_binding_tool_context_missing")
            self._validate(turn)
            _need(task_id is None or task_id == turn.session,
                  "cli_binding_task_mismatch")
            return self._identity.task_id

    def path_task_id(self, host_task_id):
        # Signed authority stays the Herdr task; SDK cwd is keyed by its raw
        # session ID. Resolve that namespace only inside this exact live tool.
        with self._lock:
            turn = self._tool.get()
            _need(turn is not None, "cli_binding_tool_context_missing")
            self._validate(turn)
            _need(host_task_id == self._identity.task_id, "cli_binding_task_mismatch")
            return turn.session

    def close(self):
        with self._lock:
            self._closed = True
            self._active = False
            self._turns.clear()
            self._owners.clear()

    @contextmanager
    def factory(self, cli_type, agent_type):
        """Caller independently verifies both classes' immutable module origins."""
        _need(isinstance(cli_type, type) and cli_type.__name__ == "HermesCLI"
              and cli_type.__module__ == "cli" and isinstance(agent_type, type)
              and agent_type.__name__ == "AIAgent" and agent_type.__module__ == "run_agent",
              "cli_binding_canonical_types_required")
        original_init = cli_type.__init__
        original_run = agent_type.run_conversation
        previous_init = vars(cli_type).get("__init__", _MISSING)
        previous_run = vars(agent_type).get("run_conversation", _MISSING)
        signature = inspect.signature(original_run)
        owner_thread = threading.get_ident()
        initialized = patched = False
        _need(_FACTORY_LOCK.acquire(blocking=False), "cli_binding_factory_overlap")
        try:
            self._check_grant()
            _need(not self._active, "cli_binding_factory_overlap")
            self._active = True
            self._agent_type = agent_type

            @functools.wraps(original_init)
            def initialize(cli, *args, **kwargs):
                nonlocal initialized
                _need(threading.get_ident() == owner_thread and not initialized
                      and type(cli) is cli_type and cli_type.__init__ is initialize,
                      "cli_binding_constructor_changed")
                initialized = True
                try:
                    self._check_grant()
                    result = original_init(cli, *args, **kwargs)
                    _need(result is None, "cli_binding_constructor_invalid")
                    self._register(cli)
                    return result
                finally:
                    initialized = False

            @functools.wraps(original_run)
            def conversation(agent, *args, **kwargs):
                _need(agent_type.run_conversation is conversation,
                      "cli_binding_conversation_changed")
                bound = signature.bind(agent, *args, **kwargs)
                with self.turn(agent, bound.arguments.get("task_id")):
                    return original_run(agent, *args, **kwargs)

            cli_type.__init__ = initialize
            agent_type.run_conversation = conversation
            patched = True
            yield
        finally:
            primary = sys.exception()
            self.close()
            changed = False
            if patched:
                for owner, name, wrapper, previous in (
                    (agent_type, "run_conversation", conversation, previous_run),
                    (cli_type, "__init__", initialize, previous_init),
                ):
                    if vars(owner).get(name) is not wrapper:
                        changed = True
                        continue
                    if previous is _MISSING:
                        delattr(owner, name)
                    else:
                        setattr(owner, name, previous)
            _FACTORY_LOCK.release()
            if changed and primary is None:
                raise PolicyDenied("cli_binding_factory_owner_changed")
