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
    # Directory anchors need traversal and metadata only. O_PATH avoids
    # requiring AppArmor directory read permission on every ancestor.
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
        and state["binding"] == binding and state["phase"] == "START_INTENT",
        "consumed_admitted_case_binding_required")
    require(authority["deadline"] > __import__("time").time(), "offline_case_expired")


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
        print("SOURCE CANDIDATE ONLY. --execute requires exact future root case/plan/preparer approval.")
        return 0
    require(args == ["--execute"] and os.geteuid() == 0, "explicit_root_execution_required")
    record = protected_json(APPROVAL)
    own = Path(__file__).absolute()
    prep = record["preparer"]
    require(record["native_argv"] == [sys.executable, "-I", "-B", str(own), "--execute"]
        and prep["entrypoint"] == str(own) and digest(protected_bytes(own)) == prep["sha256"],
        "exact_native_entrypoint_binding_required")
    require(set(prep["files"]) == {"prep_entry.py", "trusted_prepare.py", "native_preparation.py"},
            "exact_native_module_closure_required")
    for relative, expected in prep["files"].items():
        require(digest(protected_bytes(own.parent / relative)) == expected, "native_module_changed")
    consumed_case(record)
    policy = protected_json(HOST_POLICY)
    require(record["host_policy_sha256"] == digest(json.dumps(policy, sort_keys=True,
        separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()), "original_host_policy_changed")
    # -I intentionally excludes cwd/script dir. Wire only this exact verified
    # directory and the complete original+overlay root-approved code tree.
    code = policy["code"]
    require(len(code["files"]) <= 4096 and Path(code["source"]).is_absolute(), "bounded_full_core_required")
    for relative, expected in code["files"].items():
        require(type(relative) is str and relative and not relative.startswith("/")
            and all(x not in ("", ".", "..") for x in relative.split("/")), "invalid_core_member")
        require(digest(protected_bytes(Path(code["source"]) / relative, 16777216)) == expected,
                "original_or_candidate_core_changed")
    sys.path[:0] = [str(own.parent), str(Path(code["source"]))]
    from herdr import launch_plan_issuer as authority
    from herdr.private_mount_plan import ApprovedPrivateMountPlan
    from herdr.security import InvocationIdentity
    from herdr.native_fd_handoff import _connect
    from herdr.credential_isolation import SYSTEM_RUNTIME_FILES, _approved_confinement, _loaded_profile_sha256
    from herdr.credential_ingress_filter import filter_bytes
    from trusted_prepare import LinuxOps, recipe_from_approved, prepare_and_exec
    from types import SimpleNamespace
    identity = InvocationIdentity.from_dict(record["identity"])
    key = authority._digest(identity.to_json())
    plan = ApprovedPrivateMountPlan.read(authority.publication.AUTHORITY_ROOT / (key + ".json"), identity)
    plan_raw = authority.host._read_configuration(plan.path)
    plan.authorize(plan_raw["descriptors"], record["argv"])
    require(plan.sha256 == record["plan_sha256"] and authority._digest(record["argv"]) == record["argv_sha256"],
            "original_plan_changed")
    require(_loaded_profile_sha256() == _approved_confinement()["loaded_sha256"], "worker_policy_not_approved")
    ops = LinuxOps()
    require(ops.label() == prep["profile"] + " (enforce)", "exact_prep_label_required")
    reserve_once(key, authority._digest(record))
    request = {"schema_version": "herdr-native-preparation-1", "identity_sha256": key,
        "plan_sha256": plan.sha256, "preparation_sha256": authority._digest(record)}
    connection, peer = _connect(60)
    received = []; system_fds = {}
    try:
        with connection:
            packet = authority.canonical_json_bytes(request)
            require(connection.send(packet) == len(packet), "native_request_uncertain")
            answer, received = authority._receive(connection, peer)
        require(answer == {**request, "descriptor_count": len(plan_raw["descriptors"])}
            and len(received) == len(plan_raw["descriptors"]), "native_response_uncertain")
        approval = _approved_confinement()
        for name in sorted(SYSTEM_RUNTIME_FILES):
            # Resolve host distro aliases once, open and hold that regular
            # inode, hash the held FD, and mount only that held FD afterwards.
            source = Path(name).resolve(strict=True)
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            info = os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022,
                    "immutable_system_runtime_required")
            h = hashlib.sha256(); offset = 0
            while offset < info.st_size:
                raw = os.pread(fd, min(65536, info.st_size - offset), offset)
                require(bool(raw) and offset + len(raw) <= 16777216, "system_runtime_hash_bound")
                h.update(raw); offset += len(raw)
            require(h.hexdigest() == approval["system_files"][name], "system_runtime_changed")
            system_fds[name] = {"fd": fd, "device": info.st_dev, "inode": info.st_ino, "sha256": h.hexdigest()}
        def hash_held(fd):
            info = os.fstat(fd)
            require(0 <= info.st_size <= 16777216, "system_runtime_hash_bound")
            value = hashlib.sha256(); offset = 0
            while offset < info.st_size:
                chunk = os.pread(fd, min(65536, info.st_size - offset), offset)
                require(bool(chunk), "system_runtime_short_read")
                value.update(chunk); offset += len(chunk)
            return value.hexdigest()
        from herdr.resolver_namespace import TARGETS as RESOLVER_TARGETS
        api = SimpleNamespace(ApprovedPrivateMountPlan=ApprovedPrivateMountPlan,
            SYSTEM_RUNTIME_FILES=SYSTEM_RUNTIME_FILES, approved_system_files=approval["system_files"],
            RESOLVER_TARGETS=RESOLVER_TARGETS, fd_sha256=hash_held)
        recipe = recipe_from_approved(plan, plan_raw["descriptors"], record["argv"],
                                      identity=identity, api=api, system_fds=system_fds)
        from dataclasses import replace
        mapping = {entry["fd"]: fd for entry, fd in zip(plan_raw["descriptors"], received)}
        recipe = replace(recipe, mounts=tuple(replace(m, fd=mapping[m.fd])
            if m.target not in SYSTEM_RUNTIME_FILES and m.fd in mapping else m for m in recipe.mounts))
        # Use the actual core mapping (consumer/agent/etc), never invented keys.
        from herdr.policy_launch import IDENTITY_ENV
        env = {name: str(getattr(identity, field)) for field, name in IDENTITY_ENV.items()}
        prepare_and_exec(recipe, ops, root="/run/herdr-offline-private-root-03414499dd0d1986/" + key[:16],
            identity_environment=env, safe_environment={"HOME": "/home/agentops", "LANG": "C"},
            filter_program=filter_bytes(), filter_sha256=record["filter_sha256"], prep_profile=prep["profile"])
    finally:
        for fd in [*received, *(row["fd"] for row in system_fds.values())]:
            try: os.close(fd)
            except OSError: pass


if __name__ == "__main__": raise SystemExit(main())
