#!/usr/bin/env python3
"""One-time, exact-RC26 bridge for nonsecret cutover marker readability.

Root-only, explicit operator action; never invoked by the unattended watchdog.
No queue, credential, provider, budget, release tag, or service mutation.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import pwd
import grp
import stat
import subprocess
import sys

CUTOVER_FILE = Path(__file__).with_name("cutover.py")
spec = importlib.util.spec_from_file_location("cutover_marker_contract", CUTOVER_FILE)
if spec is None or spec.loader is None:
    raise SystemExit("cutover_contract_missing")
cutover = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = cutover
spec.loader.exec_module(cutover)

PINNED_CURRENT = ("v0.3.0-rc.26", "4d09b58b44167e923a0829a3d5027f646932d6b4")
OPERATOR = "quantadmin"
PRECHECK = """
import os
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
if os.access(root / "queue.json", os.R_OK):
    raise SystemExit("private_task_queue_exposed")
"""


def safe_acl_rows(raw: str) -> bool:
    lines = [line.strip() for line in raw.splitlines() if line.strip()]
    required = {
        "user::rwx", "user:quantadmin:--x", "group::r-x",
        "mask::r-x", "other::---",
    }
    return set(lines) == required and len(lines) == len(required)


def _checked_command(argv: list[str], error: str) -> str:
    result = subprocess.run(
        argv, check=False, capture_output=True, text=True, timeout=15,
        env={"PATH": "/usr/sbin:/usr/bin:/sbin:/bin", "LANG": "C.UTF-8"},
    )
    if result.returncode != 0:
        raise cutover.ReleaseError(error)
    return result.stdout


def bootstrap() -> dict[str, object]:
    cutover.need(os.geteuid() == 0, "marker_bootstrap_root_required")
    with cutover.deployment_lock():
        current = cutover.CURRENT.resolve(strict=True)
        document = json.loads((current / "RELEASE.json").read_text("utf-8"))
        cutover.need((document.get("tag"), document.get("commit")) == PINNED_CURRENT,
                     "marker_bootstrap_current_identity_mismatch")
        # As root, first enforce every existing manifest + installed unit
        # hash and marker binding. No identity exception is granted here.
        cutover.current_release_unit_hashes()

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
        cutover.need(
            stat.S_ISREG(mi.st_mode) and mi.st_uid == 0 and mi.st_gid == reader
            and stat.S_IMODE(mi.st_mode) in {0o640, 0o644}
            and mi.st_size <= 4096,
            "marker_bootstrap_file_unexpected",
        )
        before = cutover.digest_file(cutover.PUBLIC_STATE)
        # Execute-only traverse for quantadmin; never grant directory
        # read/list, group membership, or access to the durable task queue.
        _checked_command([
            "/usr/bin/setfacl", "-m", f"u:{OPERATOR}:--x", str(directory)
        ], "marker_bootstrap_acl_failed")
        os.chmod(cutover.PUBLIC_STATE, 0o644, follow_symlinks=False)
        acl = _checked_command(
            ["/usr/bin/getfacl", "-cp", str(directory)],
            "marker_bootstrap_acl_unverifiable",
        )
        cutover.need(safe_acl_rows(acl), "marker_bootstrap_acl_invalid")
        cutover.need(cutover.digest_file(cutover.PUBLIC_STATE) == before,
                     "marker_bootstrap_changed_document")
        after = os.lstat(cutover.PUBLIC_STATE)
        cutover.need(
            after.st_uid == 0 and after.st_gid == reader
            and stat.S_IMODE(after.st_mode) == 0o644,
            "marker_bootstrap_mode_invalid",
        )
        _checked_command([
            "/usr/sbin/runuser", "-u", OPERATOR, "--",
            "/usr/bin/python3", "-I", "-B", "-c", PRECHECK
        ], "marker_bootstrap_operator_probe_failed")
        return {
            "status": "marker_operator_read_ok",
            "release": PINNED_CURRENT[0],
            "commit": PINNED_CURRENT[1],
            "marker_sha256": before,
            "operator": OPERATOR,
            "scope": "execute-only directory ACL; bounded public marker",
        }


def main() -> int:
    try:
        print(json.dumps(bootstrap(), sort_keys=True))
        return 0
    except (OSError, KeyError, ValueError, subprocess.SubprocessError,
            cutover.ReleaseError) as exc:
        print("marker_access_bootstrap_failed:" + str(exc), file=sys.stderr)
        return 78


if __name__ == "__main__":
    raise SystemExit(main())
