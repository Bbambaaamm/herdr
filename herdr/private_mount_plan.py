"""Exact private launch plans issued by the existing root-owned host authority.

The worker can prepare a request. It cannot approve its own descriptors, argv,
or sources: admission requires a stable root-published record outside the repo.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib
import os
from pathlib import Path
import stat

from .security import SecurityError, InvocationIdentity, canonical_json_bytes

AUTHORITY_ROOT = Path("/etc/herdr/launch-plans")
VERSION = "herdr-private-mount-plan-1"


def require(ok, reason):
    if not ok:
        raise SecurityError(reason)


def request_for(identity, descriptors, argv):
    require(isinstance(identity, InvocationIdentity), "private mount invocation required")
    end = argv.index("--")
    writes = sorted(argv[i + 2] for i in range(end - 2) if argv[i] == "--bind-fd")
    return {"schema_version": VERSION, "identity": identity.to_json(),
            "descriptors": descriptors,
            "writable_targets": writes,
            "argv_sha256": hashlib.sha256(canonical_json_bytes(argv)).hexdigest()}


@dataclass(frozen=True)
class ApprovedPrivateMountPlan:
    path: Path
    identity: InvocationIdentity
    sha256: str
    device: int
    inode: int

    @classmethod
    def read(cls, path, identity):
        from .host_configuration import _read_configuration
        path = Path(path)
        require(path.parent == AUTHORITY_ROOT and path.name ==
                hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json",
                "private mount plan outside host authority")
        raw = _read_configuration(path)
        require(set(raw) == {"schema_version", "identity", "descriptors", "argv_sha256", "writable_targets"}
                and raw["schema_version"] == VERSION and raw["identity"] == identity.to_json(),
                "private mount plan identity mismatch")
        info = path.lstat()
        require(0 < info.st_size <= 65536 and len(canonical_json_bytes(raw)) <= 65536,
                "private mount approval exceeds launch bound")
        return cls(path, identity, hashlib.sha256(canonical_json_bytes(raw)).hexdigest(),
                   info.st_dev, info.st_ino)

    def authorize(self, descriptors, argv):
        from .host_configuration import _read_configuration
        current = type(self).read(self.path, self.identity)
        require(current == self, "private mount plan publication changed")
        raw = _read_configuration(self.path)
        named = self.path.lstat()
        require((named.st_dev, named.st_ino) == (self.device, self.inode)
                and hashlib.sha256(canonical_json_bytes(raw)).hexdigest() == self.sha256
                and raw == request_for(self.identity, descriptors, argv),
                "private mount plan differs from root approval")
        return {"schema_version": VERSION, "authority": str(self.path),
                "authority_sha256": self.sha256, "entries": descriptors}

    def evidence(self):
        return {"schema_version": VERSION, "authority": str(self.path),
                "sha256": self.sha256, "device": self.device, "inode": self.inode}

    def verify_mounted(self, pid, rows):
        from .host_configuration import _read_configuration
        from .policy_launch import BUNDLE_TARGET, CODE_TARGET, RUNTIME_TARGETS
        current = type(self).read(self.path, self.identity)
        require(current == self, "private mount plan publication changed")
        raw = _read_configuration(self.path)
        require(hashlib.sha256(canonical_json_bytes(raw)).hexdigest() == self.sha256,
                "private mount plan publication changed")
        authority = {str(BUNDLE_TARGET), str(CODE_TARGET), *map(str, RUNTIME_TARGETS),
                     "/run/herdr-bootstrap", "/run/herdr-policy/bootstrap-authority.sock",
                     "/home/agentops/.local/bin/herdr", "/home/agentops/.local/bin/hermes"}
        for entry in raw["descriptors"]:
            if entry["kind"] == "sealed-profile-data":
                continue
            target = entry["target"]
            info = Path(f"/proc/{pid}/root{target}").stat()
            mode = "rw" if target in raw["writable_targets"] else "ro"
            require(target not in authority or mode == "ro", "private authority mount writable")
            require((info.st_dev, info.st_ino) == (entry["device"], entry["inode"])
                    and mode in rows.get(target, set()) and "__stacked__" not in rows.get(target, set()),
                    "private approved mount inode or mode mismatch")


class PinnedLaunchPath:
    """Open every component without symlinks; retain the exact admitted inode."""
    def __init__(self, path, *, directory, expected=None, reservation=None):
        path = Path(path)
        require(path.is_absolute() and str(path) == os.path.normpath(str(path)),
                "private launch path is not canonical")
        self.logical, self.root, self.directory = path, path.parent, directory
        self.reservation=reservation
        isolated_destination_anchor(path)
        parent = os.open("/", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        from .owned_write_mounts import _mount_id
        anchor_mount_id = _mount_id(parent)
        protected_chain = True
        self.fd = -1
        try:
            for part in path.parts[1:-1]:
                child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                                dir_fd=parent)
                os.close(parent)
                parent = child
                info = os.fstat(parent)
                # The first mutable directory may be a genuine host mount
                # (e.g. /tmp tmpfs). Freeze that boundary's mount identity;
                # every deeper directory and the held source must share it.
                if protected_chain:
                    anchor_mount_id = _mount_id(parent)
                protected_chain = protected_chain and info.st_uid == 0 and not info.st_mode & 0o022
            self.fd = os.open(path.name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC
                              | (os.O_DIRECTORY if directory else 0), dir_fd=parent)
            held = os.fstat(self.fd)
            require(_mount_id(self.fd) == anchor_mount_id,
                    "private launch source is a mount alias below a mutable root")
            require((stat.S_ISDIR(held.st_mode) if directory else stat.S_ISREG(held.st_mode))
                    and held.st_uid == os.geteuid(), "private launch source type or owner mismatch")
            if not directory:
                require(held.st_nlink == 1 and stat.S_IMODE(held.st_mode) == 0o600,
                        "private result source is not an exclusive slot")
            self.device, self.inode = held.st_dev, held.st_ino
            if expected is not None:
                require((self.device, self.inode) == expected, "private result source inode mismatch")
        except BaseException:
            self.close()
            raise
        finally:
            os.close(parent)

    @property
    def source(self):
        return f"/proc/{os.getpid()}/fd/{self.fd}"

    def verify(self):
        held = os.fstat(self.fd)
        require((held.st_dev, held.st_ino) == (self.device, self.inode),
                "private launch held inode changed")

    def descriptor(self):
        self.verify()
        value={"source": self.source, "fd": self.fd, "device": self.device,
                "inode": self.inode, "kind": "directory" if self.directory else "file",
                "target": str(self.logical)}
        if self.reservation is not None:
            self.verify_reservation()
            value.update(kind="reserved-result",reservation=self.reservation)
        return value

    def verify_reservation(self):
        from .result_submission import verify_empty_reservation_fd
        require(self.reservation is not None,"private result reservation unavailable")
        fd=os.open(self.source,os.O_RDONLY|os.O_CLOEXEC|os.O_NONBLOCK)
        try:verify_empty_reservation_fd(fd,self.reservation)
        finally:os.close(fd)

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


def isolated_destination_anchor(path):
    """Mask the first mutable ancestor beneath an immutable host directory.

    Bwrap constructs all deeper names in a fresh tmpfs, so a same-UID rename
    cannot redirect destination resolution through a host-controlled symlink.
    """
    path = Path(path)
    home = Path("/home/agentops")
    sensitive = (home / ".hermes", home / ".ssh", home / ".aws", home / ".gnupg",
                 home / ".config", home / ".kube", Path("/proc"), Path("/dev"), Path("/run"))
    require(path.is_absolute() and str(path) == os.path.normpath(str(path))
            and not any(path == root or root in path.parents for root in sensitive),
            "private launch destination is sensitive")
    if home in path.parents:
        return home
    current = Path("/")
    for part in path.parent.parts[1:]:
        current /= part
        info = current.lstat()
        require(stat.S_ISDIR(info.st_mode), "private destination ancestor is an alias")
        if info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
            require(current != Path("/home"), "private destination anchor is untrusted")
            return current
    require(path.parent not in (Path("/"), Path("/home")), "private destination is too broad")
    return path.parent
