"""Read-only, fail-closed schema-2 readiness evidence; NEVER approval issuance.

This module reads independently root-controlled records. It cannot migrate a
policy, self-approve a profile manifest, or start a native pane/issuer.
"""
from __future__ import annotations

import hashlib
import stat
from datetime import UTC, datetime, timedelta
from pathlib import Path

from .host_configuration import (_private_profile, _read_configuration,
                                 validate_runtime_publication_binding)
from .launch_plan_issuer import VERSION as ISSUER_SCHEMA
from .runtime_publication import validate_publication_record
from .security import SecurityError, canonical_json_bytes


def _digest(record: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(record)).hexdigest()


def evaluate(host: dict, issuer: dict, *, authority_root_exists: bool,
             publication_record: dict | None = None) -> dict:
    """Static evidence, not host authority or a native root/child acceptance.

    Never return profile entries, credentials, grants, or issuer peer details.
    A supplied record is *not* evidence unless separately read from a trusted
    root-owned pathname in read_current().
    """
    private = host.get("private_launch") if isinstance(host, dict) else None
    binding = private.get("runtime_publication") if isinstance(private, dict) else None
    checks = {
        "host_schema_2": isinstance(host, dict) and type(host.get("schema_version")) is int
                         and host["schema_version"] == 2,
        "private_launch_present": isinstance(private, dict),
        "issuer_schema": isinstance(issuer, dict) and issuer.get("schema_version") == ISSUER_SCHEMA,
        "issuer_pin": isinstance(issuer, dict) and isinstance(host, dict)
                      and issuer.get("host_policy_sha256") == _digest(host),
        "issuer_timeout": isinstance(issuer, dict)
                          and type(issuer.get("request_timeout_seconds")) is int
                          and 1 <= issuer["request_timeout_seconds"] <= 60,
        "authority_directory": authority_root_exists,
        "runtime_publication_binding": isinstance(binding, dict),
        "runtime_publication_record": False,
        "profile_credential_approval": False,
        "automatic_issuer_opt_in": isinstance(private, dict)
            and isinstance(private.get("plan_handoff"), dict)
            and private["plan_handoff"].get("automatic_issuer") is True,
    }
    if isinstance(binding, dict) and isinstance(publication_record, dict):
        try:
            validate_publication_record(publication_record,
                expected_version=binding.get("version"),
                expected_approval_sha256=binding.get("approval_sha256"),
                expected_manifest_sha256={name: v["manifest_sha256"]
                    for name, v in binding["trees"].items()})
        except (SecurityError, KeyError, AttributeError, TypeError, ValueError):
            pass
        else:
            checks["runtime_publication_record"] = True
    if isinstance(private, dict) and checks["host_schema_2"]:
        try:
            _, expiry, floor = _private_profile(private)
            if not expiry > datetime.now(UTC) + timedelta(
                seconds=max(floor, host.get("grant_ttl_seconds", 0) + 60)):
                raise SecurityError("credential approval window expired or insufficient")
        except (SecurityError, KeyError, TypeError, ValueError):
            pass
        else:
            checks["profile_credential_approval"] = True
    return {"schema_version": "herdr-schema2-readiness-report-1",
            "status": "STATIC_GATES_PASS_NATIVE_E2E_PENDING" if all(checks.values())
                      else "ROOT_PREFLIGHT_BLOCKED",
            "checks": checks,
            "host_policy_sha256": _digest(host) if isinstance(host, dict) else None,
            "issuer_policy_sha256": _digest(issuer) if isinstance(issuer, dict) else None,
            "native_root_child_result_accepted": False,
            "publication_authorized": False}


def _protected_directory(path: Path) -> bool:
    try:
        path = Path(path)
        for candidate in (path, *path.parents):
            info = candidate.lstat()
            if (not stat.S_ISDIR(info.st_mode) or info.st_uid != 0
                    or info.st_mode & 0o022):
                return False
        return True
    except OSError:
        return False


def read_current(*, host_path=Path("/etc/herdr/host-policy.json"),
                 issuer_path=Path("/etc/herdr/launch-plan-issuer.json"),
                 authority_root=Path("/etc/herdr/launch-plans")) -> dict:
    """Use existing protected no-follow root reader; never follow task paths."""
    host = _read_configuration(host_path)
    issuer = _read_configuration(issuer_path)
    private = host.get("private_launch")
    binding = private.get("runtime_publication") if isinstance(private, dict) else None
    publication = None
    if isinstance(binding, dict) and isinstance(binding.get("record_path"), str):
        try:
            # The validator also checks this record's protected ancestry,
            # source inventory hashes and exact approved publication identity.
            validate_runtime_publication_binding(host)
            publication = _read_configuration(Path(binding["record_path"]))
        except (SecurityError, OSError, KeyError, ValueError, TypeError):
            publication = None
    from .launch_plan_issuer import _policy
    report = evaluate(host, issuer, authority_root_exists=_protected_directory(authority_root),
                      publication_record=publication)
    try:
        _policy()  # The existing root-owned policy gate, not a second issuer.
    except (SecurityError, OSError, ValueError, KeyError, TypeError):
        report["checks"]["native_issuer_policy"] = False
    else:
        report["checks"]["native_issuer_policy"] = True
    if not all(report["checks"].values()):
        report["status"] = "ROOT_PREFLIGHT_BLOCKED"
    return report
