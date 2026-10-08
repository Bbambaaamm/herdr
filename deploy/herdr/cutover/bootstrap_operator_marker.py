#!/usr/bin/env python3
"""Root-only, exact-RC26 bootstrap for a bounded nonsecret release marker.

Only run from the root-owned copy described in RUNBOOK.md, with pinned hashes.
No task, credential, model, lease, cost, deployment, or service mutation.
"""
from __future__ import annotations

import importlib.util
import hashlib
import json
import os
from pathlib import Path
import pwd
import grp
import stat
import subprocess
import sys

PINNED_CURRENT = ("v0.3.0-rc.26", "4d09b58b44167e923a0829a3d5027f646932d6b4")
OPERATOR = "quantadmin"
TRUSTED_ROOT = Path("/var/lib/herdr/marker-bootstrap-rc26")
PUBLIC_KEYS = frozenset({
    "version", "tag", "commit", "config_sha256",
    "payload_manifest_sha256", "deployed_at",
})
CUTOVER_FILE = Path(__file__).with_name("cutover.py")


def _require_frozen_source() -> None:
    """Reject privileged execution of mutable/unreviewed operator-owned code."""
    here = Path(__file__).absolute()
    expected = TRUSTED_ROOT / "deploy/herdr/cutover/bootstrap_operator_marker.py"
    if here != expected:
        raise SystemExit("marker_bootstrap_untrusted_entry")
    sources = [
        expected,
        TRUSTED_ROOT / "deploy/herdr/cutover/cutover.py",
        TRUSTED_ROOT / "herdr/release.py",
        TRUSTED_ROOT / "herdr/__init__.py",
    ]
    dirs = [
        TRUSTED_ROOT, TRUSTED_ROOT / "deploy",
        TRUSTED_ROOT / "deploy/herdr",
        TRUSTED_ROOT / "deploy/herdr/cutover",
        TRUSTED_ROOT / "herdr",
    ]
    for path in [*dirs, *sources]:
        info = os.lstat(path)
        correct_kind = stat.S_ISDIR(info.st_mode) if path in dirs else stat.S_ISREG(info.st_mode)
        if not correct_kind or info.st_uid != 0 or stat.S_IMODE(info.st_mode) & 0o022:
            raise SystemExit("marker_bootstrap_source_untrusted")
    if stat.S_IMODE(os.lstat(TRUSTED_ROOT).st_mode) != 0o700:
        raise SystemExit("marker_bootstrap_source_untrusted")


# Never import candidate release code as root before checking that its inode
# tree is root-owned and not writable by the unprivileged operator.
if os.geteuid() == 0:
    _require_frozen_source()

spec = importlib.util.spec_from_file_location("cutover_marker_contract", CUTOVER_FILE)
if spec is None or spec.loader is None:
    raise SystemExit("cutover_contract_missing")
cutover = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cutover
spec.loader.exec_module(cutover)

PRECHECK = """
import json, os, sys
from pathlib import Path
root = Path("/var/lib/agent-platform-herdr")
marker = root / "deployed-release.json"
assert 0 < len(marker.read_bytes()) <= 4096, "operator_marker_unreadable"
try:
    os.listdir(root)
except PermissionError:
    pass
else:
    raise SystemExit("private_state_list_exposed")
names = json.loads(sys.argv[1])
assert isinstance(names, list) and len(names) <= 128
for name in names:
    assert isinstance(name, str) and name not in ("", ".", "..") and "/" not in name
    try:
        (root / name).read_bytes()
    except PermissionError:
        continue
    except FileNotFoundError:
        raise SystemExit("private_entry_changed")
    raise SystemExit("private_state_entry_exposed")
"""


def safe_acl_rows(raw: str) -> bool:
    rows = [line.strip() for line in raw.splitlines() if line.strip()]
    expected = {
        "user::rwx", "user:quantadmin:--x", "group::r-x",
        "mask::r-x", "other::---",
    }
    return set(rows) == expected and len(rows) == len(expected)


def _checked_command(argv: list[str], error: str, *, input_text: str | None = None) -> str:
    result = subprocess.run(
        argv, check=False, capture_output=True, text=True, input=input_text,
        timeout=15, env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
    )
    if result.returncode != 0:
        raise cutover.ReleaseError(error)
    return result.stdout


def _private_filenames(directory: Path, marker: Path) -> list[str]:
    entries = sorted(directory.iterdir())
    cutover.need(len(entries) <= 128, "marker_bootstrap_state_entry_limit")
    operator = pwd.getpwnam(OPERATOR)
    groups = set(os.getgrouplist(OPERATOR, operator.pw_gid))
    names = []
    for path in entries:
        if path == marker:
            continue
        info = os.lstat(path)
        # This marker is the *only* publicly readable file in the state
        # directory. No symlinks, nested directories, world ACL or named ACL.
        cutover.need(stat.S_ISREG(info.st_mode)
                     and stat.S_IMODE(info.st_mode) & 0o007 == 0
                     and not (info.st_gid in groups and info.st_mode & stat.S_IRGRP),
                     "marker_bootstrap_private_entry_unprotected")
        acl = _checked_command(
            ["/usr/bin/getfacl", "-cp", str(path)],
            "marker_bootstrap_private_acl_unavailable",
        )
        lines = [line.strip() for line in acl.splitlines() if line.strip()]
        cutover.need(
            all(row.startswith(("user::", "group::", "mask::", "other::"))
                for row in lines)
            and any(row == "other::---" for row in lines),
            "marker_bootstrap_private_acl_unprotected",
        )
        names.append(path.name)
    return names


def _public_marker_exact(marker: Path, current: dict[str, object]) -> None:
    try:
        value = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise cutover.ReleaseError("marker_bootstrap_public_document_invalid") from exc
    cutover.need(
        type(value) is dict and set(value) == PUBLIC_KEYS
        and value.get("version") == 1
        and (value.get("tag"), value.get("commit")) == PINNED_CURRENT
        and value.get("config_sha256") == current.get("config_contract_sha256")
        and value.get("payload_manifest_sha256") == current.get("payload_manifest_sha256")
        and type(value.get("deployed_at")) is int and value["deployed_at"] > 0,
        "marker_bootstrap_public_document_invalid",
    )
    for name in ("config_sha256", "payload_manifest_sha256"):
        digest = value[name]
        cutover.need(isinstance(digest, str) and len(digest) == 64
                     and all(ch in "0123456789abcdef" for ch in digest),
                     "marker_bootstrap_public_document_invalid")


def bootstrap() -> dict[str, object]:
    cutover.need(os.geteuid() == 0, "marker_bootstrap_root_required")
    _require_frozen_source()
    with cutover.deployment_lock():
        current_path = cutover.CURRENT.resolve(strict=True)
        document = json.loads((current_path / "RELEASE.json").read_text("utf-8"))
        cutover.need((document.get("tag"), document.get("commit")) == PINNED_CURRENT,
                     "marker_bootstrap_current_identity_mismatch")
        expected_units = cutover.current_release_unit_hashes()
        # Generic release validation authenticates unit *templates*, not the
        # installed systemd files. Compare installed hashes separately.
        for installed, digest in expected_units.items():
            cutover.need(cutover.digest_file(installed) == digest,
                         "marker_bootstrap_installed_unit_drift")

        directory = cutover.PUBLIC_STATE.parent
        di = os.lstat(directory)
        owner = pwd.getpwnam("agentops").pw_uid
        reader = grp.getgrnam("agent-platform-read").gr_gid
        cutover.need(
            stat.S_ISDIR(di.st_mode) and di.st_uid == owner
            and di.st_gid == reader and stat.S_IMODE(di.st_mode) == 0o750,
            "marker_bootstrap_directory_unexpected",
        )
        mi = os.lstat(cutover.PUBLIC_STATE)
        original_mode = stat.S_IMODE(mi.st_mode)
        cutover.need(
            stat.S_ISREG(mi.st_mode) and mi.st_uid == 0 and mi.st_gid == reader
            and original_mode in {0o640, 0o644}
            and 0 < mi.st_size <= 4096,
            "marker_bootstrap_file_unexpected",
        )
        _public_marker_exact(cutover.PUBLIC_STATE, document)
        private_names = _private_filenames(directory, cutover.PUBLIC_STATE)
        before_digest = cutover.digest_file(cutover.PUBLIC_STATE)
        previous_acl = _checked_command(
            ["/usr/bin/getfacl", "-cp", str(directory)],
            "marker_bootstrap_acl_unverifiable",
        )
        try:
            _checked_command(
                ["/usr/bin/setfacl", "-m", f"u:{OPERATOR}:--x", str(directory)],
                "marker_bootstrap_acl_failed",
            )
            os.chmod(cutover.PUBLIC_STATE, 0o644, follow_symlinks=False)
            acl = _checked_command(
                ["/usr/bin/getfacl", "-cp", str(directory)],
                "marker_bootstrap_acl_unverifiable",
            )
            cutover.need(safe_acl_rows(acl), "marker_bootstrap_acl_invalid")
            cutover.need(cutover.digest_file(cutover.PUBLIC_STATE) == before_digest,
                         "marker_bootstrap_changed_document")
            after = os.lstat(cutover.PUBLIC_STATE)
            cutover.need(after.st_uid == 0 and after.st_gid == reader
                         and stat.S_IMODE(after.st_mode) == 0o644,
                         "marker_bootstrap_mode_invalid")
            _checked_command([
                "/usr/sbin/runuser", "-u", OPERATOR, "--",
                "/usr/bin/python3", "-I", "-B", "-c", PRECHECK,
                json.dumps(private_names, separators=(",", ":")),
            ], "marker_bootstrap_operator_probe_failed")
        except BaseException as exc:
            failures = []
            try:
                os.chmod(cutover.PUBLIC_STATE, original_mode, follow_symlinks=False)
            except OSError:
                failures.append("marker_mode")
            try:
                _checked_command([
                    "/usr/bin/setfacl", "--set-file=-", str(directory)
                ], "marker_bootstrap_acl_rollback_failed", input_text=previous_acl)
            except (OSError, subprocess.SubprocessError, cutover.ReleaseError):
                failures.append("directory_acl")
            try:
                restored = _checked_command(
                    ["/usr/bin/getfacl", "-cp", str(directory)],
                    "marker_bootstrap_acl_restore_unverifiable",
                )
                if restored != previous_acl or (stat.S_IMODE(
                        os.lstat(cutover.PUBLIC_STATE).st_mode) != original_mode
                        or cutover.digest_file(cutover.PUBLIC_STATE) != before_digest):
                    failures.append("identity")
            except (OSError, subprocess.SubprocessError, cutover.ReleaseError):
                failures.append("identity")
            if failures:
                raise cutover.ReleaseError(
                    "marker_bootstrap_rollback_incomplete:" + ",".join(failures)
                ) from exc
            raise
        return {
            "status": "marker_operator_read_ok",
            "release": PINNED_CURRENT[0],
            "commit": PINNED_CURRENT[1],
            "marker_sha256": before_digest,
            "operator": OPERATOR,
            "scope": "execute-only directory ACL; bounded public marker",
        }


def main() -> int:
    try:
        print(json.dumps(bootstrap(), sort_keys=True))
        return 0
    except (OSError, KeyError, ValueError, subprocess.SubprocessError) as exc:
        print("marker_access_bootstrap_failed:" + str(exc), file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
