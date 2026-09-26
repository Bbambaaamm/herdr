"""Closed metadata DTOs and explicit fixture scope projection; no I/O."""
from dataclasses import asdict, dataclass


class Invalid(ValueError):
    """Fixed reason code; never includes input data."""


def need(condition, reason='invalid_metadata'):
    if not condition:
        raise Invalid(reason)


def digest(value, sizes=(64,)):
    return type(value) is str and len(value) in sizes and all(ch in '0123456789abcdef' for ch in value)


def integer(value):
    return type(value) is int and 0 <= value < 2**53


def choice(value, options):
    return type(value) is str and value in options


class Record:
    __slots__ = ()

    def __post_init__(self):
        validate(self)


@dataclass(frozen=True, slots=True)
class Scope(Record):
    installation_id: str
    board_id: str
    source_epoch: str
    profile_id: str
    board_name: str


@dataclass(frozen=True, slots=True)
class Grant(Record):
    principal_id: str
    scopes: tuple[Scope, ...]
    expires_at: int


@dataclass(frozen=True, slots=True)
class AgentRow(Record):
    scope: Scope
    record_id: str
    status: str


@dataclass(frozen=True, slots=True)
class TaskRow(Record):
    scope: Scope
    record_id: str
    run_id: str | None
    status: str


@dataclass(frozen=True, slots=True)
class RouterRow(Record):
    scope: Scope
    record_id: str
    provider: str
    model: str
    input_tokens: int | None
    output_tokens: int | None
    cost_microusd: int | None
    reason: str


@dataclass(frozen=True, slots=True)
class RepoRow(Record):
    scope: Scope
    record_id: str
    commit: str
    dirty: bool


@dataclass(frozen=True, slots=True)
class ReportRow(Record):
    scope: Scope
    record_id: str
    status: str
    passed: int | None
    failed: int | None
    artifact_digest: str


@dataclass(frozen=True, slots=True)
class Snapshot(Record):
    version: int
    observed_at: int
    source_version: str
    rows: tuple


KINDS = {AgentRow: 'agent', TaskRow: 'task', RouterRow: 'router', RepoRow: 'repo', ReportRow: 'report'}


def validate(value):
    kind = type(value)
    if kind is Scope:
        need(all(digest(v) for v in (value.installation_id, value.board_id, value.source_epoch, value.profile_id)))
        need(choice(value.board_name, ('agent-platform', 'majak', 'quantlab')))
    elif kind is Grant:
        need(digest(value.principal_id) and integer(value.expires_at))
        need(type(value.scopes) is tuple and 1 <= len(value.scopes) <= 8)
        for scope in value.scopes:
            need(type(scope) is Scope)
            validate(scope)
        need(len(set(value.scopes)) == len(value.scopes))
    elif kind is Snapshot:
        need(type(value.version) is int and value.version == 1 and integer(value.observed_at) and digest(value.source_version))
        need(type(value.rows) is tuple and len(value.rows) <= 200)
        for row in value.rows:
            need(type(row) in KINDS)
            validate(row)
        keys = [(type(row), row.scope, row.record_id) for row in value.rows]
        need(len(set(keys)) == len(keys), 'duplicate_record')
    elif kind in KINDS:
        need(type(value.scope) is Scope and digest(value.record_id))
        validate(value.scope)
        if kind is AgentRow:
            need(choice(value.status, ('idle', 'working', 'blocked', 'done', 'unknown')))
        elif kind is TaskRow:
            need(value.run_id is None or digest(value.run_id))
            need(choice(value.status, ('ready', 'running', 'blocked', 'done', 'unknown')))
        elif kind is RouterRow:
            need(choice(value.provider, ('unknown', 'nous', 'openrouter', 'openai')))
            need(choice(value.model, ('unknown', 'fixture-free', 'gpt-6-astra')))
            need(choice(value.reason, ('baseline', 'transport_retry', 'manual_override', 'unknown')))
            need(all(v is None or integer(v) for v in (value.input_tokens, value.output_tokens, value.cost_microusd)))
        elif kind is RepoRow:
            need(digest(value.commit, (40, 64)) and type(value.dirty) is bool)
        elif kind is ReportRow:
            need(choice(value.status, ('passed', 'failed', 'pending', 'unknown')))
            need(all(v is None or integer(v) for v in (value.passed, value.failed)))
            need(digest(value.artifact_digest))
    else:
        raise Invalid('invalid_type')


def project(snapshot, grant, *, now):
    need(type(snapshot) is Snapshot and type(grant) is Grant and integer(now))
    validate(snapshot)
    validate(grant)
    need(now < grant.expires_at, 'scope_expired')
    availability = 'unknown' if now < snapshot.observed_at else 'stale' if now - snapshot.observed_at > 30 else 'available'
    rows = [dict(kind=KINDS[type(row)], **asdict(row)) for row in snapshot.rows if row.scope in grant.scopes]
    return {'version': 1, 'observed_at': snapshot.observed_at, 'source_version': snapshot.source_version,
            'availability': availability, 'stale': availability != 'available', 'fixture': True,
            'rows': rows}
