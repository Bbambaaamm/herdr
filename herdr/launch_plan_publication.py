"""Publish one explicitly approved private launch plan through the host authority.

This operator helper accepts only root-protected approval tickets. It never
promotes a worker proposal, renews an approval, or starts a service or agent.
"""
from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tempfile

from .private_mount_plan import AUTHORITY_ROOT, VERSION, request_for
from .runtime_publication import _rename_without_replacement
from .policy_launch import _verify_root_owned_ancestry
from .security import InvocationIdentity, SecurityError, canonical_json_bytes

APPROVAL_ROOT = Path("/etc/herdr/launch-plan-approvals")
TICKET_VERSION = "herdr-private-mount-issuance-1"
MAX_PLAN = 65536
MAX_TICKET = 131072


def require(condition, reason):
    if not condition:
        raise SecurityError(reason)


def _utc_now():
    return datetime.now(UTC)


def _window(ticket):
    dates = []
    for name in ("not_before", "expires_at"):
        value = ticket[name]
        require(isinstance(value, str), "approval window must use explicit timestamps")
        try:
            value = datetime.fromisoformat(value)
        except ValueError as exc:
            raise SecurityError("approval window timestamp invalid") from exc
        require(value.tzinfo is not None, "approval window must be timezone aware")
        dates.append(value)
    start, end = dates
    require(0 < (end - start).total_seconds() <= 3600, "approval window exceeds one hour")
    require(start <= _utc_now() < end, "approval window is not active")


def _target(value):
    return (isinstance(value, str) and "\0" not in value and value.startswith("/") and not value.startswith("//")
            and value != "/" and str(PurePosixPath(value)) == value
            and ".." not in PurePosixPath(value).parts)


def _shape(plan, argv, identity):
    require(set(plan) == {"schema_version", "identity", "descriptors", "argv_sha256", "writable_targets"}
            and plan["schema_version"] == VERSION, "closed private plan required")
    require(isinstance(argv, list) and 1 <= len(argv) <= 4096
            and all(isinstance(arg, str) and "\0" not in arg for arg in argv)
            and len(canonical_json_bytes(argv)) <= 32768
            and argv[0] == "/usr/bin/bwrap" and "--" in argv,
            "bounded exact bwrap command required")
    entries = plan["descriptors"]
    require(isinstance(entries, list) and 1 <= len(entries) <= 96, "bounded descriptor inventory required")
    mapping, targets = {}, set()
    ordinary = {"source", "fd", "device", "inode", "kind", "target"}
    identity_sha = hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest()
    for entry in entries:
        require(isinstance(entry, dict), "descriptor object required")
        kind = entry.get("kind")
        extra = ({"sha256", "size"} if kind == "sealed-profile-data"
                 else {"reservation"} if kind == "reserved-result" else set())
        require(isinstance(kind, str) and kind in {"file", "directory", "socket", "sealed-profile-data", "reserved-result"}
                and set(entry) == ordinary | extra
                and all(type(entry[key]) is int and entry[key] >= 0 for key in ("fd", "device", "inode"))
                and isinstance(entry["source"], str)
                and re.fullmatch(r"/proc/[1-9][0-9]{0,9}/fd/[0-9]{1,10}", entry["source"])
                and entry["source"].rsplit("/", 1)[-1] == str(entry["fd"])
                and _target(entry["target"]) and entry["fd"] not in mapping
                and entry["target"] not in targets, "descriptor shape or alias invalid")
        if kind == "sealed-profile-data":
            require(type(entry["size"]) is int and 0 <= entry["size"] <= 131072
                    and isinstance(entry["sha256"], str)
                    and re.fullmatch(r"[a-f0-9]{64}", entry["sha256"]), "sealed descriptor digest invalid")
        if kind == "reserved-result":
            binding = entry["reservation"]
            require(isinstance(binding, dict) and set(binding) == {
                "schema_version", "path", "device", "inode", "identity_sha256", "idempotency_key", "max_bytes"}
                and binding["schema_version"] == "herdr-result-reservation-1"
                and binding["path"] == entry["target"] and binding["identity_sha256"] == identity_sha
                and all(type(binding[key]) is int and binding[key] == entry[key] for key in ("device", "inode"))
                and isinstance(binding["idempotency_key"], str)
                and re.fullmatch(r"[A-Za-z0-9._:/+-]{1,256}", binding["idempotency_key"])
                and type(binding["max_bytes"]) is int and 1024 <= binding["max_bytes"] <= 131072,
                "reserved result binding differs from invocation")
        mapping[entry["fd"]] = entry
        targets.add(entry["target"])
    end = argv.index("--")
    used = set()
    for index, arg in enumerate(argv[:end]):
        if arg not in {"--bind-fd", "--ro-bind-fd", "--ro-bind-data"}:
            continue
        require(index + 2 < end and argv[index + 1].isdigit(), "FD binding is truncated")
        number = int(argv[index + 1])
        require(number in mapping and number not in used, "FD binding is missing or duplicated")
        entry = mapping[number]
        require(argv[index + 2] == entry["target"]
                and (arg == "--ro-bind-data") == (entry["kind"] == "sealed-profile-data")
                and not (arg == "--bind-fd" and entry["kind"] == "socket"), "FD binding role differs")
        used.add(number)
    require(used == set(mapping) and plan == request_for(identity, entries, argv),
            "plan differs from complete approved command")
    require(len(canonical_json_bytes(plan)) <= MAX_PLAN, "private plan exceeds consumer bound")


def _approval(path):
    from .host_configuration import _read_configuration
    path = Path(path)
    require(path.parent == APPROVAL_ROOT, "approval ticket outside fixed host authority")
    ticket = _read_configuration(path)
    info = path.lstat()
    require(info.st_nlink == 1 and 0 < info.st_size <= MAX_TICKET,
            "approval ticket must be exclusive and bounded")
    require(set(ticket) == {"schema_version", "plan", "argv", "not_before", "expires_at"}
            and ticket["schema_version"] == TICKET_VERSION
            and isinstance(ticket["plan"], dict), "closed issuance ticket required")
    identity = InvocationIdentity.from_dict(ticket["plan"].get("identity", {}))
    name = hashlib.sha256(canonical_json_bytes(identity.to_json())).hexdigest() + ".json"
    require(path.name == name, "approval filename differs from invocation")
    require(len(canonical_json_bytes(ticket)) <= MAX_TICKET, "approval ticket exceeds bound")
    _window(ticket)
    _shape(ticket["plan"], ticket["argv"], identity)
    return path, ticket, name


def _root_owner(info):
    require(info.st_uid == 0, "published approval must use new root-owned inode")


def publish_approved_launch_plan(configuration_path, *, publish=False):
    """Default is read-only preflight; publishing never replaces an old plan.

    A root operator must separately approve the complete ticket. The worker's
    proposal is never an input to this helper. Admission and bootstrap continue
    to verify actual FDs, immutable sources, profile, grant, fence and result.
    """
    if publish:
        require(os.geteuid() == 0, "launch-plan publication requires privileged operator")
    path, ticket, name = _approval(configuration_path)
    _verify_root_owned_ancestry(AUTHORITY_ROOT)
    body = canonical_json_bytes(ticket["plan"])
    record = {"destination": str(AUTHORITY_ROOT / name),
              "approval_sha256": hashlib.sha256(canonical_json_bytes(ticket)).hexdigest(),
              "plan_sha256": hashlib.sha256(body).hexdigest(), "published": False}
    if not publish:
        return record
    parent = os.open(AUTHORITY_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        fd, stage = tempfile.mkstemp(prefix=".launch-plan-", dir=AUTHORITY_ROOT)
        with os.fdopen(fd, "wb") as stream:
            stream.write(body)
            stream.flush()
            os.fchmod(stream.fileno(), 0o444)
            info = os.fstat(stream.fileno())
            _root_owner(info)
            require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
                    and stat.S_IMODE(info.st_mode) == 0o444 and info.st_size == len(body),
                    "new approval inode is not an exclusive read-only record")
            os.fsync(stream.fileno())
        # A late operator withdrawal or expiry must deny before publication.
        _, current, _ = _approval(path)
        require(current == ticket, "operator approval changed during publication")
        _window(ticket)
        _rename_without_replacement(parent, Path(stage).name, name)
        os.fsync(parent)
        return {**record, "published": True}
    finally:
        os.close(parent)
