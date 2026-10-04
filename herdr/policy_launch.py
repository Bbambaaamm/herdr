"""Host-owned frozen code and same-inode policy mounts for managed launches.

Nothing in this module authorizes a task. The caller supplies approved source
digests and a SecurityGrant; actual mount observations replace claimed assurance
before sealing. Keep snapshots until the exact owned pane has been closed.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Mapping

from .security import (
    InvocationIdentity, NetworkAccess, PolicyBundleStage, RuntimeAssurance,
    SecurityError, SecurityGrant, SealedPolicyBundle, canonical_json_bytes,
    stage_policy_bundle, load_policy_bundle,
)

BUNDLE_TARGET = Path("/run/herdr-policy/grant.bundle.json")
CODE_TARGET = Path("/run/herdr/policy-code")
_SHA = re.compile(r"^[a-f0-9]{64}$")
MAX_MOUNT_INFO = 1_048_576
RUNTIME_TARGETS = {
    Path("/home/agentops/.hermes/hermes-agent"),
    Path("/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu"),
}
IDENTITY_ENV = {
    "consumer": "HERDR_POLICY_CONSUMER", "agent_id": "HERDR_POLICY_AGENT_ID",
    "parent_agent_id": "HERDR_POLICY_PARENT_AGENT_ID", "parent_task_id": "HERDR_POLICY_PARENT_TASK_ID",
    "task_id": "HERDR_POLICY_TASK_ID", "run_token": "HERDR_POLICY_RUN_TOKEN",
    "fencing_token": "HERDR_POLICY_FENCING_TOKEN",
}


def _require(ok, code):
    if not ok:
        raise SecurityError(code)


def _open_relative(root_fd, name):
    parts = name.split("/")
    _require(parts and all(x not in {"", ".", ".."} for x in parts) and "\\" not in name,
             "unsafe snapshot source")
    directory = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            os.close(directory)
            directory = child
        return os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    finally:
        os.close(directory)


@dataclass
class FrozenTree:
    """A private copy, not a read-only alias of a mutable worker checkout."""
    path: Path
    target: Path
    fd: int
    device: int
    inode: int
    source_digest: str
    files: tuple[tuple[str, str], ...]
    max_file_bytes: int = 4_194_304

    @property
    def source(self):
        return f"/proc/{os.getpid()}/fd/{self.fd}"

    def verify(self):
        expected_files = {name for name, _ in self.files}
        expected_dirs = {"/".join(name.split("/")[:i]) for name in expected_files
                         for i in range(1, len(name.split("/")))}
        found_files, found_dirs = set(), set()
        def walk(directory_fd, prefix=""):
            for child in os.listdir(directory_fd):
                name = prefix + child
                info = os.stat(child, dir_fd=directory_fd, follow_symlinks=False)
                if stat.S_ISDIR(info.st_mode):
                    _require(name in expected_dirs, "unexpected frozen directory")
                    found_dirs.add(name)
                    fd = os.open(child, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory_fd)
                    try:
                        walk(fd, name + "/")
                    finally:
                        os.close(fd)
                else:
                    _require(stat.S_ISREG(info.st_mode) and name in expected_files,
                             "unexpected frozen file")
                    found_files.add(name)
        walk(self.fd)
        _require(found_files == expected_files and found_dirs == expected_dirs,
                 "frozen inventory differs from approved manifest")
        held, named = os.fstat(self.fd), os.lstat(self.path)
        _require(stat.S_ISDIR(held.st_mode) and stat.S_ISDIR(named.st_mode)
                 and (held.st_dev, held.st_ino) == (self.device, self.inode)
                 and (named.st_dev, named.st_ino) == (self.device, self.inode),
                 "frozen tree identity changed")
        for name, expected in self.files:
            fd = _open_relative(self.fd, name)
            try:
                info = os.fstat(fd)
                _require(stat.S_ISREG(info.st_mode) and info.st_size <= self.max_file_bytes,
                         "frozen source shape changed")
                digest, remaining = hashlib.sha256(), info.st_size
                while remaining:
                    chunk = os.read(fd, min(1_048_576, remaining))
                    _require(bool(chunk), "frozen source shortened")
                    digest.update(chunk)
                    remaining -= len(chunk)
                _require(not os.read(fd, 1) and digest.hexdigest() == expected, "frozen source digest changed")
            finally:
                os.close(fd)

    @classmethod
    def create(cls, source: Path, *, target: Path, files: Mapping[str, str],
               storage: Path, writable_roots=(), executable_files=(), max_bytes=33_554_432,
               max_file_bytes=4_194_304):
        _require(type(max_bytes) is int and 0 < max_bytes <= 2_147_483_648,
                 "snapshot byte bound required")
        _require(type(max_file_bytes) is int and 0 < max_file_bytes <= 268_435_456,
                 "snapshot file bound required")
        _require(isinstance(files, Mapping) and 0 < len(files) <= 65536,
                 "snapshot manifest required")
        _require(all(isinstance(k, str) and len(k) <= 1024
                     and isinstance(v, str) and _SHA.fullmatch(v) for k, v in files.items()),
                 "snapshot manifest shape")
        storage = Path(storage).resolve(strict=True)
        target = Path(target)
        _require(target.is_absolute() and ".." not in target.parts, "snapshot target")
        for root in writable_roots:
            root = Path(root).resolve()
            _require(storage != root and root not in storage.parents, "snapshot worker writable")
        executable_files = set(executable_files)
        _require(executable_files <= set(files), "unknown snapshot executable")
        root_fd = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        path = Path(tempfile.mkdtemp(prefix="herdr-policy-frozen-", dir=storage))
        total = 0
        try:
            for name, expected in sorted(files.items()):
                fd = _open_relative(root_fd, name)
                try:
                    info = os.fstat(fd)
                    _require(stat.S_ISREG(info.st_mode) and info.st_size <= max_file_bytes,
                             "snapshot source must be bounded regular file")
                    total += info.st_size
                    _require(total <= max_bytes, "snapshot byte limit")
                    destination = path.joinpath(*name.split("/"))
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    digest, remaining = hashlib.sha256(), info.st_size
                    with destination.open("xb") as output:
                        while remaining:
                            chunk = os.read(fd, min(remaining, 1_048_576))
                            _require(bool(chunk), "snapshot source shortened")
                            digest.update(chunk)
                            output.write(chunk)
                            remaining -= len(chunk)
                        _require(not os.read(fd, 1) and digest.hexdigest() == expected,
                                 "snapshot source differs from approved bytes")
                        output.flush()
                        os.fsync(output.fileno())
                    destination.chmod(0o500 if name in executable_files else 0o400)
                finally:
                    os.close(fd)
            # Every source pathname is resolved under held no-follow directory
            # descriptors, then the independently copied bytes are checked.
            for directory in sorted((x for x in path.rglob("*") if x.is_dir()),
                                    key=lambda x: len(x.parts), reverse=True):
                directory.chmod(0o500)
            path.chmod(0o500)
            copied_fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            info = os.fstat(copied_fd)
            result = cls(path, target, copied_fd, info.st_dev, info.st_ino,
                         hashlib.sha256(canonical_json_bytes(dict(sorted(files.items())))).hexdigest(),
                         tuple(sorted(files.items())), max_file_bytes)
            result.verify()
            return result
        except BaseException:
            if "copied_fd" in locals():
                os.close(copied_fd)
            for directory in path.rglob("*"):
                if directory.is_dir():
                    directory.chmod(0o700)
            path.chmod(0o700)
            shutil.rmtree(path)
            raise
        finally:
            os.close(root_fd)

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def cleanup_after_pane_closed(self):
        self.verify()
        # Refuse cleanup if the named storage directory was replaced. This
        # method may only be called after the caller proves its pane is closed.
        for directory in self.path.rglob("*"):
            if directory.is_dir():
                directory.chmod(0o700)
        self.path.chmod(0o700)
        self.close()
        shutil.rmtree(self.path)


def mount_rows(pid):
    with Path(f"/proc/{pid}/mountinfo").open("rb") as stream:
        raw = stream.read(MAX_MOUNT_INFO + 1)
    _require(len(raw) <= MAX_MOUNT_INFO, "mount evidence exceeds bound")
    rows = {}
    for line in raw.decode().splitlines():
        fields = line.split(" - ", 1)[0].split()
        _require(len(fields) >= 6, "malformed mount evidence")
        path = fields[4]
        for old, new in ((r"\040", " "), (r"\011", "\t"), (r"\012", "\n"), (r"\134", "\\")):
            path = path.replace(old, new)
        rows[path] = set(fields[5].split(","))
    _require(len(rows) <= 4096, "mount count exceeds bound")
    return rows


class PolicyMount:
    """Pinned grant file and independently frozen code/runtime mount objects."""
    def __init__(self, stage: PolicyBundleStage, code: FrozenTree, runtime=()):
        _require(isinstance(stage, PolicyBundleStage) and isinstance(code, FrozenTree)
                 and code.target == CODE_TARGET and all(isinstance(x, FrozenTree) for x in runtime),
                 "typed policy mount required")
        _require({x.target for x in runtime} == RUNTIME_TARGETS and len(runtime) == 2,
                 "exact immutable Hermes/Python snapshots required")
        self.stage, self.code, self.runtime = stage, code, tuple(runtime)
        targets = [str(BUNDLE_TARGET), str(code.target), *(str(x.target) for x in runtime)]
        _require(len(targets) == len(set(targets)), "duplicate policy mount target")

    def descriptors(self):
        self.stage._same_inode()
        self.code.verify()
        result = [{"source": f"/proc/{os.getpid()}/fd/{self.stage.fd}", "fd": self.stage.fd,
                   "device": self.stage.device, "inode": self.stage.inode,
                   "kind": "file", "target": str(BUNDLE_TARGET)}]
        for tree in (self.code, *self.runtime):
            tree.verify()
            result.append({"source": tree.source, "fd": tree.fd, "device": tree.device,
                           "inode": tree.inode, "kind": "directory", "target": str(tree.target)})
        return result

    def verify_mounted(self, pid, sealed: SealedPolicyBundle | None = None):
        rows = mount_rows(pid)
        root = Path(f"/proc/{pid}/root")
        for entry in self.descriptors():
            if entry["kind"] == "directory":
                target = Path(entry["target"])
                _require(not any(target in Path(path).parents for path in rows),
                         "unexpected mount below immutable policy/runtime tree")
            path = root / entry["target"].lstrip("/")
            info = path.stat()
            expected_kind = stat.S_ISREG if entry["kind"] == "file" else stat.S_ISDIR
            _require(expected_kind(info.st_mode)
                     and (info.st_dev, info.st_ino) == (entry["device"], entry["inode"])
                     and "ro" in rows.get(entry["target"], set()), "policy mount identity/readonly mismatch")
        if sealed is not None:
            _require((sealed.device, sealed.inode) == (self.stage.device, self.stage.inode),
                     "sealed policy inode mismatch")
            with (root / str(BUNDLE_TARGET).lstrip("/")).open("rb") as stream:
                raw = stream.read(131073)
            _require(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == sealed.sha256,
                     "sealed policy mount digest mismatch")
        return rows

    def observed_assurance(self, pid, attestation):
        rows = self.verify_mounted(pid)
        _require("ro" in rows.get("/", set()), "host root is not read-only")
        _require(os.readlink(f"/proc/{pid}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
                 and os.readlink(f"/proc/{pid}/ns/pid") != os.readlink("/proc/self/ns/pid"),
                 "policy process lacks sandbox namespaces")
        same_network = os.readlink(f"/proc/{pid}/ns/net") == os.readlink("/proc/self/ns/net")
        # This launch keeps provider credentials available to Hermes. It never
        # claims isolation from tool-spawned processes or a provider-only firewall.
        return RuntimeAssurance(True, hashlib.sha256(canonical_json_bytes(attestation)).hexdigest(),
                                NetworkAccess.GLOBAL if same_network else NetworkAccess.NONE,
                                tuple(sorted(path for path, modes in rows.items() if "rw" in modes)), False)

    def seal(self, pid, grant: SecurityGrant, *, identity: InvocationIdentity, attestation,
             tools, permissions, private_key, key_id, parent: SecurityGrant | None = None):
        _require(isinstance(grant, SecurityGrant) and grant.identity == identity,
                 "grant differs from admitted identity")
        _require(set(grant.scope.tools) == set(tools) and set(grant.scope.permissions) <= set(permissions),
                 "grant differs from admitted tool/permission scope")
        _require(type(pid) is int and pid > 0, "policy process id invalid")
        with Path(f"/proc/{pid}/environ").open("rb") as stream:
            raw_env = stream.read(262145)
        _require(len(raw_env) <= 262144, "policy process environment exceeds bound")
        env = {}
        for entry in raw_env.split(b"\0"):
            if b"=" in entry:
                key, value = entry.split(b"=", 1)
                _require(key not in env, "ambiguous policy process environment")
                env[key] = value
        for field, key in IDENTITY_ENV.items():
            _require(env.get(key.encode()) == str(getattr(identity, field)).encode(),
                     "policy process identity differs from admitted node")
        _require(isinstance(attestation, dict) and len(canonical_json_bytes(attestation)) <= 65536
                 and attestation.get("task_id") == identity.task_id
                 and attestation.get("run_token") == identity.run_token
                 and attestation.get("sandbox_pid") == pid,
                 "policy sandbox attestation binding")
        assurance = self.observed_assurance(pid, attestation)
        bound = replace(grant, runtime_assurance=assurance)
        if parent is not None:
            bound.require_subset_of(parent)
        if bound.process.enabled:
            _require(assurance.credentials_isolated, "process credential isolation unavailable")
        sealed = self.stage.seal(bound, private_key, key_id=key_id, expected_identity=identity,
                                 expected_attestation_sha256=assurance.sandbox_attestation_sha256)
        self.verify_mounted(pid, sealed)
        return bound, sealed

def validate_policy_evidence(evidence, *, identity: InvocationIdentity):
    keys = {"schema_version", "grant_sha256", "bundle_sha256", "bundle_device", "bundle_inode",
            "code_sha256", "runtime_sha256", "identity", "sandbox_attestation_sha256",
            "tree_identities", "process_start_ticks"}
    _require(isinstance(evidence, dict) and set(evidence) == keys
             and len(canonical_json_bytes(evidence)) <= 16384, "bounded policy evidence required")
    _require(evidence["schema_version"] == "herdr-policy-launch-2"
             and InvocationIdentity.from_dict(evidence["identity"]) == identity,
             "policy evidence identity mismatch")
    for key in ("grant_sha256", "bundle_sha256", "code_sha256", "sandbox_attestation_sha256"):
        _require(isinstance(evidence[key], str) and bool(_SHA.fullmatch(evidence[key])),
                 "policy evidence digest malformed")
    _require(all(type(evidence[key]) is int and 0 <= evidence[key] < 2**64
                 for key in ("bundle_device", "bundle_inode")) and evidence["bundle_inode"] > 0,
             "policy evidence inode malformed")
    runtime = evidence["runtime_sha256"]
    _require(isinstance(runtime, dict) and set(runtime) == set(map(str, RUNTIME_TARGETS))
             and all(isinstance(value, str) and _SHA.fullmatch(value) for value in runtime.values()),
             "policy evidence runtime incomplete")
    trees = evidence["tree_identities"]
    _require(isinstance(trees, dict) and set(trees) == {str(CODE_TARGET), *map(str, RUNTIME_TARGETS)},
             "policy tree identities incomplete")
    for tree in trees.values():
        _require(isinstance(tree, dict) and set(tree) == {"device", "inode"}
                 and all(type(v) is int and 0 <= v < 2**64 for v in tree.values())
                 and tree["inode"] > 0, "policy tree inode malformed")
    _require(type(evidence["process_start_ticks"]) is int
             and 0 < evidence["process_start_ticks"] < 2**64, "policy process identity malformed")
    return json.loads(canonical_json_bytes(evidence))


def process_start_ticks(pid):
    _require(type(pid) is int and pid > 0, "policy process id invalid")
    with Path(f"/proc/{pid}/stat").open("rb") as stream:
        raw = stream.read(4097)
    _require(len(raw) <= 4096, "process stat exceeds bound")
    fields = raw.rpartition(b") ")[2].split()
    _require(len(fields) >= 20 and fields[19].isdigit(), "process stat malformed")
    return int(fields[19])


def verify_retained_policy_evidence(evidence, *, identity, pid, attestation, now=None):
    """Reopen protected launch proof after restart; never authorize fresh calls."""
    proof = validate_policy_evidence(evidence, identity=identity)
    _require(process_start_ticks(pid) == proof["process_start_ticks"], "policy process was replaced")
    _require(isinstance(attestation, dict) and len(canonical_json_bytes(attestation)) <= 65536
             and attestation.get("task_id") == identity.task_id
             and attestation.get("run_token") == identity.run_token
             and attestation.get("sandbox_pid") == pid
             and hashlib.sha256(canonical_json_bytes(attestation)).hexdigest()
                 == proof["sandbox_attestation_sha256"], "retained attestation mismatch")
    rows = mount_rows(pid)
    _require("ro" in rows.get("/", set()), "host root is not read-only")
    _require(os.readlink(f"/proc/{pid}/ns/mnt") != os.readlink("/proc/self/ns/mnt")
             and os.readlink(f"/proc/{pid}/ns/pid") != os.readlink("/proc/self/ns/pid"),
             "policy process lacks sandbox namespaces")
    root = Path(f"/proc/{pid}/root")
    for target, expected in proof["tree_identities"].items():
        path = Path(target)
        info = (root / target.lstrip("/")).stat()
        _require(stat.S_ISDIR(info.st_mode)
                 and (info.st_dev, info.st_ino) == (expected["device"], expected["inode"])
                 and "ro" in rows.get(target, set()), "retained policy tree identity mismatch")
        _require(not any(path in Path(name).parents for name in rows),
                 "unexpected mount below immutable policy/runtime tree")
    bundle = root / str(BUNDLE_TARGET).lstrip("/")
    fd = os.open(bundle, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode)
                 and (info.st_dev, info.st_ino) == (proof["bundle_device"],proof["bundle_inode"])
                 and "ro" in rows.get(str(BUNDLE_TARGET),set()), "retained policy bundle identity mismatch")
        raw = b""
        while len(raw) <= 131072:
            chunk = os.read(fd, 131073-len(raw))
            if not chunk:
                break
            raw += chunk
        _require(len(raw) <= 131072 and hashlib.sha256(raw).hexdigest() == proof["bundle_sha256"],
                 "retained policy bundle digest mismatch")
    finally:
        os.close(fd)
    with Path(f"/proc/{pid}/environ").open("rb") as stream:
        raw_env = stream.read(262145)
    _require(len(raw_env) <= 262144, "policy process environment exceeds bound")
    env = {}
    for entry in raw_env.split(b"\0"):
        if b"=" in entry:
            key,value = entry.split(b"=",1)
            _require(key not in env, "ambiguous policy process environment")
            env[key] = value
    for field,key in IDENTITY_ENV.items():
        _require(env.get(key.encode()) == str(getattr(identity,field)).encode(),
                 "retained process policy identity mismatch")
    grant = load_policy_bundle(bundle,identity,expected_attestation_sha256=proof["sandbox_attestation_sha256"],now=now)
    _require(grant.hash == proof["grant_sha256"], "retained grant digest mismatch")
    assurance = grant.runtime_assurance
    network = (NetworkAccess.GLOBAL if os.readlink(f"/proc/{pid}/ns/net") == os.readlink("/proc/self/ns/net")
               else NetworkAccess.NONE)
    _require(assurance.network_access == network and not assurance.credentials_isolated
             and set(assurance.writable_roots) == {name for name,modes in rows.items() if "rw" in modes},
             "retained runtime assurance mismatch")
    _require(process_start_ticks(pid) == proof["process_start_ticks"], "policy process changed during verification")
    return grant


@dataclass(frozen=True)
class ApprovedTree:
    """Host-approved bytes; never build this manifest from a model request."""
    source: Path
    target: Path
    files: Mapping[str, str]
    executable_files: tuple[str, ...] = ()
    max_bytes: int = 33_554_432
    max_file_bytes: int = 4_194_304

    def __post_init__(self):
        from types import MappingProxyType
        _require(isinstance(self.files, Mapping), "approved file manifest required")
        object.__setattr__(self, "files", MappingProxyType(dict(self.files)))
        object.__setattr__(self, "executable_files", tuple(self.executable_files))

    def freeze(self, storage, writable_roots):
        return FrozenTree.create(self.source, target=self.target, files=self.files,
                                 executable_files=self.executable_files, storage=storage,
                                 writable_roots=writable_roots, max_bytes=self.max_bytes,
                                 max_file_bytes=self.max_file_bytes)


class PreparedPolicyLaunch:
    """Private host object retained until the exact owned pane closes."""
    def __init__(self, mount, grant, private_key, key_id, parent=None):
        self.mount, self.grant = mount, grant
        self._private_key, self._key_id, self._parent = private_key, key_id, parent
        self.sealed = None
        self._process_start_ticks = None

    @property
    def identity(self):
        return self.grant.identity

    def environment(self):
        return {key: str(getattr(self.identity, field)) for field, key in IDENTITY_ENV.items()}

    def seal(self, pid, attestation, *, tools, permissions):
        bound, sealed = self.mount.seal(pid, self.grant, identity=self.identity, attestation=attestation,
                                       tools=tools, permissions=permissions, private_key=self._private_key,
                                       key_id=self._key_id, parent=self._parent)
        self.grant, self.sealed = bound, sealed
        self._process_start_ticks = process_start_ticks(pid)
        self._private_key = None
        return self.evidence()

    def evidence(self):
        _require(self.sealed is not None, "launch policy is not sealed")
        return {"schema_version": "herdr-policy-launch-2", "grant_sha256": self.grant.hash,
                "bundle_sha256": self.sealed.sha256, "bundle_device": self.sealed.device,
                "bundle_inode": self.sealed.inode, "code_sha256": self.mount.code.source_digest,
                "runtime_sha256": {str(x.target): x.source_digest for x in self.mount.runtime},
                "tree_identities": {str(x.target): {"device":x.device, "inode":x.inode}
                                    for x in (self.mount.code, *self.mount.runtime)},
                "process_start_ticks": self._process_start_ticks,
                "identity": self.identity.to_json(),
                "sandbox_attestation_sha256": self.grant.runtime_assurance.sandbox_attestation_sha256}

    def cleanup_after_pane_closed(self):
        # No invocation data, model argument or environment variable selects
        # these paths. The factory created every retained object itself.
        self.mount.stage._same_inode()
        self.mount.stage.close()
        self.mount.stage.path.unlink()
        for tree in (self.mount.code, *self.mount.runtime):
            tree.cleanup_after_pane_closed()
        self._private_key = None


class HostPolicyLaunchFactory:
    """Bind an explicit host authorization to independently frozen execution.

    authorize is an in-process host authority, not a callback or identifier from
    a TaskGraph, prompt or queue record. It must return the grant accepted by the
    consumer/provider policy. Missing grants deny before a pane is created.
    """
    def __init__(self, *, code: ApprovedTree, runtime: tuple[ApprovedTree, ...],
                 storage: Path, authorize, writable_roots=(), parent_grant=None):
        _require(isinstance(code, ApprovedTree) and code.target == CODE_TARGET,
                 "approved policy code required")
        _require(len(runtime) == 2 and all(isinstance(x, ApprovedTree) for x in runtime)
                 and {x.target for x in runtime} == RUNTIME_TARGETS, "approved exact runtime required")
        _require(callable(authorize), "host policy authority required")
        _require(parent_grant is None or isinstance(parent_grant, SecurityGrant),
                 "typed parent grant required")
        self.code, self.runtime, self.storage = code, tuple(runtime), Path(storage)
        self.authorize, self.writable_roots, self.parent_grant = authorize, tuple(writable_roots), parent_grant

    def prepare_child(self, *, identity: InvocationIdentity, workspace: Path, tools, permissions):
        _require(isinstance(self.parent_grant, SecurityGrant), "accepted host parent grant required")
        return self.prepare(identity=identity, workspace=workspace, tools=tools, permissions=permissions)

    def prepare(self, *, identity: InvocationIdentity, workspace: Path, tools, permissions):
        _require(isinstance(identity, InvocationIdentity), "typed invocation identity required")
        tools, permissions = tuple(tools), tuple(permissions)
        grant = self.authorize(identity=identity, workspace=Path(workspace), tools=tools, permissions=permissions)
        _require(isinstance(grant, SecurityGrant) and grant.identity == identity,
                 "host grant unavailable or mismatched")
        _require(set(grant.scope.tools) == set(tools) and set(grant.scope.permissions) <= set(permissions),
                 "host grant exceeds admitted scope")
        path = Path(workspace).absolute()
        root = Path(grant.workspace_root).absolute()
        _require(path == root or root in path.parents, "host grant excludes admitted workspace")
        if self.parent_grant is not None:
            _require(identity.parent_task_id == self.parent_grant.identity.task_id
                     and identity.parent_agent_id == self.parent_grant.identity.agent_id,
                     "host parent grant identity mismatch")
            grant.require_subset_of(self.parent_grant)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        snapshots, stage = [], None
        try:
            for definition in (self.code, *self.runtime):
                snapshots.append(definition.freeze(self.storage, (*self.writable_roots, path)))
            import uuid
            stage = stage_policy_bundle(self.storage / ("grant-" + uuid.uuid4().hex + ".json"))
            return PreparedPolicyLaunch(PolicyMount(stage, snapshots[0], snapshots[1:]),
                                        grant, Ed25519PrivateKey.generate(), "host-launch", self.parent_grant)
        except BaseException:
            if stage is not None:
                stage.close()
                stage.path.unlink(missing_ok=True)
            for snapshot in snapshots:
                snapshot.cleanup_after_pane_closed()
            raise
