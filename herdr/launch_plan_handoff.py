"""Bounded live handoff of an untrusted proposal to the existing host authority.

Proposals are audit input, never approvals. Only the existing root-owned plan
reader can release a worker; no queue, renewal, provider or service is added.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import stat
import time
import uuid

from .private_mount_plan import ApprovedPrivateMountPlan, AUTHORITY_ROOT
from .security import SecurityError, canonical_json_bytes

VERSION = "herdr-private-mount-proposal-1"
MAX_PROPOSAL = 131072
_MISSING = "durable_private_mount_plan_unapproved"


class LaunchPlanReconciliationRequired(SecurityError):
    """Retained automatic proposal must be reconciled without a new attempt."""


def require(condition, reason):
    if not condition:
        raise SecurityError(reason)


def _directory(path):
    path = Path(path)
    require(path.is_absolute() and path.resolve(strict=True) == path,
            "canonical launch proposal directory required")
    info = path.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid()
            and stat.S_IMODE(info.st_mode) == 0o700,
            "private launch proposal directory required")
    return path, info


def _stamp(info):
    return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns,
            info.st_ctime_ns, info.st_mode, info.st_uid, info.st_nlink)


def _build(launch, builder):
    try:
        builder()
    except RuntimeError as exc:
        if str(exc) != _MISSING:
            raise
    else:
        raise SecurityError("unapproved private builder unexpectedly succeeded")
    plan, argv = launch.mount.private_mount_request, launch.mount.private_mount_argv
    from .launch_plan_publication import _shape
    _shape(plan, argv, launch.identity)
    # The native pane builder carries only these public environment literals.
    # Never persist arbitrary credential values as operator-review evidence.
    end = argv.index("--")
    public = {"HOME": "/home/agentops", "HERDR_DURABLE_SANDBOX": "1",
              "PATH": "/run/herdr/policy-code/agent-stack/policy-bin:/usr/bin:/bin"}
    for index, arg in enumerate(argv[:end]):
        if arg == "--setenv":
            require(index + 2 < end and argv[index + 1] in public
                    and argv[index + 2] == public[argv[index + 1]],
                    "launch proposal environment is not public")
    require(argv[end + 1:] == ["/bin/bash", "--noprofile", "--norc", "-i"],
            "launch proposal must use the native pane command")
    return json.loads(canonical_json_bytes(plan)), list(argv)


class LaunchPlanHandoff:
    """Configured only by the trusted host factory, before any pane exists."""
    def __init__(self, proposal_directory, timeout_seconds, *, automatic_issuer=None):
        require(type(timeout_seconds) is int and 1 <= timeout_seconds <= 60,
                "finite launch-plan handoff deadline required")
        self.directory, _ = _directory(proposal_directory)
        self.timeout_seconds = timeout_seconds
        from .launch_plan_issuer import AutomaticLaunchPlanClient
        require(automatic_issuer is None or isinstance(automatic_issuer, AutomaticLaunchPlanClient),
                "typed automatic host issuer required")
        self.automatic_issuer = automatic_issuer

    def _publish_proposal(self, launch, plan, argv):
        from .policy_launch import process_start_ticks
        from .runtime_publication import _rename_without_replacement
        name = hashlib.sha256(canonical_json_bytes(launch.identity.to_json())).hexdigest() + ".json"
        record = {"schema_version": VERSION, "plan": plan, "argv": argv,
                  "grant_sha256": launch.grant.hash,
                  "approved_profile": launch.private_profile_snapshot.identity,
                  "owner_pid": os.getpid(), "owner_start_ticks": process_start_ticks(os.getpid()),
                  "valid_until": launch.grant.expires_at}
        body = canonical_json_bytes(record)
        require(len(body) <= MAX_PROPOSAL, "launch proposal exceeds bound")
        path, directory = _directory(self.directory)
        parent = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            require((os.fstat(parent).st_dev, os.fstat(parent).st_ino) ==
                    (directory.st_dev, directory.st_ino), "launch proposal directory changed")
            stage = ".proposal-" + uuid.uuid4().hex
            fd = os.open(stage, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                         0o600, dir_fd=parent)
            with os.fdopen(fd, "wb") as stream:
                stream.write(body)
                stream.flush()
                os.fchmod(stream.fileno(), 0o400)
                info = os.fstat(stream.fileno())
                require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid()
                        and info.st_nlink == 1 and info.st_size == len(body),
                        "launch proposal inode changed")
                os.fsync(stream.fileno())
            _rename_without_replacement(parent, stage, name)
            os.fsync(parent)
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            require((named.st_dev, named.st_ino, named.st_size, named.st_mode, named.st_uid, named.st_nlink) ==
                    (info.st_dev, info.st_ino, info.st_size, info.st_mode, info.st_uid, info.st_nlink),
                    "launch proposal changed during publication")
            return path / name, body, _stamp(named), (directory.st_dev, directory.st_ino)
        finally:
            os.close(parent)

    def _verify_proposal(self, published):
        path, body, original, directory = published
        _, current = _directory(self.directory)
        require((current.st_dev, current.st_ino) == directory, "launch proposal directory changed")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            before = os.fstat(fd)
            raw = os.read(fd, MAX_PROPOSAL + 1)
            require(_stamp(before) == _stamp(os.fstat(fd)) == _stamp(path.lstat()) == original
                    and raw == body and not os.read(fd, 1), "launch proposal changed while waiting")
        finally:
            os.close(fd)

    def _live(self, launch, grant_sha256, profile):
        require(launch.grant.hash == grant_sha256
                and launch.private_profile_snapshot.identity == profile,
                "launch grant or profile changed while waiting")
        require(launch.grant.is_active(), "launch grant expired while waiting")
        require(callable(launch._private_handoff_verify)
                and launch._private_handoff_verify() is True,
                "current host launch authority unavailable")
        launch.private_profile_snapshot.verify()
        launch.mount.require_immutable_runtime()
        launch.mount.private_workspace_pin.verify()
        launch.mount.private_result_pin.verify_reservation()

    def await_approval(self, launch, builder):
        deadline = time.monotonic() + self.timeout_seconds
        require(launch.mount.private_mount_plan is None and launch.sealed is None,
                "launch-plan handoff is before seal only")
        grant_sha256 = launch.grant.hash
        profile = json.loads(canonical_json_bytes(launch.private_profile_snapshot.identity))
        self._live(launch, grant_sha256, profile)
        plan, argv = _build(launch, builder)
        try:
            published = self._publish_proposal(launch, plan, argv)
        except FileExistsError as exc:
            if self.automatic_issuer is not None:
                raise LaunchPlanReconciliationRequired("task_launch_plan_reconciliation_required: retained proposal") from exc
            raise
        if self.automatic_issuer is not None:
            try:
                self._verify_proposal(published)
                self._live(launch, grant_sha256, profile)
                self.automatic_issuer.issue(launch, published, deadline=deadline)
            except (OSError, ValueError, SecurityError):
                # A lost reply does not authorize a second issuance. Reconcile
                # only the existing root plan while retaining these exact FDs.
                pass
            fixed = getattr(launch, '_private_issuer_reconciliation_deadline', None)
            deadline = deadline if fixed is None else fixed
        try:
            destination = AUTHORITY_ROOT / published[0].name
            while True:
                self._verify_proposal(published)
                self._live(launch, grant_sha256, profile)
                current_plan, current_argv = _build(launch, builder)
                require(current_plan == plan and current_argv == argv,
                        "held launch command changed while waiting")
                require(time.monotonic() < deadline, "launch-plan handoff timed out")
                try:
                    approved = ApprovedPrivateMountPlan.read(destination, launch.identity)
                except FileNotFoundError:
                    time.sleep(min(0.2, max(0, deadline - time.monotonic())))
                    continue
                approved.authorize(plan["descriptors"], argv)
                self._verify_proposal(published)
                self._live(launch, grant_sha256, profile)
                require(time.monotonic() < deadline, "launch-plan handoff timed out")
                launch._private_handoff_state = (published, deadline, grant_sha256, profile)
                return destination
        except (OSError, ValueError, SecurityError) as exc:
            if self.automatic_issuer is not None:
                raise LaunchPlanReconciliationRequired(
                    "task_launch_plan_reconciliation_required: " + str(exc)) from exc
            raise

    def verify_bound(self, launch):
        require(isinstance(launch._private_handoff_state, tuple),
                "completed live launch-plan handoff required")
        published, deadline, grant_sha256, profile = launch._private_handoff_state
        self._verify_proposal(published)
        self._live(launch, grant_sha256, profile)
        record = json.loads(published[1])
        require(launch.mount.private_mount_request == record["plan"]
                and launch.mount.private_mount_argv == record["argv"],
                "bound launch command changed after handoff")
        launch.mount.private_mount_plan.authorize(record["plan"]["descriptors"], record["argv"])
        require(time.monotonic() < deadline, "launch-plan handoff timed out")
