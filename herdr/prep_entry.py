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


def consumed_case(record):
    binding = record["case_binding"]
    require(binding["nonce"] == NONCE, "exact_offline_case_required")
    authority = protected_json(CUSTODY / "authority.json")
    marker = protected_json(CUSTODY / ("used-" + NONCE + ".json"))
    state = protected_json(CUSTODY / "state.json")
    require(digest(canonical(authority)) == binding["authority_sha256"] and marker == binding
        and state["binding"] == binding and state["phase"] in {"ADMITTED", "PREPARED"},
        "consumed_admitted_case_binding_required")
    require(type(authority["deadline"]) in (int, float) and
        authority["deadline"] > __import__("time").time() and
        ("deadline" not in record or record["deadline"] <= authority["deadline"]), "offline_case_expired")


def reserve_once(identity_sha256, approval_sha256):
    """Subordinate intent; never a grant. Uncertainty permanently denies retry."""
    parent = os.open(CUSTODY, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(parent)
        require(info.st_uid == 0 and not info.st_mode & 0o077, "private_root_custody_required")
        fd = os.open("native-prep-intent-" + identity_sha256 + ".json",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent)
        try:
            raw = canonical({"identity_sha256": identity_sha256, "approval_sha256": approval_sha256})
            require(os.write(fd, raw) == len(raw), "native_intent_incomplete")
            os.fsync(fd)
        finally: os.close(fd)
        os.fsync(parent)
    finally: os.close(parent)


def main(argv=None):
    args = sys.argv[1:] if argv is None else argv
    if args in ([], ["--help"]):
        print("SOURCE CANDIDATE ONLY: --execute root/child requires exact future root roster and consumed case.")
        return 0
    require((args == ["--execute", "root"] or len(args) == 4 and args[:3] ==
        ["--execute", "child", "--identity-sha256"] and re.fullmatch("[0-9a-f]{64}", args[3]))
        and os.geteuid() == 0, "explicit_root_role_required")
    roster = protected_json(Path("/etc/herdr/offline-03414499dd0d1986/roster.json"))
    helper = roster["preparer"]
    required = {"prep_entry.py", "prep_entry_v2.py", "trusted_prepare.py", "case_roster.py", "preparation_contract.py"}
    require(set(helper["files"]) == required and helper["entrypoint"] == str(Path(__file__).absolute()),
            "exact_preparation_source_closure_required")
    for name, expected in helper["files"].items():
        require(digest(protected_bytes(Path(__file__).with_name(name))) == expected, "preparation_module_changed")
    consumed_case({"case_binding": roster["case_binding"], "deadline": roster["deadline"]})
    sys.path.insert(0, str(Path(__file__).absolute().parent))
    from prep_entry_v2 import run
    return run(args[1], protected_json, protected_bytes, reserve_once,
               identity_sha256=args[3] if len(args) == 4 else None)


if __name__ == "__main__": raise SystemExit(main())
