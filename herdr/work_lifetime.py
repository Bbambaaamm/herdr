"""Reserve existing signed grant lifetime; never extend or replace authority."""
from datetime import UTC, datetime, timedelta
from .work_cycle import require
from .security import SecurityGrant

def check_wall_seconds(plan, hygiene=None):
    seconds=sum(check.timeout_seconds+13 for check in plan.checks)
    if hygiene is not None:seconds+=hygiene.timeout_seconds+13
    return seconds

def require_grant_lifetime(grant, seconds):
    require(isinstance(grant,SecurityGrant) and type(seconds) is int and 0<=seconds<=3600,
            "bounded existing work grant required")
    require(grant.is_active() and grant.is_active(datetime.now(UTC)+timedelta(seconds=seconds+5)),
            "work grant lifetime is shorter than the complete bounded request")
