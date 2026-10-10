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


def _finish_cleanup(actions):
    """Attempt every independent release while retaining the first failure."""
    first = None
    for action in actions:
        try:
            action()
        except BaseException as error:
            if first is None:
                first = (error, error.__traceback__)
    if first is not None:
        raise first[0].with_traceback(first[1])


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


def _verify_root_owned_ancestry(path: Path) -> None:
    """Require every source ancestor to be a non-alias root-controlled inode.

    A readonly bwrap mount of a same-UID-writable directory is NOT immutable:
    the host user can rename or rewrite children after bwrap starts. Trusted
    release trees must therefore live under a root-owned, non-writable chain.
    """
    path = Path(path)
    _require(path.is_absolute() and str(path) == os.path.normpath(str(path))
             and ".." not in path.parts, "immutable root path invalid")
    current = Path("/")
    for component in ("", *path.parts[1:]):
        if component:
            current /= component
        info = os.lstat(current)
        _require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0
                 and not stat.S_IMODE(info.st_mode) & 0o022,
                 "immutable source ancestor not root protected")


def _verify_immutable_entry(info: os.stat_result) -> None:
    _require(info.st_uid == 0 and not stat.S_IMODE(info.st_mode) & 0o022,
             "immutable source entry writable by host user")


@dataclass
class FrozenTree:
    """An approved code tree, either transient or root-owned and immutable."""
    path: Path
    target: Path
    fd: int
    device: int
    inode: int
    source_digest: str
    files: tuple[tuple[str, str], ...]
    max_file_bytes: int = 4_194_304
    immutable_host_source: bool = False

    @property
    def source(self):
        return f"/proc/{os.getpid()}/fd/{self.fd}"

    def verify(self):
        if self.immutable_host_source:
            _verify_root_owned_ancestry(self.path)
        expected_files = {name for name, _ in self.files}
        expected_dirs = {"/".join(name.split("/")[:i]) for name in expected_files
                         for i in range(1, len(name.split("/")))}
        found_files, found_dirs = set(), set()
        def walk(directory_fd, prefix=""):
            for child in os.listdir(directory_fd):
                name = prefix + child
                info = os.stat(child, dir_fd=directory_fd, follow_symlinks=False)
                if self.immutable_host_source:
                    _verify_immutable_entry(info)
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
        if self.immutable_host_source:
            _verify_immutable_entry(held)
            _verify_immutable_entry(named)
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
                if self.immutable_host_source:
                    _verify_immutable_entry(info)
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

    @classmethod
    def attach_immutable(cls, source: Path, *, target: Path,
                         files: Mapping[str, str], max_bytes=33_554_432,
                         max_file_bytes=4_194_304):
        """Pin an operator-published root-owned tree, never a user-writable copy.

        The complete manifest is already approved by the trusted host policy.
        This method verifies bytes/ownership without creating or modifying
        *any* host file; source directory FD remains live until pane cleanup.
        """
        _require(isinstance(files, Mapping) and 0 < len(files) <= 65536
                 and all(isinstance(name, str) and 0 < len(name) <= 1024
                         and isinstance(digest, str) and _SHA.fullmatch(digest)
                         for name, digest in files.items()),
                 "immutable approved manifest invalid")
        _require(type(max_bytes) is int and 0 < max_bytes <= 2_147_483_648
                 and type(max_file_bytes) is int and 0 < max_file_bytes <= 268_435_456,
                 "immutable source bounds invalid")
        source, target = Path(source), Path(target)
        _require(target.is_absolute() and ".." not in target.parts,
                 "immutable mount target invalid")
        _verify_root_owned_ancestry(source)
        fd = os.open(source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            info = os.fstat(fd)
            _verify_immutable_entry(info)
            # Bound the approved published asset before walking or hashing.
            # An unlisted file/dir is rejected by verify(), never ignored.
            total = 0
            for name in sorted(files):
                item_fd = _open_relative(fd, name)
                try:
                    entry = os.fstat(item_fd)
                    _require(stat.S_ISREG(entry.st_mode)
                             and entry.st_size <= max_file_bytes,
                             "immutable published asset file invalid")
                    _verify_immutable_entry(entry)
                    total += entry.st_size
                    _require(total <= max_bytes,
                             "immutable published asset exceeds bound")
                finally:
                    os.close(item_fd)
            result = cls(
                source, target, fd, info.st_dev, info.st_ino,
                hashlib.sha256(canonical_json_bytes(dict(sorted(files.items())))).hexdigest(),
                tuple(sorted(files.items())), max_file_bytes, True,
            )
            result.verify()
            return result
        except BaseException:
            os.close(fd)
            raise

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def cleanup_after_pane_closed(self):
        if self.fd < 0:
            return
        if self.immutable_host_source:
            # Never chmod, unlink or delete an operator-published immutable
            # release tree. The host controller owns publication/retention;
            # the worker only closes its held read-only directory descriptor,
            # even if the independent verification reported root-side drift.
            try:
                self.verify()
            finally:
                self.close()
            return
        try:
            self.verify()
            # Refuse deletion if the named storage directory was replaced.
            for directory in self.path.rglob("*"):
                if directory.is_dir():
                    directory.chmod(0o700)
            self.path.chmod(0o700)
            shutil.rmtree(self.path)
        finally:
            self.close()


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
        modes=set(fields[5].split(","))
        if path in rows:
            rows[path].update(modes)
            rows[path].add("__stacked__")
        else: rows[path]=modes
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
        self.bootstrap = None
        self.private_workspace_pin = None
        self.private_result_pin = None
        self.private_mount_plan = None
        self.private_mount_request = None
        self.private_identity = None
        self.private_cli_pins = {}
        targets = [str(BUNDLE_TARGET), str(code.target), *(str(x.target) for x in runtime)]
        _require(len(targets) == len(set(targets)), "duplicate policy mount target")

    def require_immutable_runtime(self) -> None:
        """Hard activation gate, separate from one-time SHA attestation."""
        _require(all(tree.immutable_host_source for tree in
                     (self.code, *self.runtime)),
                 "private profile requires root-protected runtime sources")
        # Do not trust only a boolean asserted by a caller. Recheck the held
        # read-only inodes and all roots before any sandbox spawn.
        for tree in (self.code, *self.runtime):
            tree.verify()
    def immutable_source_evidence(self):
        self.require_immutable_runtime()
        from .host_bootstrap import read_frozen_file, SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE
        for artifact in (SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE):
            read_frozen_file(self.code, artifact)
        from .private_mount_plan import ApprovedPrivateMountPlan
        _require(isinstance(self.private_mount_plan, ApprovedPrivateMountPlan)
                 and ApprovedPrivateMountPlan.read(self.private_mount_plan.path, self.private_identity)
                     == self.private_mount_plan, "private mount approval unavailable or changed")
        return {
            "schema_version": "herdr-immutable-sources-1",
            "authority": "root-published",
            "trees": {str(tree.target): {"source": str(tree.path),
                      "manifest_sha256": tree.source_digest}
                      for tree in (self.code, *self.runtime)},
            "executables": {name: dict(self.code.files)[name]
                            for name in (SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE)},
            "mount_plan": self.private_mount_plan.evidence(),
        }

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
        if self.bootstrap is not None:
            from .host_bootstrap import HostBootstrap
            _require(isinstance(self.bootstrap,HostBootstrap),"typed host bootstrap required")
            result.extend(self.bootstrap.descriptors())
        return result

    def verify_mounted(self, pid, sealed: SealedPolicyBundle | None = None):
        rows = mount_rows(pid)
        if self.private_workspace_pin is not None:
            from .private_mount_plan import ApprovedPrivateMountPlan
            _require(isinstance(self.private_mount_plan, ApprovedPrivateMountPlan),
                     "private mount plan unavailable")
            self.private_mount_plan.verify_mounted(pid, rows)
        root = Path(f"/proc/{pid}/root")
        for entry in self.descriptors():
            if entry["kind"] == "directory":
                target = Path(entry["target"])
                _require(not any(target in Path(path).parents for path in rows),
                         "unexpected mount below immutable policy/runtime tree")
            path = root / entry["target"].lstrip("/")
            info = path.stat()
            expected_kind = {"file":stat.S_ISREG,"directory":stat.S_ISDIR,
                             "socket":stat.S_ISSOCK}[entry["kind"]]
            _require(expected_kind(info.st_mode)
                     and (info.st_dev, info.st_ino) == (entry["device"], entry["inode"])
                     and "ro" in rows.get(entry["target"], set())
                     and "__stacked__" not in rows.get(entry["target"],set()),
                     "policy mount identity/readonly mismatch")
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
    modern=isinstance(evidence,dict) and evidence.get("schema_version")=="herdr-policy-launch-3"
    if modern: keys.add("bootstrap")
    if isinstance(evidence, dict) and "approved_profile" in evidence:
        keys.add("approved_profile")
        keys.add("immutable_sources")
    _require(isinstance(evidence, dict) and set(evidence) == keys
             and len(canonical_json_bytes(evidence)) <= 16384, "bounded policy evidence required")
    _require(evidence["schema_version"] in {"herdr-policy-launch-2","herdr-policy-launch-3"}
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
    if "approved_profile" in evidence:
        from .private_profile_namespace import profile_identity, PrivateProfileError
        profile = evidence["approved_profile"]
        _require(isinstance(profile, dict)
                 and set(profile) == {"name", "files", "manifest_sha256"}
                 and isinstance(profile["files"], dict),
                 "approved profile evidence malformed")
        try:
            canonical = profile_identity(profile["name"], profile["files"])
        except (PrivateProfileError, TypeError, ValueError) as exc:
            raise SecurityError("approved profile evidence malformed") from exc
        _require(profile == canonical, "approved profile evidence digest mismatch")
        sources = evidence["immutable_sources"]
        from .host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE
        _require(isinstance(sources, dict)
                 and set(sources) == {"schema_version", "authority", "trees", "executables", "mount_plan"}
                 and sources["schema_version"] == "herdr-immutable-sources-1"
                 and sources["authority"] == "root-published"
                 and isinstance(sources["trees"], dict)
                 and set(sources["trees"]) == set(trees)
                 and isinstance(sources["executables"], dict)
                 and set(sources["executables"]) == {SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE}
                 and all(isinstance(v, str) and _SHA.fullmatch(v)
                         for v in sources["executables"].values()),
                 "immutable source evidence malformed")
        plan = sources["mount_plan"]
        from .private_mount_plan import AUTHORITY_ROOT, VERSION
        _require(isinstance(plan, dict)
                 and set(plan) == {"schema_version", "authority", "sha256", "device", "inode"}
                 and plan["schema_version"] == VERSION
                 and isinstance(plan["authority"], str)
                 and Path(plan["authority"]).parent == AUTHORITY_ROOT
                 and Path(plan["authority"]).name == hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json"
                 and isinstance(plan["sha256"], str) and _SHA.fullmatch(plan["sha256"])
                 and all(type(plan[k]) is int and 0 < plan[k] < 2**64 for k in ("device", "inode")),
                 "immutable mount plan evidence malformed")
        for target, source in sources["trees"].items():
            digest = evidence["code_sha256"] if target == str(CODE_TARGET) else runtime[target]
            _require(isinstance(source, dict)
                     and set(source) == {"source", "manifest_sha256"}
                     and isinstance(source["source"], str)
                     and Path(source["source"]).is_absolute()
                     and os.path.normpath(source["source"]) == source["source"]
                     and source["manifest_sha256"] == digest,
                     "immutable source evidence binding mismatch")
    if modern:
        from .host_bootstrap import validate_continuation
        bootstrap=evidence["bootstrap"]
        _require(isinstance(bootstrap,dict) and set(bootstrap)=={"continuation","bootstrap_tree"},
                 "bootstrap proof incomplete")
        validate_continuation(bootstrap["continuation"],identity=identity,
                              bundle_sha256=evidence["bundle_sha256"])
        tree=bootstrap["bootstrap_tree"]
        _require(isinstance(tree,dict) and set(tree)=={"device","inode","source_digest"}
                 and all(type(tree[key]) is int and 0<tree[key]<2**64 for key in ("device","inode"))
                 and isinstance(tree["source_digest"],str) and _SHA.fullmatch(tree["source_digest"]),
                 "bootstrap tree evidence malformed")
    return json.loads(canonical_json_bytes(evidence))


def verify_retained_immutable_sources(proof):
    """Re-establish root publication after restart using the signed manifest hash.

    Reconstructing the manifest here is safe only because its digest and exact
    source inode are already authenticated by the retained launch bundle.
    """
    from .private_mount_plan import ApprovedPrivateMountPlan
    expected = proof["immutable_sources"]["mount_plan"]
    approval = ApprovedPrivateMountPlan.read(Path(expected["authority"]), InvocationIdentity.from_dict(proof["identity"]))
    _require(approval.evidence() == expected, "retained private mount approval changed")
    for target, source in proof["immutable_sources"]["trees"].items():
        path = Path(source["source"])
        _verify_root_owned_ancestry(path)
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        files, total, entries = {}, [0], [0]
        def walk(directory, prefix="", depth=0):
            _require(depth <= 32, "retained immutable source depth exceeds bound")
            for name in os.listdir(directory):
                entries[0] += 1
                _require(entries[0] <= 131072, "retained immutable inventory exceeds bound")
                relative = prefix + name
                info = os.stat(name, dir_fd=directory, follow_symlinks=False)
                _verify_immutable_entry(info)
                if stat.S_ISDIR(info.st_mode):
                    child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                    dir_fd=directory)
                    try:
                        walk(child, relative + "/", depth + 1)
                    finally:
                        os.close(child)
                else:
                    _require(stat.S_ISREG(info.st_mode) and len(files) < 65536
                             and info.st_size <= 268435456,
                             "retained immutable source shape changed")
                    total[0] += info.st_size
                    _require(total[0] <= 2147483648, "retained immutable source exceeds bound")
                    item = _open_relative(fd, relative)
                    try:
                        digest = hashlib.sha256()
                        remaining = info.st_size
                        while remaining:
                            chunk = os.read(item, min(1048576, remaining))
                            _require(bool(chunk), "retained immutable source shortened")
                            digest.update(chunk)
                            remaining -= len(chunk)
                        _require(not os.read(item, 1), "retained immutable source grew")
                        files[relative] = digest.hexdigest()
                    finally:
                        os.close(item)
        try:
            held = os.fstat(fd)
            _require({"device": held.st_dev, "inode": held.st_ino} == proof["tree_identities"][target],
                     "retained immutable source inode changed")
            walk(fd)
            _require(hashlib.sha256(canonical_json_bytes(dict(sorted(files.items())))).hexdigest()
                     == source["manifest_sha256"], "retained immutable source manifest changed")
            if target == str(CODE_TARGET):
                _require(all(files.get(name) == digest for name, digest in
                             proof["immutable_sources"]["executables"].items()),
                         "retained immutable bootstrap executable changed")
        finally:
            os.close(fd)


def process_start_ticks(pid):
    _require(type(pid) is int and pid > 0, "policy process id invalid")
    with Path(f"/proc/{pid}/stat").open("rb") as stream:
        raw = stream.read(4097)
    _require(len(raw) <= 4096, "process stat exceeds bound")
    fields = raw.rpartition(b") ")[2].split()
    _require(len(fields) >= 20 and fields[19].isdigit(), "process stat malformed")
    return int(fields[19])


def verify_retained_policy_evidence(evidence, *, identity, pid, attestation, now=None, require_bootstrap=True):
    """Reopen protected launch proof after restart; never authorize fresh calls."""
    proof = validate_policy_evidence(evidence, identity=identity)
    _require(process_start_ticks(pid) == proof["process_start_ticks"], "policy process was replaced")
    _require(isinstance(attestation, dict) and len(canonical_json_bytes(attestation)) <= 65536
             and attestation.get("task_id") == identity.task_id
             and attestation.get("run_token") == identity.run_token
             and attestation.get("sandbox_pid") == pid
             and hashlib.sha256(canonical_json_bytes(attestation)).hexdigest()
                 == proof["sandbox_attestation_sha256"], "retained attestation mismatch")
    _require(attestation.get("approved_profile") == proof.get("approved_profile"),
             "retained approved profile differs from signed attestation")
    _require(attestation.get("immutable_sources") == proof.get("immutable_sources"),
             "retained immutable sources differ from signed attestation")
    if "approved_profile" in proof:
        verify_retained_immutable_sources(proof)
    rows = mount_rows(pid)
    if "approved_profile" in proof:
        from .private_mount_plan import ApprovedPrivateMountPlan
        ApprovedPrivateMountPlan.read(
            Path(proof["immutable_sources"]["mount_plan"]["authority"]), identity).verify_mounted(pid, rows)
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
                 and "ro" in rows.get(target, set()) and "__stacked__" not in rows.get(target,set()),
                 "retained policy tree identity mismatch")
        _require(not any(path in Path(name).parents for name in rows),
                 "unexpected mount below immutable policy/runtime tree")
    bundle = root / str(BUNDLE_TARGET).lstrip("/")
    fd = os.open(bundle, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        _require(stat.S_ISREG(info.st_mode)
                 and (info.st_dev, info.st_ino) == (proof["bundle_device"],proof["bundle_inode"])
                 and "ro" in rows.get(str(BUNDLE_TARGET),set())
                 and "__stacked__" not in rows.get(str(BUNDLE_TARGET),set()),
                 "retained policy bundle identity mismatch")
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
    if "approved_profile" in proof:
        approved = proof["approved_profile"]
        profile_root = root / "home/agentops/.hermes/profiles" / approved["name"]
        _require("ro" in rows.get("/home/agentops", set())
                 and "ro" in rows.get("/home/agentops/.hermes/profiles/"
                                      + approved["name"] + "/config.yaml", set()),
                 "retained approved profile mount unverified")
        for relative, digest in approved["files"].items():
            target = "/home/agentops/.hermes/profiles/" + approved["name"] + "/" + relative
            _require("ro" in rows.get(target, set()),
                     "retained approved profile file is not readonly")
            file = profile_root / relative
            fd = os.open(file, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                info = os.fstat(fd)
                _require(stat.S_ISREG(info.st_mode) and info.st_size <= 131072,
                         "retained approved profile file shape changed")
                raw = os.read(fd, 131073)
                _require(len(raw) == info.st_size
                         and hashlib.sha256(raw).hexdigest() == digest,
                         "retained approved profile bytes changed")
            finally:
                os.close(fd)
    if require_bootstrap:
        _require(proof["schema_version"]=="herdr-policy-launch-3",
                 "authenticated agent bootstrap proof required")
    if proof["schema_version"]=="herdr-policy-launch-3":
        from .host_bootstrap import verify_retained_bootstrap
        verify_retained_bootstrap(proof,identity=identity,shell_pid=pid)
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


@dataclass(frozen=True)
class ApprovedImmutableTree:
    """Reviewed root-published Hermes/Python code, immutable against host UID.

    This deliberately does not copy source files into agentops-owned storage.
    The host release operator must first publish the complete approved tree
    under a root-owned, non-writable ancestry. No runtime chmod/chown or sudo.
    """
    source: Path
    target: Path
    files: Mapping[str, str]
    max_bytes: int = 33_554_432
    max_file_bytes: int = 4_194_304
    executable_files: tuple[str, ...] | None = None

    def __post_init__(self):
        from types import MappingProxyType
        _require(isinstance(self.source, Path) and self.source.is_absolute(),
                 "immutable approved tree source invalid")
        _require(isinstance(self.target, Path) and self.target.is_absolute(),
                 "immutable approved tree target invalid")
        _require(isinstance(self.files, Mapping) and len(self.files) > 0,
                 "immutable approved tree manifest required")
        object.__setattr__(self, "files", MappingProxyType(dict(self.files)))
        if self.executable_files is not None:
            _require(all(isinstance(name,str) for name in self.executable_files)
                     and set(self.executable_files)<=set(self.files),"immutable executable inventory invalid")
            object.__setattr__(self,"executable_files",tuple(self.executable_files))

    def freeze(self, storage, writable_roots):
        # Avoid path aliases via worker writable roots even when a temporary
        # directory happens to have root ownership. This is a separate
        # root-owned publisher, never a child-created copy.
        path = self.source
        for raw in writable_roots:
            root = Path(raw).absolute()
            _require(not (path == root or root in path.parents),
                     "immutable source overlaps writable workspace")
        tree = FrozenTree.attach_immutable(
            path, target=self.target, files=self.files,
            max_bytes=self.max_bytes, max_file_bytes=self.max_file_bytes,
        )
        try:
            if self.executable_files is not None:
                for name in self.files:
                    fd=_open_relative(tree.fd,name)
                    try:
                        bits=os.fstat(fd).st_mode&0o111
                        _require(bits==(0o111 if name in self.executable_files else 0),
                                 "immutable executable mode differs from approval")
                    finally:os.close(fd)
            return tree
        except BaseException:
            tree.close()
            raise


@dataclass(frozen=True)
class ApprovedProfile:
    """Host-owned, review-bound profile digests (never sourced from a task).

    Only the host launch factory can supply this object. The untrusted agent
    receives neither the authority to approve file hashes nor raw credentials.
    """
    name: str
    source: Path
    files: Mapping[str, str]

    def __post_init__(self):
        from types import MappingProxyType
        from .private_profile_namespace import _PROFILE, _relative, _HEX, _MAX_FILES
        _require(isinstance(self.name, str) and bool(_PROFILE.fullmatch(self.name)),
                 "approved profile name invalid")
        _require(isinstance(self.source, Path) and self.source.is_absolute()
                 and self.source.name == self.name,
                 "approved profile source invalid")
        _require(isinstance(self.files, Mapping)
                 and 2 <= len(self.files) <= _MAX_FILES
                 and {"config.yaml", ".env"} <= set(self.files),
                 "approved profile manifest required")
        for relative, digest in self.files.items():
            _relative(relative)
            _require(isinstance(digest, str) and bool(_HEX.fullmatch(digest)),
                     "approved profile digest invalid")
        object.__setattr__(self, "files", MappingProxyType(dict(self.files)))

    @property
    def identity(self) -> dict[str, object]:
        from .private_profile_namespace import profile_identity
        return profile_identity(self.name, self.files)

    def freeze(self):
        from .private_profile_namespace import PrivateProfileSnapshot
        return PrivateProfileSnapshot.from_approved(
            self.source, name=self.name, approved_sha256=self.files,
        )


_LIVE_PREPARED_LAUNCHES = {}


def _launch_key(identity):
    return canonical_json_bytes(identity.to_json())


class PreparedPolicyLaunch:
    """Private host object retained until the exact owned pane closes."""
    def __init__(self, mount, grant, private_key, key_id, parent=None,
                 private_profile_snapshot=None):
        from .private_profile_namespace import PrivateProfileSnapshot
        _require(private_profile_snapshot is None
                 or isinstance(private_profile_snapshot, PrivateProfileSnapshot),
                 "typed host profile snapshot required")
        self.mount, self.grant = mount, grant
        self.private_profile_snapshot = private_profile_snapshot
        self._private_key, self._key_id, self._parent = private_key, key_id, parent
        self.sealed = None
        self._process_start_ticks = None
        self._bootstrap_receipt = None
        self._published_bootstrap_receipt = None
        self._continuation_sink = None
        self._ownership = None
        if private_profile_snapshot is not None and isinstance(mount, PolicyMount):
            from .private_mount_plan import PinnedLaunchPath
            mount.private_workspace_pin = PinnedLaunchPath(Path(grant.workspace_root), directory=True)
            mount.private_identity = grant.identity

    @property
    def identity(self):
        return self.grant.identity

    def environment(self):
        from .launch_environment import require_clean_environment
        require_clean_environment(os.environ)
        return {key: str(getattr(self.identity, field)) for field, key in IDENTITY_ENV.items()}

    def verify_spawn_source(self, inspect_source):
        from .launch_environment import require_clean_spawn_source
        _require(callable(inspect_source),"host startup source inspector required")
        require_clean_spawn_source(inspect_source())

    def bind_result_slot(self, path, idempotency_key):
        from dataclasses import replace
        from .result_submission import ResultSlot, TOOL, reservation_binding
        _require(self._private_key is not None, "result slot must bind before seal")
        rule = next((rule for rule in self.grant.tool_rules if rule.tool == TOOL), None)
        _require(rule is not None and rule.result_slot is None, "result submission authority required")
        slot = ResultSlot.bind(path, self.identity, idempotency_key)
        if self.private_profile_snapshot is not None:
            from .private_mount_plan import PinnedLaunchPath
            self.mount.private_result_pin = PinnedLaunchPath(
                Path(slot.path), directory=False, expected=(slot.device, slot.inode),
                reservation=reservation_binding(slot))
            self.mount.private_result_pin.verify_reservation()
        self.grant = replace(self.grant, tool_rules=tuple(
            replace(rule,result_slot=slot) if rule.tool == TOOL else rule for rule in self.grant.tool_rules))
        if self._parent is not None:
            self.grant.require_logical_subset_of(self._parent)

    def bind_private_mount_plan(self, path):
        from .private_mount_plan import ApprovedPrivateMountPlan
        _require(self.private_profile_snapshot is not None and self.sealed is None,
                 "private mount plan must bind before seal")
        _require(self.mount.private_mount_plan is None, "private mount plan is one-shot")
        self.mount.private_mount_plan = ApprovedPrivateMountPlan.read(path, self.identity)

    def prepare_private_command(self, builder):
        """Validate the exact approved command while descriptors are still held.

        The caller must do this before creating any pane. Root records remain
        outside worker control; a missing issuer/record is an explicit denial.
        """
        from .private_mount_plan import AUTHORITY_ROOT
        _require(self.private_profile_snapshot is not None and self.sealed is None,
                 "private command must approve before pane creation")
        if self.mount.private_mount_plan is None:
            # Building records a bounded request without starting bwrap. Only
            # its missing-approval denial can lead to reading a root record.
            try:builder()
            except RuntimeError as exc:
                if str(exc)!="durable_private_mount_plan_unapproved":raise
            _require(self.mount.private_mount_request is not None,
                     "exact private mount request unavailable")
            name=hashlib.sha256(canonical_json_bytes(self.identity.to_json())).hexdigest()+".json"
            self.bind_private_mount_plan(AUTHORITY_ROOT/name)
        return builder()

    def seal(self, pid, attestation, *, tools, permissions):
        approved = (self.private_profile_snapshot.identity
                    if self.private_profile_snapshot is not None else None)
        _require(isinstance(attestation, dict)
                 and attestation.get("approved_profile") == approved,
                 "approved profile must match signed sandbox attestation")
        if approved is not None:
            _require(self.mount.private_result_pin is not None,"private result reservation unavailable")
            self.mount.private_result_pin.verify_reservation()
            # Identity-consistent profile is not sufficient if the live host
            # can rewrite imported Hermes/Python code after first attestation.
            self.mount.require_immutable_runtime()
            sources = self.mount.immutable_source_evidence()
            _require("immutable_sources" not in attestation
                     or attestation["immutable_sources"] == sources,
                     "immutable source attestation mismatch")
            attestation["immutable_sources"] = sources
        bound, sealed = self.mount.seal(pid, self.grant, identity=self.identity, attestation=attestation,
                                       tools=tools, permissions=permissions, private_key=self._private_key,
                                       key_id=self._key_id, parent=self._parent)
        self.grant, self.sealed = bound, sealed
        self._process_start_ticks = process_start_ticks(pid)
        self._private_key = None
        _require(self.mount.bootstrap is not None,"immutable host bootstrap unavailable")
        self.mount.bootstrap.register(pid,attestation)
        return self.evidence()

    def set_continuation_sink(self, sink):
        _require(callable(sink) and self._continuation_sink is None,
                 "one durable host continuation sink required")
        self._continuation_sink=sink

    def _observe_bootstrap_continuation(self, receipt):
        _require(callable(self._continuation_sink),"durable host continuation sink unavailable")
        self._bootstrap_receipt=receipt
        try:
            _require(self._continuation_sink(self.evidence()) is True,
                     "durable host continuation publication denied")
            self._published_bootstrap_receipt=receipt
        except BaseException:
            self._bootstrap_receipt=None
            raise

    def arm_bootstrap(self):
        _require(self.mount.bootstrap is not None,"immutable host bootstrap unavailable")
        self.mount.bootstrap.arm()

    def confirm_bootstrap(self):
        _require(self.mount.bootstrap is not None,"immutable host bootstrap unavailable")
        self._bootstrap_receipt=self.mount.bootstrap.confirm()
        if self.private_profile_snapshot is not None:
            self.mount.private_result_pin.verify_reservation()
        return self.evidence()

    def verify_bootstrap(self):
        _require(self._bootstrap_receipt is not None,"authenticated agent bootstrap unavailable")
        _require(self.mount.bootstrap.confirm(timeout_seconds=0) is self._bootstrap_receipt,
                 "authenticated agent bootstrap changed")

    def evidence(self):
        _require(self.sealed is not None, "launch policy is not sealed")
        proof={"schema_version": "herdr-policy-launch-2", "grant_sha256": self.grant.hash,
                "bundle_sha256": self.sealed.sha256, "bundle_device": self.sealed.device,
                "bundle_inode": self.sealed.inode, "code_sha256": self.mount.code.source_digest,
                "runtime_sha256": {str(x.target): x.source_digest for x in self.mount.runtime},
                "tree_identities": {str(x.target): {"device":x.device, "inode":x.inode}
                                    for x in (self.mount.code, *self.mount.runtime)},
                "process_start_ticks": self._process_start_ticks,
                "identity": self.identity.to_json(),
                "sandbox_attestation_sha256": self.grant.runtime_assurance.sandbox_attestation_sha256}
        if self.private_profile_snapshot is not None:
            proof["approved_profile"] = self.private_profile_snapshot.identity
            proof["immutable_sources"] = self.mount.immutable_source_evidence()
        if self._bootstrap_receipt is not None:
            proof["schema_version"]="herdr-policy-launch-3"
            proof["bootstrap"]=self.mount.bootstrap.evidence(self._bootstrap_receipt)
        return proof

    def cleanup_after_pane_closed(self):
        actions = []
        if not getattr(self, "_resources_closed", False):
            for pin in (getattr(self.mount, "private_workspace_pin", None),
                        getattr(self.mount, "private_result_pin", None)):
                if pin is not None:
                    actions.append(pin.close)
            actions.extend(lambda fd=fd: os.close(fd)
                           for fd in getattr(self.mount, "private_cli_pins", {}).values())
            if hasattr(self.mount, "private_cli_pins"):
                self.mount.private_cli_pins = {}
            def release_stage():
                try:
                    self.mount.stage._same_inode()
                    self.mount.stage.path.unlink()
                finally:
                    self.mount.stage.close()
            actions.append(release_stage)
            if self.mount.bootstrap is not None:
                actions.append(self.mount.bootstrap.cleanup_after_pane_closed)
            actions.extend(tree.cleanup_after_pane_closed
                           for tree in (self.mount.code, *self.mount.runtime))
        if self.private_profile_snapshot is not None:
            actions.append(self.private_profile_snapshot.close)
        if self._ownership is not None:
            def release_ownership():
                self._ownership.cleanup_after_pane_closed()
                self._ownership = None
            actions.append(release_ownership)
        try:
            _finish_cleanup(actions)
        finally:
            self._private_key = None
            self._resources_closed = True
            if _LIVE_PREPARED_LAUNCHES.get(_launch_key(self.identity)) is self:
                del _LIVE_PREPARED_LAUNCHES[_launch_key(self.identity)]


class HostPolicyLaunchFactory:
    """Bind an explicit host authorization to independently frozen execution.

    authorize is an in-process host authority, not a callback or identifier from
    a TaskGraph, prompt or queue record. It must return the grant accepted by the
    consumer/provider policy. Missing grants deny before a pane is created.
    """
    def __init__(self, *, code: ApprovedTree | ApprovedImmutableTree,
                 runtime: tuple[ApprovedTree | ApprovedImmutableTree, ...],
                 storage: Path, authorize, writable_roots=(), parent_grant=None,
                 approved_profile: ApprovedProfile | None = None,
                 profile_preflight=None,
                 parent_approved_profile: ApprovedProfile | None = None,
                 parent_launch: PreparedPolicyLaunch | None = None,
                 retained_parent_verify=None):
        approved_types = (ApprovedTree, ApprovedImmutableTree)
        _require(isinstance(code, approved_types) and code.target == CODE_TARGET,
                 "approved policy code required")
        _require(len(runtime) == 2 and all(isinstance(x, approved_types) for x in runtime)
                 and {x.target for x in runtime} == RUNTIME_TARGETS,
                 "approved exact runtime required")
        _require(callable(authorize), "host policy authority required")
        _require(parent_grant is None or isinstance(parent_grant, SecurityGrant),
                 "typed parent grant required")
        _require(approved_profile is None or isinstance(approved_profile, ApprovedProfile),
                 "typed host approved profile required")
        _require(profile_preflight is None or callable(profile_preflight),
                 "typed host profile preflight required")
        _require(parent_approved_profile is None
                 or isinstance(parent_approved_profile, ApprovedProfile),
                 "typed parent host profile approval required")
        _require(parent_launch is None or isinstance(parent_launch, PreparedPolicyLaunch),
                 "typed live parent launch required")
        _require(retained_parent_verify is None or callable(retained_parent_verify),
                 "host retained parent verifier required")
        self.approved_profile = approved_profile
        self.parent_approved_profile = parent_approved_profile
        self.parent_launch = parent_launch
        self.retained_parent_verify = retained_parent_verify
        self.profile_preflight = profile_preflight
        self.code, self.runtime, self.storage = code, tuple(runtime), Path(storage)
        self.authorize, self.writable_roots, self.parent_grant = authorize, tuple(writable_roots), parent_grant

    def prepare_child(self, *, identity: InvocationIdentity, workspace: Path, tools, permissions,
                      owned_write_roots=None):
        tools = tuple(tools)
        _require("herdr_delegate_child" not in tools, "child-bound delegation transport unavailable")
        _require(isinstance(self.parent_grant, SecurityGrant), "accepted host parent grant required")
        if self.approved_profile is not None:
            _require(isinstance(self.parent_approved_profile, ApprovedProfile)
                     and self.parent_approved_profile.identity == self.approved_profile.identity,
                     "child approved profile differs from host parent approval")
            if self.retained_parent_verify is not None:
                parent,profile=self.retained_parent_verify()
                _require(isinstance(parent,SecurityGrant)
                         and parent==self.parent_grant
                         and profile==self.approved_profile.identity,
                         "child approved profile differs from verified retained parent")
            else:
                _require(isinstance(self.parent_launch, PreparedPolicyLaunch)
                     and self.parent_launch.sealed is not None
                     and self.parent_launch.identity == self.parent_grant.identity
                     and self.parent_launch.grant.hash == self.parent_grant.hash
                     and self.parent_launch.private_profile_snapshot is not None,
                         "child approved profile requires accepted live parent launch")
                _require(self.parent_launch.evidence().get("approved_profile")
                     == self.approved_profile.identity,
                         "child approved profile differs from signed parent evidence")
        return self.prepare(identity=identity,workspace=workspace,tools=tools,permissions=permissions,
                            owned_write_roots=owned_write_roots)

    def prepare(self, *, identity: InvocationIdentity, workspace: Path, tools, permissions,
                owned_write_roots=None):
        _require(isinstance(identity, InvocationIdentity), "typed invocation identity required")
        tools, permissions = tuple(tools), tuple(permissions)
        grant = self.authorize(identity=identity, workspace=Path(workspace), tools=tools, permissions=permissions)
        _require(isinstance(grant, SecurityGrant) and grant.identity == identity,
                 "host grant unavailable or mismatched")
        if owned_write_roots is not None:
            from dataclasses import replace
            _require(isinstance(owned_write_roots,tuple) and len(owned_write_roots)<=64
                     and len(set(owned_write_roots))==len(owned_write_roots),"finite owned write roots required")
            roots=tuple(Path(item).absolute() for item in owned_write_roots)
            workspace_root=Path(grant.workspace_root).absolute()
            _require(all(root!=workspace_root and workspace_root in root.parents
                         and root.resolve(strict=True)==root for root in roots),"owned write root outside workspace")
            write_rules=tuple(rule for rule in grant.tool_rules if rule.tool in {"write_file","patch"})
            _require(not write_rules or bool(roots),"file writer has no owned write mount")
            _require(all(any(root==Path(limit) or Path(limit) in root.parents for limit in rule.allowed_roots)
                         for rule in write_rules for root in roots),"owned write root exceeds host rule")
            grant=replace(grant,tool_rules=tuple(
                replace(rule,allowed_roots=tuple(str(root) for root in roots))
                if rule.tool in {"write_file","patch"} else rule for rule in grant.tool_rules))
        _require(set(grant.scope.tools) == set(tools) and set(grant.scope.permissions) <= set(permissions),
                 "host grant exceeds admitted scope")
        path = Path(workspace).absolute()
        root = Path(grant.workspace_root).absolute()
        _require(path == root or root in path.parents, "host grant excludes admitted workspace")
        if self.parent_grant is not None:
            _require(identity.parent_task_id == self.parent_grant.identity.task_id
                     and identity.parent_agent_id == self.parent_grant.identity.agent_id,
                     "host parent grant identity mismatch")
            grant.require_logical_subset_of(self.parent_grant)
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
        from .launch_ownership import LaunchOwnership
        ownership = LaunchOwnership.create(self.storage, identity)
        snapshots, stage, profile_snapshot = [], None, None
        try:
            for definition in (self.code, *self.runtime):
                snapshots.append(definition.freeze(ownership.directory, (*self.writable_roots, path)))
            # A trusted host-owned manifest is the only way to enable the new
            # profile. Bind it after the existing grant/parent admission, never
            # to model-supplied profile hashes or task routing metadata.
            # Credential preflight (including optional refresh) must precede
            # sealing, otherwise a subsequent refresh updates only the live
            # host profile and leaves the immutable child snapshot expired.
            if self.approved_profile is not None:
                _require(callable(self.profile_preflight),
                         "approved profile preflight authority missing")
                _require(self.profile_preflight(self.approved_profile.name) is True,
                         "approved profile preflight denied")
                profile_snapshot = self.approved_profile.freeze()
            import uuid
            stage = stage_policy_bundle(ownership.directory / ("grant-" + uuid.uuid4().hex + ".json"))
            prepared=PreparedPolicyLaunch(PolicyMount(stage, snapshots[0], snapshots[1:]),
                                          grant, Ed25519PrivateKey.generate(), "host-launch", self.parent_grant,
                                          private_profile_snapshot=profile_snapshot)
            prepared._ownership = ownership
            from .host_bootstrap import HostBootstrap
            prepared.mount.bootstrap=HostBootstrap.create(
                prepared,storage=ownership.directory,writable_roots=(*self.writable_roots,path))
            _LIVE_PREPARED_LAUNCHES[_launch_key(identity)] = prepared
            return prepared
        except BaseException:
            actions = []
            if "prepared" in locals():
                for pin in (prepared.mount.private_workspace_pin, prepared.mount.private_result_pin):
                    if pin is not None:
                        actions.append(pin.close)
            if stage is not None:
                actions.extend((stage.close, lambda: stage.path.unlink(missing_ok=True)))
            actions.extend(snapshot.cleanup_after_pane_closed for snapshot in snapshots)
            if profile_snapshot is not None:
                actions.append(profile_snapshot.close)
            actions.append(ownership.cleanup_after_pane_closed)
            try:
                _finish_cleanup(actions)
            except BaseException:
                # The preparation failure remains primary; all closes ran.
                pass
            raise


    def cleanup_orphan(self, identity):
        prepared = _LIVE_PREPARED_LAUNCHES.get(_launch_key(identity))
        if prepared is not None:
            _require(prepared.identity == identity and prepared._ownership.storage == self.storage,
                     "live policy ownership changed")
            prepared.cleanup_after_pane_closed()
            return True
        from .launch_ownership import cleanup_orphan
        return cleanup_orphan(self.storage, identity)
