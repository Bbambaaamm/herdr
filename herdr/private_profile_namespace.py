"""Bounded sealed Hermes profile inputs for an isolated private HOME namespace.

This module does not authorize model execution or deploy a profile. A host
authority must provide trusted exact content digests before using a snapshot.
Host input bytes are copied into sealed anonymous memory, never into a disk
working tree. A sandbox can mount those bytes under a private HOME tmpfs so
the host's mutable ~/.hermes path cannot be substituted mid-session.
"""
from __future__ import annotations

from dataclasses import dataclass
import fcntl
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Mapping

_PROFILE = re.compile(r"[a-z0-9][a-z0-9_-]{0,31}\Z")
_HEX = re.compile(r"[a-f0-9]{64}\Z")
_MAX_FILES = 16
_MAX_FILE_BYTES = 131_072
_MAX_TOTAL_BYTES = 524_288
_HOME = Path("/home/agentops")
_RUNTIME = ("sessions", "cache", "logs", "pastes")
# Linux memfd seal constants (some Python builds omit exported names).
_F_GET_SEALS = getattr(fcntl, "F_GET_SEALS", 1034)
_F_ADD_SEALS = getattr(fcntl, "F_ADD_SEALS", 1033)
_REQUIRED_SEALS = (getattr(fcntl, "F_SEAL_SEAL", 1)
                   | getattr(fcntl, "F_SEAL_SHRINK", 2)
                   | getattr(fcntl, "F_SEAL_GROW", 4)
                   | getattr(fcntl, "F_SEAL_WRITE", 8))


class PrivateProfileError(RuntimeError):
    pass


def _need(ok: bool, reason: str) -> None:
    if not ok:
        raise PrivateProfileError(reason)


def _relative(name: str) -> tuple[str, ...]:
    _need(isinstance(name, str) and 0 < len(name) <= 256, "profile_path_invalid")
    parsed = PurePosixPath(name)
    parts = name.split("/")
    _need(not parsed.is_absolute() and len(parts) <= 8
          and all(part not in ("", ".", "..") and len(part) <= 80 for part in parts)
          and "\\" not in name, "profile_path_invalid")
    # Runtime/storage files must NEVER be reintroduced as frozen inputs.
    _need(parts[0] not in {
        "sessions", "logs", "cache", "pastes", "state.db", ".hermes_history",
        "state.db-wal", "state.db-shm",
    }, "profile_mutable_input_denied")
    return tuple(parts)


def _open_beneath(root_fd: int, name: str) -> int:
    parts = _relative(name)
    parent = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                            dir_fd=parent)
            os.close(parent)
            parent = child
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                     dir_fd=parent)
        return fd
    finally:
        os.close(parent)


@dataclass
class SealedProfileInput:
    relative: str
    fd: int
    size: int
    sha256: str

    def verify(self) -> None:
        _need(self.fd >= 0, "profile_seal_closed")
        info = os.fstat(self.fd)
        _need(stat.S_ISREG(info.st_mode) and info.st_size == self.size,
              "profile_seal_identity_invalid")
        actual = fcntl.fcntl(self.fd, _F_GET_SEALS)
        _need(actual & _REQUIRED_SEALS == _REQUIRED_SEALS,
              "profile_seal_missing")
        _need(hashlib.sha256(os.pread(self.fd, self.size, 0)).hexdigest()
              == self.sha256, "profile_seal_digest_invalid")

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1


@dataclass
class PrivateProfileSnapshot:
    name: str
    files: tuple[SealedProfileInput, ...]
    home: Path = _HOME

    @classmethod
    def from_approved(
        cls, source_profile: Path, *, name: str,
        approved_sha256: Mapping[str, str],
        home: Path = _HOME,
    ) -> "PrivateProfileSnapshot":
        _need(isinstance(name, str) and bool(_PROFILE.fullmatch(name)),
              "profile_name_invalid")
        _need(home == _HOME, "profile_home_policy_invalid")
        _need(isinstance(approved_sha256, Mapping)
              and 2 <= len(approved_sha256) <= _MAX_FILES
              and {"config.yaml", ".env"} <= set(approved_sha256),
              "profile_manifest_invalid")
        for relative, digest in approved_sha256.items():
            _relative(relative)
            _need(isinstance(digest, str) and bool(_HEX.fullmatch(digest)),
                  "profile_manifest_invalid")
        root_fd = os.open(source_profile, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        copies: list[SealedProfileInput] = []
        total = 0
        try:
            root_info = os.fstat(root_fd)
            _need(stat.S_ISDIR(root_info.st_mode), "profile_source_invalid")
            for name_path, expected_digest in sorted(approved_sha256.items()):
                source = _open_beneath(root_fd, name_path)
                try:
                    info = os.fstat(source)
                    _need(stat.S_ISREG(info.st_mode)
                          and 0 <= info.st_size <= _MAX_FILE_BYTES,
                          "profile_source_size_invalid")
                    total += info.st_size
                    _need(total <= _MAX_TOTAL_BYTES, "profile_source_total_exceeded")
                    raw = bytearray()
                    while len(raw) < info.st_size:
                        chunk = os.read(source, min(65536, info.st_size-len(raw)))
                        _need(bool(chunk), "profile_source_short_read")
                        raw.extend(chunk)
                    _need(not os.read(source, 1)
                          and hashlib.sha256(raw).hexdigest() == expected_digest,
                          "profile_source_digest_mismatch")
                    memfd = os.memfd_create("herdr-sealed-profile",
                                           os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
                    try:
                        offset = 0
                        while offset < len(raw):
                            count = os.write(memfd, raw[offset:])
                            _need(count > 0, "profile_seal_write_failed")
                            offset += count
                        os.lseek(memfd, 0, os.SEEK_SET)
                        fcntl.fcntl(memfd, _F_ADD_SEALS, _REQUIRED_SEALS)
                        sealed = SealedProfileInput(name_path, memfd, len(raw), expected_digest)
                        sealed.verify()
                        copies.append(sealed)
                    except BaseException:
                        os.close(memfd)
                        raise
                    finally:
                        raw[:] = bytes(len(raw))
                finally:
                    os.close(source)
            return cls(name, tuple(copies), home)
        except BaseException:
            for item in copies:
                item.close()
            raise
        finally:
            os.close(root_fd)

    @property
    def destination(self) -> Path:
        return self.home / ".hermes/profiles" / self.name

    def mount_arguments(self) -> list[str]:
        """Construct only profile/home mounts; caller must pin code/workspace.

        Mount the entire HOME root privately, under root-owned /home. The
        mutable host ~/.hermes parent and nested profile paths disappear from
        the sandbox namespace. The profile inputs are read-only bwrap copies.
        """
        self.verify()
        parent = os.lstat(self.home.parent)
        _need(stat.S_ISDIR(parent.st_mode) and parent.st_uid == 0
              and not stat.S_IMODE(parent.st_mode) & 0o022,
              "profile_home_anchor_untrusted")
        roots = [
            self.home / ".hermes",
            self.home / ".hermes/profiles",
            self.destination,
        ]
        dirs = [*roots]
        for file in self.files:
            parts = _relative(file.relative)
            for index in range(1, len(parts)):
                folder = self.destination.joinpath(*parts[:index])
                if folder not in dirs:
                    dirs.append(folder)
        args = ["--tmpfs", str(self.home)]
        for path in dirs:
            args.extend(["--dir", str(path)])
        for file in self.files:
            args.extend([
                "--ro-bind-data", str(file.fd), str(self.destination/file.relative),
            ])
        for name in _RUNTIME:
            args.extend(["--dir", str(self.destination/name)])
        return args

    def verify(self) -> None:
        _need(bool(_PROFILE.fullmatch(self.name)) and self.home == _HOME,
              "profile_snapshot_invalid")
        _need(2 <= len(self.files) <= _MAX_FILES
              and {"config.yaml", ".env"} <= {x.relative for x in self.files},
              "profile_snapshot_invalid")
        _need(len({x.relative for x in self.files}) == len(self.files),
              "profile_snapshot_invalid")
        for file in self.files:
            _relative(file.relative)
            file.verify()

    def close(self) -> None:
        for file in self.files:
            file.close()

    def __enter__(self) -> "PrivateProfileSnapshot":
        self.verify()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
