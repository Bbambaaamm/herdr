"""Exclusive projection of the ACTUAL authenticated host continuation."""
import os
from pathlib import Path
import stat
from .case_roster import ROSTER_PATH, CONTEXT_ROOT, SUFFIX, Roster, canonical, digest, require, load_roster


def publish_sdk_phase(launch, evidence):
    from herdr.policy_launch import PreparedPolicyLaunch
    from herdr.host_bootstrap import validate_continuation
    from herdr.security import InvocationIdentity
    from .prep_entry import protected_json
    require(isinstance(launch, PreparedPolicyLaunch) and launch.sealed is not None,
            "sealed_original_host_launch_required")
    roster = load_roster(protected_json, InvocationIdentity)
    role = roster.role_for(launch.identity)
    require(os.geteuid() == 1001 and os.getpid() == roster.document["controller"]["pid"], "original_controller_required")
    continuation = validate_continuation(evidence["bootstrap"]["continuation"], identity=launch.identity,
                                          bundle_sha256=launch.sealed.sha256)
    require(launch._bootstrap_receipt is not None and continuation == launch._bootstrap_receipt,
            "canonical_authenticated_continuation_required")
    context = protected_json(Path(CONTEXT_ROOT) / (role + ".json"))
    runtime = protected_json(Path(CONTEXT_ROOT) / (role + ".runtime.json"))
    require(context["identity"] == launch.identity.to_json() and runtime["context_sha256"] == digest(context)
        and context["slot_sha256"] == digest(roster.slot(role)) and
        context["child_projection_sha256"] == roster.projection_sha256(role),
            "original_runtime_context_changed")
    record = {"schema": "herdr-canonical-sdk-phase-2", "roster_sha256": roster.sha256,
        "context_sha256": digest(context), "identity": launch.identity.to_json(),
        "init_pid": runtime["pid"], "init_start_ticks": runtime["start_ticks"],
        "sealed_grant_sha256": launch.grant.hash, "bundle_sha256": launch.sealed.sha256,
        "continuation": continuation.to_json()}
    parent = Path("/var/lib/herdr-offline-controller-" + SUFFIX)
    info = parent.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == 1001 and not info.st_mode & 0o077,
            "private_controller_state_required")
    directory_name = parent / "observer-phases"
    try: directory_name.mkdir(mode=0o700)
    except FileExistsError: pass
    directory = os.open(directory_name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(directory)
        require(info.st_uid == 1001 and not info.st_mode & 0o077, "private_phase_directory_required")
        fd = os.open(role + ".json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o400, dir_fd=directory)
        try:
            raw = canonical(record); require(len(raw) <= 65536 and os.write(fd, raw) == len(raw), "phase_projection_incomplete")
            os.fchmod(fd, 0o400); os.fsync(fd)
        finally: os.close(fd)
        os.fsync(directory)
    finally: os.close(directory)
    return True
