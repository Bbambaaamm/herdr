"""Reserve existing signed grant lifetime; never extend or replace authority."""
from datetime import UTC, datetime, timedelta
from contextlib import contextmanager
from contextvars import ContextVar
import time
from .work_cycle import require
from .security import SecurityGrant

def check_wall_seconds(plan, hygiene=None):
    seconds=sum(check.timeout_seconds+13 for check in plan.checks)
    if hygiene is not None:seconds+=hygiene.timeout_seconds+13
    return seconds+120  # Finite host inventory/copy/publication/receipt allowance.

def require_grant_lifetime(grant, seconds):
    require(isinstance(grant,SecurityGrant) and type(seconds) is int and 0<=seconds<=3600,
            "bounded existing work grant required")
    require(grant.is_active() and grant.is_active(datetime.now(UTC)+timedelta(seconds=seconds+5)),
            "work grant lifetime is shorter than the complete bounded request")

_DEADLINE=ContextVar("herdr-work-deadline",default=None)

def remaining_work_seconds(default=30):
    deadline=_DEADLINE.get()
    if deadline is None:return default
    left=deadline-time.monotonic()
    require(left>0,"complete host work request deadline exhausted")
    return min(default,left)

def require_work_time(seconds=0):
    deadline=_DEADLINE.get()
    require(deadline is None or time.monotonic()+seconds<deadline,
            "complete host work request deadline exhausted")

@contextmanager
def bounded_host_request(seconds):
    require(type(seconds) is int and 0<seconds<=900,"complete host request exceeds bound")
    parent=_DEADLINE.get()
    deadline=time.monotonic()+seconds
    token=_DEADLINE.set(min(parent,deadline) if parent is not None else deadline)
    try:
        yield
        require_work_time()
    finally:_DEADLINE.reset(token)
