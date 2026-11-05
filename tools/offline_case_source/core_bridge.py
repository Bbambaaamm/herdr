"""Concrete accepted API wiring; source candidate only, no import-time effects.

This is the host-side admission implementation missing from the current F1
NativeHost seam. Inject only OS/native Herdr IO for inert tests. The API object
in production is constructed by accepted_api() from the pinned full core tree.
"""
from dataclasses import dataclass
from pathlib import Path
import hashlib
import importlib.util
import json
import os
import stat
import time


class Denied(RuntimeError): pass
def require(ok, message):
    if not ok: raise Denied(message)


class DurableLaunchJournal:
    """Subordinate, no-replace receipts in the canonical attempt directory.

    A receipt is evidence only. It never creates a grant, task, lease or
    reservation. The caller must select the original attempt directory from
    the canonical task and must revalidate its task/fence before each effect.
    """
    def __init__(self, directory):
        self.directory = Path(directory)
        require(self.directory.is_absolute() and ".." not in self.directory.parts and
                self.directory.resolve(strict=True) == self.directory,
                "canonical attempt directory required")
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and
                    stat.S_IMODE(info.st_mode) == 0o700,
                    "canonical attempt custody changed")
        finally:
            os.close(fd)

    @staticmethod
    def _name(event):
        require(type(event) is str and 0 < len(event) <= 256 and
                all(c.isascii() and (c.isalnum() or c in "-_") for c in event),
                "invalid launch receipt name")
        return "offline-case-" + hashlib.sha256(event.encode()).hexdigest() + ".json"

    def _directory_fd(self):
        fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        info = os.fstat(fd)
        if not (stat.S_ISDIR(info.st_mode) and info.st_uid == os.geteuid() and
                stat.S_IMODE(info.st_mode) == 0o700):
            os.close(fd)
            raise Denied("canonical attempt custody changed")
        return fd

    def publish_once(self, event, value):
        name = self._name(event)
        raw = json.dumps({"event": event, "value": value}, sort_keys=True,
                         separators=(",", ":"), allow_nan=False).encode()
        require(0 < len(raw) <= 65536, "bounded launch receipt required")
        directory = self._directory_fd()
        try:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory)
            try:
                require(os.write(fd, raw) == len(raw), "launch receipt write uncertain")
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(directory)
        finally:
            os.close(directory)
        return True

    def read_once(self, event):
        name = self._name(event)
        directory = self._directory_fd()
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=directory)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode) and before.st_uid == os.geteuid()
                        and stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1
                        and 0 < before.st_size <= 65536, "launch receipt identity changed")
                raw = os.read(fd, before.st_size + 1)
                after = os.fstat(fd)
                named = os.stat(name, dir_fd=directory, follow_symlinks=False)
                stamp = lambda x: (x.st_dev, x.st_ino, x.st_size, x.st_mtime_ns, x.st_ctime_ns)
                require(len(raw) == before.st_size and stamp(before) == stamp(after) == stamp(named),
                        "launch receipt changed during read")
                def unique(pairs):
                    result = {}
                    for key, item in pairs:
                        require(key not in result, "duplicate launch receipt field")
                        result[key] = item
                    return result
                value = json.loads(raw, object_pairs_hook=unique,
                    parse_constant=lambda _: (_ for _ in ()).throw(Denied("nonfinite launch receipt")))
                require(type(value) is dict and set(value) == {"event", "value"}
                        and value["event"] == event, "foreign launch receipt")
                return value["value"]
            finally:
                os.close(fd)
        finally:
            os.close(directory)

    def publish_continuation(self, identity, evidence):
        return self.publish_once("continuation-" + identity.task_id, evidence)


@dataclass(frozen=True)
class LaunchSpec:
    identity: object
    workspace: Path
    result_slot: Path
    idempotency_key: str
    tools: tuple
    permissions: tuple
    real_binary: Path
    marker: str
    pane_id: str


class NativeHerdrHost:
    """Actual factory/observed-seal/bootstrap/retained-reference composition.

    Existing scheduler owns task/lease/fence identities. Specs are selected from
    its admitted records, never manufactured from a prompt or this adapter.
    The root launcher is privileged separately; the factory host keeps its
    configured host_uid and its existing work/budget/broker authority.
    """
    def __init__(self, *, api, factory, registry, admission, scheduler,
                 runner, prep, journal):
        require(isinstance(factory, api.HostPolicyLaunchFactory), "typed_original_factory_required")
        require(isinstance(registry, api.AdmissionRegistry), "original_admission_registry_required")
        require(isinstance(admission, api.AdmissionControl), "original_admission_control_required")
        require(isinstance(scheduler, api.DynamicChildScheduler) and
                isinstance(scheduler.ownership_registry, api.OwnershipRegistry),
                "original_owned_scheduler_required")
        self.api, self.factory, self.registry, self.admission = api, factory, registry, admission
        self.scheduler = scheduler
        self.runner, self.prep, self.journal = runner, prep, journal
        self.launches = {}

    def reserve(self, *, identity, graph, usage, tools, lease):
        # The actual registry locks, combines cross-runtime usage, invokes
        # AdmissionControl.check and durably stores exact task/fence binding.
        self.registry.reserve(self.admission, identity, graph, usage, tools, lease)
        self.journal.publish_once("reservation-" + lease.task_id, {
            "agent_id": lease.agent_id, "task_id": lease.task_id,
            "fencing_token": lease.fencing_token, "lease_until": lease.lease_until})

    def prepare(self, spec, *, parent=None, retained_parent_verify=None):
        api = self.api
        require(isinstance(spec.identity, api.InvocationIdentity), "typed_scheduler_identity_required")
        record = self.scheduler._tasks.get(spec.identity.task_id)
        require(record is not None and record.agent_id == spec.identity.agent_id
                and record.run_token == spec.identity.run_token
                and record.fencing_token == spec.identity.fencing_token
                and (record.parent_task_id is None or
                     record.parent_task_id == spec.identity.parent_task_id)
                and (record.parent_agent_id is None or
                     record.parent_agent_id == spec.identity.parent_agent_id)
                and tuple(record.node.tools) == spec.tools
                and tuple(record.node.permissions) == spec.permissions,
                "scheduler_fence_or_scope_changed")
        admission_root = self.scheduler.ownership_registry.root
        require(isinstance(admission_root, Path) and admission_root.is_absolute()
                and ".." not in admission_root.parts,
                "existing_ownership_epoch_root_required")
        require(spec.identity.task_id not in self.launches, "launch_retry_forbidden")
        self.journal.publish_once("prepare-intent-" + spec.identity.task_id,
            {"identity": spec.identity.to_json()})
        factory = self.factory
        if parent is not None:
            require(isinstance(parent, api.PreparedPolicyLaunch) and parent.sealed is not None,
                    "accepted_parent_launch_required")
            parent.verify_bootstrap()
            # No arbitrary replacement authorize callback: the accepted host
            # configuration rebuilds the same original policy under its parent.
            require(callable(retained_parent_verify), "retained_parent_verifier_required")
            factory = api.build_host_policy_factory(parent_grant=parent.grant,
                configuration_path=api.HOST_POLICY_CONFIG,
                retained_parent_verify=retained_parent_verify)
            prepared = factory.prepare_child(identity=spec.identity, workspace=spec.workspace,
                tools=spec.tools, permissions=spec.permissions)
        else:
            prepared = factory.prepare(identity=spec.identity, workspace=spec.workspace,
                tools=spec.tools, permissions=spec.permissions)
        self.launches[spec.identity.task_id] = prepared  # retain even on later failure
        require(prepared.private_profile_snapshot is not None and prepared.sealed is None,
                "host_profile_projection_required")
        api.reserve_empty_result(spec.result_slot, spec.identity, spec.idempotency_key)
        prepared.bind_result_slot(spec.result_slot, spec.idempotency_key)
        self.journal.publish_once("prepared-" + spec.identity.task_id,
            {"identity": spec.identity.to_json(), "grant_hash": prepared.grant.hash})
        builder = lambda: api.sandbox.command(spec.workspace, spec.real_binary,
            writable=(spec.result_slot,), policy=api.sandbox.POLICY,
            **({"root_workspace_writable": False} if parent is None else {"child_workspace_writable": False}),
            pinned_worktree=prepared.mount.private_workspace_pin, policy_mount=prepared.mount,
            admission_root=admission_root,
            private_profile_snapshot=prepared.private_profile_snapshot,
            hermes_profile=prepared.private_profile_snapshot.name)
        # This obtains/validates the ORIGINAL exact root plan. Its current
        # issuer policy may deny; no local bypass or fabricated approval exists.
        prepared.prepare_private_command(builder)
        return prepared

    def seal_observed(self, spec, prepared, *, sandbox_pid, attestation):
        api = self.api
        require(prepared is self.launches.get(spec.identity.task_id)
                and prepared.sealed is None and type(sandbox_pid) is int and sandbox_pid > 0,
                "one_owned_prepared_process_required")
        prepared.verify_private_handoff()
        # No caller-controlled runtime booleans are accepted as assurance.
        # sandbox.verify + PolicyMount.seal perform actual observations.
        require(api.sandbox.verify(sandbox_pid, spec.real_binary, spec.marker,
            policy=api.sandbox.POLICY, attempts=1,
            pinned_worktree=prepared.mount.private_workspace_pin,
            child_workspace_writable=False, policy_mount=prepared.mount,
            private_profile_snapshot=prepared.private_profile_snapshot), "physical_boundary_unverified")
        require(attestation["sandbox_pid"] == sandbox_pid and
                attestation["task_id"] == spec.identity.task_id and
                attestation["run_token"] == spec.identity.run_token and
                attestation["fencing_token"] == spec.identity.fencing_token and
                attestation["approved_profile"] == prepared.private_profile_snapshot.identity,
                "observed_attestation_identity_changed")
        prepared.set_continuation_sink(lambda evidence: self.journal.publish_continuation(
            spec.identity, evidence))
        evidence = prepared.seal(sandbox_pid, attestation, tools=spec.tools, permissions=spec.permissions)
        self.journal.publish_once("sealed-" + spec.identity.task_id, evidence)
        return evidence

    def start_sdk(self, spec, prepared, *, sandbox_pid, verify_boundary):
        require(prepared is self.launches.get(spec.identity.task_id) and prepared.sealed is not None,
                "sealed_launch_required")
        prepared.arm_bootstrap()
        # Accepted helper keeps the registered shell alive, invokes the fixed
        # policy-bin/hermes -> stage1 -> held CP311/stage2 route, and checks the
        # authenticated peer before returning. Never direct-exec stage2.
        answer = self.api.sandbox.start_sandbox_agent(self.runner.invoke, spec.pane_id,
            spec.marker, sandbox_pid, spec.identity.agent_id,
            ["-p", prepared.private_profile_snapshot.name, "chat", "--toolsets", "none",
             "--max-turns", "1", "--run-budget", "900"],
            verify_boundary=verify_boundary,
            bootstrap_peer=lambda *, timeout_seconds: prepared.mount.bootstrap.confirm(timeout_seconds=timeout_seconds),
            timeout_seconds=60)
        evidence = prepared.confirm_bootstrap()
        prepared.verify_bootstrap()
        self.journal.publish_once("bootstrapped-" + spec.identity.task_id, evidence)
        return answer

    def verify_retained(self, spec, prepared, *, pid, attestation):
        return self.api.verify_retained_policy_evidence(prepared.evidence(),
            identity=spec.identity, pid=pid, attestation=attestation, require_bootstrap=True)

    def release_after_observed_empty(self, spec, prepared, observation):
        # Ownership/holder scan is required BEFORE any resources are removed.
        require(observation.get("complete") is True and observation.get("fenced") is True
                and all(observation.get(k) == [] for k in ("descendants", "fds", "maps", "profile_holders"))
                and observation.get("case_cgroup_empty") is True,
                "retain_unknown_until_all_holders_closed")
        prepared.cleanup_after_pane_closed()
        self.registry.release(spec.identity.agent_id, task_id=spec.identity.task_id,
                              fencing_token=spec.identity.fencing_token)
        self.journal.publish_once("retired-" + spec.identity.task_id, observation)

    def recover_cleanup_after_empty(self, identity, observation):
        """Retire original launch storage after host death without preparing again."""
        require(isinstance(identity, self.api.InvocationIdentity), "typed original identity required")
        intent = self.journal.read_once("prepare-intent-" + identity.task_id)
        require(type(intent) is dict and set(intent) == {"identity"}
                and intent["identity"] == identity.to_json(),
                "original launch intent unavailable")
        require(observation.get("complete") is True and observation.get("fenced") is True
                and observation.get("case_cgroup_empty") is True and
                all(observation.get(k) == [] for k in
                    ("descendants", "fds", "maps", "profile_holders")),
                "retain unknown launch holders")
        try:
            retired = self.journal.read_once("retired-" + identity.task_id)
        except FileNotFoundError:
            retired = None
        if retired is not None:
            require(retired == observation, "retired observation changed")
            return True
        try:
            prepared = self.journal.read_once("prepared-" + identity.task_id)
        except FileNotFoundError:
            prepared = None
        if prepared is not None:
            require(type(prepared) is dict and prepared.get("identity") == identity.to_json()
                    and type(prepared.get("grant_hash")) is str and prepared["grant_hash"],
                    "prepared launch receipt changed")
        removed = self.factory.cleanup_orphan(identity)
        require(removed is True or removed is False and prepared is None,
                "original launch storage could not retire")
        self.registry.release(identity.agent_id, task_id=identity.task_id,
                              fencing_token=identity.fencing_token)
        self.journal.publish_once("retired-" + identity.task_id, observation)
        return True


class NativeHerdrRunner:
    """Literal native Herdr CLI, no shell command construction or SDK fallback."""
    def __init__(self, executable, io=None):
        self.executable, self.io = str(executable), io or NativeCommandIO()
    def invoke(self, arguments, *, timeout_seconds):
        require(type(arguments) is list and all(type(x) is str and "\0" not in x for x in arguments)
                and arguments[:2] in (["pane", "get"], ["pane", "process-info"], ["pane", "run"],
                                      ["pane", "wait-output"],
                                      ["agent", "rename"], ["agent", "get"]), "native_operation_outside_case")
        if arguments[:2] == ["pane", "wait-output"]:
            require(len(arguments) == 11 and arguments[3:4] == ["--regex"]
                    and arguments[4].startswith("^HERDR_PROMPT_") and arguments[4].endswith("$")
                    and len(arguments[4]) == 63
                    and all(ch in "0123456789abcdef" for ch in arguments[4][14:-1])
                    and arguments[5:9] == ["--source", "recent-unwrapped", "--lines", "20"]
                    and arguments[9] == "--timeout" and arguments[10].isdecimal()
                    and 1 <= int(arguments[10]) <= 75000,
                    "unbounded_or_foreign_pane_wait")
        result = self.io.run([self.executable, *arguments], timeout=timeout_seconds)
        require(result.returncode == 0, "native_command_failed")
        if arguments[:2] == ["pane", "run"]:
            require(result.stdout == result.stderr == b"", "native_input_unacknowledged")
            return None
        require(len(result.stdout) <= 1048576 and result.stderr == b"", "native_result_unknown")
        return json.loads(result.stdout)


class NativeCommandIO:
    """Concrete command boundary; inert tests replace this single process effect."""
    def run(self, arguments, *, timeout):
        import subprocess
        require(type(arguments) is list and all(type(value) is str and "\0" not in value
                for value in arguments) and 0 < timeout <= 75,
                "bounded_literal_native_command_required")
        return subprocess.run(arguments, stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
            timeout=timeout, env={"PATH": "/usr/bin:/usr/local/bin", "LANG": "C"})


def accepted_api():
    """Call only inside the immutable host release, AFTER source pin validation."""
    from types import SimpleNamespace
    from herdr.policy_launch import HostPolicyLaunchFactory, PreparedPolicyLaunch, verify_retained_policy_evidence
    from herdr.security import InvocationIdentity
    from herdr.host_configuration import build_host_policy_factory, HOST_POLICY_CONFIG
    from herdr.runtime import AdmissionRegistry
    from herdr.admission import AdmissionControl
    from herdr.child_ownership import OwnershipRegistry
    from herdr.scheduler import DynamicChildScheduler
    from herdr.result_submission import reserve_empty_result
    import herdr.policy_launch as source
    sandbox_path = Path(source.__file__).resolve().parents[1] / "agent-stack/bin/agent_durable_sandbox.py"
    definition = importlib.util.spec_from_file_location("herdr_native_bridge_sandbox", sandbox_path)
    sandbox = importlib.util.module_from_spec(definition)
    import sys
    sys.modules[definition.name] = sandbox
    definition.loader.exec_module(sandbox)
    return SimpleNamespace(HostPolicyLaunchFactory=HostPolicyLaunchFactory,
        PreparedPolicyLaunch=PreparedPolicyLaunch, InvocationIdentity=InvocationIdentity,
        build_host_policy_factory=build_host_policy_factory, HOST_POLICY_CONFIG=HOST_POLICY_CONFIG,
        AdmissionRegistry=AdmissionRegistry, OwnershipRegistry=OwnershipRegistry,
        DynamicChildScheduler=DynamicChildScheduler,
        AdmissionControl=AdmissionControl, reserve_empty_result=reserve_empty_result,
        verify_retained_policy_evidence=verify_retained_policy_evidence, sandbox=sandbox)
