"""Physical host composition of the one-use policy bootstrap.

This host-only object owns frozen bootstrap bytes and a private Unix listener.
Neither the queue record nor a prompt can select its files, socket or authority.
"""
from __future__ import annotations

import hashlib
from datetime import datetime
import json
import os
import shutil
import socket
import stat
import tempfile
import threading
import time
from pathlib import Path

from .bootstrap_authority import (
    BootstrapAuthority, BootstrapAuthorityError, BootstrapExpectation,
    BootstrapContinuation, PeerProcess, inspect_peer,
)
from .security import InvocationIdentity, SecurityError, canonical_json_bytes

BOOTSTRAP_TARGET = Path("/run/herdr-bootstrap")
SOCKET_TARGET = Path("/run/herdr-policy/bootstrap-authority.sock")
SHIM_SOURCE = "agent-stack/policy-bin/hermes"
STAGE1_SOURCE = "agent-stack/bin/agent-hermes-policy-stage1"
STAGE2_SOURCE = "agent-stack/bin/agent-hermes-policy-run"
PYTHON_TARGET = Path("/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu")
PYTHON_EXECUTABLE = "bin/python3.11"


def _require(ok, message):
    if not ok:
        raise SecurityError(message)


def read_frozen_file(tree, name, limit=4_194_304):
    from .policy_launch import _open_relative
    _require(name in dict(tree.files), "bootstrap file is not host-approved")
    fd = _open_relative(tree.fd, name)
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_size <= limit,
                 "bootstrap source must be bounded regular file")
        chunks = []
        remaining = limit + 1
        while remaining:
            part = os.read(fd, min(65536, remaining))
            if not part:
                break
            chunks.append(part)
            remaining -= len(part)
        raw = b"".join(chunks)
        _require(len(raw) <= limit and hashlib.sha256(raw).hexdigest() == dict(tree.files)[name],
                 "bootstrap source differs from host-approved bytes")
        return raw, info.st_dev, info.st_ino
    finally:
        os.close(fd)


def validate_continuation(raw, *, identity: InvocationIdentity, bundle_sha256: str):
    keys = {"schema_version", "identity", "peer_pid", "process_start_ticks",
            "proof_sha256", "stage1_sha256", "stage2_sha256", "python_sha256",
            "bundle_sha256", "python_device", "python_inode"}
    _require(isinstance(raw, dict) and set(raw) == keys
             and raw["schema_version"] == "herdr-bootstrap-continuation-1",
             "complete host bootstrap continuation required")
    try:
        receipt = BootstrapContinuation(**{key: value for key, value in raw.items()
                                         if key != "schema_version"})
    except (BootstrapAuthorityError, TypeError, ValueError) as exc:
        raise SecurityError("malformed host bootstrap continuation") from exc
    _require(dict(receipt.identity) == identity.to_json()
             and receipt.bundle_sha256 == bundle_sha256,
             "bootstrap continuation binding mismatch")
    return receipt


class _DurableBootstrapAuthority(BootstrapAuthority):
    def __init__(self, *, owner, **kwargs):
        self._owner=owner
        super().__init__(**kwargs)

    def _continue(self,key,session,request):
        super()._continue(key,session,request)
        receipt=self.continuation(InvocationIdentity.from_dict(session.expectation.identity))
        try:
            self._owner.launch._observe_bootstrap_continuation(receipt)
        except Exception as exc:
            raise BootstrapAuthorityError("durable bootstrap publication failed") from exc


class HostBootstrap:
    def __init__(self, launch, tree, proof, listener, socket_path, socket_fd):
        self.launch, self.tree, self.proof = launch, tree, proof
        self.listener, self.socket_path, self.socket_fd = listener, socket_path, socket_fd
        info = os.fstat(socket_fd)
        self.socket_identity = (info.st_dev, info.st_ino)
        self.authority = _DurableBootstrapAuthority(
            owner=self, peer_authorizer=self._authorize_peer,
            stage1_path=str(launch.mount.code.target / STAGE1_SOURCE),
        )
        self._stop = threading.Event()
        self._thread = None
        self._armed_ticks = None
        self._claimed_peer = None
        self._shell_pid = self._shell_ticks = None
        self._attestation = None
        self._guard = threading.Lock()
        self.work_authority = None
        self.work_verify = None
        self.work_budget = None

    @classmethod
    def create(cls, launch, *, storage, writable_roots):
        from .policy_launch import FrozenTree
        storage = Path(storage).resolve(strict=True)
        for root in writable_roots:
            root = Path(root).resolve()
            _require(storage != root and root not in storage.parents,
                     "bootstrap storage is worker-writable")
        code, runtime = launch.mount.code, launch.mount.runtime
        shim, _, _ = read_frozen_file(code, SHIM_SOURCE)
        stage1, _, _ = read_frozen_file(code, STAGE1_SOURCE)
        read_frozen_file(code, STAGE2_SOURCE)
        proof = {"schema_version": "herdr-policy-bootstrap-1",
                 "authority": "herdr-host-frozen-tree", "identity": launch.identity.to_json(),
                 "trees": {str(tree.target): {"device": tree.device, "inode": tree.inode,
                           "source_digest": tree.source_digest, "snapshot_kind": "host-frozen-copy"}
                           for tree in (code, *runtime)}}
        source = Path(tempfile.mkdtemp(prefix="bootstrap-source-", dir=storage))
        tree = listener = socket_fd = socket_dir = None
        try:
            items = {"hermes": shim, "agent-hermes-policy-stage1": stage1,
                     "immutable-trees.json": canonical_json_bytes(proof)}
            for name, raw in items.items():
                with (source / name).open("xb") as stream:
                    stream.write(raw)
                    stream.flush()
                    os.fsync(stream.fileno())
            tree = FrozenTree.create(
                source, target=BOOTSTRAP_TARGET,
                files={name: hashlib.sha256(raw).hexdigest() for name, raw in items.items()},
                executable_files=("hermes", "agent-hermes-policy-stage1"),
                storage=storage, writable_roots=writable_roots)
            socket_dir = Path(tempfile.mkdtemp(prefix="bootstrap-broker-", dir=storage))
            socket_path = socket_dir / "s"
            listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            # A proc directory FD keeps AF_UNIX's sockaddr under 108 bytes even
            # when the private operation storage path is long.
            directory_fd = os.open(socket_dir, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                listener.bind(f"/proc/self/fd/{directory_fd}/s")
            finally:
                os.close(directory_fd)
            os.chmod(socket_path, 0o600)
            listener.listen(8)
            listener.settimeout(0.25)
            socket_fd = os.open(socket_path, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC)
            return cls(launch, tree, proof, listener, socket_path, socket_fd)
        except BaseException:
            if socket_fd is not None:
                os.close(socket_fd)
            if listener is not None:
                listener.close()
            if socket_dir is not None:
                (socket_dir / "s").unlink(missing_ok=True)
                socket_dir.rmdir()
            if tree is not None:
                tree.cleanup_after_pane_closed()
            raise
        finally:
            shutil.rmtree(source)

    def descriptors(self):
        self.tree.verify()
        held, named = os.fstat(self.socket_fd), self.socket_path.lstat()
        _require(stat.S_ISSOCK(held.st_mode) and stat.S_ISSOCK(named.st_mode)
                 and (held.st_dev, held.st_ino) == self.socket_identity
                 and (named.st_dev, named.st_ino) == self.socket_identity,
                 "bootstrap broker socket identity changed")
        return [
            {"source": self.tree.source, "fd": self.tree.fd, "device": self.tree.device,
             "inode": self.tree.inode, "kind": "directory", "target": str(BOOTSTRAP_TARGET)},
            {"source": f"/proc/{os.getpid()}/fd/{self.socket_fd}", "fd": self.socket_fd,
             "device": held.st_dev, "inode": held.st_ino,
             "kind": "socket", "target": str(SOCKET_TARGET)},
        ]

    def register(self, shell_pid, attestation):
        from .policy_launch import process_start_ticks
        _require(self.launch.sealed is not None and self._shell_pid is None,
                 "bootstrap requires a newly sealed physical launch")
        from .launch_environment import process_environment, require_clean_environment
        require_clean_environment(process_environment(shell_pid))
        self.launch.mount.verify_mounted(shell_pid, self.launch.sealed)
        self._shell_pid, self._shell_ticks = shell_pid, process_start_ticks(shell_pid)
        self._attestation = json.loads(canonical_json_bytes(attestation))
        python = next(tree for tree in self.launch.mount.runtime if tree.target == PYTHON_TARGET)
        pyraw, pydev, pyino = read_frozen_file(python, PYTHON_EXECUTABLE, 268_435_456)
        # Execute the approved code-tree inode, never the mutable transport copy.
        stage1, dev, ino = read_frozen_file(self.launch.mount.code, STAGE1_SOURCE)
        stage2, _, _ = read_frozen_file(self.launch.mount.code, STAGE2_SOURCE)
        expectation = BootstrapExpectation(
            identity=self.launch.identity.to_json(),
            proof_sha256=hashlib.sha256(canonical_json_bytes(self.proof)).hexdigest(),
            stage1_sha256=hashlib.sha256(stage1).hexdigest(),
            stage2_sha256=hashlib.sha256(stage2).hexdigest(),
            python_sha256=hashlib.sha256(pyraw).hexdigest(),
            bundle_sha256=self.launch.sealed.sha256, parent_pid=shell_pid,
            parent_start_ticks=self._shell_ticks, stage1_device=dev, stage1_inode=ino,
            python_device=pydev, python_inode=pyino,
            valid_until=min(time.time()+59,datetime.fromisoformat(self.launch.grant.expires_at.replace('Z','+00:00')).timestamp()))
        self.authority.register(expectation)
        self._thread = threading.Thread(target=self._serve, name="herdr-host-bootstrap", daemon=True)
        self._thread.start()

    def arm(self):
        _require(self._shell_pid is not None and self._thread is not None
                 and self._thread.is_alive(), "host bootstrap is not registered")
        _require(callable(self.launch._continuation_sink),"durable host continuation sink required")
        with self._guard:
            _require(self._armed_ticks is None, "host bootstrap start already authorized")
            self._armed_ticks = int(time.clock_gettime(time.CLOCK_BOOTTIME) * os.sysconf("SC_CLK_TCK"))

    def _authorize_peer(self, peer: PeerProcess, expected: BootstrapExpectation):
        from .policy_launch import process_start_ticks, IDENTITY_ENV
        with self._guard:
            if (self._armed_ticks is None or self._claimed_peer is not None
                    or peer.start_ticks < self._armed_ticks
                    or peer.ppid != self._shell_pid
                    or process_start_ticks(self._shell_pid) != self._shell_ticks
                    or dict(expected.identity) != self.launch.identity.to_json()):
                return False
            self.launch.mount.verify_mounted(peer.pid, self.launch.sealed)
            for namespace in ("mnt", "pid", "net"):
                if os.readlink(f"/proc/{peer.pid}/ns/{namespace}") != os.readlink(
                        f"/proc/{self._shell_pid}/ns/{namespace}"):
                    return False
            with Path(f"/proc/{peer.pid}/environ").open("rb") as stream:
                raw = stream.read(262145)
            _require(len(raw) <= 262144, "bootstrap environment exceeds bound")
            env = {}
            for item in raw.split(b"\0"):
                if b"=" in item:
                    key, value = item.split(b"=", 1)
                    _require(key not in env, "ambiguous bootstrap identity environment")
                    env[key] = value
            from .launch_environment import require_clean_environment
            require_clean_environment({key.decode("utf-8"):value.decode("utf-8") for key,value in env.items()})
            for field, key in IDENTITY_ENV.items():
                if env.get(key.encode()) != str(getattr(self.launch.identity, field)).encode():
                    return False
            # Exact trusted interpreter, immutable script bytes and argv are
            # independently checked by BootstrapAuthority before this claim.
            # The namespace/mount/identity/start-intent checks bind that safe
            # execution to this physically attested launch, not public markers.
            self._claimed_peer = (peer.pid, peer.start_ticks)
            return True

    def _serve(self):
        while not self._stop.is_set():
            try:
                connection, _ = self.listener.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            from .work_authority import dispatch_work_connection
            if not dispatch_work_connection(self, connection):
                self.authority.dispatch_connection(connection)

    def confirm(self, *, timeout_seconds=10):
        receipt = self.launch._published_bootstrap_receipt or self.authority.wait_for_continuation(
            self.launch.identity, timeout_seconds=timeout_seconds)
        _require(self.launch._published_bootstrap_receipt is receipt,
                 "bootstrap continuation is not durably published")
        peer = inspect_peer(receipt.peer_pid)
        _require(self._claimed_peer == (peer.pid, peer.start_ticks)
                 and (peer.pid, peer.start_ticks) == (receipt.peer_pid, receipt.process_start_ticks)
                 and (peer.exe_device, peer.exe_inode) == (receipt.python_device, receipt.python_inode),
                 "authenticated bootstrap process changed")
        self.launch.mount.verify_mounted(peer.pid, self.launch.sealed)
        return receipt

    def evidence(self, receipt):
        _require(isinstance(receipt, BootstrapContinuation)
                 and (self.launch._published_bootstrap_receipt is receipt
                      or self.authority.continuation(self.launch.identity) is receipt),
                 "host-authenticated continuation receipt required")
        return {"continuation": receipt.to_json(),
                "bootstrap_tree": {"device": self.tree.device, "inode": self.tree.inode,
                                   "source_digest": self.tree.source_digest}}

    def cleanup_after_pane_closed(self):
        from .policy_launch import _finish_cleanup
        if self.socket_fd < 0 and self.tree.fd < 0:
            return
        def stop_listener():
            self._stop.set()
            self.listener.close()
        def join_thread():
            if self._thread is not None:
                self._thread.join(6)
                _require(not self._thread.is_alive(), "bootstrap broker still serving")
        def close_socket():
            if self.socket_fd >= 0:
                os.close(self.socket_fd)
                self.socket_fd = -1
        def unlink_socket():
            # Verify the named socket before unlinking; never remove a replacement.
            try:
                info = self.socket_path.lstat()
            except FileNotFoundError:
                return
            _require((info.st_dev, info.st_ino) == self.socket_identity,
                     "bootstrap broker socket identity changed")
            self.socket_path.unlink()
            self.socket_path.parent.rmdir()
        _finish_cleanup([self.descriptors, stop_listener,
                         lambda: self.authority.close(timeout_seconds=6),
                         join_thread, close_socket, unlink_socket,
                         self.tree.cleanup_after_pane_closed])


def _read_regular(path, limit):
    fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    try:
        info=os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode) and info.st_size<=limit,
                 "retained bootstrap file invalid")
        data=bytearray()
        while len(data)<=limit:
            part=os.read(fd,min(65536,limit+1-len(data)))
            if not part: break
            data.extend(part)
        _require(len(data)<=limit,"retained bootstrap file exceeds bound")
        return bytes(data),info
    finally: os.close(fd)


def verify_retained_bootstrap(proof, *, identity, shell_pid):
    """Reopen the actual authenticated agent, fixed bootstrap and source bytes."""
    from .policy_launch import mount_rows,process_start_ticks,CODE_TARGET,IDENTITY_ENV
    bootstrap=proof["bootstrap"]
    receipt=validate_continuation(bootstrap["continuation"],identity=identity,
                                  bundle_sha256=proof["bundle_sha256"])
    pid=receipt.peer_pid
    _require(process_start_ticks(pid)==receipt.process_start_ticks,
             "authenticated agent process was replaced")
    for namespace in ("mnt","pid","net"):
        _require(os.readlink(f"/proc/{pid}/ns/{namespace}")==os.readlink(
                  f"/proc/{shell_pid}/ns/{namespace}"),
                 "authenticated agent left attested sandbox")
    rows=mount_rows(pid);root=Path(f"/proc/{pid}/root")
    target=str(BOOTSTRAP_TARGET);tree=bootstrap["bootstrap_tree"]
    info=(root/target.lstrip("/")).stat()
    _require(stat.S_ISDIR(info.st_mode)
             and (info.st_dev,info.st_ino)==(tree["device"],tree["inode"])
             and "ro" in rows.get(target,set()) and "__stacked__" not in rows.get(target,set())
             and not any(BOOTSTRAP_TARGET in Path(name).parents for name in rows),
             "retained bootstrap mount changed")
    base=root/target.lstrip("/")
    inventory={}
    with os.scandir(base) as entries:
        for entry in entries:
            _require(entry.name in {"hermes","agent-hermes-policy-stage1","immutable-trees.json"}
                     and len(inventory)<3,"unexpected retained bootstrap entry")
            raw,_=_read_regular(base/entry.name,4_194_304)
            inventory[entry.name]=hashlib.sha256(raw).hexdigest()
    _require(set(inventory)=={"hermes","agent-hermes-policy-stage1","immutable-trees.json"}
             and hashlib.sha256(canonical_json_bytes(dict(sorted(inventory.items())))).hexdigest()==tree["source_digest"],
             "retained bootstrap bytes changed")
    expected_proof={"schema_version":"herdr-policy-bootstrap-1","authority":"herdr-host-frozen-tree",
        "identity":identity.to_json(),"trees":{
            path:{**node,"source_digest":proof["code_sha256"] if path==str(CODE_TARGET)
                  else proof["runtime_sha256"][path],"snapshot_kind":"host-frozen-copy"}
            for path,node in proof["tree_identities"].items()}}
    raw,_=_read_regular(base/"immutable-trees.json",65536)
    _require(raw==canonical_json_bytes(expected_proof)
             and inventory["immutable-trees.json"]==receipt.proof_sha256
             and inventory["agent-hermes-policy-stage1"]==receipt.stage1_sha256
             and not os.path.lexists(base/"no-bytecode-cache"),
             "retained bootstrap authority/identity mismatch")
    raw,_=_read_regular(root/str(CODE_TARGET).lstrip("/")/STAGE2_SOURCE,4_194_304)
    _require(hashlib.sha256(raw).hexdigest()==receipt.stage2_sha256,
             "retained stage-two source changed")
    raw,py=_read_regular(root/str(PYTHON_TARGET).lstrip("/")/PYTHON_EXECUTABLE,268_435_456)
    active=os.stat(f"/proc/{pid}/exe")
    _require((active.st_dev,active.st_ino)==(receipt.python_device,receipt.python_inode)
             and (py.st_dev,py.st_ino)==(receipt.python_device,receipt.python_inode)
             and hashlib.sha256(raw).hexdigest()==receipt.python_sha256,
             "retained authenticated interpreter changed")
    with Path(f"/proc/{pid}/environ").open("rb") as stream: raw=stream.read(262145)
    _require(len(raw)<=262144,"authenticated agent environment exceeds bound")
    env={}
    for entry in raw.split(b"\0"):
        if b"=" in entry:
            key,value=entry.split(b"=",1)
            _require(key not in env,"ambiguous authenticated agent identity")
            env[key]=value
    for field,key in IDENTITY_ENV.items():
        _require(env.get(key.encode())==str(getattr(identity,field)).encode(),
                 "authenticated agent identity mismatch")
    _require(process_start_ticks(pid)==receipt.process_start_ticks,
             "authenticated agent changed during verification")
    return receipt


__all__ = ["HostBootstrap", "BOOTSTRAP_TARGET", "SOCKET_TARGET",
           "validate_continuation", "read_frozen_file", "verify_retained_bootstrap"]
