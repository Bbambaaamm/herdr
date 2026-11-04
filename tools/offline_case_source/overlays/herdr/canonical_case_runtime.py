"""One-case composition of the existing worker, work and child authorities.

This is SOURCE, not a runnable approval. The default transport enters this class
only inside the immutable UID1001 host entrypoint. Effect requests are data for
the authenticated UID0 operator. They confer no launch-plan or grant authority.
All replayable state is in the ORIGINAL task attempt and original journals.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
import hashlib
import os
import time

from offline_case.case import BUDGET, CASE, NONCE, Denied, canonical, require, sha
from herdr.security import InvocationIdentity

READ_OPERATIONS = frozenset({"fenced", "started", "cgroup_identity", "observe_all", "retired"})
RECOVERY_OPERATIONS = READ_OPERATIONS | {"fence", "retire"}


def identity_key(identity):
    return sha(canonical(identity.to_json()))


@dataclass
class LiveLaunch:
    """Custody cache only. Losing it forbids launch continuation, not recovery."""
    role: str
    identity: InvocationIdentity
    launch: object
    pane: str
    marker: str
    workspace: Path
    result: Path
    policy: Path
    ticket: object = None
    sandbox_pid: int | None = None
    attestation: dict | None = None
    work: object = None
    record: object = None
    pins: object = None
    prepared_grant_sha256: str | None = None


class CanonicalCaseRuntime:
    def __init__(self, *, parts, journal, effects, binding, recovery=False):
        from herdr.policy_launch import HostPolicyLaunchFactory
        from herdr.work_contract_host import HostWorkContractFactory
        from herdr.admission import AdmissionControl
        from herdr.runtime import AdmissionRegistry
        require(isinstance(parts["identity"], InvocationIdentity) and
                isinstance(parts["factory"], HostPolicyLaunchFactory) and
                isinstance(parts["work_factory"], HostWorkContractFactory) and
                isinstance(parts["admission_control"], AdmissionControl) and
                isinstance(parts["admission_registry"], AdmissionRegistry),
                "original typed canonical components required")
        self.parts, self.journal, self.io = parts, journal, effects
        self.binding, self.recovery = dict(binding), recovery
        self.live = {}
        self.child_scheduler = None
        self.child_authority = None
        self.pending_root_pane = None
        self._validate_identity(parts["task"])

    @classmethod
    def from_configuration(cls, packet, *, recovery=False):
        from herdr.canonical_case_claim import canonical_components, attempt_journal
        from herdr.canonical_case_effects import CanonicalHostEffects
        effects = CanonicalHostEffects()
        if not recovery:
            # No admission/budget writes until original UID0 custody is consumed
            # and cleanup is armed. Recovery deliberately has no live grant gate.
            effects.require_live_case(packet["binding"])
        parts = canonical_components(packet["task_id"], packet["run_token"], recovery=recovery)
        require(parts["identity"].fencing_token == packet["fencing_token"], "canonical fence changed")
        return cls(parts=parts, journal=attempt_journal(parts), effects=effects,
                   binding=packet["binding"], recovery=recovery)

    def _validate_identity(self, task):
        from herdr.canonical_case_claim import claimed_root_identity
        actual = claimed_root_identity(task)
        require(actual == self.parts["identity"] and task.get("max_attempts") == 1 and
                task.get("ownership_epoch") == {"version": 1, "run_token": actual.run_token,
                                                "fencing_token": actual.fencing_token},
                "original claimed attempt changed")

    def _read(self, name, default=None):
        try: return self.journal.read_once(name)
        except FileNotFoundError: return default

    def _record(self, name, value):
        """Idempotent receipt publication; effect intents use _intent instead."""
        old = self._read(name)
        if old is not None:
            require(old == value, "canonical receipt changed")
            return old
        self.journal.publish_once(name, value)
        require(self.journal.read_once(name) == value, "canonical receipt readback failed")
        return value

    def _intent(self, name, value):
        require(self._read(name) is None, "consumed or uncertain operation; recovery only")
        self.journal.publish_once(name, value)
        require(self.journal.read_once(name) == value, "effect intent readback failed")

    def _effect(self, request):
        previous = "0" * 64
        for sequence in range(1, 17):
            name = "root-effect-request-" + str(sequence)
            old = self._read(name)
            if old is not None:
                previous = sha(canonical(old))
                continue
            packet = {"schema": "canonical-case-root-effect-1", "sequence": sequence,
                "previous_sha256": previous, "binding": self.binding, "request": request}
            packet["request_sha256"] = sha(canonical(packet))
            self._intent(name, packet)
            return packet
        raise Denied("root effect sequence exhausted")

    def _bound(self):
        admitted = self._read("single-case-root-admit")
        require(type(admitted) is dict and admitted["binding"] == self.binding and
                admitted["task_id"] == self.parts["identity"].task_id and
                admitted["run_token"] == self.parts["identity"].run_token and
                admitted["fencing_token"] == self.parts["identity"].fencing_token,
                "original consumed case claim unavailable")
        self._validate_identity(self.io.current_task(self.parts, historical=True))
        require(self.io.boot_id() == self.binding["boot_id"], "case boot changed")

    def _births(self):
        self._bound()
        require(not self.recovery and self._read("case-fence-intent") is None,
                "case fenced or custody lost; recovery only")
        self.io.require_live_case(self.binding)
        task = self.io.current_task(self.parts, historical=False)
        self._validate_identity(task)
        require(task.get("attempt_state") in {"dispatching", "accepted"}, "root no longer live")

    @contextmanager
    def operation(self, packet):
        from herdr.canonical_case_claim import operation_guard
        require(packet["binding"] == self.binding and
                all(packet[name] == getattr(self.parts["identity"], name) for name in
                    ("task_id", "run_token", "fencing_token")), "foreign canonical operation")
        with operation_guard(self.parts):
            yield

    def admit(self, authority):
        from herdr.admission import AgentIdentity, TaskGraphSpec, ResourceUsage
        from herdr.work_configuration import _reviewed_graph
        require(not self.recovery, "recovery cannot admit")
        self.io.validate_authority(authority, self.binding)
        task = self.io.current_task(self.parts, historical=False)
        self._validate_identity(task)
        require(task["attempt_state"] in {"dispatching", "accepted"}, "unclaimed root")
        catalogue = self.parts["work_factory"].host_admission
        graph = _reviewed_graph(catalogue["definition"], task)
        require(graph is not None and len(graph.nodes) == 1, "original reviewed root graph required")
        usage = self.io.resource_usage()
        require(isinstance(usage, ResourceUsage), "actual resource observation required")
        node = graph.nodes[0]
        agent = AgentIdentity(role=node.role, repo=task["repo"], issue=str(task.get("issue") or ""),
            parent_role=None, parent_tools=frozenset(), paper_only=False)
        spec = TaskGraphSpec(node_count=1, max_depth=1, max_fanout=0, root_task=task["id"])
        # AdmissionControl is a child execution/resource gate. The root-only
        # delegation infrastructure tool is authorized by its original reviewed
        # graph and factory, never by treating ROOT as a child-slot reservation.
        tools = tuple(tool for tool in node.tools if tool != "herdr_delegate_child")
        decision = self.parts["admission_control"].check(agent, spec, usage, tools)
        require(bool(decision), "original root admission denied")
        self._intent("single-case-root-admit", {"binding": self.binding,
            "task_id": task["id"], "run_token": task["run_token"],
            "fencing_token": task["fencing_token"]})
        return {"binding": self.binding, "kind": "CANONICAL_RUNNING_ROOT_CLAIM",
                "task_id": task["id"], "run_token": task["run_token"],
                "fencing_token": task["fencing_token"], "task_sha256": sha(canonical(task)),
                "work_catalogue_sha256": sha(canonical(catalogue))}

    def prepare(self, authority, phase):
        self._births()
        self.io.validate_authority(authority, self.binding)
        require(phase in {"begin", "ticket", "seal"}, "unknown preparation phase")
        if phase == "begin":
            self._intent("root-prepare-intent", {"binding": self.binding,
                "identity": self.parts["identity"].to_json()})
            task = self.parts["task"]
            task["task_file"] = str(self.parts["root"] / "running" / (task["id"] + ".json"))
            # Original factory profile preflight and HostBootstrap.create both
            # consume the authenticated observer/ROOT base. Produce only actual
            # canonical identity/controller/PTY facts first; no grant or plan is
            # invented before the original factory creates them in ticket.
            self.pending_root_pane = self.io.early_root_pane(task)
            packet = self._effect(self.io.root_base_request(self.parts, self.binding, self.pending_root_pane))
            self._record("root-startup-challenge", {"sha256": packet["request_sha256"]})
            return packet
        if phase == "ticket" and "root" not in self.live:
            require(self.pending_root_pane is not None, "actual ROOT base/pane custody lost")
            self.live["root"] = self._prepare_root()
        entry = self._live("root")
        if phase == "ticket":
            return self._ticket(entry)
        self._seal(entry)
        proof = self.io.preparation_proof(entry, self.binding)
        require(proof == {"binding": self.binding, "sdk_imported": False,
            "setup_fds_closed": True, "setup_paths_hidden": True}, "actual prep proof unavailable")
        self._record("root-prepared", proof)
        return proof

    def _live(self, role):
        entry = self.live.get(role)
        require(isinstance(entry, LiveLaunch), "launch custody lost; cold recovery only")
        return entry

    def _prepare_root(self):
        from agent_completion_evidence import store_for
        from herdr.evidence import binding, digest
        from herdr.work_configuration import preflight_handoff, reviewed_root_model_arguments
        from herdr.result_submission import reserve_empty_result
        task, factory = self.parts["task"], self.parts["factory"]
        identity, work = self.parts["identity"], self.parts["work_factory"]
        task["task_file"] = str(self.parts["root"] / "running" / (task["id"] + ".json"))
        launch = factory.prepare(identity=identity, workspace=Path(task["workspace"]),
            tools=tuple(task["parent_tools"]), permissions=tuple(task["parent_permissions"]))
        require(launch.identity == identity and launch.private_profile_snapshot is not None,
                "actual private ROOT launch required")
        profile = launch.private_profile_snapshot
        # Retains original model selection check even though this case sends no
        # prompt and has zero external effects. Never invokes profile refresh here.
        reviewed_root_model_arguments(work, profile)
        completion = store_for(self.parts["root"], task).read("plan", digest(binding(task)))
        preflight_handoff(work, launch, completion, require_slot=False)
        result = reserve_empty_result(self.parts["root"] / "results" / (task["id"] + ".json"),
                                      identity, task["idempotency_key"])
        launch.bind_result_slot(result, task["idempotency_key"])
        from herdr.canonical_case_claim import task_session_identity
        _, marker = task_session_identity(task)
        policy = self.io.sandbox.frozen_policy()
        entry = LiveLaunch("root", identity, launch, "", marker, Path(task["workspace"]), result, policy,
                           work=work, prepared_grant_sha256=launch.grant.hash)
        work.workspace_pin = launch.mount.private_workspace_pin
        launch.prepare_private_command(lambda: self.io.sandbox.command(entry.workspace,
            self.io.real_binary, writable=(result,), policy=policy, policy_mount=launch.mount,
            admission_root=self.parts["root"], root_workspace_writable=False,
            pinned_worktree=launch.mount.private_workspace_pin,
            private_profile_snapshot=profile, hermes_profile=profile.name))
        require(self.pending_root_pane is not None, "ROOT base must precede factory preparation")
        entry.pane, observed_marker = self.pending_root_pane
        from herdr.canonical_startup_observation import AuthenticatedStartupObservation
        launch.verify_spawn_source(lambda: self.io.pane_pid(entry.pane),
            observation=AuthenticatedStartupObservation("root-startup-source", self._read("root-startup-challenge")["sha256"]))
        require(observed_marker == marker, "original root pane marker changed")
        self._save_launch(entry, "prepared-command")
        return entry

    def _ticket(self, entry):
        from herdr.native_ticket_v2 import NativePreparationTicket
        self._intent(entry.role + "-ticket-intent", {"identity": entry.identity.to_json()})
        ticket = NativePreparationTicket.admit(entry.launch, case_binding=self.binding,
            scheduler=self.child_scheduler if entry.role == "child" else None)
        entry.ticket = ticket
        request = self.io.preparation_request(entry, ticket, self.binding)
        self._record(entry.role + "-preparation-request", request)
        return self._effect(request)

    def _seal(self, entry):
        from herdr.ownership_release import capture_namespace_lifetime
        self._births()
        require(entry.ticket is not None, "original ticket custody required")
        entry.ticket.revalidate()
        self._intent(entry.role + "-seal-intent", {"identity": entry.identity.to_json()})
        pid, attestation = self.io.observe_prepared(entry)
        require(type(pid) is int and pid > 0 and attestation["sandbox_pid"] == pid and
            all(attestation[k] == getattr(entry.identity, k) for k in
                ("task_id", "run_token", "fencing_token")) and
            attestation["pane_id"] == entry.pane and attestation["marker"] == entry.marker and
            attestation["approved_profile"] == entry.launch.private_profile_snapshot.identity,
            "observed native preparation identity changed")
        entry.launch.verify_private_handoff()
        require(self.io.verify_boundary(entry, pid), "original observed sandbox verifier denied")
        node = self.child_scheduler.task_node(entry.identity.task_id) if entry.role == "child" else None
        tools = node.tools if node is not None else tuple(self.parts["task"]["parent_tools"])
        permissions = node.permissions if node is not None else tuple(self.parts["task"]["parent_permissions"])
        proof = entry.launch.seal(pid, attestation, tools=tools, permissions=permissions)
        entry.sandbox_pid, entry.attestation = pid, attestation
        lifetime = capture_namespace_lifetime(pid)
        self._record(entry.role + "-namespace", lifetime)
        if entry.role == "root":
            self._bind_root_work(entry, proof)
        else:
            scheduler, rec = self.child_scheduler, entry.record
            require(scheduler.attest_execution_sandbox(rec.id, rec.run_token, rec.agent_id,
                entry.pane, entry.marker, sandbox_pid=pid,
                policy_sha256=attestation["policy_sha256"], invocation_policy=proof),
                "original child observed seal rejected")
            scheduler.record_namespace_lifetime(rec.id, lifetime)
            port = self.child_authority.prepare_work(rec, entry.launch)
            require(port is not None, "actual child work and four callbacks required")
            entry.work = self.child_authority.work_factories[identity_key(entry.identity)]
        self._guard_work_callbacks(entry)
        self._save_launch(entry, "sealed")

    def _bind_root_work(self, entry, proof):
        from agent_completion_evidence import spec_digest, store_for
        from herdr.evidence import binding, digest
        from herdr.work_configuration import preflight_handoff, bind_reviewed_parent, bind_root_handoff
        task, work, launch = self.parts["task"], entry.work, entry.launch
        session = self.io.root_session(entry, task, proof)
        task["execution_session"] = session
        self.io.persist_task(self.parts, task)
        completion = store_for(self.parts["root"], task).read("plan", digest(binding(task)))
        preflight_handoff(work, launch, completion)
        # Canonical parent is created only AFTER observed ROOT seal, exactly as
        # worker1137->1158. No artificial root Lease or child preclaim exists.
        require(bind_reviewed_parent(work, task, launch) is not None, "canonical parent unavailable")
        cycle = work.prepare(identity=entry.identity, workspace=entry.workspace,
            grant=launch.grant, spec_sha256=spec_digest(task))
        task["work_contract"] = {"version": 1, "plan_sha256": cycle.plan.hash,
            "identity": entry.identity.to_json(), "phase": cycle.phase.value,
            "environment_sha256": cycle.plan.environment_sha256}
        bind_root_handoff(work, task, launch, cycle)
        bootstrap = launch.mount.bootstrap
        bootstrap.work_authority = work.authorize_invocation
        bootstrap.work_verify = work.verify_request
        bootstrap.work_budget = work.budget_effect
        bootstrap.work_observe = work.observe_sdk
        self.io.persist_task(self.parts, task)

    def _guard_work_callbacks(self, entry):
        bootstrap = entry.launch.mount.bootstrap
        for name, method in (("work_authority", "authorize_invocation"),
                ("work_verify", "verify_request"), ("work_budget", "budget_effect"),
                ("work_observe", "observe_sdk")):
            actual = getattr(entry.work, method)
            require(getattr(bootstrap, name).__self__ is entry.work, "original work callback missing")
            require(getattr(bootstrap, name).__func__ is actual.__func__, "original callback method changed")
        # Preserve exact MethodType checks in work_authority and host transport.
        # This additional finite gate is called by their original ingress path.
        bootstrap.case_live_guard = self._births

    def run(self, budget, phase):
        self._births()
        require(budget == BUDGET and phase in {"root", "child-ticket", "child-seal", "ingress"},
                "foreign run budget or phase")
        require(self._read("root-prepared") is not None and self._read("case-cgroup") is not None,
                "root preparation and exact owned unit required")
        if phase == "root":
            self._intent("case-run-intent", {"binding": self.binding})
            root = self._live("root")
            self._start_sdk(root)
            packet = self._effect(self.io.child_parent_source_request(root, self.binding))
            self._record("child-parent-startup-challenge", {"sha256": packet["request_sha256"]})
            return packet
        if phase == "child-ticket" and "child" not in self.live:
            self.live["child"] = self._prepare_child(self._live("root"))
        child = self._live("child")
        if phase == "child-ticket": return self._ticket(child)
        if phase == "child-seal":
            self._seal(child)
            self._start_sdk(child)
            return {"binding": self.binding, "outcome": "BOOTSTRAP_CONTINUATION_ONLY",
                    "root": True, "managed_children": 1}
        root = self._live("root")
        # The original bootstrap yields different process-bound references.
        require(self.io.host_reference(root) != self.io.host_reference(child),
                "ROOT and CHILD reference must be distinct")
        self._exercise_ingress(root)
        self._exercise_ingress(child)
        result = {"binding": self.binding, "completed": True, "root": True, "managed_children": 1,
            "outcome": "SDK_GUARDED_FIXTURE_INGRESS_ONLY", "semantic_child_acceptance": "NOT_ESTABLISHED",
            "parent_dependency": "NOT_ESTABLISHED", "E2E184": "NOT_ESTABLISHED"}
        self._record("case-finished", result)
        return result

    def _exercise_ingress(self, entry):
        """Actual SDK prompt -> guarded Unix ingress -> canonical fixture I/O."""
        from herdr.canonical_case_probe import probe_message, verify_probe_receipt
        text = probe_message(entry.identity, entry.launch.grant.hash, entry.role)
        self._intent(entry.role + "-sdk-ingress-intent", {"identity": entry.identity.to_json(),
            "grant_sha256": entry.launch.grant.hash, "prompt_sha256": sha(text.encode())})
        if entry.role == "child":
            rec, scheduler = entry.record, self.child_scheduler
            scheduler.bind_child_prompt(rec.id, text)
            require(scheduler.bind_execution_session(rec.id, rec.run_token, rec.agent_id,
                entry.pane, entry.marker), "canonical child session binding denied")
            require(scheduler.mark_child_delivery_started(rec.id, rec.run_token, rec.agent_id,
                rec.fencing_token, rec.idempotency_key), "original child no-resend delivery denied")
        else:
            self.parts["task"]["execution_session"]["economic_delivery_attempted"] = True
            self.io.persist_task(self.parts, self.parts["task"])
        # No controller-side WorkAuthorityClient/model callback. The owned actual
        # Hermes SDK process performs the original guarded API request itself.
        self.io.invoke(["agent", "prompt", entry.identity.agent_id, text,
            "--wait", "--timeout", "120000"], timeout_seconds=125)
        receipt = verify_probe_receipt(entry.work, entry.launch, role=entry.role)
        self._record(entry.role + "-sdk-ingress", receipt)

    def _require_offline_sdk_config(self, profile):
        import os
        import hashlib
        import json
        from herdr.private_profile_namespace import PrivateProfileSnapshot
        require(isinstance(profile, PrivateProfileSnapshot), "original held SDK profile required")
        profile.verify()
        members = [item for item in profile.files if item.relative == "config.yaml"]
        require(len(members) == 1, "one original held SDK config required")
        item = members[0]
        raw = os.pread(item.fd, item.size + 1, 0)
        require(len(raw) == item.size and hashlib.sha256(raw).hexdigest() == item.sha256,
                "original approved SDK config changed")
        config = json.loads(raw)
        require(config.get("model", {}).get("provider") == "nous" and
                config.get("updates", {}).get("check") is False and
                config.get("display", {}).get("interface") == "classic",
                "new original profile approval for supported bounded startup config required")
        require(profile.sdk_policy() is not None, "original empty SDK fallback policy required")

    def _start_sdk(self, entry):
        self._require_offline_sdk_config(entry.launch.private_profile_snapshot)
        from herdr.sdk_phase import publish_sdk_phase
        from herdr.work_configuration import bind_reviewed_parent
        require(entry.launch.sealed is not None and entry.work is not None, "work before SDK required")
        self._intent(entry.role + "-sdk-start-intent", {"identity": entry.identity.to_json()})
        def continuation(evidence):
            self._births()
            if entry.role == "root":
                task = self.parts["task"]
                bind_reviewed_parent(entry.work, task, entry.launch, evidence=evidence, recheck=True)
                task["execution_session"]["invocation_policy"] = evidence
                self.io.persist_task(self.parts, task)
            else:
                rec = entry.record
                require(self.child_scheduler.attest_execution_sandbox(rec.id, rec.run_token, rec.agent_id,
                    entry.pane, entry.marker, sandbox_pid=entry.sandbox_pid,
                    policy_sha256=entry.attestation["policy_sha256"], invocation_policy=evidence),
                    "canonical CHILD continuation denied")
            # SAME authenticated continuation sink; no fabricated host PID tag.
            publish_sdk_phase(entry.launch, evidence)
            self._record(entry.role + "-continuation", evidence)
            return True
        entry.launch.set_continuation_sink(continuation)
        entry.launch.arm_bootstrap()
        if entry.role == "child": self.child_scheduler.mark_pre_delivery_agent_start(entry.record.id)
        # Actual helper retains PID1 and runs shim -> stage1 -> held CP311/stage2.
        self.io.sandbox.start_sandbox_agent(self.io.invoke, entry.pane, entry.marker,
            entry.sandbox_pid, entry.identity.agent_id,
            ["-p", entry.launch.private_profile_snapshot.name, "chat", "--toolsets", "none",
             "--max-turns", "1", "--run-budget", "900"],
            verify_boundary=lambda: self.io.verify_boundary(entry, entry.sandbox_pid),
            bootstrap_peer=lambda *, timeout_seconds: entry.launch.mount.bootstrap.confirm(
                timeout_seconds=timeout_seconds), timeout_seconds=60)
        proof = entry.launch.confirm_bootstrap()
        entry.launch.verify_bootstrap()
        require(self._read(entry.role + "-continuation") == proof, "authenticated sink missing")
        self._record(entry.role + "-bootstrap-continuation", {"identity": entry.identity.to_json(),
            "evidence": proof, "reference": self.io.host_reference(entry)})
        self._save_launch(entry, "bootstrap-continuation")

    def _prepare_child(self, root):
        from agent_durable_children import attempt_directory, replay_host_scheduler
        from agent_completion_evidence import child_completion_for_root
        from herdr.host_configuration import child_factory_for_root
        from herdr.work_configuration import original_derived_children
        from herdr.scheduler import ChildProposal, DenyDecision
        from herdr.child_ownership import ChildOwnership, OwnershipRegistry
        from herdr.ownership_inventory import LegacyOwnershipInventory
        from herdr.ownership_release import HostOwnershipRelease
        from herdr.child_evidence import child_identity, child_workspace
        from herdr.owned_write_mounts import OwnedWritePins
        from herdr.runtime import HerdrChildRuntime
        from herdr.result_submission import reserve_empty_result
        self._births()
        root.launch.verify_bootstrap()
        task = self.parts["task"]
        task_file = Path(task["task_file"])
        verified = {"task_id": task["id"], "run_token": task["run_token"],
            "agent": root.identity.agent_id, "pane": root.pane, "marker": root.marker}
        factory = child_factory_for_root(task_file, verified)
        authority = child_completion_for_root(task_file, verified, factory=factory)
        require(authority is not None, "original child completion/work authority missing")
        derived = original_derived_children(self.parts["root"], task, identity=root.identity)
        require(derived is not None and len(derived["children"]) == 1, "one original protected child required")
        row = next(iter(derived["children"].values()))
        scope, model = row["scope"], row["model_policy"]
        directory = attempt_directory(self.parts["root"], task["id"], task["run_token"])
        scheduler = replay_host_scheduler(self.parts["root"], directory / "scheduler.jsonl")
        scheduler.completion_authority = authority
        require(not scheduler.children_of(task["id"]), "child already claimed; recovery only")
        scheduler.ownership_parent = root.identity
        scheduler.ownership_registry = OwnershipRegistry(self.parts["root"],
            verify_legacy=LegacyOwnershipInventory(self.parts["root"]),
            verify_release=HostOwnershipRelease(self.parts["root"]))
        ownership_data = next(item["ownership"] for item in
            self.parts["work_factory"].host_admission["definition"]["managed_children"]["children"]
            if item["key"] == row["key"])
        ownership = ChildOwnership.from_json(ownership_data)
        proposal = ChildProposal(parent_role=task["parent_role"], parent_tools=tuple(task["parent_tools"]),
            parent_permissions=tuple(task["parent_permissions"]), child_role=scope["role"],
            child_tools=tuple(scope["tools"]), child_permissions=tuple(scope["permissions"]),
            child_task=scope["objective"], child_model=model["model"], child_fallback_model=model["fallback_model"],
            worktree_identity=scope["worktree_identity"], ownership=ownership)
        proposal = authority.prepare_delegation(proposal, parent_task_id=task["id"],
            parent_agent_id=root.identity.agent_id, repo=task["repo"], issue=str(task["issue"]))
        self._intent("child-dispatch-intent", {"parent": root.identity.to_json(), "declaration_sha256": sha(canonical(row))})
        node = scheduler.spawn_child(task["id"], proposal, delegation_key=row["key"], parent_run_token=task["run_token"])
        require(not isinstance(node, DenyDecision), "original protected child proposal denied")
        leases = scheduler.dispatch(task_ids={node.id}, managed_start=True)
        require(len(leases) == 1 and leases[0].task_id == node.id, "one actual canonical child Lease required")
        rec = scheduler.record_for(node.id)
        identity = child_identity(rec)
        self._record("child-claim", {"identity": identity.to_json(), "parent": root.identity.to_json(),
            "idempotency_key": rec.idempotency_key, "lease_until": rec.lease.lease_until})
        self.child_scheduler, self.child_authority = scheduler, authority
        workspace = child_workspace(rec)[0]
        pinned = self.io.pin_child(workspace, rec.worktree_identity)
        runtime = HerdrChildRuntime(scheduler, self.io.runner, cwd=workspace, pinned_worktree=pinned,
            policy_launch_factory=factory, snapshot_path=directory / "swarm.json",
            env=self.io.child_environment(root, task), admission=self.parts["admission_control"],
            admission_registry=self.parts["admission_registry"])
        runtime.prepare()
        runtime._admit_child(rec.lease)  # Original AgentIdentity/TaskGraphSpec/real usage/Lease.
        require(scheduler.record_child_pane_intent(rec.id, rec.run_token, rec.agent_id,
            rec.fencing_token, rec.idempotency_key, "child-" + rec.run_token), "child pane intent denied")
        pins = OwnedWritePins(rec.ownership, pinned)
        scheduler.bind_owned_write_mounts(rec.id, pins)
        launch = factory.prepare_child(identity=identity, workspace=workspace,
            tools=node.tools, permissions=node.permissions, owned_write_roots=pins.roots)
        authority.prepare(rec)
        authority.preflight_work(rec, launch)
        (directory / "results").mkdir(mode=0o700, exist_ok=True)
        result = reserve_empty_result(directory / "results" / (rec.id + ".result.json"), identity, rec.idempotency_key)
        launch.bind_result_slot(result, rec.idempotency_key)
        policy = self.io.sandbox.frozen_policy()
        launch.prepare_private_command(lambda: self.io.sandbox.command(workspace, self.io.real_binary,
            writable=(result,), policy=policy, policy_mount=launch.mount, admission_root=self.parts["root"],
            child_workspace_writable=False, pinned_worktree=pinned, owned_write_pins=pins,
            private_profile_snapshot=launch.private_profile_snapshot, hermes_profile=launch.private_profile_snapshot.name))
        require(scheduler.mark_child_split_started(rec.id, rec.run_token, rec.agent_id,
            rec.fencing_token, rec.idempotency_key), "original child split intent denied")
        pane = self.io.child_pane(root, rec, launch, self._read("child-parent-startup-challenge")["sha256"])
        marker = "child-" + rec.run_token
        require(scheduler.bind_pre_delivery_pane(rec.id, rec.run_token, rec.agent_id, pane, marker),
                "original child pane binding denied")
        entry = LiveLaunch("child", identity, launch, pane, marker, workspace, result, policy, record=rec, pins=pins,
                           prepared_grant_sha256=launch.grant.hash)
        self._save_launch(entry, "prepared-command")
        return entry

    def _save_launch(self, entry, phase):
        record = {"binding": self.binding, "role": entry.role, "identity": entry.identity.to_json(),
            "pane_id": entry.pane, "marker": entry.marker, "workspace": str(entry.workspace),
            "result_slot": str(entry.result), "grant_sha256": entry.launch.grant.hash,
            "prepared_grant_sha256": entry.prepared_grant_sha256,
            "sandbox_pid": entry.sandbox_pid, "attestation": entry.attestation,
            "plan_sha256": entry.launch.mount.private_mount_plan.sha256}
        self._record(entry.role + "-launch-" + phase, record)

    def claim_unit(self, unit):
        self._births()
        require(unit == CASE and self._read("root-prepared") is not None, "unprepared case unit")
        self._intent("case-unit-claim", {"unit": unit, "binding": self.binding,
            "source_sha256": self.io.unit_source(unit), "boot_id": self.binding["boot_id"]})
        return self._effect({"kind": "OBSERVE_CASE_UNIT", "role": "case", "binding": self.binding,
            "claim": self._read("case-unit-claim")})

    def bind_cgroup(self, identity):
        self._births()
        claim = self._read("case-unit-claim")
        require(claim is not None, "original unit claim unavailable")
        receipt = self.io.root_unit_receipt(self.binding, claim)
        require(tuple(receipt["cgroup"]) == tuple(identity), "client cgroup tuple differs from root receipt")
        self._record("case-cgroup", receipt)
        return receipt["cgroup"]

    def started(self):
        self._bound()
        if self._read("case-cgroup") is not None: return True
        require(self._read("case-unit-claim") is None, "owned unit start uncertain; reconcile only")
        return False

    def cgroup_identity(self):
        self._bound()
        row = self._read("case-cgroup")
        return row["cgroup"] if row is not None else None

    def _scheduler(self):
        from agent_durable_children import attempt_directory, replay_host_scheduler, ledger_required
        directory = attempt_directory(self.parts["root"], self.parts["task"]["id"], self.parts["task"]["run_token"])
        if not (directory / "scheduler.jsonl").exists():
            require(not ledger_required(directory), "required canonical ledger missing")
            return None
        require(ledger_required(directory), "canonical ledger sentinel missing")
        return replay_host_scheduler(self.parts["root"], directory / "scheduler.jsonl")

    def fence(self):
        from herdr.work_budget import StopScope
        self._bound()
        self._record("case-fence-intent", {"binding": self.binding, "root": self.parts["identity"].to_json()})
        scheduler = self._scheduler()
        identities = [self.parts["identity"]]
        if scheduler is not None:
            from herdr.child_evidence import child_identity
            children = scheduler.children_of(self.parts["task"]["id"])
            require(len(children) <= 1, "foreign child in case ledger")
            for rec in children:
                require(rec.parent_run_token == self.parts["identity"].run_token, "foreign parent attempt")
                identities.append(child_identity(rec))
                # Before actual SDK prompt delivery use the original failed
                # pre-delivery path. Delivered ingress stays held until complete
                # root holder closure permits nonsemantic CANCELLED retirement.
                if rec.attempt_state != "terminal" and rec.economic_delivery_attempted is not True:
                    require(scheduler.fail_child_pre_delivery(rec.id, rec.run_token, rec.agent_id,
                        rec.fencing_token, rec.idempotency_key, "offline-case-fenced-before-delivery",
                        cleanup_complete=False, pane_creation_attempted=rec.pre_delivery_pane_creation_attempted),
                        "original child task fence unavailable")
                elif rec.attempt_state != "terminal":
                    # Post-delivery state stays held. Stop births now; the narrow
                    # existing-scheduler retirement extension runs only AFTER
                    # exact complete root holder closure in retire().
                    scheduler.cancel(rec.id, reason="offline-case-delivery-fenced-retained")
        authority = self.parts["work_factory"].budget_authority
        for identity in identities:
            authority.stop(stop_id=sha(canonical({"binding": self.binding, "identity": identity.to_json()})),
                scope=StopScope.TASK, target=identity.task_id, source="canonical-offline-case",
                reason_code="offline-case-fenced", resume_condition="no-resume-single-attempt")
        self._record("case-fenced", {"binding": self.binding, "identities": [x.to_json() for x in identities]})
        return self.fenced()

    def fenced(self):
        from herdr.work_budget import StopScope
        self._bound()
        row = self._read("case-fenced")
        if row is None: return False
        authority = self.parts["work_factory"].budget_authority
        allocation = self.parts["work_factory"].budget_definition["allocation"]["allocation_id"]
        stops = authority.snapshot(allocation)["active_stops"]
        for identity in row["identities"]:
            expected = sha(canonical({"binding": self.binding, "identity": identity}))
            require(any(stop["stop_id"] == expected and stop["scope"] == StopScope.TASK.value and
                        stop["target"] == identity["task_id"] for stop in stops), "canonical scoped stop missing")
        return True

    def observe_all(self, phase="complete"):
        self._bound()
        require(self.fenced(), "closure before durable task fence")
        require(phase in {"begin", "complete"}, "unknown historical observation phase")
        if phase == "begin":
            return self._effect({"kind": "OBSERVE_CLOSURE", "role": "case", "binding": self.binding,
                "roster": self._historical_roster(),
                "namespaces": {role: self._read(role + "-namespace") for role in ("root", "child")}})
        observation = self.io.historical_closure(self.binding, self._historical_roster())
        require(observation == {"fenced": True, "case_cgroup_empty": True,
            "descendants": [], "fds": [], "maps": [], "profile_holders": [],
            "complete": True, "boot_id": self.binding["boot_id"]}, "incomplete historical holders")
        self._record("case-observed-empty", observation)
        return observation

    def _historical_roster(self):
        rows = []
        for role in ("root", "child"):
            prepared = self._read(role + "-launch-prepared-command")
            if prepared is None: continue
            row = self._read(role + "-launch-bootstrap-continuation") or self._read(role + "-launch-sealed") or prepared
            rows.append(row)
        return rows

    def retire(self, observation):
        self._bound()
        require(self.fenced() and observation == self.observe_all(), "retirement requires fresh complete closure")
        self._record("case-retire-intent", {"binding": self.binding, "observation": observation})
        scheduler = self._scheduler()
        roster = self._historical_roster()
        for row in reversed(roster):
            identity = InvocationIdentity.from_dict(row["identity"])
            role = row["role"]
            self.io.require_historical_namespace_closed(self.binding, row,
                self._read(role + "-namespace"))
            if role in self.live:
                live = self.live[role]
                if live.pins is not None:
                    live.pins.close()
                    live.pins.worktree.close()
                    live.pins = None
                live.launch.cleanup_after_pane_closed()
            else:
                # Existing orphan cleanup refuses a still-live original host.
                # Recovery NEVER reconstructs signer/FD custody or prepares again.
                self.parts["factory"].cleanup_orphan(identity)
            if role == "child":
                require(scheduler is not None, "child scheduler missing on retirement")
                rec = scheduler.record_for(identity.task_id)
                require(rec.run_token == identity.run_token and rec.fencing_token == identity.fencing_token,
                    "original child identity changed during retirement")
                if rec.economic_delivery_attempted is True:
                    scheduler.retire_fenced_case_execution(rec.id, self.binding)
                else:
                    require(rec.attempt_state == "terminal" and rec.lease is None and
                        scheduler.mark_pre_delivery_cleanup_complete(rec.id), "original child cleanup record denied")
                if rec.ownership_reservation:
                    require(scheduler.release_child_ownership(rec.id), "original HostOwnershipRelease denied")
                self.parts["admission_registry"].release(identity.agent_id,
                    task_id=identity.task_id, fencing_token=identity.fencing_token)
            self._record(role + "-resources-retired", {"identity": identity.to_json(), "binding": self.binding})
        # Release is verified by original store readers, not by this receipt.
        self.io.verify_releases(self.parts, scheduler, roster)
        self._record("case-retired", {"binding": self.binding, "identities": [r["identity"] for r in roster]})
        return self.retired()

    def retired(self):
        self._bound()
        row = self._read("case-retired")
        if row is None: return False
        self.io.verify_releases(self.parts, self._scheduler(), self._historical_roster())
        return row["binding"] == self.binding and self.fenced()


def dispatch_with(runtime, packet):
    """Finite original host transport target. No arbitrary command/plugin port."""
    op, args = packet["operation"], packet["arguments"]
    allowed = {"admit": {"authority"}, "prepare": {"authority", "phase"},
        "run": {"budget", "phase"}, "claim_unit": {"unit"}, "bind_cgroup": {"identity"},
        "retire": {"observation"}, **{name: set() for name in READ_OPERATIONS | {"fence"}}}
    allowed["observe_all"] = {"phase"}
    require(op in allowed and set(args) == allowed[op], "closed canonical operation arguments required")
    with runtime.operation(packet):
        if op == "admit": return runtime.admit(args["authority"])
        if op == "prepare": return runtime.prepare(args["authority"], args["phase"])
        if op == "run": return runtime.run(args["budget"], args["phase"])
        if op == "claim_unit": return runtime.claim_unit(args["unit"])
        if op == "bind_cgroup": return runtime.bind_cgroup(args["identity"])
        if op == "retire": return runtime.retire(args["observation"])
        if op == "observe_all": return runtime.observe_all(args["phase"])
        return getattr(runtime, op)()


_LIVE = None


def dispatch(packet):
    global _LIVE
    require(type(packet) is dict and packet.get("case") == NONCE, "foreign case")
    if packet["operation"] == "admit":
        require(_LIVE is None, "case already consumed by this host")
        # Cache BEFORE admit: if its reply is lost, a second admit cannot restart.
        _LIVE = CanonicalCaseRuntime.from_configuration(packet)
    runtime = _LIVE
    if runtime is None:
        require(packet["operation"] in RECOVERY_OPERATIONS, "host custody lost; recovery only")
        runtime = CanonicalCaseRuntime.from_configuration(packet, recovery=True)
    return dispatch_with(runtime, packet)
