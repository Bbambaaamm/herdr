"""Host-side one-use bootstrap provenance authority for Herdr #76.

The broker lives outside the model-writable sandbox. Stage one connects over a
host-created Unix socket; SO_PEERCRED plus the registered pane-shell identity
binds the connection to the exact process. The same connected socket survives
execve into stage two, so public environment variables and FD numbers are never
authority by themselves.
"""
from __future__ import annotations

import hashlib
import json
import os
import socket
import stat
import struct
import threading
import math
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping
from types import MappingProxyType
from .security import InvocationIdentity, SecurityError

SOCKET_PATH = Path("/run/herdr-policy/bootstrap-authority.sock")
STAGE1_PATH = "/run/herdr-bootstrap/agent-hermes-policy-stage1"
MAX_MESSAGE = 8192
_SHA256_CHARS = frozenset("0123456789abcdef")


class BootstrapAuthorityError(ValueError):
    pass


def _sha(value: object, name: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != 64
        or any(ch not in _SHA256_CHARS for ch in value)
    ):
        raise BootstrapAuthorityError(f"invalid {name}")
    return value


def _canonical(value: Mapping[str, object]) -> bytes:
    try:
        raw = json.dumps(
            value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BootstrapAuthorityError("invalid bootstrap JSON") from exc
    if len(raw) > MAX_MESSAGE - 1:
        raise BootstrapAuthorityError("bootstrap message exceeds bound")
    return raw


def identity_key(identity: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical(dict(identity))).hexdigest()


@dataclass(frozen=True)
class PeerProcess:
    pid: int
    ppid: int
    start_ticks: int
    exe_device: int
    exe_inode: int
    argv: tuple[str, ...]


@dataclass(frozen=True)
class BootstrapExpectation:
    identity: Mapping[str, object]
    proof_sha256: str
    stage1_sha256: str
    stage2_sha256: str
    python_sha256: str
    bundle_sha256: str
    parent_pid: int
    parent_start_ticks: int
    stage1_device: int
    stage1_inode: int
    python_device: int
    python_inode: int

    def __post_init__(self) -> None:
        try:
            identity=InvocationIdentity.from_dict(self.identity).to_json()
        except (SecurityError,TypeError,ValueError) as exc:
            raise BootstrapAuthorityError("full admitted bootstrap identity required") from exc
        object.__setattr__(self,"identity",MappingProxyType(identity))
        _canonical(dict(self.identity))
        for name in ("proof_sha256", "stage1_sha256", "stage2_sha256", "python_sha256", "bundle_sha256"):
            _sha(getattr(self, name), name)
        for name in ("parent_pid", "parent_start_ticks", "stage1_device", "stage1_inode", "python_device", "python_inode"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise BootstrapAuthorityError(f"invalid {name}")


@dataclass(frozen=True)
class BootstrapContinuation:
    """Host observation of the same authenticated process after verified exec."""
    identity: Mapping[str, object]
    peer_pid: int
    process_start_ticks: int
    proof_sha256: str
    stage1_sha256: str
    stage2_sha256: str
    python_sha256: str
    bundle_sha256: str
    python_device: int
    python_inode: int

    def __post_init__(self):
        try:
            identity = InvocationIdentity.from_dict(self.identity).to_json()
        except (SecurityError, TypeError, ValueError) as exc:
            raise BootstrapAuthorityError("full continuation identity required") from exc
        object.__setattr__(self, "identity", MappingProxyType(identity))
        for name in ("proof_sha256", "stage1_sha256", "stage2_sha256",
                     "python_sha256", "bundle_sha256"):
            _sha(getattr(self, name), name)
        for name in ("peer_pid", "process_start_ticks", "python_device", "python_inode"):
            if type(getattr(self, name)) is not int or getattr(self, name) <= 0:
                raise BootstrapAuthorityError("invalid continuation process identity")

    def to_json(self):
        return {"schema_version": "herdr-bootstrap-continuation-1",
                **{name: (dict(value) if name == "identity" else value)
                   for name, value in self.__dict__.items()}}


@dataclass
class _Session:
    peer_pid: int
    peer_start_ticks: int
    proof_sha256: str
    bundle_sha256: str
    python_device: int
    python_inode: int
    expectation: BootstrapExpectation
    continued: bool = False


def _proc_stat(pid: int) -> tuple[int, int]:
    with Path(f"/proc/{pid}/stat").open("rb") as stream: raw=stream.read(4097)
    if len(raw)>4096: raise BootstrapAuthorityError("process stat exceeds bound")
    raw=raw.decode("utf-8")
    end = raw.rfind(")")
    if end < 0:
        raise BootstrapAuthorityError("malformed process stat")
    fields = raw[end + 2:].split()
    if len(fields) <= 19:
        raise BootstrapAuthorityError("short process stat")
    return int(fields[1]), int(fields[19])


def inspect_peer(pid: int) -> PeerProcess:
    ppid, start_ticks = _proc_stat(pid)
    exe = os.stat(f"/proc/{pid}/exe")
    with Path(f"/proc/{pid}/cmdline").open("rb") as stream: raw=stream.read(16385)
    if len(raw) > 16384:
        raise BootstrapAuthorityError("bootstrap argv exceeds bound")
    try:
        argv = tuple(x.decode("utf-8") for x in raw.split(b"\0") if x)
    except UnicodeDecodeError as exc:
        raise BootstrapAuthorityError("bootstrap argv is not UTF-8") from exc
    if _proc_stat(pid)!=(ppid,start_ticks):
        raise BootstrapAuthorityError("bootstrap process changed during observation")
    return PeerProcess(pid, ppid, start_ticks, exe.st_dev, exe.st_ino, argv)




def inspect_stage1(pid: int, stage1_path: str) -> tuple[int, int, str]:
    """Read the exact stage-one file visible in the peer mount namespace."""
    if not stage1_path.startswith("/"):
        raise BootstrapAuthorityError("stage-one path must be absolute")
    proc_path = f"/proc/{pid}/root{stage1_path}"
    try:
        fd = os.open(proc_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    except OSError as exc:
        raise BootstrapAuthorityError("stage-one file unavailable") from exc
    digest = hashlib.sha256()
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise BootstrapAuthorityError("stage-one file is not regular")
        total = 0
        while True:
            chunk = os.read(fd, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > 4 * 1024 * 1024:
                raise BootstrapAuthorityError("stage-one file exceeds bound")
            digest.update(chunk)
        return info.st_dev, info.st_ino, digest.hexdigest()
    finally:
        os.close(fd)


def _peer_pid(connection: socket.socket) -> int:
    if not hasattr(socket, "SO_PEERCRED"):
        raise BootstrapAuthorityError("SO_PEERCRED unavailable")
    raw = connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, struct.calcsize("3i"))
    pid, _uid, _gid = struct.unpack("3i", raw)
    if pid <= 0:
        raise BootstrapAuthorityError("invalid peer pid")
    return pid


def _recv_line(connection: socket.socket) -> dict[str, object]:
    data = bytearray()
    while len(data) < MAX_MESSAGE:
        chunk = connection.recv(min(1024, MAX_MESSAGE - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in data:
            line, tail = bytes(data).split(b"\n", 1)
            if tail:
                raise BootstrapAuthorityError("multiple bootstrap messages in one read")
            try:
                value = json.loads(line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise BootstrapAuthorityError("malformed bootstrap message") from exc
            if not isinstance(value, dict):
                raise BootstrapAuthorityError("bootstrap message must be object")
            return value
    raise BootstrapAuthorityError("unterminated bootstrap message")


class BootstrapAuthority:
    """One-use registry populated by the host after physical #82 verification."""

    def __init__(
        self,
        *,
        stage0_path: Path = Path("/usr/bin/python3"),
        stage1_path: str = STAGE1_PATH,
        peer_inspector: Callable[[int], PeerProcess] = inspect_peer,
        stage1_inspector: Callable[[int, str], tuple[int, int, str]] = inspect_stage1,
        peer_authorizer: Callable[[PeerProcess, BootstrapExpectation], bool] | None = None,
    ) -> None:
        info = os.stat(stage0_path)
        if not stat.S_ISREG(info.st_mode):
            raise BootstrapAuthorityError("stage-zero interpreter must be regular")
        if not callable(peer_authorizer):
            raise BootstrapAuthorityError("host peer authorizer required")
        self._stage0 = (info.st_dev, info.st_ino)
        self._stage0_path = str(stage0_path)
        self._stage1_path = stage1_path
        self._inspect = peer_inspector
        self._inspect_stage1 = stage1_inspector
        self._authorize_peer = peer_authorizer
        self._expected: dict[str, BootstrapExpectation] = {}
        self._sessions: dict[str, _Session] = {}
        self._consumed: set[str] = set()
        self._lock = threading.Lock()
        self._changed = threading.Condition(self._lock)
        self._continuations: dict[str, BootstrapContinuation] = {}

    def register(self, expectation: BootstrapExpectation) -> str:
        key = identity_key(expectation.identity)
        with self._lock:
            if key in self._expected or key in self._sessions or key in self._consumed:
                raise BootstrapAuthorityError("bootstrap identity already registered or consumed")
            if len(self._expected)+len(self._sessions)+len(self._consumed)>=4096:
                raise BootstrapAuthorityError("bootstrap registry capacity exhausted")
            self._expected[key] = expectation
        return key

    def _begin(
        self, connection: socket.socket, request: Mapping[str, object]
    ) -> tuple[str, _Session]:
        required = {"op", "identity", "proof_sha256", "stage1_sha256", "stage2_sha256", "python_sha256", "bundle_sha256"}
        if set(request) != required or request.get("op") != "stage1":
            raise BootstrapAuthorityError("invalid stage-one request")
        identity = request["identity"]
        if not isinstance(identity, Mapping):
            raise BootstrapAuthorityError("invalid stage-one identity")
        key = identity_key(identity)
        with self._lock:
            expectation = self._expected.get(key)
        if expectation is None or dict(identity) != dict(expectation.identity):
            raise BootstrapAuthorityError("stage-one identity not registered")
        if (
            request["proof_sha256"] != expectation.proof_sha256
            or request["stage1_sha256"] != expectation.stage1_sha256
            or request["stage2_sha256"] != expectation.stage2_sha256
            or request["python_sha256"] != expectation.python_sha256
            or request["bundle_sha256"] != expectation.bundle_sha256
        ):
            raise BootstrapAuthorityError("stage-one digest mismatch")

        pid = _peer_pid(connection)
        peer = self._inspect(pid)
        if peer.pid != pid or peer.ppid != expectation.parent_pid:
            raise BootstrapAuthorityError("stage-one parent process mismatch")
        parent = self._inspect(expectation.parent_pid)
        if parent.start_ticks != expectation.parent_start_ticks:
            raise BootstrapAuthorityError("stage-one parent process was replaced")
        if (peer.exe_device, peer.exe_inode) != self._stage0:
            raise BootstrapAuthorityError("stage-one did not use trusted stage-zero interpreter")
        expected_prefix = (self._stage0_path, "-I", "-S", self._stage1_path)
        if tuple(peer.argv[:4]) != expected_prefix or "-c" in peer.argv[:4]:
            raise BootstrapAuthorityError("stage-one argv mismatch")
        # The host integration (#82) must independently bind this exact peer
        # to the already-attested launch intent/process identity. Merely being
        # a child of the pane shell with readable public digests is not enough.
        try:
            authorized = self._authorize_peer(peer, expectation) is True
        except Exception as exc:
            raise BootstrapAuthorityError("host peer authorization failed") from exc
        if not authorized:
            raise BootstrapAuthorityError("stage-one peer not host-authorized")
        stage1_device, stage1_inode, stage1_sha256 = self._inspect_stage1(pid, self._stage1_path)
        if (
            (stage1_device, stage1_inode) != (expectation.stage1_device, expectation.stage1_inode)
            or stage1_sha256 != expectation.stage1_sha256
        ):
            raise BootstrapAuthorityError("stage-one provenance mismatch")

        session = _Session(
            peer_pid=peer.pid,
            peer_start_ticks=peer.start_ticks,
            proof_sha256=expectation.proof_sha256,
            bundle_sha256=expectation.bundle_sha256,
            python_device=expectation.python_device,
            python_inode=expectation.python_inode,
            expectation=expectation,
        )
        with self._lock:
            if key in self._sessions:
                raise BootstrapAuthorityError("bootstrap identity already claimed")
            self._expected.pop(key, None)
            self._consumed.add(key)
            self._sessions[key] = session
        return key, session

    def _continue(
        self, key: str, session: _Session, request: Mapping[str, object]
    ) -> None:
        if set(request) != {"op", "identity", "proof_sha256", "bundle_sha256"} or request.get("op") != "stage2":
            raise BootstrapAuthorityError("invalid stage-two request")
        identity = request["identity"]
        if not isinstance(identity, Mapping) or identity_key(identity) != key:
            raise BootstrapAuthorityError("stage-two identity mismatch")
        with self._lock:
            current = self._sessions.get(key)
        if current is not session or session.continued:
            raise BootstrapAuthorityError("bootstrap session is not active")

        peer = self._inspect(session.peer_pid)
        if peer.pid != session.peer_pid or peer.start_ticks != session.peer_start_ticks:
            raise BootstrapAuthorityError("stage-two process identity changed")
        if (peer.exe_device, peer.exe_inode) != (session.python_device, session.python_inode):
            raise BootstrapAuthorityError("stage-two interpreter identity mismatch")
        if request["proof_sha256"] != session.proof_sha256:
            raise BootstrapAuthorityError("stage-two proof mismatch")
        if request["bundle_sha256"] != session.bundle_sha256:
            raise BootstrapAuthorityError("stage-two bundle mismatch")
        expected = session.expectation
        receipt = BootstrapContinuation(
            identity=expected.identity, peer_pid=peer.pid,
            process_start_ticks=peer.start_ticks,
            proof_sha256=expected.proof_sha256, stage1_sha256=expected.stage1_sha256,
            stage2_sha256=expected.stage2_sha256, python_sha256=expected.python_sha256,
            bundle_sha256=expected.bundle_sha256, python_device=expected.python_device,
            python_inode=expected.python_inode)
        with self._changed:
            if self._sessions.get(key) is not session or session.continued:
                raise BootstrapAuthorityError("bootstrap session is not active")
            session.continued = True
            self._continuations[key] = receipt
            self._changed.notify_all()

    def handle_connection(self, connection: socket.socket) -> None:
        key: str | None = None
        try:
            begin = _recv_line(connection)
            key, session = self._begin(connection, begin)
            connection.sendall(b"stage1-ok\n")
            cont = _recv_line(connection)
            self._continue(key, session, cont)
            connection.sendall(b"stage2-ok\n")
        except (BootstrapAuthorityError, OSError):
            try:
                connection.sendall(b"denied\n")
            except OSError:
                pass
        finally:
            if key is not None:
                with self._lock:
                    self._sessions.pop(key, None)

    def continuation(self, identity: InvocationIdentity) -> BootstrapContinuation | None:
        if not isinstance(identity, InvocationIdentity):
            raise BootstrapAuthorityError("typed admitted continuation identity required")
        with self._lock:
            return self._continuations.get(identity_key(identity.to_json()))

    def wait_for_continuation(self, identity: InvocationIdentity, *,
                              timeout_seconds: float = 10) -> BootstrapContinuation:
        if (not isinstance(identity, InvocationIdentity)
                or type(timeout_seconds) not in (int, float)
                or not math.isfinite(timeout_seconds) or not 0 <= timeout_seconds <= 60):
            raise BootstrapAuthorityError("bounded continuation wait required")
        key = identity_key(identity.to_json())
        deadline = time.monotonic() + timeout_seconds
        with self._changed:
            while key not in self._continuations:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise BootstrapAuthorityError("authenticated continuation unavailable")
                self._changed.wait(remaining)
            return self._continuations[key]

    def pending(self) -> int:
        with self._lock:
            return len(self._expected)


def serve_bootstrap_authority(listener: socket.socket, authority: BootstrapAuthority) -> None:
    """Serve registered launches; one malformed/disconnected peer never kills the broker."""
    while True:
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(5)
            authority.handle_connection(connection)


__all__ = [
    "BootstrapAuthority",
    "BootstrapAuthorityError",
    "BootstrapExpectation",
    "BootstrapContinuation",
    "PeerProcess",
    "SOCKET_PATH",
    "identity_key",
    "inspect_peer",
    "inspect_stage1",
    "serve_bootstrap_authority",
]
