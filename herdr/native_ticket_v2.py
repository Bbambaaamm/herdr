"""Typed host ticket selecting one slot of the same-authority frozen roster."""
from dataclasses import dataclass
import os
from pathlib import Path
import time
from .case_roster import Roster, ROSTER_PATH, canonical, digest, require, load_roster
from .preparation_contract import derive_record, request_for, native_argv

_CONSTRUCTION = object()


@dataclass(frozen=True)
class NativePreparationTicket:
    roster: Roster
    role: str
    identity: object
    plan: object
    descriptors: tuple
    argv: tuple
    record: dict
    _construction: object
    scheduler: object = None

    def __post_init__(self): require(self._construction is _CONSTRUCTION, "admitted_host_ticket_required")

    @classmethod
    def admit(cls, launch, *, case_binding, scheduler=None):
        from herdr.policy_launch import PreparedPolicyLaunch, process_start_ticks
        from herdr.private_mount_plan import ApprovedPrivateMountPlan
        from herdr.security import InvocationIdentity
        from herdr.host_configuration import _read_configuration
        from herdr.launch_plan_issuer import _policy, _host_peer
        require(isinstance(launch, PreparedPolicyLaunch) and launch.sealed is None and
            launch.private_profile_snapshot is not None, "typed_unsealed_host_preparation_required")
        roster = load_roster(_read_configuration, InvocationIdentity)
        boot = Path("/proc/sys/kernel/random/boot_id").read_text().strip()
        roster.live(now=time.time(), boot_id=boot)
        require(case_binding == roster.document["case_binding"] and os.geteuid() == os.getegid() == 1001,
                "original_case_host_binding_required")
        issuer, policy = _policy()
        peer = _host_peer(os.getpid(), 1001, 1001, issuer, policy)
        controller = roster.document["controller"]
        require(peer == (controller["pid"], 1001, 1001, controller["start_ticks"]) and
            digest(policy) == roster.document["host_policy_sha256"], "original_host_controller_changed")
        root_identity = InvocationIdentity.from_dict(roster.slot("root")["identity"])
        if launch.identity == root_identity:
            require(set(roster.document["slots"]) == {"root"}, "initial_root_only_base_required")
            role = "root"
        else:
            from .child_projection import canonical_child_claim
            canonical_child_claim(scheduler, launch.identity, root_identity)
            require("child" not in roster.roles, "child_preparation_already_consumed")
            role = "child"
        plan = launch.mount.private_mount_plan
        require(isinstance(plan, ApprovedPrivateMountPlan) and launch.grant.is_active(), "original_live_plan_required")
        descriptors = launch.mount.private_mount_request["descriptors"]
        argv = launch.mount.private_mount_argv
        plan.authorize(descriptors, argv)
        launch.verify_private_handoff()
        record = derive_record(roster, role, identity=launch.identity.to_json(),
            plan=launch.mount.private_mount_request, argv=argv, grant_hash=launch.grant.hash,
            expires_at=launch.grant.expires_at, approved_profile=launch.private_profile_snapshot.identity)
        require(record["plan_sha256"] == plan.sha256, "canonical_prepared_plan_differs")
        return cls(roster, role, launch.identity, plan, tuple(descriptors), tuple(argv), record, _CONSTRUCTION, scheduler)

    @property
    def command(self): return native_argv(self.roster, self.role, digest(self.identity.to_json()))
    @property
    def request(self): return request_for(self.roster, self.role, self.plan.sha256, identity=self.identity.to_json())
    def revalidate(self):
        from herdr.host_configuration import _read_configuration
        from herdr.security import InvocationIdentity
        current = load_roster(_read_configuration, InvocationIdentity)
        require(current.sha256 == self.roster.sha256, "original_roster_changed")
        if self.role == "child":
            from .child_projection import canonical_child_claim
            canonical_child_claim(self.scheduler, self.identity,
                InvocationIdentity.from_dict(current.slot("root")["identity"]))
        if self.role == "child" and "child" in current.roles:
            require(current.slot("child")["identity"] == self.identity.to_json(), "different_child_already_appended")
        self.plan.authorize(list(self.descriptors), list(self.argv))
        return self
