"""Monotonic same-authority child append AFTER canonical parent/child claim.

No new issuer, reservation, signature, grant or model authority. The only
production publisher is the original root DescriptorCustody redemption path,
after its original _validate/_host_peer/plan/parent checks have succeeded.
"""
import hashlib
import os
from pathlib import Path
import re
import stat
from .case_roster import (Roster, CONTEXT_ROOT, SUFFIX, canonical, digest, require)


def canonical_child_claim(scheduler, identity, root_identity):
    from herdr.scheduler import (DynamicChildScheduler, TaskRecord, Lease, _canonical_payload_parent,
                                 _validate_canonical_record)
    from herdr.taskgraph import LifecycleState
    require(isinstance(scheduler, DynamicChildScheduler), "actual_canonical_scheduler_required")
    root = scheduler._tasks.get(root_identity.task_id)
    child = scheduler._tasks.get(identity.task_id)
    require(isinstance(root, TaskRecord) and isinstance(child, TaskRecord), "actual_existing_task_records_required")
    parent = _canonical_payload_parent(root.canonical_parent)
    _validate_canonical_record(root, parent, bound=True)
    require(parent.identity == root_identity and child.parent_run_token == root_identity.run_token
        and child.parent_task_id == root_identity.task_id and child.parent_agent_id == root_identity.agent_id
        and child.state is LifecycleState.RUNNING and child.attempt_state == "accepted"
        and isinstance(child.lease, Lease) and child.lease.lease_until > scheduler.clock()
        and child.run_token == identity.run_token and child.agent_id == identity.agent_id
        and child.id == identity.task_id and child.lease.task_id == identity.task_id
        and child.lease.agent_id == identity.agent_id and child.lease.fencing_token == identity.fencing_token
        and child.pre_delivery_pane_creation_attempted is True and child.execution_marker == "child-" + identity.run_token,
        "canonical_dispatched_child_binding_required")
    events = scheduler.audit_log.replay()
    require(len(events) <= 100000, "bounded_canonical_journal_required")
    claims = [event for event in events if event.get("event") == "claim" and
        event.get("task_id") == identity.task_id and event.get("run_token") == identity.run_token]
    require(len(claims) == 1 and claims[0].get("managed_start", {}).get("identity") == identity.to_json(),
            "one_actual_canonical_managed_claim_required")
    return {"identity": identity.to_json(), "root_identity": root_identity.to_json(),
        "parent_admission_sha256": digest(parent.to_json()), "claim_sha256": digest(claims[0])}


def measured_stdio(pid, authority):
    streams = {}
    for number in (0, 1, 2):
        name = f"/proc/{pid}/fd/{number}"
        link = os.readlink(name); info = os.stat(name)
        require(re.fullmatch(r"/dev/pts/[0-9]+", link or "") and stat.S_ISCHR(info.st_mode)
            and info.st_uid == 1001 and 136 <= os.major(info.st_rdev) <= 143,
            "original_owned_child_pty_required")
        streams[str(number)] = {"path": link, "device": info.st_dev, "inode": info.st_ino, "rdev": info.st_rdev}
    require(streams["0"] == streams["1"] == streams["2"], "one_actual_child_terminal_required")
    return streams


def child_document(roster, *, grant, parent_grant, request, peer, root_context, root_phase, stdio):
    """Only validated original typed grants/context; no free slot/identity input."""
    from herdr.security import SecurityGrant, InvocationIdentity
    from herdr.host_bootstrap import validate_continuation
    require(isinstance(roster, Roster) and set(roster.document["slots"]) == {"root"}
        and roster.child_raw is None and isinstance(grant, SecurityGrant) and isinstance(parent_grant, SecurityGrant),
        "original_typed_child_and_parent_required")
    root_identity = InvocationIdentity.from_dict(roster.slot("root")["identity"])
    require(parent_grant.identity == root_identity and parent_grant.is_active() and grant.is_active()
        and parent_grant.hash == grant.parent_grant_hash and request["parent_grant"] == parent_grant.to_json()
        and request["grant"] == grant.to_json() and request["policy_sha256"] == roster.document["host_policy_sha256"]
        and request["proposal"]["plan"]["identity"] == grant.identity.to_json(),
        "original_validated_parent_child_request_changed")
    require(root_context["roster_sha256"] == roster.sha256 and root_context["identity"] == root_identity.to_json()
        and root_phase["roster_sha256"] == roster.sha256 and root_phase["context_sha256"] == digest(root_context)
        and root_phase["identity"] == root_identity.to_json() and root_phase["sealed_grant_sha256"] == parent_grant.hash,
        "actual_sealed_parent_bootstrap_projection_required")
    validate_continuation(root_phase["continuation"], identity=root_identity, bundle_sha256=root_phase["bundle_sha256"])
    slot = {"identity": grant.identity.to_json(), "workspace": grant.workspace_root,
        "unit": "herdr-offline-child-" + SUFFIX + ".service", "stdio": stdio,
        "marker": "child-" + grant.identity.run_token}
    document = {"schema": "herdr-canonical-child-projection-3", "root_roster_sha256": roster.sha256,
        "root_context_sha256": digest(root_context), "slot": slot, "grant_sha256": grant.hash,
        "parent_grant_sha256": parent_grant.hash, "parent_bundle_sha256": root_phase["bundle_sha256"],
        "plan_sha256": digest(request["proposal"]["plan"]), "original_request_sha256": digest(request),
        "original_peer": list(peer)}
    roster.with_child(canonical(document), InvocationIdentity, root_context=root_context)
    return document


def publish_child(document):
    """Original root authority only; exclusive durable append, never replace."""
    require(os.geteuid() == 0, "original_root_custody_publisher_required")
    directory = os.open(CONTEXT_ROOT, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        info = os.fstat(directory)
        require(info.st_uid == 0 and not info.st_mode & 0o022, "protected_original_context_directory_required")
        fd = os.open("child-slot.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o640, dir_fd=directory)
        try:
            raw = canonical(document); require(len(raw) <= 65536 and os.write(fd, raw) == len(raw), "child_append_uncertain")
            os.fchown(fd, 0, 1001); os.fchmod(fd, 0o640); os.fsync(fd)
        finally: os.close(fd)
        os.fsync(directory)
    finally: os.close(directory)
