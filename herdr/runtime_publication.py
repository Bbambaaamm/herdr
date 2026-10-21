"""Operator-only publication of reviewed runtime payloads into new root inodes.

This is a release helper, not a daemon, admission authority, or activation path.
No worker may publish; callers must explicitly run it as a release operator.
"""
from __future__ import annotations
import ctypes
import hashlib
import os
from pathlib import Path
import re
import stat
import tempfile

from .policy_launch import (
    ApprovedTree, FrozenTree, CODE_TARGET, RUNTIME_TARGETS,
    _open_relative, _verify_root_owned_ancestry,
)
from .security import SecurityError, canonical_json_bytes


def require(ok, reason):
    if not ok:
        raise SecurityError(reason)


def copy_reviewed_payload(tree, storage):
    """Copy reviewed bytes into fresh inodes; never adopt/chown a source inode."""
    require(isinstance(tree, ApprovedTree), "typed runtime publication tree required")
    fd = os.open(tree.source, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for name in tree.files:
            item = _open_relative(fd, name)
            try:
                info = os.fstat(item)
                require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1,
                        "runtime publication source alias denied")
            finally:
                os.close(item)
        # Holding the root prevents source-ancestor rename from substituting
        # another tree. create() hashes the independently copied payload.
        copied = FrozenTree.create(
            f"/proc/{os.getpid()}/fd/{fd}/.", target=tree.target,
            files=tree.files, storage=storage, executable_files=tree.executable_files,
            max_bytes=tree.max_bytes, max_file_bytes=tree.max_file_bytes,
        )
        try:
            # Runtime payloads contain no credentials and must be readable by
            # agentops after root creates them. Root ownership and no write
            # bits provide integrity; owner-only 0400/0500 would deny launch.
            for name in tree.files:
                item = _open_relative(copied.fd, name)
                try:
                    os.fchmod(item, 0o555 if name in tree.executable_files else 0o444)
                finally:
                    os.close(item)
            for directory in [*(p for p in copied.path.rglob("*") if p.is_dir()), copied.path]:
                directory.chmod(0o555)
            copied.verify()
            return copied
        except BaseException:
            copied.close()
            raise
    finally:
        os.close(fd)


def _rename_without_replacement(parent_fd, source, destination):
    libc = ctypes.CDLL(None, use_errno=True)
    rename = getattr(libc, "renameat2", None)
    require(rename is not None, "atomic no-replace publication unavailable")
    rename.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint)
    rename.restype = ctypes.c_int
    if rename(parent_fd, os.fsencode(source), parent_fd, os.fsencode(destination), 1):
        error = ctypes.get_errno()
        raise OSError(error, os.strerror(error))


def publish_reviewed_runtime(configuration_path, *, publish=False):
    """Validate a root-approved request by default; publish only explicitly.

    Failures retain the new hidden staging directory for operator diagnosis;
    no existing release, deployment symlink, credential or task store is edited.
    """
    if publish:
        require(os.geteuid() == 0, "runtime publication requires privileged release operator")
    from .host_configuration import _read_configuration, _tree
    raw = _read_configuration(configuration_path)
    require(set(raw) == {"schema_version", "version", "destination", "trees"}
            and raw["schema_version"] == "herdr-runtime-publication-1",
            "closed runtime publication schema required")
    version = raw["version"]
    require(isinstance(version, str) and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,95}", version)
            and version not in {".", ".."}, "runtime publication version invalid")
    require(isinstance(raw["trees"], dict) and set(raw["trees"]) == {"code", "hermes", "python"},
            "complete runtime publication required")
    trees = {name: _tree(value) for name, value in raw["trees"].items()}
    require(trees["code"].target == CODE_TARGET
            and {trees["hermes"].target, trees["python"].target} == RUNTIME_TARGETS,
            "runtime publication targets invalid")
    from .host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE, PYTHON_TARGET, PYTHON_EXECUTABLE
    require(trees["python"].target == PYTHON_TARGET
            and trees["hermes"].target == next(t for t in RUNTIME_TARGETS if t != PYTHON_TARGET),
            "runtime publication role targets invalid")
    require({SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE, "agent-stack/policy-bin/herdr"}
            <= set(trees["code"].files), "complete runtime entrypoints required")
    require({SHIM_SOURCE, "agent-stack/policy-bin/herdr"} <= set(trees["code"].executable_files)
            and PYTHON_EXECUTABLE in trees["python"].files
            and PYTHON_EXECUTABLE in trees["python"].executable_files,
            "runtime executable entrypoint approval required")
    parent = Path(raw["destination"])
    _verify_root_owned_ancestry(parent)
    require(parent != Path("/"), "runtime publication destination too broad")
    if not publish:
        return {"version": version, "destination": str(parent / version), "published": False,
                "approval_sha256": hashlib.sha256(canonical_json_bytes(raw)).hexdigest()}
    parent_fd = os.open(parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        stage = Path(tempfile.mkdtemp(prefix=".runtime-publication-", dir=parent))
        for name, tree in trees.items():
            copied = copy_reviewed_payload(tree, stage)
            try:
                os.rename(copied.path, stage / name)
                copied.path = stage / name
                copied.verify()
                checked = FrozenTree.attach_immutable(
                    copied.path, target=tree.target, files=tree.files,
                    max_bytes=tree.max_bytes, max_file_bytes=tree.max_file_bytes,
                )
                checked.close()
            finally:
                copied.close()
        record = {"schema_version": raw["schema_version"], "version": version,
                  "approval_sha256": hashlib.sha256(canonical_json_bytes(raw)).hexdigest(),
                  "trees": {name: {"source": str(parent / version / name),
                            "manifest_sha256": hashlib.sha256(canonical_json_bytes(
                                dict(sorted(tree.files.items())))).hexdigest()}
                            for name, tree in trees.items()}}
        with (stage / "publication.json").open("xb") as stream:
            stream.write(canonical_json_bytes(record))
            stream.flush()
            os.fchmod(stream.fileno(), 0o444)
            os.fsync(stream.fileno())
        # Persist every directory entry before the atomic version publication.
        for directory in [*(p for p in stage.rglob("*") if p.is_dir()), stage]:
            fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
            try:
                os.fchmod(fd, 0o555)
                os.fsync(fd)
            finally:
                os.close(fd)
        _rename_without_replacement(parent_fd, stage.name, version)
        os.fsync(parent_fd)
        return {**record, "destination": str(parent / version), "published": True}
    finally:
        os.close(parent_fd)
