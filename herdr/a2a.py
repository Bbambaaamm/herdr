"""Offline A2A 1.0 gateway contract. Remote execution never grants Herdr authority."""
from __future__ import annotations

import hashlib
import base64
import binascii
import contextlib
import fcntl
import json
import os
import re
import stat
import unicodedata
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol
from urllib.parse import urlsplit

from herdr.capability import ExecutorDescriptor, Health, RuntimeStateSnapshot
from herdr.scheduler import ChildProposal

VERSION = "1.0"
HEADER = {"A2A-Version": VERSION}
MAX_CARD = 32_768
MAX_RESPONSE = 131_072
MAX_PARTS = 16
MAX_REMOTE_ID_BYTES = 4096
MAX_CANDIDATES = 64
MAX_RESPONSE_CANDIDATES = MAX_PARTS + 1  # status.message + bounded artifacts
MAX_BINDING = (
    MAX_CANDIDATES * (MAX_RESPONSE + 2 * MAX_REMOTE_ID_BYTES + 1024)
    + 64 * 1024
)
ECONOMIC_CLAIM_ROOT = Path("/var/lib/herdr/a2a-economic-claims")
_ID = re.compile(r"^[A-Za-z0-9._:@/+-]{1,256}$")
_SECRET = re.compile(r"(?i)(secret|password|credential|private.?key|api.?key|access.?token|authorization|cookie|bearer\s|ghp_[a-z0-9]{20,}|sk-[a-z0-9]{20,}|xox[baprs]-)")
_CARD_SECRET_VALUE = re.compile(
    r"(?i)(bearer\s+\S{12,}|ghp_[a-z0-9]{20,}|sk-[a-z0-9]{20,}|xox[baprs]-[a-z0-9-]{12,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|(?:password|api.?key|access.?token|authorization)\s*[:=]\s*\S+)"
)
_STATES = frozenset("TASK_STATE_UNSPECIFIED TASK_STATE_SUBMITTED TASK_STATE_WORKING TASK_STATE_COMPLETED TASK_STATE_FAILED TASK_STATE_CANCELED TASK_STATE_REJECTED TASK_STATE_INPUT_REQUIRED TASK_STATE_AUTH_REQUIRED".split())
_TERMINAL = frozenset("TASK_STATE_COMPLETED TASK_STATE_FAILED TASK_STATE_CANCELED TASK_STATE_REJECTED".split())
_BINDINGS = frozenset({"JSONRPC", "GRPC", "HTTP+JSON"})


class A2AError(ValueError):
    pass


def _id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not _ID.fullmatch(value) or _SECRET.search(value):
        raise A2AError(f"invalid {label}")
    return value


def _label(value: Any, label: str) -> str:
    if not isinstance(value, str) or not 1 <= len(value) <= 256 or any(unicodedata.category(c) in {"Cc","Cf","Cs"} for c in value):
        raise A2AError(f"invalid {label}")
    return value


def _bounded(value: Any, limit: int, *, secret_scan: bool = True) -> bytes:
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError, OverflowError) as exc:
        raise A2AError("invalid JSON") from exc
    if len(data) > limit or (secret_scan and _SECRET.search(data.decode())):
        raise A2AError("oversized or secret-like metadata")
    return data


def _reject_secret_values(value: Any) -> None:
    if isinstance(value, str):
        if _CARD_SECRET_VALUE.search(value):
            raise A2AError("raw secret-like value")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if (
                isinstance(key, str)
                and re.fullmatch(r"(?i)(password|api.?key|access.?token|authorization|credential)", key)
                and isinstance(item, str)
                and item
            ):
                raise A2AError("raw secret-like value")
            _reject_secret_values(item)
        return
    if isinstance(value, list):
        for item in value:
            _reject_secret_values(item)


def _remote_id(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value:
        raise A2AError(f"invalid {label}")
    raw = value.encode("utf-8")
    if (
        len(raw) > MAX_REMOTE_ID_BYTES
        or any(unicodedata.category(c) in {"Cc", "Cf", "Cs"} for c in value)
    ):
        raise A2AError(f"invalid {label}")
    return value


def _object(value: Any, keys: set[str], required: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - keys:
        raise A2AError("invalid object fields")
    return value


def _url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise A2AError("invalid interface URL")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise A2AError("invalid interface URL port") from exc
    if (port is not None and not 1 <= port <= 65535) or parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise A2AError("interface requires a plain HTTPS URL")
    return value


def _part_url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 4096:
        raise A2AError("invalid part URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise A2AError("part URL requires HTTPS without embedded credentials")
    return value


def _interface_address(value: Any, binding: str) -> str:
    # A2A v1.0.1 requires AgentInterface.url to be an absolute HTTPS URL for
    # every core binding, including GRPC. The binding changes transport
    # semantics, not the production URL/TLS contract.
    if binding not in _BINDINGS:
        raise A2AError("unsupported binding")
    return _url(value)


def _tenant(value: Any) -> str:
    """Bound the opaque AgentInterface tenant without imposing local ID syntax."""
    if not isinstance(value, str):
        raise A2AError("invalid tenant")
    try:
        raw = value.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise A2AError("invalid tenant") from exc
    if len(raw) > MAX_REMOTE_ID_BYTES:
        raise A2AError("invalid tenant")
    return value


@dataclass(frozen=True)
class Interface:
    url: str
    protocol_binding: str
    tenant: str | None
    protocol_version: str

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(_bounded(asdict(self), MAX_CARD, secret_scan=False)).hexdigest()


@dataclass(frozen=True)
class AgentCard:
    name: str
    interfaces: tuple[Interface, ...]
    fingerprint: str
    input_modes: tuple[str,...] = ()

    @property
    def supports_text_input(self):
        return any(mode.split(";",1)[0].strip().lower() in
                   {"text","text/plain","text/*","*/*"} for mode in self.input_modes)


def parse_card(raw: Any) -> AgentCard:
    _bounded(raw, MAX_CARD, secret_scan=False)
    _reject_secret_values(raw)
    card = _object(raw, {"name", "description", "version", "supportedInterfaces", "capabilities", "skills", "defaultInputModes", "defaultOutputModes", "provider", "documentationUrl", "iconUrl", "securitySchemes", "securityRequirements", "signatures"}, {"name", "description", "version", "supportedInterfaces", "capabilities", "skills", "defaultInputModes", "defaultOutputModes"})
    name = _label(card["name"], "card name")
    _label(card["description"], "description")
    _label(card["version"], "version")
    capabilities = card["capabilities"]
    if not isinstance(capabilities, dict):
        raise A2AError("invalid capabilities")
    extensions = capabilities.get("extensions", [])
    if not isinstance(extensions, list) or len(extensions) > 32:
        raise A2AError("invalid capability extensions")
    for extension in extensions:
        if not isinstance(extension, dict):
            raise A2AError("invalid capability extension")
        required = extension.get("required", False)
        if type(required) is not bool:
            raise A2AError("invalid capability extension")
        if required:
            # #71 intentionally implements no A2A extensions. Fail before
            # admission/economic dispatch instead of relying on a remote error.
            raise A2AError("unsupported required extension")
    if not isinstance(card["skills"], list) or not 1 <= len(card["skills"]) <= 32:
        raise A2AError("invalid skills")
    skill_ids=set()
    skill_input_modes=[]
    for skill in card["skills"]:
        item = _object(skill, {"id", "name", "description", "tags", "examples", "inputModes", "outputModes", "securityRequirements"}, {"id", "name", "description", "tags"})
        skill_id=_remote_id(item["id"], "skill id")
        if skill_id in skill_ids:raise A2AError("duplicate remote skill id")
        skill_ids.add(skill_id)
        for mode_key in ("inputModes","outputModes"):
            if mode_key in item:
                modes=item[mode_key]
                if not isinstance(modes,list) or not modes or len(modes)>32:
                    raise A2AError("invalid skill modes")
                for mode in modes:_label(mode,"skill mode")
        skill_input_modes.extend(item.get("inputModes",[]))
        _label(item["name"], "skill name")
        _label(item["description"], "skill description")
        if not isinstance(item["tags"], list) or not item["tags"] or any(not isinstance(tag, str) or not tag for tag in item["tags"]):
            raise A2AError("invalid skill tags")
    for mode_key in ("defaultInputModes", "defaultOutputModes"):
        modes = card[mode_key]
        if not isinstance(modes, list) or not modes or len(modes) > 32 or any(not isinstance(mode, str) or not mode for mode in modes):
            raise A2AError("invalid modes")
        for mode in modes:_label(mode,"mode")
    entries = card["supportedInterfaces"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 8:
        raise A2AError("invalid interfaces")
    interfaces = []
    for item in entries:
        entry = _object(item, {"url", "protocolBinding", "tenant", "protocolVersion"}, {"url", "protocolBinding", "protocolVersion"})
        binding = entry["protocolBinding"]
        if not isinstance(binding, str) or binding not in _BINDINGS or entry["protocolVersion"] != VERSION:
            raise A2AError("unsupported binding/version")
        interfaces.append(Interface(
            _interface_address(entry["url"], binding),
            binding,
            _tenant(entry["tenant"]) if "tenant" in entry else None,
            VERSION,
        ))
    return AgentCard(name, tuple(interfaces), hashlib.sha256(_bounded(raw, MAX_CARD, secret_scan=False)).hexdigest(),
                     tuple(sorted(set(card["defaultInputModes"]+skill_input_modes))))


@dataclass(frozen=True)
class Admission:
    """Explicit local policy, created independently of discovery."""
    card_fingerprint: str
    interface_fingerprint: str
    executor_id: str
    provider_id: str
    capability_id: str
    runtime_id: str
    tools: tuple[str, ...]
    binding_root: str

    def __post_init__(self) -> None:
        for value in (self.card_fingerprint, self.interface_fingerprint):
            if not re.fullmatch(r"[0-9a-f]{64}", value):
                raise A2AError("invalid admission fingerprint")
        for name in ("executor_id", "provider_id", "capability_id", "runtime_id"):
            _id(getattr(self, name), name)
        if not isinstance(self.tools, tuple) or len(self.tools) > 32:
            raise A2AError("invalid tools")
        for tool in self.tools:
            _id(tool, "tool")
        if (
            not isinstance(self.binding_root, str)
            or not self.binding_root
            or "\x00" in self.binding_root
        ):
            raise A2AError("invalid binding root")
        root = Path(self.binding_root)
        if not root.is_absolute() or ".." in root.parts:
            raise A2AError("invalid binding root")
        object.__setattr__(self, "binding_root", str(root))


def authorize(card: AgentCard, policy: Admission) -> Interface:
    if card.fingerprint != policy.card_fingerprint:
        raise A2AError("card not locally admitted")
    matches = [i for i in card.interfaces if i.fingerprint == policy.interface_fingerprint]
    if len(matches) != 1:
        raise A2AError("interface not locally admitted")
    return matches[0]


def registration(card: AgentCard, policy: Admission, *, observed_at: str, ttl_seconds: int, registry_hash: str) -> tuple[ExecutorDescriptor, RuntimeStateSnapshot, dict[str, str]]:
    interface = authorize(card, policy)
    executor = ExecutorDescriptor(policy.executor_id, VERSION, policy.provider_id, policy.capability_id, policy.runtime_id, f"a2a:{card.fingerprint}", interface.protocol_binding, "bounded", policy.tools)
    runtime = RuntimeStateSnapshot(executor.id, observed_at, ttl_seconds, Health.UNKNOWN, None, None, "unobserved", registry_hash)
    return executor, runtime, {"card_fingerprint": card.fingerprint, "interface_fingerprint": interface.fingerprint, "admission": "local"}


@dataclass(frozen=True)
class Identity:
    parent_agent_id: str
    child_agent_id: str
    task_id: str
    run_token: str
    fencing_token: int
    idempotency_key: str

    def __post_init__(self) -> None:
        for name in ("parent_agent_id", "child_agent_id", "task_id", "run_token", "idempotency_key"):
            _id(getattr(self, name), name)
        if type(self.fencing_token) is not int or not 0 <= self.fencing_token < 2**63:
            raise A2AError("invalid fence")

    @property
    def message_id(self) -> str:
        return "herdr-" + hashlib.sha256(_bounded(asdict(self), 4096)).hexdigest()


@dataclass(frozen=True)
class Candidate:
    identity: Identity
    remote_task_id: str | None
    remote_context_id: str | None
    kind: str
    digest: str
    content_json: bytes
    acceptance: str = "requires_shared_85_acceptance"

    @property
    def content(self) -> Any:
        return json.loads(self.content_json)


def _candidate_record(candidate: Candidate) -> dict[str, Any]:
    return {
        "remote_task_id": candidate.remote_task_id,
        "remote_context_id": candidate.remote_context_id,
        "kind": candidate.kind,
        "digest": candidate.digest,
        "content": candidate.content,
    }


def _candidate_from_record(identity: Identity, raw: Any) -> Candidate:
    item = _object(
        raw,
        {"remote_task_id", "remote_context_id", "kind", "digest", "content"},
        {"remote_task_id", "remote_context_id", "kind", "digest", "content"},
    )
    task = _remote_id(item["remote_task_id"], "remote task id") if item["remote_task_id"] is not None else None
    context = _remote_id(item["remote_context_id"], "remote context id") if item["remote_context_id"] is not None else None
    if item["kind"] not in {"message", "artifact"}:
        raise A2AError("invalid candidate kind")
    content_json = _bounded(item["content"], MAX_RESPONSE, secret_scan=False)
    _reject_secret_values(item["content"])
    digest = hashlib.sha256(content_json).hexdigest()
    if not isinstance(item["digest"], str) or item["digest"] != digest:
        raise A2AError("candidate digest mismatch")
    return Candidate(identity, task, context, item["kind"], digest, content_json)


def _merge_candidate_records(existing: Any, candidates: tuple[Candidate, ...]) -> list[dict[str, Any]]:
    if not isinstance(existing, list):
        raise A2AError("invalid recovery candidates")
    records = list(existing)
    seen = {
        (item.get("kind"), item.get("digest"), item.get("remote_task_id"), item.get("remote_context_id"))
        for item in records if isinstance(item, dict)
    }
    for candidate in candidates:
        record = _candidate_record(candidate)
        key = (record["kind"], record["digest"], record["remote_task_id"], record["remote_context_id"])
        if key not in seen:
            records.append(record)
            seen.add(key)
    if len(records) > MAX_CANDIDATES:
        raise A2AError("candidate recovery count exceeds bound")
    # Every candidate has already passed _candidate/_parse_response's targeted
    # raw-secret validation. Do not apply the broader metadata keyword scan
    # here: benign result prose such as "password reset instructions" must not
    # become unpersistable after the remote effect has already happened.
    _bounded(records, MAX_BINDING, secret_scan=False)
    return records


class Transport(Protocol):
    def discover(self, url: str, headers: Mapping[str, str]) -> Any: ...
    def send(self, interface: Interface, message: Mapping[str, Any], headers: Mapping[str, str]) -> Any: ...
    def get(self, interface: Interface, request: Mapping[str, Any], headers: Mapping[str, str]) -> Any: ...
    def cancel(self, interface: Interface, request: Mapping[str, Any], headers: Mapping[str, str]) -> Any: ...


def discover_card(transport: Transport, origin: str) -> AgentCard:
    """Read discovery metadata; this does not produce an admitted executor."""
    url = _url(origin)
    parsed = urlsplit(url)
    if parsed.path not in ("", "/"):
        raise A2AError("discovery requires an origin")
    return parse_card(transport.discover(url.rstrip("/") + "/.well-known/agent-card.json", HEADER))


def _open_durable_directory(path: Path) -> int:
    """Open/create an absolute directory component-wise without following symlinks.

    Every new directory entry is fsynced in its parent before descending. The
    returned FD pins the final directory inode, so later binding/lock operations
    never re-resolve an attacker-swappable ancestor pathname.
    """
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise A2AError("invalid binding directory")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
    current = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            if not part or part in {".", ".."}:
                raise A2AError("invalid binding directory")
            created = False
            try:
                next_fd = os.open(part, flags, dir_fd=current)
            except FileNotFoundError:
                try:
                    os.mkdir(part, 0o700, dir_fd=current)
                    created = True
                except FileExistsError:
                    pass
                except OSError as exc:
                    raise A2AError("cannot create binding directory") from exc
                if created:
                    os.fsync(current)
                try:
                    next_fd = os.open(part, flags, dir_fd=current)
                except OSError as exc:
                    raise A2AError("invalid binding directory") from exc
            except OSError as exc:
                raise A2AError("invalid binding directory") from exc
            info = os.fstat(next_fd)
            if not stat.S_ISDIR(info.st_mode):
                os.close(next_fd)
                raise A2AError("invalid binding directory")
            # Fsync every ancestor directory, not only directories created by
            # this call. A caller may have created an existing multi-level
            # binding path immediately before constructing the store.
            os.fsync(current)
            if created:
                os.fsync(next_fd)
            os.close(current)
            current = next_fd
        os.fsync(current)
        return current
    except BaseException:
        os.close(current)
        raise


class BindingStore:
    """Durable dispatch state plus a host-admitted per-identity economic claim."""

    def __init__(self, path: Path, *, authority_root: Path | None = None):
        self.path = Path(path)
        if not self.path.is_absolute() or not self.path.name or ".." in self.path.parts:
            raise A2AError("invalid binding path")
        self.authority_root = Path(authority_root) if authority_root is not None else self.path.parent
        if not self.authority_root.is_absolute() or ".." in self.authority_root.parts:
            raise A2AError("invalid binding authority root")
        try:
            self.path.relative_to(self.authority_root)
        except ValueError as exc:
            raise A2AError("binding path outside authority root") from exc

    @contextlib.contextmanager
    def locked(self):
        directory = _open_durable_directory(self.path.parent)
        lock_name = self.path.name + ".lock"
        try:
            lock = os.open(
                lock_name,
                os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o600,
                dir_fd=directory,
            )
            try:
                if not stat.S_ISREG(os.fstat(lock).st_mode):
                    raise A2AError("invalid binding lock")
                fcntl.flock(lock, fcntl.LOCK_EX)
                current = os.stat(lock_name, dir_fd=directory, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (
                    os.fstat(lock).st_dev,
                    os.fstat(lock).st_ino,
                ):
                    raise A2AError("binding lock changed")
                yield directory
            finally:
                os.close(lock)
        finally:
            os.close(directory)

    def claim_economic(
        self, identity: Identity, card_fingerprint: str, interface_fingerprint: str
    ) -> None:
        """Permanently claim this Herdr economic identity before remote dispatch.

        The claim is independent of the caller-selected binding filename. A
        retry with another binding path under the same admitted root therefore
        cannot create a second remote attempt.
        """
        root = _open_durable_directory(ECONOMIC_CLAIM_ROOT)
        name = identity.message_id + ".claim"
        payload = _bounded(
            {
                "identity": asdict(identity),
                "message_id": identity.message_id,
                "card_fingerprint": card_fingerprint,
                "interface_fingerprint": interface_fingerprint,
            },
            8192,
            secret_scan=False,
        )
        fd = -1
        try:
            try:
                fd = os.open(
                    name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600,
                    dir_fd=root,
                )
            except FileExistsError as exc:
                raise A2AError("delivery already started; reconcile ambiguous send") from exc
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode):
                raise A2AError("invalid economic claim")
            view = memoryview(payload)
            while view:
                written = os.write(fd, view)
                if written <= 0:
                    raise A2AError("short economic claim write")
                view = view[written:]
            os.fsync(fd)
            os.fsync(root)
        finally:
            if fd >= 0:
                os.close(fd)
            os.close(root)

    def _read(self, directory: int) -> dict[str, Any] | None:
        try:
            fd = os.open(
                self.path.name,
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC,
                dir_fd=directory,
            )
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise A2AError("invalid binding path") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > MAX_BINDING:
                raise A2AError("invalid or oversized binding")
            chunks = bytearray()
            while len(chunks) <= MAX_BINDING:
                chunk = os.read(fd, min(65536, MAX_BINDING + 1 - len(chunks)))
                if not chunk:
                    break
                chunks.extend(chunk)
            if len(chunks) > MAX_BINDING:
                raise A2AError("oversized binding")
            data = json.loads(bytes(chunks))
        finally:
            os.close(fd)
        _object(
            data,
            {
                "identity", "message_id", "card_fingerprint", "interface_fingerprint",
                "delivery", "remote_task_id", "remote_context_id", "cancel_intent",
                "last_observation", "candidates",
            },
            {
                "identity", "message_id", "card_fingerprint", "interface_fingerprint",
                "delivery", "remote_task_id", "remote_context_id", "cancel_intent",
                "last_observation", "candidates",
            },
        )
        identity = Identity(**data["identity"])
        if (
            identity.message_id != data["message_id"]
            or data["delivery"] not in {"send_started", "bound", "direct"}
        ):
            raise A2AError("invalid binding")
        if not all(
            isinstance(data[key], str) and re.fullmatch(r"[0-9a-f]{64}", data[key])
            for key in ("card_fingerprint", "interface_fingerprint")
        ):
            raise A2AError("invalid binding fingerprint")
        if type(data["cancel_intent"]) is not bool:
            raise A2AError("invalid cancel intent")
        for key in ("remote_task_id", "remote_context_id"):
            if data[key] is not None:
                _remote_id(data[key], key)
        if (
            not isinstance(data["candidates"], list)
            or len(data["candidates"]) > MAX_CANDIDATES
        ):
            raise A2AError("invalid recovery candidates")
        for item in data["candidates"]:
            _candidate_from_record(identity, item)
        if data["delivery"] == "bound" and not data["remote_task_id"]:
            raise A2AError("invalid remote binding")
        if data["delivery"] != "bound" and data["remote_task_id"] is not None:
            raise A2AError("invalid remote binding")
        if (
            data["last_observation"] is not None
            and data["last_observation"] not in _STATES | {"direct", "message"}
        ):
            raise A2AError("invalid observation")
        return data

    def read(self) -> dict[str, Any] | None:
        with self.locked() as directory:
            return self._read(directory)

    @staticmethod
    def require_response_capacity(data: Mapping[str, Any]) -> None:
        """Reserve worst-case bounded response capacity before remote effects.

        A valid A2A response may contain one TaskStatus.message plus MAX_PARTS
        artifacts. We never make GetTask/CancelTask if such a response could
        overflow the durable recovery ledger after the remote effect occurred.
        """
        candidates = data.get("candidates")
        if not isinstance(candidates, list):
            raise A2AError("invalid recovery candidates")
        if len(candidates) + MAX_RESPONSE_CANDIDATES > MAX_CANDIDATES:
            raise A2AError("candidate recovery capacity exhausted")
        # MAX_BINDING is dimensioned for MAX_CANDIDATES worst-case candidate
        # records. This additionally proves the current record itself is sane.
        _bounded(data, MAX_BINDING, secret_scan=False)

    def _write(self, directory: int, data: dict[str, Any], *, create: bool = False) -> None:
        raw = _bounded(data, MAX_BINDING, secret_scan=False)
        tmp = ".a2a-" + uuid.uuid4().hex
        fd = os.open(
            tmp,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=directory,
        )
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if create:
                try:
                    os.link(
                        tmp,
                        self.path.name,
                        src_dir_fd=directory,
                        dst_dir_fd=directory,
                        follow_symlinks=False,
                    )
                except FileExistsError as exc:
                    raise A2AError("delivery already started; reconcile ambiguous send") from exc
            else:
                os.replace(
                    tmp,
                    self.path.name,
                    src_dir_fd=directory,
                    dst_dir_fd=directory,
                )
            os.fsync(directory)
        finally:
            try:
                os.unlink(tmp, dir_fd=directory)
            except FileNotFoundError:
                pass

    def write(self, data: dict[str, Any]) -> None:
        with self.locked() as directory:
            self._write(directory, data)

    def create(self, data: dict[str, Any]) -> None:
        with self.locked() as directory:
            self._write(directory, data, create=True)


def _parts(raw: Any) -> Any:
    if not isinstance(raw, list) or not 1 <= len(raw) <= MAX_PARTS:
        raise A2AError("invalid parts")
    for part in raw:
        if not isinstance(part, dict):
            raise A2AError("invalid part")
        if sum(k in part for k in ("text", "raw", "url", "data")) != 1:
            raise A2AError("invalid part content")
        if "url" in part:
            _part_url(part["url"])
        if "text" in part and not isinstance(part["text"], str):
            raise A2AError("invalid text")
        if "raw" in part:
            if not isinstance(part["raw"], str):
                raise A2AError("invalid raw part")
            try:
                encoded = part["raw"].encode("ascii")
                # ProtoJSON parsers must accept standard and URL-safe base64,
                # with or without padding. Normalize to strict standard base64
                # and then validate the normalized representation.
                normalized = encoded.replace(b"-", b"+").replace(b"_", b"/")
                normalized += b"=" * ((-len(normalized)) % 4)
                base64.b64decode(normalized, validate=True)
            except (UnicodeEncodeError, ValueError, binascii.Error) as exc:
                raise A2AError("invalid base64 raw part") from exc
        if "data" in part:
            _bounded(part["data"], MAX_RESPONSE, secret_scan=False)
            _reject_secret_values(part["data"])
        for field in ("mediaType", "filename"):
            if field in part and (not isinstance(part[field], str) or len(part[field]) > 256):
                raise A2AError("invalid part metadata")
        if "metadata" in part and not isinstance(part["metadata"], dict):
            raise A2AError("invalid part metadata")
    return raw


def _candidate(identity: Identity, task: str | None, context: str | None, kind: str, content: Any) -> Candidate:
    raw = _bounded(content, MAX_RESPONSE, secret_scan=False)
    _reject_secret_values(content)
    return Candidate(identity, task, context, kind, hashlib.sha256(raw).hexdigest(), raw)


def _response_object(value: Any, required: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict) or not required <= value.keys():
        raise A2AError("invalid response object")
    return value


def _parse_response(
    raw: Any,
    identity: Identity,
    binding: dict[str, Any] | None = None,
    *,
    allow_bare_task: bool = False,
    discard_history: bool = False,
) -> tuple[str, str | None, str | None, tuple[Candidate, ...]]:
    if discard_history and isinstance(raw,dict):
        # CancelTask has no historyLength parameter. History is not a candidate
        # or authority input; discard it before bounding/scanning persisted data.
        if isinstance(raw.get("task"),dict):
            task=dict(raw["task"])
            if "history" in task and not isinstance(task["history"],list):
                raise A2AError("invalid task history")
            task.pop("history",None)
            raw={**raw,"task":task}
        elif "message" not in raw:
            raw=dict(raw)
            if "history" in raw and not isinstance(raw["history"],list):
                raise A2AError("invalid task history")
            raw.pop("history",None)
    _bounded(raw, MAX_RESPONSE, secret_scan=False)
    _reject_secret_values(raw)
    if not isinstance(raw, dict):
        raise A2AError("expected task or message")
    if allow_bare_task and "task" not in raw and "message" not in raw:
        if not {"id", "status"} <= raw.keys():
            raise A2AError("expected task")
        envelope: Mapping[str, Any] = {"task": raw}
    else:
        known = [key for key in ("task", "message") if key in raw]
        if len(known) != 1:
            raise A2AError("expected task or message")
        envelope = raw
    if "message" in envelope:
        if binding and binding["remote_task_id"]:
            raise A2AError("bound task cannot become direct message")
        msg = _response_object(envelope["message"], {"messageId", "role", "parts"})
        _remote_id(msg["messageId"], "messageId")
        if msg["role"] != "ROLE_AGENT":
            raise A2AError("expected agent message")
        _parts(msg["parts"])
        if "contextId" not in msg:
            raise A2AError("agent message requires contextId")
        context = _remote_id(msg["contextId"], "contextId")
        task_id = _remote_id(msg["taskId"], "taskId") if "taskId" in msg else None
        observation = "message" if task_id is not None else "direct"
        return observation, task_id, context, (
            _candidate(identity, task_id, context, "message", msg),
        )
    task = _response_object(envelope["task"], {"id", "status"})
    task_id = _remote_id(task["id"], "task id")
    context = _remote_id(task["contextId"], "context id") if "contextId" in task else None
    if binding and (binding["remote_task_id"] != task_id or binding["remote_context_id"] != context):
        raise A2AError("remote binding mismatch")
    status = _response_object(task["status"], {"state"})
    state = status["state"]
    if not isinstance(state, str) or state not in _STATES:
        raise A2AError("invalid task state")
    artifacts = task.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) > MAX_PARTS:
        raise A2AError("invalid artifacts")
    candidates = []
    if "message" in status:
        msg = _response_object(status["message"], {"messageId", "role", "parts"})
        _remote_id(msg["messageId"], "messageId")
        if msg["role"] != "ROLE_AGENT":
            raise A2AError("expected agent status message")
        _parts(msg["parts"])
        if "contextId" not in msg:
            raise A2AError("agent status message requires contextId")
        message_context = _remote_id(msg["contextId"], "contextId")
        if context is not None and message_context != context:
            raise A2AError("status message context mismatch")
        if "taskId" in msg and _remote_id(msg["taskId"], "taskId") != task_id:
            raise A2AError("status message task mismatch")
        candidates.append(
            _candidate(
                identity,
                task_id,
                context if context is not None else message_context,
                "message",
                msg,
            )
        )
    for artifact in artifacts:
        item = _response_object(artifact, {"artifactId", "parts"})
        _remote_id(item["artifactId"], "artifactId")
        _parts(item["parts"])
        candidates.append(_candidate(identity, task_id, context, "artifact", item))
    return state, task_id, context, tuple(candidates)


class Gateway:
    def __init__(self, transport: Transport, store: BindingStore, card: AgentCard, policy: Admission):
        self.transport, self.store, self.card, self.policy = transport, store, card, policy
        self.interface = authorize(card, policy)
        if self.store.authority_root != Path(self.policy.binding_root):
            raise A2AError("binding authority root not locally admitted")

    def _bound(self, identity: Identity, directory: int) -> dict[str, Any]:
        data = self.store._read(directory)
        if data is None or data["identity"] != asdict(identity) or data["card_fingerprint"] != self.card.fingerprint or data["interface_fingerprint"] != self.interface.fingerprint:
            raise A2AError("local identity or admission mismatch")
        return data

    def send(self, identity: Identity, text: str) -> tuple[Candidate, ...]:
        if not self.card.supports_text_input:
            raise A2AError("remote card does not support text input")
        if not isinstance(text, str) or not text or len(text.encode()) > 8192 or _SECRET.search(text):
            raise A2AError("invalid message text")
        with self.store.locked() as directory:
            if self.store._read(directory) is not None:
                raise A2AError("delivery already started; reconcile ambiguous send")
            # The durable identity claim is independent of this binding filename,
            # so switching paths cannot create a second economic attempt.
            self.store.claim_economic(
                identity, self.card.fingerprint, self.interface.fingerprint
            )
            data = {"identity": asdict(identity), "message_id": identity.message_id, "card_fingerprint": self.card.fingerprint, "interface_fingerprint": self.interface.fingerprint, "delivery": "send_started", "remote_task_id": None, "remote_context_id": None, "cancel_intent": False, "last_observation": None, "candidates": []}
            self.store._write(directory, data, create=True)
            request = {
                "message": {"messageId": identity.message_id, "role": "ROLE_USER", "parts": [{"text": text}]},
                "configuration": {"returnImmediately": True},
            }
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.send(self.interface, request, HEADER)
            state, task, context, candidates = _parse_response(response, identity)
            data.update(delivery="bound" if task else "direct", remote_task_id=task, remote_context_id=context, last_observation=state)
            if candidates:
                data["candidates"] = _merge_candidate_records(data["candidates"], candidates)
            self.store._write(directory, data)
            return candidates

    def poll(self, identity: Identity) -> tuple[Candidate, ...]:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if data["delivery"] == "direct":
                return tuple(_candidate_from_record(identity, item) for item in data["candidates"])
            if data["delivery"] != "bound":
                raise A2AError("no bound remote task; reconciliation required")
            self.store.require_response_capacity(data)
            request = {"id": data["remote_task_id"], "historyLength": 0}
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.get(self.interface, request, HEADER)
            state, _, _, candidates = _parse_response(
                response, identity, data, allow_bare_task=True
            )
            data["last_observation"] = state
            if candidates:
                data["candidates"] = _merge_candidate_records(data["candidates"], candidates)
            self.store._write(directory, data)
            return candidates

    def recover(self, identity: Identity) -> tuple[Candidate, ...]:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            return tuple(_candidate_from_record(identity, item) for item in data["candidates"])

    def cancel(self, identity: Identity) -> tuple[Candidate, ...]:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if data["delivery"] != "bound":
                raise A2AError("no bound remote task")
            data["cancel_intent"] = True
            self.store._write(directory, data)
        return self.retry_cancel(identity)

    def retry_cancel(self, identity: Identity) -> tuple[Candidate, ...]:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if not data["cancel_intent"] or data["delivery"] != "bound":
                raise A2AError("no durable cancel intent")
            self.store.require_response_capacity(data)
            request = {"id": data["remote_task_id"]}
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.cancel(self.interface, request, HEADER)
            state, _, _, candidates = _parse_response(
                response, identity, data, allow_bare_task=True, discard_history=True
            )
            data["last_observation"] = state
            if candidates:
                data["candidates"] = _merge_candidate_records(data["candidates"], candidates)
            self.store._write(directory, data)
            return candidates


def decode_child_proposal(candidate: Candidate, *, parent_role: str, parent_tools: tuple[str, ...], parent_permissions: tuple[str, ...]) -> ChildProposal:
    """Decode candidate data only. Caller may evaluate; gateway never spawns."""
    if candidate.kind != "artifact":
        raise A2AError("proposal requires artifact")
    parts = candidate.content["parts"]
    if len(parts) != 1 or "text" not in parts[0]:
        raise A2AError("proposal requires one text part")
    raw = json.loads(parts[0]["text"])
    _bounded(raw, 4096)
    proposal = _object(raw, {"child_role", "child_tools", "child_permissions", "child_task"}, {"child_role", "child_tools", "child_permissions", "child_task"})
    for key in ("child_tools", "child_permissions"):
        if not isinstance(proposal[key], list) or len(proposal[key]) > 32:
            raise A2AError("invalid proposal list")
        for item in proposal[key]:
            _id(item, key)
    child_task = proposal["child_task"]
    if not isinstance(child_task, str) or not child_task.strip() or len(child_task.encode("utf-8")) > 8192:
        raise A2AError("invalid child task")
    return ChildProposal(parent_role, parent_tools, _id(proposal["child_role"], "child role"), tuple(proposal["child_tools"]), child_task=child_task, parent_permissions=parent_permissions, child_permissions=tuple(proposal["child_permissions"]))
