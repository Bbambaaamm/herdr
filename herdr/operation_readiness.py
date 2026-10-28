"""Operational readiness only; admission and accounting stay in the host factory."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import stat


class ReadinessError(RuntimeError):
    pass


def require(ok, reason):
    if not ok:
        raise ReadinessError(reason)


@dataclass(frozen=True)
class Lifetimes:
    grant_seconds: int
    work_seconds: int
    preparation_seconds: int
    cleanup_seconds: int
    skew_seconds: int = 30

    def credential_seconds(self):
        values = tuple(self.__dict__.values())
        require(all(type(v) is int and v > 0 for v in values), "invalid_lifetime")
        return max(self.grant_seconds, self.work_seconds + self.cleanup_seconds) + self.preparation_seconds + self.skew_seconds

    def require_admin(self, remaining):
        require(remaining >= self.preparation_seconds + self.work_seconds + self.cleanup_seconds + self.skew_seconds,
                "administrator_window_insufficient")


def capacity(available, *, floor, start_guard, preparation_peak=0, growth_allowance=0, warning_margin=268435456):
    values = (available, floor, start_guard, preparation_peak, growth_allowance, warning_margin)
    require(all(type(v) is int and v >= 0 for v in values), "invalid_capacity")
    required = floor + start_guard + preparation_peak + growth_allowance
    return {"ready": available >= required, "available_bytes": available, "required_bytes": required,
            "missing_bytes": max(0, required - available), "margin_bytes": available - required,
            "capacity_warning": available < required + warning_margin}


def read_protected(path, *, owner=0, limit=1048576):
    """No writable or symlinked ancestor; snapshot the final regular file once."""
    path = Path(path)
    require(path.is_absolute() and ".." not in path.parts, "absolute_protected_path_required")
    fd = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        for index, part in enumerate(path.parts[1:]):
            info = os.fstat(fd)
            require(info.st_uid == owner and not info.st_mode & 0o022, "protected_ancestry_required")
            last = index == len(path.parts) - 2
            flags = os.O_RDONLY | os.O_NONBLOCK if last else os.O_PATH | os.O_DIRECTORY
            nxt = os.open(part, flags | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            os.close(fd)
            fd = nxt
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode) and before.st_uid == owner and before.st_nlink == 1
                and not before.st_mode & 0o222 and 0 < before.st_size <= limit, "protected_file_required")
        body = bytearray()
        while len(body) < before.st_size:
            block = os.read(fd, min(1048576, before.st_size - len(body)))
            require(bool(block), "protected_snapshot_shortened")
            body.extend(block)
        require(not os.read(fd, 1) and before == os.fstat(fd), "protected_snapshot_changed")
        return bytes(body)
    finally:
        os.close(fd)


def load_composition(path, expected_sha256):
    body = read_protected(path)
    require(hashlib.sha256(body).hexdigest() == expected_sha256, "composition_digest_changed")
    value = json.loads(body)
    require(set(value) == {"schema_version", "runtime", "files", "lifetimes", "capacity", "pilot"}
            and value["schema_version"] == "herdr-approved-pilot-composition-1", "composition_schema")
    require(type(value["files"]) is dict and 1 <= len(value["files"]) <= 64, "composition_files")
    for source, expected in value["files"].items():
        require(hashlib.sha256(read_protected(source, limit=33554432)).hexdigest() == expected,
                "composition_source_changed")
    Lifetimes(**value["lifetimes"]).credential_seconds()
    return value


def require_new_failure_evidence(previous, current):
    """A repeated preparation failure without new evidence requires reconciliation."""
    if previous and previous["reason_code"] == current["reason_code"]:
        require(previous["evidence_sha256"] != current["evidence_sha256"], "unchanged_failure_requires_reconciliation")


def require_offline_acceptance(proof, composition_sha256, *, now_epoch):
    fields={"schema_version","composition_sha256","checked_at_epoch","ordinary_worker_used","actual_sdk_used",
            "host_ipc_used","work_tools_verified","validation_verified","result_accepted","provider_http_requests",
            "authentication_http_requests","fixture_only"}
    require(set(proof)==fields and proof["schema_version"]=="herdr-ordinary-offline-acceptance-1", "offline_proof_schema")
    require(proof["composition_sha256"]==composition_sha256, "offline_proof_composition_changed")
    for field in ("ordinary_worker_used","actual_sdk_used","host_ipc_used","work_tools_verified",
                  "validation_verified","result_accepted","fixture_only"):
        require(proof[field] is True, "offline_cycle_not_accepted")
    require(type(proof["provider_http_requests"])is int and proof["provider_http_requests"]==0
            and type(proof["authentication_http_requests"])is int and proof["authentication_http_requests"]==0,
            "offline_external_effect_recorded")
    at=proof["checked_at_epoch"]
    require(type(at) in (int,float) and 0<=now_epoch-at<=86400, "offline_proof_stale")
