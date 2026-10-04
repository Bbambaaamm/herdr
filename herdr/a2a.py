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
_ID = re.compile(r"^[A-Za-z0-9._:@/+-]{1,256}$")
_SECRET = re.compile(r"(?i)(secret|password|credential|private.?key|api.?key|access.?token|authorization|cookie|bearer\s|ghp_[a-z0-9]{20,}|sk-[a-z0-9]{20,}|xox[baprs]-)")
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
    if not isinstance(value, str) or not 1 <= len(value) <= 256 or any(ord(c) < 32 for c in value) or _SECRET.search(value):
        raise A2AError(f"invalid {label}")
    return value


def _bounded(value: Any, limit: int) -> bytes:
    try:
        data = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
    except (TypeError, ValueError, OverflowError) as exc:
        raise A2AError("invalid JSON") from exc
    if len(data) > limit or _SECRET.search(data.decode()):
        raise A2AError("oversized or secret-like metadata")
    return data


def _object(value: Any, keys: set[str], required: set[str]) -> Mapping[str, Any]:
    if not isinstance(value, dict) or not required <= value.keys() or value.keys() - keys:
        raise A2AError("invalid object fields")
    return value


def _url(value: Any) -> str:
    if not isinstance(value, str) or len(value) > 2048:
        raise A2AError("invalid interface URL")
    parsed = urlsplit(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment or parsed.query:
        raise A2AError("interface requires a plain HTTPS URL")
    return value


def _interface_address(value: Any, binding: str) -> str:
    if binding != "GRPC":
        return _url(value)
    if not isinstance(value, str) or len(value) > 2048 or _SECRET.search(value):
        raise A2AError("invalid GRPC address")
    if value.startswith("https://"):
        return _url(value)
    if not re.fullmatch(r"[A-Za-z0-9.-]+:[0-9]{1,5}", value):
        raise A2AError("invalid GRPC address")
    host, port = value.rsplit(":", 1)
    if host.startswith("-") or ".." in host or not 1 <= int(port) <= 65535:
        raise A2AError("invalid GRPC address")
    return value


@dataclass(frozen=True)
class Interface:
    url: str
    protocol_binding: str
    tenant: str | None
    protocol_version: str

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(_bounded(asdict(self), MAX_CARD)).hexdigest()


@dataclass(frozen=True)
class AgentCard:
    name: str
    interfaces: tuple[Interface, ...]
    fingerprint: str


def parse_card(raw: Any) -> AgentCard:
    _bounded(raw, MAX_CARD)
    card = _object(raw, {"name", "description", "version", "supportedInterfaces", "capabilities", "skills", "defaultInputModes", "defaultOutputModes", "provider", "documentationUrl", "iconUrl", "securitySchemes", "securityRequirements", "signatures"}, {"name", "description", "version", "supportedInterfaces", "capabilities", "skills", "defaultInputModes", "defaultOutputModes"})
    name = _label(card["name"], "card name")
    _label(card["description"], "description")
    _label(card["version"], "version")
    if not isinstance(card["capabilities"], dict):
        raise A2AError("invalid capabilities")
    if not isinstance(card["skills"], list) or len(card["skills"]) > 32:
        raise A2AError("invalid skills")
    for skill in card["skills"]:
        item = _object(skill, {"id", "name", "description", "tags", "examples", "inputModes", "outputModes", "securityRequirements"}, {"id", "name", "description", "tags"})
        _id(item["id"], "skill id")
        _label(item["name"], "skill name")
        _label(item["description"], "skill description")
        if not isinstance(item["tags"], list) or not item["tags"] or any(not isinstance(tag, str) or not tag for tag in item["tags"]):
            raise A2AError("invalid skill tags")
    for mode_key in ("defaultInputModes", "defaultOutputModes"):
        modes = card[mode_key]
        if not isinstance(modes, list) or not modes or len(modes) > 32 or any(not isinstance(mode, str) or not mode for mode in modes):
            raise A2AError("invalid modes")
    entries = card["supportedInterfaces"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= 8:
        raise A2AError("invalid interfaces")
    interfaces = []
    for item in entries:
        entry = _object(item, {"url", "protocolBinding", "tenant", "protocolVersion"}, {"url", "protocolBinding", "protocolVersion"})
        binding = entry["protocolBinding"]
        if not isinstance(binding, str) or binding not in _BINDINGS or entry["protocolVersion"] != VERSION:
            raise A2AError("unsupported binding/version")
        interfaces.append(Interface(_interface_address(entry["url"], binding), binding, _id(entry["tenant"], "tenant") if "tenant" in entry else None, VERSION))
    return AgentCard(name, tuple(interfaces), hashlib.sha256(_bounded(raw, MAX_CARD)).hexdigest())


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


class BindingStore:
    """Single dispatch binding with durable, serialized state transitions."""
    def __init__(self, path: Path):
        self.path = Path(path)

    @contextlib.contextmanager
    def locked(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        directory = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        lock_name = self.path.name + ".lock"
        try:
            lock = os.open(lock_name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=directory)
            try:
                if not stat.S_ISREG(os.fstat(lock).st_mode):
                    raise A2AError("invalid binding lock")
                fcntl.flock(lock, fcntl.LOCK_EX)
                current = os.stat(lock_name, dir_fd=directory, follow_symlinks=False)
                if (current.st_dev, current.st_ino) != (os.fstat(lock).st_dev, os.fstat(lock).st_ino):
                    raise A2AError("binding lock changed")
                yield directory
            finally:
                os.close(lock)
        finally:
            os.close(directory)

    def _read(self, directory: int) -> dict[str, Any] | None:
        try:
            fd = os.open(self.path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise A2AError("invalid binding path") from exc
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_size > 4096:
                raise A2AError("invalid or oversized binding")
            raw = os.read(fd, 4097)
            if len(raw) > 4096:
                raise A2AError("oversized binding")
            data = json.loads(raw)
        finally:
            os.close(fd)
        _object(data, {"identity", "message_id", "card_fingerprint", "interface_fingerprint", "delivery", "remote_task_id", "remote_context_id", "cancel_intent", "last_observation"}, {"identity", "message_id", "card_fingerprint", "interface_fingerprint", "delivery", "remote_task_id", "remote_context_id", "cancel_intent", "last_observation"})
        identity = Identity(**data["identity"])
        if identity.message_id != data["message_id"] or data["delivery"] not in {"send_started", "bound", "direct"}:
            raise A2AError("invalid binding")
        if not all(isinstance(data[key], str) and re.fullmatch(r"[0-9a-f]{64}", data[key]) for key in ("card_fingerprint", "interface_fingerprint")):
            raise A2AError("invalid binding fingerprint")
        if type(data["cancel_intent"]) is not bool:
            raise A2AError("invalid cancel intent")
        for key in ("remote_task_id", "remote_context_id"):
            if data[key] is not None:
                _id(data[key], key)
        if data["delivery"] == "bound" and not data["remote_task_id"]:
            raise A2AError("invalid remote binding")
        if data["delivery"] != "bound" and data["remote_task_id"] is not None:
            raise A2AError("invalid remote binding")
        if data["last_observation"] is not None and data["last_observation"] not in _STATES | {"direct"}:
            raise A2AError("invalid observation")
        return data

    def read(self) -> dict[str, Any] | None:
        with self.locked() as directory:
            return self._read(directory)

    def _write(self, directory: int, data: dict[str, Any], *, create: bool = False) -> None:
        raw = _bounded(data, 4096)
        tmp = ".a2a-" + uuid.uuid4().hex
        fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
        try:
            with os.fdopen(fd, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            if create:
                try:
                    os.link(tmp, self.path.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
                except FileExistsError as exc:
                    raise A2AError("delivery already started; reconcile ambiguous send") from exc
            else:
                os.replace(tmp, self.path.name, src_dir_fd=directory, dst_dir_fd=directory)
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
        _object(part, {"text", "raw", "url", "data", "mediaType", "filename", "metadata"}, set())
        if sum(k in part for k in ("text", "raw", "url", "data")) != 1:
            raise A2AError("invalid part content")
        if "url" in part:
            _url(part["url"])
        if "text" in part and not isinstance(part["text"], str):
            raise A2AError("invalid text")
        if "raw" in part:
            if not isinstance(part["raw"], str):
                raise A2AError("invalid raw part")
            try:
                base64.b64decode(part["raw"], validate=True)
            except (ValueError, binascii.Error) as exc:
                raise A2AError("invalid base64 raw part") from exc
        if "data" in part:
            _bounded(part["data"], MAX_RESPONSE)
        for field in ("mediaType", "filename"):
            if field in part and (not isinstance(part[field], str) or len(part[field]) > 256):
                raise A2AError("invalid part metadata")
        if "metadata" in part and not isinstance(part["metadata"], dict):
            raise A2AError("invalid part metadata")
    return raw


def _candidate(identity: Identity, task: str | None, context: str | None, kind: str, content: Any) -> Candidate:
    raw = _bounded(content, MAX_RESPONSE)
    return Candidate(identity, task, context, kind, hashlib.sha256(raw).hexdigest(), raw)


def _parse_response(raw: Any, identity: Identity, binding: dict[str, Any] | None = None) -> tuple[str, str | None, str | None, tuple[Candidate, ...]]:
    _bounded(raw, MAX_RESPONSE)
    envelope = _object(raw, {"task", "message"}, set())
    if len(envelope) != 1:
        raise A2AError("expected task or message")
    if "message" in envelope:
        if binding and binding["remote_task_id"]:
            raise A2AError("bound task cannot become direct message")
        msg = _object(envelope["message"], {"messageId", "contextId", "taskId", "role", "parts", "metadata", "extensions", "referenceTaskIds"}, {"messageId", "role", "parts"})
        _id(msg["messageId"], "messageId")
        if msg["role"] != "ROLE_AGENT":
            raise A2AError("expected agent message")
        _parts(msg["parts"])
        if "contextId" not in msg:
            raise A2AError("agent message requires contextId")
        context = _id(msg["contextId"], "contextId")
        if "taskId" in msg:
            _id(msg["taskId"], "taskId")
        return "direct", None, context, (_candidate(identity, None, context, "message", msg),)
    task = _object(envelope["task"], {"id", "contextId", "status", "artifacts", "history", "metadata"}, {"id", "status"})
    task_id = _id(task["id"], "task id")
    context = _id(task["contextId"], "context id") if "contextId" in task else None
    if binding and (binding["remote_task_id"] != task_id or binding["remote_context_id"] != context):
        raise A2AError("remote binding mismatch")
    status = _object(task["status"], {"state", "message", "timestamp"}, {"state"})
    state = status["state"]
    if not isinstance(state, str) or state not in _STATES:
        raise A2AError("invalid task state")
    artifacts = task.get("artifacts", [])
    if not isinstance(artifacts, list) or len(artifacts) > MAX_PARTS:
        raise A2AError("invalid artifacts")
    candidates = []
    for artifact in artifacts:
        item = _object(artifact, {"artifactId", "name", "description", "parts", "metadata", "extensions"}, {"artifactId", "parts"})
        _id(item["artifactId"], "artifactId")
        _parts(item["parts"])
        candidates.append(_candidate(identity, task_id, context, "artifact", item))
    return state, task_id, context, tuple(candidates)


class Gateway:
    def __init__(self, transport: Transport, store: BindingStore, card: AgentCard, policy: Admission):
        self.transport, self.store, self.card, self.policy = transport, store, card, policy
        self.interface = authorize(card, policy)

    def _bound(self, identity: Identity, directory: int) -> dict[str, Any]:
        data = self.store._read(directory)
        if data is None or data["identity"] != asdict(identity) or data["card_fingerprint"] != self.card.fingerprint or data["interface_fingerprint"] != self.interface.fingerprint:
            raise A2AError("local identity or admission mismatch")
        return data

    def send(self, identity: Identity, text: str) -> tuple[Candidate, ...]:
        if not isinstance(text, str) or not text or len(text.encode()) > 8192 or _SECRET.search(text):
            raise A2AError("invalid message text")
        with self.store.locked() as directory:
            if self.store._read(directory) is not None:
                raise A2AError("delivery already started; reconcile ambiguous send")
            data = {"identity": asdict(identity), "message_id": identity.message_id, "card_fingerprint": self.card.fingerprint, "interface_fingerprint": self.interface.fingerprint, "delivery": "send_started", "remote_task_id": None, "remote_context_id": None, "cancel_intent": False, "last_observation": None}
            self.store._write(directory, data, create=True)
            request = {"message": {"messageId": identity.message_id, "role": "ROLE_USER", "parts": [{"text": text}]}}
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.send(self.interface, request, HEADER)
            state, task, context, candidates = _parse_response(response, identity)
            data.update(delivery="bound" if task else "direct", remote_task_id=task, remote_context_id=context, last_observation=state)
            self.store._write(directory, data)
            return candidates

    def poll(self, identity: Identity) -> tuple[Candidate, ...]:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if data["delivery"] != "bound":
                raise A2AError("no bound remote task; reconciliation required")
            request = {"id": data["remote_task_id"]}
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.get(self.interface, request, HEADER)
            state, _, _, candidates = _parse_response(response, identity, data)
            data["last_observation"] = state
            self.store._write(directory, data)
            return candidates

    def cancel(self, identity: Identity) -> None:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if data["delivery"] != "bound":
                raise A2AError("no bound remote task")
            data["cancel_intent"] = True
            self.store._write(directory, data)
        self.retry_cancel(identity)

    def retry_cancel(self, identity: Identity) -> None:
        with self.store.locked() as directory:
            data = self._bound(identity, directory)
            if not data["cancel_intent"] or data["delivery"] != "bound":
                raise A2AError("no durable cancel intent")
            request = {"id": data["remote_task_id"]}
            if self.interface.tenant is not None:
                request["tenant"] = self.interface.tenant
            response = self.transport.cancel(self.interface, request, HEADER)
            state, _, _, _ = _parse_response(response, identity, data)
            data["last_observation"] = state
            self.store._write(directory, data)


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
    return ChildProposal(parent_role, parent_tools, _id(proposal["child_role"], "child role"), tuple(proposal["child_tools"]), child_task=proposal["child_task"], parent_permissions=parent_permissions, child_permissions=tuple(proposal["child_permissions"]))
