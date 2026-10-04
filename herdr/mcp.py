"""Policy-governed MCP 2026-07-28 adapters.

The host supplies authenticated task context, immutable toolset, approved
bindings, registry observations and an active-task authority callback.
Remote metadata/results never grant tools or terminalize Herdr tasks.
"""
from __future__ import annotations

import base64
import hashlib
import http.client
import json
import math
import os
import re
import sqlite3
import subprocess
import sys
import time
import threading
from functools import wraps
from collections.abc import Callable
from contextlib import closing, contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlsplit

from .capability import (
    CapabilityDescriptor, CapabilityRegistry, CapabilityRequirement, CapabilityScope,
    DataPolicy, ExecutorDescriptor, Feature, Latency, Modality, ProviderDescriptor,
    RegistrySnapshot, RuntimeStateSnapshot,
)

PROTOCOL = "2026-07-28"
VERSION = "1.0.0"
META = "io.modelcontextprotocol/"
TASKS = META + "tasks"
LIMIT = 2_000_000
_NAME = re.compile(r"^[A-Za-z0-9_.-]{1,128}$")
_HASH = re.compile(r"^[0-9a-f]{64}$")


class GatewayError(RuntimeError):
    code = "invalid_request"


class PolicyDenied(GatewayError):
    code = "policy_denied"


class GatewayUnavailable(GatewayError):
    code = "provider_unavailable"


class DeliveryUncertain(GatewayError):
    code = "delivery_uncertain"


class RetryExhausted(DeliveryUncertain):
    code = "read_retry_exhausted"


class ReconciliationRequired(DeliveryUncertain):
    code = "remote_task_reconciliation_required"


class RemoteProtocolError(GatewayError):
    code = "upstream_protocol_error"


def encoded(value) -> bytes:
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
                          allow_nan=False).encode()
        if len(data) > LIMIT:
            raise GatewayError("bounded payload exceeded")
        return data
    except (ValueError, TypeError, RecursionError) as exc:
        raise GatewayError("invalid JSON payload") from exc


def hashed(value) -> str:
    return hashlib.sha256(encoded(value)).hexdigest()


def decode(raw: bytes):
    if len(raw) > LIMIT:
        raise GatewayError("bounded payload exceeded")
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise GatewayError("duplicate JSON object key")
            result[key] = value
        return result
    def finite_float(value):
        number = float(value)
        if not math.isfinite(number):
            raise GatewayError("nonfinite JSON")
        return number
    try:
        return json.loads(raw, object_pairs_hook=unique, parse_float=finite_float,
                          parse_constant=lambda _: (_ for _ in ()).throw(GatewayError("nonfinite JSON")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise GatewayError("invalid JSON encoding") from exc


def identifier(value, *, maximum=128):
    if not isinstance(value, str) or not value or len(value) > maximum or any(ord(c) < 32 for c in value):
        raise GatewayError("invalid bounded identity")
    return value


def header_value(value) -> str:
    if type(value) in {int, float}:
        if (type(value) is float and (not math.isfinite(value) or not value.is_integer())
                or not -(2**53 - 1) <= value <= 2**53 - 1):
            raise GatewayError("routing header integer exceeds safe range")
        value = int(value)
    value = str(value).lower() if type(value) is bool else str(value)
    if len(value) > 8192:
        raise GatewayError("routing header exceeds bounded length")
    if (value != value.strip() or any(ord(c) < 32 or ord(c) > 126 for c in value)
            or (value.startswith("=?base64?") and value.endswith("?="))):
        value = "=?base64?" + base64.b64encode(value.encode()).decode() + "?="
    if len(value) > 8192:
        raise GatewayError("encoded routing header exceeds bounded length")
    return value


def schema_headers(schema: dict) -> tuple:
    """Validate static primitive header annotations; never execute schema code."""
    result, names = [], set()
    def walk(value, path=(), reachable=True, depth=0):
        if depth > 16:
            raise GatewayError("schema nesting exceeded")
        if isinstance(value, dict):
            if "x-mcp-header" in value:
                name = value["x-mcp-header"]
                if (not reachable or not path or value.get("type") not in {"string", "integer", "boolean"}
                        or not isinstance(name, str) or not re.fullmatch(r"[!#$%&'*+.^_A-Za-z0-9|-]{1,64}", name)
                        or name.lower() in names):
                    raise GatewayError("invalid schema routing header")
                names.add(name.lower())
                result.append((path, name))
            for key, child in value.items():
                if key == "properties" and isinstance(child, dict):
                    for name, item in child.items():
                        walk(item, path + (name,), reachable, depth + 1)
                elif key in {"$defs", "definitions", "patternProperties", "dependentSchemas"} and isinstance(child, dict):
                    for item in child.values():
                        walk(item, path, False, depth + 1)
                elif key in {"additionalProperties", "unevaluatedProperties", "propertyNames",
                             "contentSchema", "items", "contains", "unevaluatedItems",
                             "not", "if", "then", "else"}:
                    walk(child, path, False, depth + 1)
                elif key in {"allOf", "anyOf", "oneOf", "prefixItems"} and isinstance(child, list):
                    for item in child:
                        walk(item, path, False, depth + 1)
    walk(schema)
    return tuple(result)


def validate_schema(schema: dict, instance=None, *, check_only=False):
    """Run full JSON Schema validation in a bounded disposable process.

    External references are always denied. The subprocess deadline bounds
    pathological regex, recursive refs and composition complexity.
    """
    payload = encoded({"schema": schema, "instance": instance, "check_only": check_only})
    try:
        # Use the trusted sibling helper and isolated imports; a worker's cwd,
        # PYTHONPATH and preload/credential environment must not choose its code.
        environment = {"PATH": os.defpath, "LANG": "C.UTF-8"}
        if os.name == "nt" and os.environ.get("SYSTEMROOT"):
            environment["SYSTEMROOT"] = os.environ["SYSTEMROOT"]
        result = subprocess.run([sys.executable, "-I", str(Path(__file__).with_name("mcp_schema.py"))],
                                input=payload, capture_output=True, timeout=3, env=environment)
    except (OSError, subprocess.SubprocessError) as exc:
        raise GatewayUnavailable("schema validator unavailable or bounded timeout") from exc
    if result.returncode == 1:
        raise GatewayError("schema or instance rejected")
    if result.returncode != 0 or result.stdout != b"valid":
        raise GatewayUnavailable("JSON Schema runtime dependency or bounded process unavailable")


@dataclass(frozen=True)
class TaskIdentity:
    consumer: str
    task_id: str
    attempt: int
    fencing_token: int
    idempotency_key: str

    def __post_init__(self):
        for value in (self.consumer, self.task_id, self.idempotency_key):
            identifier(value)
        if any(type(x) is not int or x < 1 for x in (self.attempt, self.fencing_token)):
            raise GatewayError("attempt/fence must be positive integers")

    @property
    def hash(self):
        return hashed(asdict(self))


@dataclass(frozen=True)
class ToolBinding:
    name: str
    logical_id: str
    tool_class: str
    permissions: tuple[str, ...]
    read_only: bool
    definition_hash: str

    def __post_init__(self):
        if not _NAME.fullmatch(self.name) or not _NAME.fullmatch(self.logical_id):
            raise GatewayError("invalid tool binding name")
        if self.tool_class not in {"CORE", "CONDITIONAL", "PRIVILEGED"}:
            raise GatewayError("unknown logical tool class")
        if type(self.read_only) is not bool or not self.permissions or not _HASH.fullmatch(self.definition_hash):
            raise GatewayError("tool effect, permissions and pinned definition are required")
        for permission in self.permissions:
            identifier(permission)


@dataclass(frozen=True)
class ServerBinding:
    id: str
    consumer: str
    version: str
    data_policy: DataPolicy
    tools: tuple[ToolBinding, ...]
    resources: tuple[tuple[str, str], ...] = ()
    tasks: bool = False
    subscriptions: bool = False

    def __post_init__(self):
        if not isinstance(self.id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", self.id) or not _NAME.fullmatch(self.consumer):
            raise GatewayError("invalid provider identity")
        identifier(self.version)
        if (not isinstance(self.data_policy, DataPolicy) or type(self.tasks) is not bool
                or type(self.subscriptions) is not bool):
            raise GatewayError("typed provider policy required")
        if len({x.name for x in self.tools}) != len(self.tools) or len({x.logical_id for x in self.tools}) != len(self.tools):
            raise GatewayError("duplicate tool binding")
        if (len({uri for uri, _ in self.resources}) != len(self.resources)
                or len({logical for _, logical in self.resources}) != len(self.resources)
                or {logical for _, logical in self.resources} & {x.logical_id for x in self.tools}):
            raise GatewayError("duplicate resource binding")
        for uri, logical in self.resources:
            identifier(uri, maximum=1024)
            if not _NAME.fullmatch(logical):
                raise GatewayError("invalid resource capability")


@dataclass(frozen=True)
class NodeToolset:
    version: str
    reason: str
    registry_hash: str
    tools: tuple[str, ...]
    scope: CapabilityScope
    argument_policy_hash: str
    max_calls: int = 16
    readonly_retries: int = 1
    timeout_seconds: int = 15

    def __post_init__(self):
        identifier(self.version)
        identifier(self.reason, maximum=1024)
        if not _HASH.fullmatch(self.registry_hash) or not _HASH.fullmatch(self.argument_policy_hash) or not isinstance(self.scope, CapabilityScope):
            raise GatewayError("pinned registry and typed scope required")
        if len(self.tools) != len(set(self.tools)) or not set(self.tools) <= set(self.scope.tools):
            raise PolicyDenied("node toolset exceeds its closed scope")
        if (type(self.max_calls) is not int or not 1 <= self.max_calls <= 256
                or type(self.readonly_retries) is not int or not 0 <= self.readonly_retries <= 2
                or type(self.timeout_seconds) is not int or not 1 <= self.timeout_seconds <= 30):
            raise GatewayError("invalid bounded execution policy")

    @property
    def hash(self):
        return hashed({"version": self.version, "reason": self.reason,
                       "registry_hash": self.registry_hash, "tools": list(self.tools),
                       "scope": self.scope.to_json(), "argument_policy_hash": self.argument_policy_hash, "max_calls": self.max_calls,
                       "readonly_retries": self.readonly_retries, "timeout_seconds": self.timeout_seconds})


@dataclass(frozen=True)
class CallContext:
    identity: TaskIdentity
    toolset: NodeToolset
    parent_scope: CapabilityScope
    consumer_scope: CapabilityScope

    def __post_init__(self):
        self.toolset.scope.require_subset_of(self.parent_scope)
        self.toolset.scope.require_subset_of(self.consumer_scope)

    @property
    def hash(self):
        return hashed({"identity": asdict(self.identity), "toolset": self.toolset.hash,
                       "parent_scope": self.parent_scope.hash, "consumer_scope": self.consumer_scope.hash})


@dataclass(frozen=True)
class Outcome:
    state: str
    result_hash: str | None = None
    result: dict | None = None
    remote_task_id: str | None = None
    replay: bool = False
    # Observed transport completion is never scheduler/review/merge authority.
    authority: str = "remote_observation"
    task_metadata: dict | None = None


def locked(method):
    @wraps(method)
    def invoke(self, *args, **kwargs):
        with self._mutex:
            return method(self, *args, **kwargs)
    return invoke


class CallLedger:
    """Host-owned SQLite ledger: FULL synchronous commits before transmission.

    It contains identity, request/result digests, bounded codes, operational task
    handles and the approved validation schemas frozen before delivery. Raw args, credentials and response text are not
    audit data. It must be outside every worker-writable sandbox mount.
    """
    def __init__(self, root: Path, *, writable_roots: tuple[Path, ...] = ()):
        if root.is_symlink():
            raise PolicyDenied("ledger root is a symlink")
        self.root = root.resolve()
        if any(self.root == x.resolve() or self.root.is_relative_to(x.resolve()) for x in writable_roots):
            raise PolicyDenied("ledger overlaps writable worker mounts")
        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.path = self.root / "mcp.sqlite3"
        if self.path.is_symlink():
            raise PolicyDenied("ledger database is a symlink")
        self._mutex = threading.RLock()
        self.db = sqlite3.connect(self.path, timeout=5, isolation_level=None, check_same_thread=False)
        os.chmod(self.path, 0o600)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS calls(
          key TEXT PRIMARY KEY, context_hash TEXT NOT NULL, request_hash TEXT NOT NULL,
          consumer TEXT NOT NULL, task_id TEXT NOT NULL, server TEXT NOT NULL,
          state TEXT NOT NULL, deliveries INTEGER NOT NULL DEFAULT 0,
          result_hash TEXT, remote_task_id TEXT, next_poll REAL, polls INTEGER NOT NULL DEFAULT 0,
          method TEXT NOT NULL, subject TEXT NOT NULL, reserved_cost INTEGER NOT NULL DEFAULT 0,
          unknown_cost INTEGER NOT NULL DEFAULT 0, validation_plan_json TEXT, remote_task_json TEXT);
        CREATE TABLE IF NOT EXISTS contexts(
          hash TEXT PRIMARY KEY, identity_json TEXT NOT NULL, toolset_hash TEXT NOT NULL,
          parent_scope_hash TEXT NOT NULL, consumer_scope_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS budgets(
          consumer TEXT, task_id TEXT, ceiling INTEGER NOT NULL, cost_ceiling INTEGER,
          PRIMARY KEY(consumer,task_id));
        CREATE TABLE IF NOT EXISTS audit(
          seq INTEGER PRIMARY KEY, key TEXT, code TEXT NOT NULL, at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS health(
          server TEXT PRIMARY KEY, failures INTEGER NOT NULL, open_until REAL NOT NULL);
        """)
        columns = {row[1] for row in self.db.execute("PRAGMA table_info(calls)")}
        for name in ("validation_plan_json", "remote_task_json"):
            if name not in columns:
                self.db.execute(f"ALTER TABLE calls ADD COLUMN {name} TEXT")
        self.db.row_factory = sqlite3.Row

    @locked
    def close(self):
        self.db.close()

    @locked
    def bind(self, context):
        self.db.execute("INSERT OR IGNORE INTO contexts VALUES(?,?,?,?,?)",
                        (context.hash, encoded(asdict(context.identity)).decode(), context.toolset.hash,
                         context.parent_scope.hash, context.consumer_scope.hash))

    @locked
    def polling(self, key, now):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("UPDATE calls SET polls=polls+1 WHERE key=?", (key,))
            self.audit(key, "remote_poll_reserved", now)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    @contextmanager
    def lock(self, key):
        import fcntl
        fd = os.open(self.root / (key + ".lock"), os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
        try:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise GatewayUnavailable("call already active") from exc
            yield
        finally:
            os.close(fd)

    @locked
    def get(self, key):
        row = self.db.execute("SELECT * FROM calls WHERE key=?", (key,)).fetchone()
        return dict(row) if row else None

    @locked
    def audit(self, key, code, now):
        if not re.fullmatch(r"[a-z_]{1,64}", code):
            raise GatewayError("invalid audit reason")
        self.db.execute("INSERT INTO audit(key,code,at) VALUES(?,?,?)", (key, code, now))

    @locked
    def reserve(self, key, context, request_hash, server, now, method, subject, validation_plan=None, *, retryable=False):
        row = self.get(key)
        if row:
            if row["context_hash"] != context.hash or row["request_hash"] != request_hash:
                self.audit(key, "idempotency_conflict", now)
                raise PolicyDenied("operation key reused for different scope/request")
            eligible = (row["state"] == "prepared" and row["deliveries"] == 0
                        or retryable and row["state"] == "delivery_uncertain")
            if not row["validation_plan_json"] and validation_plan is not None and eligible:
                self.db.execute("BEGIN IMMEDIATE")
                try:
                    self.db.execute("UPDATE calls SET validation_plan_json=? WHERE key=? AND validation_plan_json IS NULL",
                                    (encoded(validation_plan).decode(), key))
                    self.audit(key, "validation_plan_backfilled", now)
                    self.db.execute("COMMIT")
                except Exception:
                    self.db.execute("ROLLBACK")
                    raise
                row = self.get(key)
            return row
        self.db.execute("BEGIN IMMEDIATE")
        try:
            self.db.execute("INSERT INTO calls(key,context_hash,request_hash,consumer,task_id,server,state,method,subject,validation_plan_json) VALUES(?,?,?,?,?,?,?,?,?,?)",
                            (key, context.hash, request_hash, context.identity.consumer,
                             context.identity.task_id, server, "prepared", method, subject,
                             encoded(validation_plan).decode() if validation_plan is not None else None))
            self.audit(key, "prepared", now)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise
        return self.get(key)

    @locked
    def sending(self, key, context, now, estimated_cost=None):
        identity = context.identity
        self.db.execute("BEGIN IMMEDIATE")
        try:
            row = self.db.execute("SELECT ceiling,cost_ceiling FROM budgets WHERE consumer=? AND task_id=?",
                                  (identity.consumer, identity.task_id)).fetchone()
            ceiling = min(row["ceiling"], context.toolset.max_calls) if row else context.toolset.max_calls
            proposed = context.toolset.scope.max_cost_microusd
            ceilings = [value for value in (row["cost_ceiling"] if row else None, proposed) if value is not None]
            cost_ceiling = min(ceilings) if ceilings else None
            prior = self.db.execute("SELECT deliveries,reserved_cost,unknown_cost FROM calls WHERE consumer=? AND task_id=?",
                                    (identity.consumer, identity.task_id)).fetchall()
            used = sum(item["deliveries"] for item in prior)
            used_cost = sum(item["reserved_cost"] for item in prior)
            unknown = any(item["unknown_cost"] for item in prior)
            if used >= ceiling:
                raise PolicyDenied("cumulative task tool-call budget exhausted")
            if estimated_cost is not None and (type(estimated_cost) is not int or estimated_cost < 0):
                raise PolicyDenied("invalid runtime cost quote")
            if cost_ceiling is not None and (unknown or estimated_cost is None or used_cost + estimated_cost > cost_ceiling):
                raise PolicyDenied("cumulative reserved tool-call cost budget exhausted or unknown")
            self.db.execute("INSERT INTO budgets VALUES(?,?,?,?) ON CONFLICT(consumer,task_id) DO UPDATE SET ceiling=excluded.ceiling,cost_ceiling=excluded.cost_ceiling",
                            (identity.consumer, identity.task_id, ceiling, cost_ceiling))
            # Uncertainty is committed before a byte can reach the provider.
            self.db.execute("UPDATE calls SET state='delivery_uncertain', deliveries=deliveries+1,reserved_cost=reserved_cost+?,unknown_cost=MAX(unknown_cost,?) WHERE key=?",
                            (estimated_cost or 0, int(estimated_cost is None), key))
            self.audit(key, "transmission_reserved", now)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    @locked
    def observed(self, key, state, result, now, remote_task_id=None, next_poll=None):
        self.db.execute("BEGIN IMMEDIATE")
        try:
            metadata = None
            if remote_task_id is not None and all(name in result for name in (
                    "taskId", "status", "createdAt", "lastUpdatedAt")):
                metadata = encoded({name: result[name] for name in (
                    "taskId", "status", "createdAt", "lastUpdatedAt", "ttlMs", "pollIntervalMs")
                    if name in result}).decode()
            self.db.execute(
                "UPDATE calls SET state=?,result_hash=?,remote_task_id=?,next_poll=?, "
                "remote_task_json=COALESCE(?,remote_task_json) WHERE key=?",
                (state, hashed(result), remote_task_id, next_poll, metadata, key))
            self.audit(key, state, now)
            self.db.execute("COMMIT")
        except Exception:
            self.db.execute("ROLLBACK")
            raise

    @locked
    def health(self, server, now):
        row = self.db.execute("SELECT * FROM health WHERE server=?", (server,)).fetchone()
        return not row or row["open_until"] <= now

    @locked
    def failure(self, server, now):
        self.db.execute(
            "INSERT INTO health(server,failures,open_until) VALUES(?,1,0) "
            "ON CONFLICT(server) DO UPDATE SET failures=health.failures+1, "
            "open_until=CASE WHEN health.failures+1>=3 THEN ? ELSE 0 END",
            (server, now + 60))

    @locked
    def healthy(self, server):
        self.db.execute("DELETE FROM health WHERE server=?", (server,))


class HTTPTransport:
    """Fixed host-approved endpoint; no redirects, cookies or discovery URLs."""
    def __init__(self, endpoint: str, credential: Callable[[], str] | None = None, *, allow_loopback=False):
        parsed = urlsplit(endpoint)
        if (parsed.username or parsed.password or parsed.query or parsed.fragment or not parsed.hostname
                or (parsed.scheme != "https" and not (
                    allow_loopback and parsed.scheme == "http" and parsed.hostname in {"127.0.0.1", "::1"}))):
            raise PolicyDenied("endpoint must be host-approved credential-free HTTPS")
        self.endpoint, self.parsed, self.credential = endpoint, parsed, credential

    def request(self, message: dict, *, timeout: int, extra_headers: dict | None = None):
        return tuple(self.stream(message, timeout=timeout, extra_headers=extra_headers))

    def stream(self, message: dict, *, timeout: int, extra_headers: dict | None = None):
        """Yield bounded response messages; generator close cancels HTTP/SSE."""
        raw = encoded(message)
        params = message.get("params", {})
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream",
                   "MCP-Protocol-Version": PROTOCOL, "Mcp-Method": message["method"]}
        name = params.get("name", params.get("uri", params.get("taskId")))
        if name is not None:
            headers["Mcp-Name"] = header_value(name)
        headers.update(extra_headers or {})
        if self.credential:
            secret = self.credential()
            if not isinstance(secret, str) or not secret or any(ord(c) < 32 for c in secret):
                raise PolicyDenied("credential reference did not resolve safely")
            headers["Authorization"] = "Bearer " + secret
        connection_class = http.client.HTTPSConnection if self.parsed.scheme == "https" else http.client.HTTPConnection
        connection = connection_class(self.parsed.hostname, self.parsed.port, timeout=timeout)
        deadline = time.monotonic() + timeout
        try:
            connection.connect()
            sock = connection.sock
            sock.settimeout(max(0.01, deadline - time.monotonic()))
            connection.request("POST", self.parsed.path or "/", body=raw, headers=headers)
            sock.settimeout(max(0.01, deadline - time.monotonic()))
            response = connection.getresponse()
            if response.status != 200:
                # Includes redirects: credential/data never follows an unapproved URL.
                raise GatewayUnavailable("provider returned non-success HTTP status")
            content_type = response.getheader("Content-Type", "").split(";")[0].strip().lower()
            if content_type not in {"application/json", "text/event-stream"}:
                raise GatewayError("unsupported provider content type")
            buffer, total, messages, pending_cr = b"", 0, [], False
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise GatewayUnavailable("provider deadline exceeded")
                sock.settimeout(remaining)
                chunk = response.read1(65536)
                total += len(chunk)
                if total > LIMIT:
                    raise GatewayError("bounded response exceeded")
                if not chunk:
                    if content_type == "application/json":
                        yield decode(buffer)
                        return
                    raise DeliveryUncertain("SSE closed without final response")
                if content_type == "text/event-stream":
                    if pending_cr and chunk.startswith(b"\n"):
                        chunk = chunk[1:]
                    pending_cr = chunk.endswith(b"\r")
                    chunk = chunk.replace(b"\r\n", b"\n").replace(b"\r", b"\n")
                buffer += chunk
                if content_type == "application/json" and response.isclosed():
                    yield decode(buffer)
                    return
                if content_type == "text/event-stream":
                    while b"\n\n" in buffer:
                        event, buffer = buffer.split(b"\n\n", 1)
                        lines = [x[5:].lstrip() for x in event.split(b"\n") if x.startswith(b"data:")]
                        if not lines:
                            continue
                        item = decode(b"\n".join(lines))
                        messages.append(None)
                        if len(messages) > 256:
                            raise GatewayError("bounded SSE message count exceeded")
                        yield item
                        if isinstance(item, dict) and item.get("id") == message["id"]:
                            return
        except GatewayError:
            raise
        except (OSError, http.client.HTTPException) as exc:
            raise DeliveryUncertain("provider transport did not yield a known response") from exc
        finally:
            connection.close()


def request_message(context: CallContext, method: str, params: dict, request_id: str, *, tasks=False):
    capabilities = {"extensions": {TASKS: {}}} if tasks else {}
    meta = {META + "protocolVersion": PROTOCOL, META + "clientInfo": {"name": "herdr", "version": VERSION},
            META + "clientCapabilities": capabilities,
            "org.herdr/task": {**asdict(context.identity), "toolset_hash": context.toolset.hash}}
    return {"jsonrpc": "2.0", "id": request_id, "method": method, "params": {**params, "_meta": meta}}


class ClientAdapter:
    def __init__(self, server: ServerBinding, transport, ledger: CallLedger, *, clock=time.time):
        self.server, self.transport, self.ledger, self.clock = server, transport, ledger, clock
        self.definitions = {}
        self.catalog_hash = None
        self.expires_at = 0.0
        self._catalog_mutex = threading.RLock()
        self._catalog_generation = 0

    def invalidate(self):
        with self._catalog_mutex:
            self._catalog_generation += 1
            self.expires_at = 0.0

    def exchange(self, context, method, params, request_id, *, extra_headers=None):
        self.ledger.bind(context)
        self.ledger.audit(context.hash, "mcp_request", self.clock())
        message = request_message(context, method, params, request_id, tasks=self.server.tasks)
        messages = self.transport.request(message, timeout=context.toolset.timeout_seconds,
                                          extra_headers=extra_headers)
        response, notifications = None, []
        for item in messages:
            if not isinstance(item, dict) or item.get("jsonrpc") != "2.0":
                raise GatewayError("invalid protocol message")
            if "id" in item:
                if item["id"] != request_id or response is not None or ("result" in item) == ("error" in item):
                    raise GatewayError("response identity or shape mismatch")
                response = item
            elif "method" in item:
                if not isinstance(item["method"], str) or item["method"] not in {"notifications/progress", "notifications/message"}:
                    raise GatewayError("unsolicited remote request or event")
                notifications.append(item)
            else:
                raise GatewayError("invalid protocol notification")
        if response is None:
            raise DeliveryUncertain("no exact request response")
        if "error" in response:
            if not isinstance(response["error"], dict) or type(response["error"].get("code")) is not int:
                raise GatewayError("malformed protocol error")
            return {"resultType": "protocol_error", "code": response["error"]["code"]}, tuple(notifications)
        result = response["result"]
        if isinstance(result, dict) and "_meta" in result and not isinstance(result["_meta"], dict):
            raise GatewayError("invalid response metadata")
        if (not isinstance(result, dict) or not isinstance(result.get("resultType"), str)
                or result["resultType"] not in {"complete", "input_required", "task"}):
            raise GatewayError("unrecognized protocol result type")
        if result["resultType"] == "task" and (method != "tools/call" or not self.server.tasks):
            raise GatewayError("unnegotiated asynchronous task result")
        return result, tuple(notifications)

    def listen(self, context, filters, request_id):
        self.ledger.bind(context)
        self.ledger.audit(context.hash, "subscription_opened", self.clock())
        message = request_message(context, "subscriptions/listen",
                                  {"notifications": filters}, request_id, tasks=self.server.tasks)
        if not callable(getattr(self.transport, "stream", None)):
            raise GatewayUnavailable("subscription transport is unavailable")
        acknowledged = None
        with closing(self.transport.stream(message, timeout=context.toolset.timeout_seconds)) as stream:
            for index, item in enumerate(stream):
                if index >= 65:
                    raise GatewayError("subscription event count exceeded")
                if not isinstance(item, dict) or item.get("jsonrpc") != "2.0":
                    raise GatewayError("invalid subscription message")
                params = item.get("params", {})
                if not isinstance(params, dict):
                    raise GatewayError("invalid subscription parameters")
                if "id" in item and not isinstance(item.get("result"), dict):
                    raise GatewayError("invalid subscription response")
                metadata = params.get("_meta", {}) if "id" not in item else item["result"].get("_meta", {})
                if not isinstance(metadata, dict) or metadata.get(META + "subscriptionId") != request_id:
                    raise GatewayError("subscription correlation mismatch")
                if index == 0:
                    if "id" in item or item.get("method") != "notifications/subscriptions/acknowledged":
                        raise GatewayError("subscription acknowledgment must precede events")
                    acknowledged = params.get("notifications")
                    if not isinstance(acknowledged, dict) or set(acknowledged) - set(filters):
                        raise GatewayError("subscription acknowledgment expanded filter")
                    for key, value in acknowledged.items():
                        if key == "resourceSubscriptions":
                            if not isinstance(value, list) or any(uri not in filters[key] for uri in value):
                                raise GatewayError("subscription acknowledgment expanded resources")
                        elif value is not True or filters[key] is not True:
                            raise GatewayError("invalid acknowledged notification type")
                    yield item
                    continue
                if "id" in item:
                    if (item["id"] != request_id or item.get("result", {}).get("resultType") != "complete"):
                        raise GatewayError("invalid subscription closure")
                    return
                method = item.get("method")
                permitted = (method == "notifications/tools/list_changed" and acknowledged.get("toolsListChanged") is True
                             or method == "notifications/resources/list_changed" and acknowledged.get("resourcesListChanged") is True
                             or method == "notifications/resources/updated" and params.get("uri") in acknowledged.get("resourceSubscriptions", []))
                if not permitted:
                    raise PolicyDenied("unrequested subscription event or remote command")
                yield item
        if acknowledged is None:
            raise DeliveryUncertain("subscription closed without acknowledgment")

    def discover(self, context: CallContext, now: float):
        if not self.ledger.health(self.server.id, now):
            raise GatewayUnavailable("provider circuit is open")
        try:
            definitions = self._discover(context, now)
        except GatewayError as exc:
            self.ledger.audit(context.hash, "discovery_failed", self.clock())
            self.ledger.failure(self.server.id, self.clock())
            raise
        self.ledger.healthy(self.server.id)
        return definitions

    def _discover(self, context: CallContext, now: float):
        with self._catalog_mutex:
            generation = self._catalog_generation
        definitions, cursor, cursors, ttl = {}, None, set(), 300
        allowed = {x.name: x for x in self.server.tools}
        for page in range(16):
            params = {"cursor": cursor} if cursor else {}
            result, _ = self.exchange(context, "tools/list", params, "discover-" + str(page))
            if result.get("resultType") != "complete" or not isinstance(result.get("tools"), list):
                raise GatewayError("invalid tools discovery")
            for row in result["tools"]:
                if not isinstance(row, dict) or not isinstance(row.get("name"), str):
                    raise GatewayError("invalid discovered tool")
                if row["name"] not in allowed:
                    continue
                if row["name"] in definitions or len(definitions) >= 128:
                    raise GatewayError("duplicate or oversized discovery")
                binding = allowed[row["name"]]
                if hashed(row) != binding.definition_hash:
                    raise PolicyDenied("tool definition changed; versioned policy replan required")
                annotations = row.get("annotations", {})
                if not isinstance(annotations, dict):
                    raise GatewayError("tool annotations must be an object")
                for hint in ("readOnlyHint", "destructiveHint", "idempotentHint", "openWorldHint"):
                    if hint in annotations and type(annotations[hint]) is not bool:
                        raise GatewayError("tool annotation hint must be boolean")
                if "title" in annotations and not isinstance(annotations["title"], str):
                    raise GatewayError("tool annotation title must be a string")
                schema = row.get("inputSchema")
                if not isinstance(schema, dict):
                    raise GatewayError("tool input schema is required")
                validate_schema(schema, check_only=True)
                schema_headers(schema)
                if "outputSchema" in row:
                    validate_schema(row["outputSchema"], check_only=True)
                definitions[row["name"]] = decode(encoded(row))
            raw_ttl = result.get("ttlMs", 0)
            if type(raw_ttl) is not int or not 0 <= raw_ttl <= 2**53 - 1:
                raise GatewayError("invalid discovery TTL")
            ttl = min(ttl, raw_ttl / 1000)
            cursor = result.get("nextCursor")
            if cursor is None:
                break
            identifier(cursor, maximum=1024)
            if cursor in cursors:
                raise GatewayError("discovery cursor loop")
            cursors.add(cursor)
        else:
            raise GatewayError("discovery page budget exhausted")
        if set(definitions) != set(allowed):
            raise GatewayUnavailable("approved tool missing from provider discovery")
        with self._catalog_mutex:
            if generation != self._catalog_generation:
                raise GatewayUnavailable("discovery invalidated during refresh")
            self.definitions = definitions
            self.catalog_hash = hashed(definitions)
            self.expires_at = now + ttl
        return definitions

    @property
    def policy_hash(self):
        return hashed({"id": self.server.id, "consumer": self.server.consumer,
                       "version": self.server.version, "data_policy": self.server.data_policy.to_json(),
                       "tools": [asdict(x) for x in self.server.tools],
                       "resources": self.server.resources, "tasks": self.server.tasks,
                       "subscriptions": self.server.subscriptions,
                       "endpoint": getattr(self.transport, "endpoint", None)})

    def registry_snapshot(self) -> RegistrySnapshot:
        # Static approved declarations do not require loading unused servers.
        # Actual definitions and availability are checked at first admitted use.
        server = self.server
        capabilities, executors = [], []
        provider_id = "mcp." + server.id
        for binding in server.tools:
            capability_id = provider_id + "." + binding.logical_id
            capabilities.append(CapabilityDescriptor(
                capability_id, hashed(asdict(binding)), "mcp.tools.v1", (Feature.MCP, Feature.TOOL_USE),
                (Modality.TEXT,), (Modality.TEXT,), None, None, None, Latency.STANDARD, server.data_policy))
            executors.append(ExecutorDescriptor(capability_id + ".executor", VERSION, provider_id,
                                               capability_id, provider_id + ".runtime", "mcp.gateway",
                                               "http", "stateless", (binding.logical_id,)))
        for uri, logical in server.resources:
            capability_id = provider_id + "." + logical
            capabilities.append(CapabilityDescriptor(capability_id, server.version, "mcp.resources.v1", (Feature.MCP,),
                                (Modality.TEXT,), (Modality.TEXT,), None, None, None, Latency.STANDARD, server.data_policy))
            executors.append(ExecutorDescriptor(capability_id + ".executor", VERSION, provider_id, capability_id,
                                provider_id + ".runtime", "mcp.gateway", "http", "stateless", (logical,)))
        provider = ProviderDescriptor(provider_id, self.policy_hash, tuple(x.id for x in capabilities),
                                      "cost-unknown", server.data_policy, ("http",), ("stateless",))
        return RegistrySnapshot(tuple(capabilities), (provider,), tuple(executors))


class McpGateway:
    def __init__(self, ledger: CallLedger, registry: CapabilityRegistry, clients: tuple[ClientAdapter, ...],
                 *, authority: Callable[[CallContext], bool], runtime_states: Callable,
                 argument_authority: Callable, argument_policy_hash: str, clock: Callable[[], float] = time.time):
        if (not callable(authority) or not callable(runtime_states)
                or not callable(argument_authority) or not _HASH.fullmatch(argument_policy_hash)):
            raise PolicyDenied("host task/argument authority and pinned runtime policy required")
        self.ledger, self.registry = ledger, registry
        self.clients = {client.server.id: client for client in clients}
        if len(self.clients) != len(clients):
            raise GatewayError("duplicate provider")
        self.authority, self.runtime_states, self.clock = authority, runtime_states, clock
        self.argument_authority, self.argument_policy_hash = argument_authority, argument_policy_hash
        self._client_policies = {name: client.policy_hash for name, client in self.clients.items()}
        if any(client.ledger is not ledger for client in clients):
            raise PolicyDenied("client must share the protected gateway ledger")

    def _catalog(self, context, client):
        if self.clock() >= client.expires_at:
            client.discover(context, self.clock())
            self.ledger.audit(context.hash, "discovery_refreshed", self.clock())
        return client.definitions

    def _static_admit(self, context: CallContext, server: str, logical: str, permissions: tuple[str, ...]):
        if isinstance(context, CallContext):
            self.ledger.bind(context)
        if not isinstance(context, CallContext) or not self.authority(context):
            raise PolicyDenied("task attempt/fence is not actively admitted")
        context.toolset.scope.require_subset_of(context.parent_scope)
        context.toolset.scope.require_subset_of(context.consumer_scope)
        if (context.toolset.registry_hash != self.registry.snapshot.hash
                or context.toolset.argument_policy_hash != self.argument_policy_hash):
            raise PolicyDenied("registry or argument policy changed; toolset replan required")
        client = self.clients.get(server)
        if not client or client.server.consumer != context.identity.consumer:
            raise PolicyDenied("provider outside consumer")
        if client.policy_hash != self._client_policies[server]:
            raise PolicyDenied("provider endpoint or execution policy changed; replan required")
        if logical not in context.toolset.tools:
            raise PolicyDenied("tool omitted from declared minimal node toolset")
        if not set(permissions) <= set(context.toolset.scope.permissions):
            raise PolicyDenied("required permissions outside frozen scope")
        return client

    def _admit(self, context: CallContext, server: str, logical: str, permissions: tuple[str, ...], *, tools=True, quote=False):
        snapshot = self.registry.snapshot
        client = self._static_admit(context, server, logical, permissions)
        if snapshot.hash != context.toolset.registry_hash:
            raise PolicyDenied("registry changed during admission; toolset replan required")
        scope, data = context.toolset.scope, client.server.data_policy
        regions = sorted(set(data.regions) & set(scope.regions))
        classes = sorted(set(data.data_classes) & set(scope.data_classes), key=lambda value: value.value)
        if not regions or not classes:
            raise PolicyDenied("provider data policy has no granted region or data class")
        req = CapabilityRequirement(
            "mcp." + server + "." + logical,
            (Feature.MCP, Feature.TOOL_USE) if tools else (Feature.MCP,),
            (Modality.TEXT,), (Modality.TEXT,), (logical,), permissions,
            regions[0], classes[0], data.egress, data.retention, data.training,
            None, None, None, scope.max_cost_microusd)
        states = self.runtime_states(req, client)
        found = CapabilityRegistry(snapshot).candidates(
            req, scope, states, at=datetime.fromtimestamp(self.clock(), UTC).isoformat())
        self._static_admit(context, server, logical, permissions)
        if not found.matches:
            raise PolicyDenied("capability registry denied runtime call")
        if not self.ledger.health(server, self.clock()):
            raise GatewayUnavailable("provider circuit is open")
        selected = next((state for state in states if state.executor_id == found.matches[0].executor_id), None)
        return (client, selected.estimated_cost_microusd if selected else None) if quote else client

    def _replay(self, context, client, method, params, operation_key, *, readonly):
        identifier(operation_key)
        key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id,
                      "operation_key": operation_key})
        request_hash = hashed({"server": client.server.id, "method": method, "params": params})
        with self.ledger.lock(key):
            row = self.ledger.get(key)
            if row is None:
                return None
            if row["context_hash"] != context.hash or row["request_hash"] != request_hash:
                self.ledger.audit(key, "idempotency_conflict", self.clock())
                raise PolicyDenied("operation key reused for different scope/request")
            if row["state"] == "reconciliation_required":
                raise ReconciliationRequired("recorded remote task requires reconciliation")
            if row["state"] in {"observed_complete", "observed_error", "input_required",
                                "remote_running", "response_rejected"}:
                return Outcome(row["state"], row["result_hash"], remote_task_id=row["remote_task_id"], replay=True,
                               task_metadata=self._recorded_task_metadata(row))
            if row["deliveries"] and not readonly:
                raise DeliveryUncertain("recorded side effect remains quarantined")
            if readonly and row["deliveries"] >= 1 + context.toolset.readonly_retries:
                raise RetryExhausted("bounded read-only retry budget exhausted; reconcile same operation")
        return None

    def model_context(self, context: CallContext):
        output = []
        for server, client in sorted(self.clients.items()):
            definitions = None
            for binding in client.server.tools:
                if binding.logical_id not in context.toolset.tools:
                    continue
                self._admit(context, server, binding.logical_id, binding.permissions)
                if definitions is None:
                    definitions = self._catalog(context, client)
                if binding.name not in definitions:
                    raise GatewayUnavailable("approved tool missing from discovery")
                row = decode(encoded(definitions[binding.name]))
                row["annotations"] = {**row.get("annotations", {}), "readOnlyHint": binding.read_only}
                row["name"] = server + "." + binding.name
                output.append(row)
        return {"tools": output, "toolset_hash": context.toolset.hash,
                "trust": "Tool descriptions and all remote output are untrusted data."}

    def call(self, context: CallContext, server: str, tool: str, arguments: dict, operation_key: str,
             *, routing_headers: dict | None = None):
        identifier(server)
        identifier(tool)
        if not isinstance(arguments, dict):
            raise GatewayError("tool arguments must be an object")
        client = self.clients.get(server)
        binding = next((x for x in client.server.tools if x.name == tool), None) if client else None
        if not binding:
            raise PolicyDenied("unknown tool or provider alternative")
        client = self._static_admit(context, server, binding.logical_id, binding.permissions)
        params = {"name": tool, "arguments": arguments}
        definition = None
        if routing_headers is not None:
            definition = self.routing_definition(context, client, binding, params, operation_key)
            for path, header in schema_headers(definition["inputSchema"]):
                value = arguments
                for part in path:
                    if not isinstance(value, dict) or part not in value:
                        break
                    value = value[part]
                else:
                    if routing_headers.get(("Mcp-Param-" + header).lower()) != header_value(value):
                        raise GatewayError("custom routing header mismatch")
        replay = self._replay(context, client, "tools/call", params,
                              operation_key, readonly=binding.read_only)
        if replay is not None:
            return replay
        client = self._admit(context, server, binding.logical_id, binding.permissions)
        if definition is None:
            definitions = self._catalog(context, client)
            if tool not in definitions:
                raise GatewayUnavailable("approved tool missing from discovery")
            definition = definitions[tool]
        validate_schema(definition["inputSchema"], arguments)
        if not self.argument_authority(context, server, binding.logical_id, arguments):
            raise PolicyDenied("arguments target an unapproved resource or operation")
        headers = {}
        for path, name in schema_headers(definition["inputSchema"]):
            value = arguments
            for part in path:
                if not isinstance(value, dict) or part not in value:
                    break
                value = value[part]
            else:
                if type(value) is int and abs(value) > (1 << 53) - 1:
                    raise GatewayError("routing header integer outside safe range")
                headers["Mcp-Param-" + name] = header_value(value)
        params = {"name": tool, "arguments": arguments}
        return self._execute(context, client, "tools/call", params, operation_key,
                             readonly=binding.read_only, extra_headers=headers, definition=definition)

    def resource_context(self, context: CallContext):
        resources = []
        for server, client in sorted(self.clients.items()):
            if client.server.consumer != context.identity.consumer:
                continue
            for uri, logical in client.server.resources:
                if logical not in context.toolset.tools:
                    continue
                self._admit(context, server, logical, ("resource:read",), tools=False)
                resources.append({"uri": uri, "name": server + "." + logical,
                                  "_meta": {"org.herdr/provider": server}})
        return resources

    def read_resource(self, context: CallContext, server: str, uri: str, operation_key: str):
        identifier(server)
        identifier(uri, maximum=4096)
        client = self.clients.get(server)
        logical = dict(client.server.resources).get(uri) if client else None
        if logical is None:
            raise PolicyDenied("resource URI is outside explicit allowlist")
        self._static_admit(context, server, logical, ("resource:read",))
        replay = self._replay(context, client, "resources/read", {"uri": uri}, operation_key, readonly=True)
        if replay is not None:
            return replay
        self._admit(context, server, logical, ("resource:read",), tools=False)
        return self._execute(context, client, "resources/read", {"uri": uri}, operation_key, readonly=True)

    def _execute(self, context, client, method, params, operation_key, *, readonly, extra_headers=None, definition=None):
        identifier(operation_key)
        # One operation key belongs to this task, independent of caller-selected
        # artifact bytes, provider alternatives or policy version.
        key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id,
                      "operation_key": operation_key})
        request_hash = hashed({"server": client.server.id, "method": method, "params": params})
        # Reject oversized wire headers before reserving a delivery or cost.
        routed_name = params.get("name", params.get("uri"))
        if routed_name is not None:
            header_value(routed_name)
        if sum(len(k) + len(v) for k, v in (extra_headers or {}).items()) > 32_768:
            raise GatewayError("aggregate routing headers exceed bound")
        persisted_subject = (params["name"] if method == "tools/call"
                             else dict(client.server.resources)[params["uri"]])
        with self.ledger.lock(key):
            validation_plan = None
            if definition is not None:
                validation_plan = {"definition_hash": hashed(definition),
                                   "inputSchema": definition["inputSchema"],
                                   "outputSchema": definition.get("outputSchema")}
            maximum = 1 + context.toolset.readonly_retries if readonly else 1
            previous = self.ledger.get(key)
            retryable = readonly and (previous is None or previous["deliveries"] < maximum)
            row = self.ledger.reserve(key, context, request_hash, client.server.id, self.clock(),
                                      method, persisted_subject, validation_plan,
                                      retryable=retryable)
            if row["state"] == "reconciliation_required":
                raise ReconciliationRequired("recorded remote task requires reconciliation")
            if row["state"] in {"observed_complete", "observed_error", "input_required", "remote_running", "response_rejected"}:
                return Outcome(row["state"], row["result_hash"], remote_task_id=row["remote_task_id"], replay=True,
                               task_metadata=self._recorded_task_metadata(row))
            if row["deliveries"] and not readonly:
                raise DeliveryUncertain("side effect quarantined; reconcile same operation without redispatch")
            for _ in range(maximum - row["deliveries"]):
                # Revalidate fencing/scope immediately before every transport send.
                logical = next((x.logical_id for x in client.server.tools if x.name == params.get("name")), None)
                if logical:
                    binding = next(x for x in client.server.tools if x.logical_id == logical)
                    _, estimate = self._admit(context, client.server.id, logical, binding.permissions, quote=True)
                    if not self.argument_authority(context, client.server.id, logical, params["arguments"]):
                        raise PolicyDenied("argument policy denied immediately before transmission")
                else:
                    resource = dict(client.server.resources)[params["uri"]]
                    _, estimate = self._admit(context, client.server.id, resource, ("resource:read",), tools=False, quote=True)
                permissions = binding.permissions if logical else ("resource:read",)
                subject = logical if logical else resource
                self._static_admit(context, client.server.id, subject, permissions)
                self.ledger.sending(key, context, self.clock(), estimate)
                communication_started = False
                try:
                    self._static_admit(context, client.server.id, subject, permissions)
                    communication_started = True
                    result, notifications = client.exchange(context, method, params, key, extra_headers=extra_headers)
                    for _notification in notifications:
                        self.ledger.audit(key, "untrusted_notification", self.clock())
                    if result["resultType"] == "task":
                        state, due = self._task_state(result, definition)
                        remote = result["taskId"]
                    elif result["resultType"] == "input_required":
                        # No automatic elicitation, OAuth, callback or tool expansion.
                        state, remote, due = "input_required", None, None
                    elif result["resultType"] == "protocol_error":
                        state, remote, due = "observed_error", None, None
                    else:
                        if method == "resources/read":
                            contents = result.get("contents")
                            if not isinstance(contents, list) or not contents or any(
                                    not isinstance(x, dict) or x.get("uri") != params["uri"] for x in contents):
                                raise PolicyDenied("remote resource contents escaped allowlist")
                        elif not isinstance(result.get("content"), list) or type(result.get("isError", False)) is not bool:
                            raise GatewayError("invalid tool result")
                        if definition and "outputSchema" in definition:
                            if "structuredContent" not in result:
                                raise GatewayError("declared structured output is missing")
                            validate_schema(definition["outputSchema"], result["structuredContent"])
                        state = "observed_error" if result.get("isError") else "observed_complete"
                        remote, due = None, None
                    self.ledger.observed(key, state, result, self.clock(), remote, due)
                    self.ledger.healthy(client.server.id)
                    return Outcome(state, hashed(result), result, remote)
                except GatewayError as exc:
                    self.ledger.audit(key, exc.code, self.clock())
                    if not communication_started:
                        # A local fence/policy race says nothing about provider health.
                        self.ledger.observed(key, "response_rejected", {"code": exc.code}, self.clock())
                        raise
                    self.ledger.failure(client.server.id, self.clock())
                    permanent = not isinstance(exc, (GatewayUnavailable, DeliveryUncertain))
                    if not readonly:
                        self.ledger.audit(key, "mutation_response_unverified", self.clock())
                        if isinstance(exc, DeliveryUncertain):
                            raise
                        raise DeliveryUncertain("mutation response unverified; reconcile unknown side effect") from exc
                    if permanent:
                        self.ledger.observed(key, "response_rejected", {"code": exc.code}, self.clock())
                    if not readonly or permanent:
                        raise
            raise RetryExhausted("bounded read-only retry budget exhausted; reconcile same operation")

    @staticmethod
    def _remote_task(result):
        identifier(result.get("taskId"))
        if (not isinstance(result.get("status"), str)
                or result["status"] not in {"working", "input_required", "completed", "failed", "cancelled"}):
            raise GatewayError("invalid remote task state")
        for name in ("createdAt", "lastUpdatedAt"):
            value = result.get(name)
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                if parsed.tzinfo is None:
                    raise ValueError()
            except (AttributeError, ValueError, TypeError) as exc:
                raise GatewayError("invalid remote task time") from exc
        if "ttlMs" not in result:
            raise GatewayError("remote task TTL is missing")
        if result.get("ttlMs") is not None and (type(result["ttlMs"]) is not int or not 0 <= result["ttlMs"] <= 2**53 - 1):
            raise GatewayError("invalid remote task TTL")
        if "pollIntervalMs" in result and (type(result["pollIntervalMs"]) is not int or not 0 <= result["pollIntervalMs"] <= 86_400_000):
            raise GatewayError("invalid bounded polling interval")

    def _task_state(self, result, definition):
        self._remote_task(result)
        status = result["status"]
        if status == "completed":
            completed = result.get("result")
            if (not isinstance(completed, dict) or completed.get("resultType") != "complete"
                    or not isinstance(completed.get("content"), list)
                    or type(completed.get("isError", False)) is not bool):
                raise GatewayError("completed remote task has invalid tool result")
            if definition and "outputSchema" in definition:
                if "structuredContent" not in completed:
                    raise GatewayError("completed task structured result is missing")
                validate_schema(definition["outputSchema"], completed["structuredContent"])
            if completed.get("isError"):
                status = "failed"
        elif status == "input_required" and not isinstance(result.get("inputRequests"), dict):
            raise GatewayError("remote task input requests are missing")
        elif status == "failed" and not isinstance(result.get("error"), dict):
            raise GatewayError("failed remote task error is missing")
        state = {"working": "remote_running", "input_required": "remote_running",
                 "completed": "observed_complete", "failed": "observed_error", "cancelled": "observed_error"}[status]
        due = (self.clock() + max(1, result.get("pollIntervalMs", 1000) / 1000)
               if state == "remote_running" else None)
        return state, due

    def _recorded_task_metadata(self, row):
        raw = row.get("remote_task_json")
        if row["state"] != "remote_running" or not raw:
            return None
        try:
            metadata = decode(raw.encode())
            self._remote_task(metadata)
            if metadata["taskId"] != row["remote_task_id"]:
                raise GatewayError("recorded task identity mismatch")
            return metadata
        except GatewayError as exc:
            raise ReconciliationRequired("recorded remote task metadata requires reconciliation") from exc

    @staticmethod
    def _recorded_definition(row, binding):
        raw = row.get("validation_plan_json")
        if not raw:
            raise DeliveryUncertain("admitted validation plan is missing; reconcile legacy task")
        plan = decode(raw.encode())
        if (not isinstance(plan, dict) or set(plan) != {"definition_hash", "inputSchema", "outputSchema"}
                or plan["definition_hash"] != binding.definition_hash
                or not isinstance(plan["inputSchema"], dict)):
            raise PolicyDenied("recorded validation plan differs from approved binding")
        definition = {"inputSchema": plan["inputSchema"]}
        if plan["outputSchema"] is not None:
            definition["outputSchema"] = plan["outputSchema"]
        return definition

    def routing_definition(self, context, client, binding, params, operation):
        self._static_admit(context, client.server.id, binding.logical_id, binding.permissions)
        identifier(operation)
        key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id,
                      "operation_key": operation})
        row = self.ledger.get(key)
        if row is not None:
            request_hash = hashed({"server": client.server.id, "method": "tools/call", "params": params})
            if row["context_hash"] != context.hash or row["request_hash"] != request_hash:
                raise PolicyDenied("operation key reused for different scope/request")
            eligible = (row["state"] == "prepared" and row["deliveries"] == 0
                        or binding.read_only and row["state"] == "delivery_uncertain"
                        and row["deliveries"] < 1 + context.toolset.readonly_retries)
            if row["validation_plan_json"] or not eligible:
                return self._recorded_definition(row, binding)
        self._admit(context, client.server.id, binding.logical_id, binding.permissions)
        return self._catalog(context, client)[binding.name]

    def poll(self, context: CallContext, operation_key: str):
        key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id, "operation_key": operation_key})
        return self.poll_record(context, key)

    def poll_record(self, context: CallContext, key: str):
        if not isinstance(key, str) or not _HASH.fullmatch(key):
            raise GatewayError("invalid durable remote task handle")
        with self.ledger.lock(key):
            row = self.ledger.get(key)
            if not row or row["context_hash"] != context.hash:
                raise PolicyDenied("remote task does not belong to this exact context")
            client = self.clients.get(row["server"])
            if client is None:
                raise PolicyDenied("recorded task provider is no longer configured")
            binding = next((x for x in client.server.tools if x.name == row["subject"]), None)
            if binding is None:
                raise PolicyDenied("poll has no approved tool binding")
            self._static_admit(context, client.server.id, binding.logical_id, binding.permissions)
            if row["state"] == "reconciliation_required":
                raise ReconciliationRequired("recorded remote task requires reconciliation")
            if row["state"] != "remote_running":
                return Outcome(row["state"], row["result_hash"], replay=True)
            if self.clock() < row["next_poll"]:
                raise GatewayUnavailable("remote polling interval has not elapsed")
            if row["polls"] >= 32:
                raise DeliveryUncertain("bounded task polling budget exhausted; reconcile remote task")
            client = self.clients.get(row["server"])
            if client is None:
                raise PolicyDenied("recorded task provider is no longer configured")
            binding = next((x for x in client.server.tools if x.name == row["subject"]), None)
            if binding is None:
                raise PolicyDenied("poll has no approved tool binding")
            self._admit(context, client.server.id, binding.logical_id, binding.permissions)
            if not self.ledger.health(client.server.id, self.clock()):
                raise GatewayUnavailable("provider circuit is open")
            # Require the admitted schema BEFORE consuming a possibly short-lived
            # remote terminal result. Never rediscover after tasks/get succeeds.
            self._recorded_definition(row, binding)
            self.ledger.polling(key, self.clock())
            try:
                result, _ = client.exchange(context, "tasks/get", {"taskId": row["remote_task_id"]}, key + ".poll." + str(row["polls"]))
                if result.get("resultType") == "protocol_error":
                    self.ledger.observed(key, "reconciliation_required", {"code": result["code"]},
                                         self.clock(), row["remote_task_id"])
                    self.ledger.healthy(client.server.id)
                    raise ReconciliationRequired("remote task lookup rejected; reconcile protected handle")
                self._remote_task(result)
                if result.get("resultType") != "complete" or result["taskId"] != row["remote_task_id"]:
                    raise GatewayError("remote task correlation mismatch")
                definition = self._recorded_definition(row, binding)
                state, due = self._task_state(result, definition)
                self.ledger.observed(key, state, result, self.clock(), row["remote_task_id"], due)
                self.ledger.healthy(client.server.id)
                return Outcome(state, hashed(result), result, row["remote_task_id"])
            except GatewayError as exc:
                self.ledger.audit(key, exc.code, self.clock())
                if not isinstance(exc, ReconciliationRequired):
                    self.ledger.failure(client.server.id, self.clock())
                raise

    def observe_event(self, context: CallContext, server: str, message: dict):
        """Bounded authenticated subscription observations, never lifecycle writes."""
        if (not isinstance(context, CallContext) or not self.authority(context)
                or server not in self.clients or self.clients[server].server.consumer != context.identity.consumer
                or context.toolset.registry_hash != self.registry.snapshot.hash
                or context.toolset.argument_policy_hash != self.argument_policy_hash):
            raise PolicyDenied("event outside active task/consumer policy")
        encoded(message)
        if not isinstance(message, dict) or not isinstance(message.get("params", {}), dict):
            raise GatewayError("invalid event shape")
        method = message.get("method")
        if not isinstance(method, str) or message.get("jsonrpc") != "2.0" or "id" in message:
            raise GatewayError("invalid event")
        if method in {"notifications/tools/list_changed", "notifications/resources/list_changed"}:
            self.clients[server].invalidate()
            code = "discovery_invalidated"
        elif method == "notifications/resources/updated":
            uri = identifier(message.get("params", {}).get("uri"), maximum=4096)
            logical = dict(self.clients[server].server.resources).get(uri)
            if logical is None:
                raise PolicyDenied("resource event outside allowlist")
            self._admit(context, server, logical, ("resource:read",), tools=False)
            code = "resource_observed"
        else:
            raise PolicyDenied("unsupported event or remote lifecycle command")
        self.ledger.audit(context.identity.hash, code, self.clock())
        return code

    def listen(self, context: CallContext, server: str, filters: dict, operation_key: str):
        """One explicitly admitted, bounded subscription window; never auto-reconnect."""
        identifier(operation_key)
        client = self.clients.get(server)
        if not client or not client.server.subscriptions:
            raise PolicyDenied("subscriptions are not host-approved for provider")
        if (not isinstance(filters, dict) or not filters
                or set(filters) - {"toolsListChanged", "resourcesListChanged", "resourceSubscriptions"}):
            raise PolicyDenied("unsupported subscription filter")
        quote = None
        def admit():
            nonlocal quote
            estimates = []
            for name, value in filters.items():
                if name == "resourceSubscriptions":
                    if (not isinstance(value, list) or not value or len(value) > 32
                            or any(not isinstance(uri, str) for uri in value) or len(value) != len(set(value))):
                        raise GatewayError("invalid bounded resource subscriptions")
                    for uri in value:
                        logical = dict(client.server.resources).get(uri)
                        if logical is None:
                            raise PolicyDenied("subscription resource outside allowlist")
                        _, estimate = self._admit(context, server, logical, ("resource:read",), tools=False, quote=True)
                        estimates.append(estimate)
                elif value is not True:
                    raise GatewayError("notification filters must explicitly opt in")
                elif name == "toolsListChanged":
                    chosen = [x for x in client.server.tools if x.logical_id in context.toolset.tools]
                    if not chosen:
                        raise PolicyDenied("tool events require a declared tool")
                    _, estimate = self._admit(context, server, chosen[0].logical_id, chosen[0].permissions, quote=True)
                    estimates.append(estimate)
                else:
                    chosen = [logical for _, logical in client.server.resources if logical in context.toolset.tools]
                    if not chosen:
                        raise PolicyDenied("resource events require a declared resource")
                    _, estimate = self._admit(context, server, chosen[0], ("resource:read",), tools=False, quote=True)
                    estimates.append(estimate)
            quote = None if any(value is None for value in estimates) else max(estimates)
        declared = [x for x in client.server.tools if x.logical_id in context.toolset.tools]
        resources = [logical for _, logical in client.server.resources if logical in context.toolset.tools]
        if declared:
            self._static_admit(context, server, declared[0].logical_id, declared[0].permissions)
        elif resources:
            self._static_admit(context, server, resources[0], ("resource:read",))
        else:
            raise PolicyDenied("subscription requires a declared capability")
        replay = self._replay(context, client, "subscriptions/listen", {"filters": filters}, operation_key, readonly=False)
        if replay is not None:
            return replay
        admit()
        key = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id, "operation_key": operation_key})
        request_hash = hashed({"server": server, "method": "subscriptions/listen", "params": {"filters": filters}})
        with self.ledger.lock(key):
            row = self.ledger.reserve(key, context, request_hash, server, self.clock(), "subscriptions/listen", hashed(filters))
            if row["state"] in {"observed_complete", "response_rejected"}:
                return Outcome(row["state"], row["result_hash"], replay=True)
            if row["deliveries"]:
                raise DeliveryUncertain("subscription window cannot reopen after uncertain delivery")
            admit()
            self.ledger.sending(key, context, self.clock(), quote)
            events, acknowledged = [], False
            closure = "graceful"
            try:
                with closing(client.listen(context, filters, key)) as stream:
                    for item in stream:
                        admit()
                        if item["method"] == "notifications/subscriptions/acknowledged":
                            acknowledged = True
                            continue
                        code = self.observe_event(context, server, item)
                        events.append({"code": code, "sha256": hashed(item)})
                        if len(events) >= 64:
                            closure = "bounded"
                            break
            except (GatewayUnavailable, DeliveryUncertain) as exc:
                self.ledger.audit(key, exc.code, self.clock())
                self.ledger.failure(server, self.clock())
                if not acknowledged:
                    if isinstance(exc, DeliveryUncertain):
                        raise
                    raise DeliveryUncertain("subscription delivery lacks acknowledgment; reconcile window") from exc
                closure = "disconnected"
            except GatewayError as exc:
                self.ledger.audit(key, exc.code, self.clock())
                self.ledger.failure(server, self.clock())
                if not acknowledged:
                    raise DeliveryUncertain("subscription acknowledgment unverified; reconcile window") from exc
                self.ledger.observed(key, "response_rejected", {"code": exc.code}, self.clock())
                raise
            result = {"kind": "subscription_observation", "events": events, "closure": closure}
            self.ledger.observed(key, "observed_complete", result, self.clock())
            if closure in {"graceful", "bounded"}:
                self.ledger.healthy(server)
            return Outcome("observed_complete", hashed(result), result)


class ServerAdapter:
    """Authenticated MCP server adapter; caller owns approved listener/envelope.

    Authentication resolves to host-owned context. Request _meta only correlates;
    it can never construct or expand the grant.
    """
    def __init__(self, gateway: McpGateway, resolve_context: Callable, *, origins: tuple[str, ...]):
        if not callable(resolve_context):
            raise PolicyDenied("authenticated context resolver required")
        self.gateway, self.resolve_context, self.origins = gateway, resolve_context, origins

    def handle(self, raw: bytes, *, authorization: str | None, origin: str | None = None, headers: dict | None = None):
        if origin is not None and origin not in self.origins:
            return 403, encoded({"error": "origin_denied"})
        context = self.resolve_context(authorization)
        if not isinstance(context, CallContext):
            return 403, encoded({"error": "authentication_required"})
        request_id = None
        try:
            request = decode(raw)
            if not isinstance(request, dict) or request.get("jsonrpc") != "2.0" or type(request.get("id")) not in {str, int}:
                raise GatewayError("invalid JSON-RPC request")
            incoming_id = request["id"]
            if (isinstance(incoming_id, str) and len(incoming_id) > 128
                    or type(incoming_id) is int and not -(2**53 - 1) <= incoming_id <= 2**53 - 1):
                raise GatewayError("request identity exceeds bounded range")
            request_id = incoming_id
            params, method = request.get("params"), request.get("method")
            if not isinstance(params, dict) or not isinstance(method, str):
                raise GatewayError("invalid request parameters")
            meta = params.get("_meta", {})
            if not isinstance(meta, dict):
                raise GatewayError("invalid request metadata")
            if meta.get(META + "protocolVersion") != PROTOCOL or not isinstance(meta.get(META + "clientCapabilities"), dict):
                raise GatewayError("unsupported or absent per-request protocol fields")
            capabilities = meta[META + "clientCapabilities"]
            if not isinstance(capabilities.get("extensions", {}), dict):
                raise GatewayError("invalid client extensions")
            info = meta.get(META + "clientInfo")
            if not isinstance(info, dict) or not isinstance(info.get("name"), str) or not isinstance(info.get("version"), str):
                raise GatewayError("client information is required")
            if meta.get("org.herdr/task") != {**asdict(context.identity), "toolset_hash": context.toolset.hash}:
                raise PolicyDenied("request does not bind authenticated task identity")
            if headers is not None:
                if not isinstance(headers, dict) or len(headers) > 128:
                    raise GatewayError("invalid bounded HTTP headers")
                normalized = {}
                for name, value in headers.items():
                    if (not isinstance(name, str) or not re.fullmatch(r"[!#$%&'*+.^_A-Za-z0-9|-]{1,128}", name)
                            or name.lower() in normalized or not isinstance(value, str)
                            or len(value) > 8192 or chr(13) in value or chr(10) in value):
                        raise GatewayError("invalid or ambiguous HTTP header")
                    normalized[name.lower()] = value
                headers = normalized
                if headers.get("mcp-protocol-version") != PROTOCOL or headers.get("mcp-method") != method:
                    raise GatewayError("HTTP protocol header mismatch")
                name = params.get("name", params.get("uri", params.get("taskId")))
                if name is not None and headers.get("mcp-name") != header_value(name):
                    raise GatewayError("HTTP routing header mismatch")
            if method == "server/discover":
                if not self.gateway.authority(context):
                    raise PolicyDenied("inactive task")
                capabilities = {"tools": {}, "resources": {}}
                if any(client.server.tasks for client in self.gateway.clients.values()
                       if client.server.consumer == context.identity.consumer):
                    capabilities["extensions"] = {TASKS: {}}
                result = {"resultType": "complete", "serverInfo": {"name": "herdr", "version": VERSION},
                          "capabilities": capabilities}
            elif method == "tools/list":
                result = {"resultType": "complete", "tools": self.gateway.model_context(context)["tools"], "ttlMs": 0}
            elif method == "tools/call":
                name = params.get("name")
                if not isinstance(name, str) or "." not in name:
                    raise PolicyDenied("fully qualified tool required")
                if not isinstance(params.get("arguments"), dict):
                    raise GatewayError("tool arguments must be an object")
                server, tool = name.split(".", 1)
                upstream = self.gateway.clients.get(server)
                if upstream and upstream.server.tasks and TASKS not in meta[META + "clientCapabilities"].get("extensions", {}):
                    return 400, encoded({"jsonrpc": "2.0", "id": request_id,
                        "error": {"code": -32021, "message": "missing_required_client_capability",
                                  "data": {"requiredCapabilities": {"extensions": {TASKS: {}}}}}})
                operation = identifier(meta.get("org.herdr/operation"))
                if headers is None:
                    outcome = self.gateway.call(context, server, tool, params["arguments"], operation)
                else:
                    outcome = self.gateway.call(context, server, tool, params["arguments"], operation,
                                                routing_headers=headers)
                if outcome.result is not None and outcome.result.get("resultType") == "protocol_error":
                    raise RemoteProtocolError("upstream tools/call protocol rejection")
                if outcome.result is None and outcome.state == "remote_running":
                    handle = hashed({"consumer": context.identity.consumer, "task_id": context.identity.task_id,
                                     "operation_key": operation})
                    if outcome.task_metadata is not None and outcome.task_metadata["status"] == "working":
                        result = {"resultType": "task", **outcome.task_metadata, "taskId": handle}
                    else:
                        # Legacy or input-required descriptors lack retained question payload.
                        # The protected handle lets clients retrieve the current remote state.
                        result = {"resultType": "complete", "isError": True,
                                  "_meta": {"org.herdr/taskHandle": handle},
                                  "content": [{"type": "text", "text": "Recorded task requires tasks/get using the protected handle."}]}
                elif outcome.result is None:
                    result = {"resultType": "complete", "isError": True,
                              "content": [{"type": "text", "text": "Recorded outcome requires artifact reconciliation; operation was not repeated."}]}
                else:
                    result = decode(encoded(outcome.result))
                    if result.get("resultType") == "task":
                        result["taskId"] = hashed({"consumer": context.identity.consumer,
                            "task_id": context.identity.task_id, "operation_key": operation})
                result.setdefault("_meta", {})["org.herdr/outcomeHash"] = outcome.result_hash
            elif method == "tasks/get":
                if TASKS not in capabilities.get("extensions", {}):
                    raise PolicyDenied("task capability was not negotiated")
                handle = params.get("taskId")
                outcome = self.gateway.poll_record(context, handle)
                if outcome.result is None:
                    raise DeliveryUncertain("task replay requires recorded artifact reconciliation")
                result = decode(encoded(outcome.result))
                result["taskId"] = handle
                result.setdefault("_meta", {})["org.herdr/outcomeHash"] = outcome.result_hash
            elif method == "resources/list":
                result = {"resultType": "complete", "resources": self.gateway.resource_context(context), "ttlMs": 0}
            elif method == "resources/read":
                server = identifier(meta.get("org.herdr/provider"))
                outcome = self.gateway.read_resource(context, server, params.get("uri"), identifier(meta.get("org.herdr/operation")))
                if outcome.result is None:
                    raise DeliveryUncertain("resource replay has no raw payload; reconcile its recorded digest")
                if outcome.result.get("resultType") == "protocol_error":
                    raise RemoteProtocolError("upstream resources/read protocol rejection")
                result = outcome.result
            else:
                raise PolicyDenied("method is outside exposed Herdr authority")
            result.setdefault("_meta", {})[META + "serverInfo"] = {"name": "herdr", "version": VERSION}
            return 200, encoded({"jsonrpc": "2.0", "id": request_id, "result": result})
        except GatewayError as exc:
            code = -32602 if exc.code == "invalid_request" else -32000
            self.gateway.ledger.audit(context.identity.hash, exc.code, self.gateway.clock())
            status = (403 if isinstance(exc, PolicyDenied) else
                      503 if isinstance(exc, GatewayUnavailable) else
                      502 if isinstance(exc, (DeliveryUncertain, RemoteProtocolError)) else 400)
            return status, encoded(
                {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": exc.code,
                 "data": {"retryable": isinstance(exc, GatewayUnavailable),
                          "reconcileRequired": isinstance(exc, DeliveryUncertain)}}})
