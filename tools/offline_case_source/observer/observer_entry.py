"""Proposed root prep process entry. Default/--help has zero effects.

Only a future exact root-published native-preparation record and consumed
offline-case binding permit --execute. This source has NOT been authorized
for host execution, installed or physically tested.
"""
from __future__ import annotations
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import stat
import sys

APPROVAL = Path("/etc/herdr/native-preparation.json")
HOST_POLICY = Path("/etc/herdr/host-policy.json")
CUSTODY = Path("/var/lib/herdr-offline-03414499dd0d1986")
NONCE = "03414499dd0d1986968b2393d44275d0"


def require(ok, code):
    if not ok: raise RuntimeError(code)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode()


def digest(raw): return hashlib.sha256(raw).hexdigest()


def protected_bytes(name, maximum=4194304):
    """Whole-path no-follow, root owner/mode, bounded stable bytes."""
    target = Path(name)
    require(target.is_absolute() and ".." not in target.parts, "fixed_absolute_input_required")
    directory = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for component in target.parts[1:-1]:
            opened = os.open(component, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=directory)
            os.close(directory); directory = opened
            info = os.fstat(directory)
            require(info.st_uid == 0 and not info.st_mode & 0o022, "protected_ancestry_required")
        fd = os.open(target.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
        try:
            before = os.fstat(fd)
            require(stat.S_ISREG(before.st_mode) and before.st_uid == 0 and before.st_nlink == 1
                and not before.st_mode & 0o022 and 0 < before.st_size <= maximum, "protected_file_required")
            pieces = []; total = 0
            while total <= maximum:
                raw = os.read(fd, min(65536, maximum + 1 - total))
                if not raw: break
                pieces.append(raw); total += len(raw)
            stamp = lambda x: (x.st_dev, x.st_ino, x.st_mode, x.st_uid, x.st_nlink,
                                x.st_size, x.st_mtime_ns, x.st_ctime_ns)
            result = b"".join(pieces)
            require(len(result) == before.st_size and stamp(before) == stamp(os.fstat(fd)) ==
                    stamp(os.stat(target.name, dir_fd=directory, follow_symlinks=False)), "protected_input_changed")
            return result
        finally: os.close(fd)
    finally: os.close(directory)


def protected_json(name):
    def unique(rows):
        result = {}
        for key, value in rows:
            require(key not in result, "duplicate_root_input_key")
            result[key] = value
        return result
    return json.loads(protected_bytes(name), object_pairs_hook=unique,
                      parse_constant=lambda _x: (_ for _ in ()).throw(RuntimeError("nonfinite_root_input")))


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args in ([], ["--help"]):
        print("SOURCE CANDIDATE ONLY: --serve requires exact future root observer profile/roster.")
        return 0
    require(args == ["--serve"] and os.geteuid() == os.getegid() == 0, "explicit_root_observer_required")
    path = Path("/etc/herdr/offline-03414499dd0d1986/roster.json")
    doc = protected_json(path); helper = doc["observer"]
    required = {"observer_entry.py", "trusted_observer.py", "case_roster.py", "prep_entry.py",
                "metadata_provider.py"}
    require(set(helper["files"]) == required and helper["entrypoint"] == str(Path(__file__).absolute()),
            "exact_observer_source_closure_required")
    require(sys.argv == [helper["entrypoint"], "--serve"] and sys.executable == helper["python"],
            "exact_observer_python_entry_required")
    for name, value in helper["files"].items():
        require(digest(protected_bytes(Path(__file__).with_name(name))) == value, "observer_module_changed")
    policy = protected_json(Path("/etc/herdr/host-policy.json"))
    code = policy["code"]; total = 0
    require(type(code["files"]) is dict and 1 <= len(code["files"]) <= 4096, "bounded_complete_core_required")
    for name, value in code["files"].items():
        require(type(name) is str and name and not name.startswith("/") and
            all(x not in ("", ".", "..") for x in name.split("/")), "canonical_core_member_required")
        raw = protected_bytes(Path(code["source"]) / name, 16777216); total += len(raw)
        require(total <= 201326592 and digest(raw) == value, "approved_core_changed")
    sys.path[:0] = [str(Path(__file__).absolute().parent), code["source"]]
    from herdr.security import InvocationIdentity
    from case_roster import Roster, canonical
    from trusted_observer import LinuxObserverOps, serve
    roster = Roster.parse(canonical(doc), InvocationIdentity)
    require(digest(canonical(policy)) == roster.document["host_policy_sha256"], "original_policy_changed")
    return serve(LinuxObserverOps(protected_json, InvocationIdentity))

if __name__ == '__main__': raise SystemExit(main())
