"""Finite native/source metadata effects for canonical_case_runtime.

Nothing runs at import. This file must be installed in the SAME immutable core
as the original issuer, worker and reviewed 03R2 modules. No effect is executed
by the annex's tests: only the adapters below are replaced with finite IO.
"""
from __future__ import annotations
from pathlib import Path
from datetime import UTC, datetime
import hashlib
import json
import os
import stat
import subprocess
import time

from offline_case.case import NONCE, CASE, Denied, require, canonical, sha, pinned_bytes, parse

BASE = Path("/opt/agent-platform/herdr-offline-03414499dd0d1986")
META = Path("/var/lib/herdr-offline-observer-03414499dd0d1986/contexts")
SESSION = "offline-" + NONCE[:20]


class NativeRunner:
    def __init__(self, executable, env): self.executable, self.env = executable, env
    def run(self, args, timeout_seconds=30):
        from herdr.runtime import CommandResult
        require(type(args) is list and all(type(x) is str and "\0" not in x for x in args),
                "literal native arguments required")
        require(0 < timeout_seconds <= 900, "bounded native operation required")
        result = subprocess.run([str(self.executable), "--session", SESSION, *args],
            env=self.env, stdin=subprocess.DEVNULL, capture_output=True,
            timeout=timeout_seconds, check=False)
        require(len(result.stdout) <= 1048576 and len(result.stderr) <= 131072, "native response oversized")
        return CommandResult(result.returncode, result.stdout.decode("utf8"), result.stderr.decode("utf8"))


class CanonicalHostEffects:
    def __init__(self):
        import agent_durable_sandbox as sandbox
        from herdr.launch_environment import sanitize_environment
        # The binary and argv are independently checked by the original factory
        # and immutable release. Never take a binary/provider URL from a packet.
        from offline_case.native_source import NATIVE_TARGET
        self.real_binary = NATIVE_TARGET
        self.sandbox = sandbox
        self.env = sanitize_environment({"HOME": "/home/agentops", "USER": "agentops", "LOGNAME": "agentops",
            "PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"})
        self.runner = NativeRunner(self.real_binary, self.env)

    def invoke(self, args, *, timeout_seconds):
        from herdr.runtime import _json_result
        answer = self.runner.run(args, timeout_seconds=timeout_seconds)
        if args[:2] == ["pane", "run"]:
            require(answer.returncode == 0 and answer.stdout == answer.stderr == "", "native pane input unknown")
            return None
        return _json_result(answer, "canonical offline native command")

    def boot_id(self):
        from offline_case.admission import _process_read
        return _process_read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip()

    def current_task(self, parts, *, historical):
        if historical:
            from herdr.canonical_case_claim import read_held_task
            return read_held_task(parts["root"], parts["identity"].task_id, parts["identity"].run_token).task
        from herdr.host_configuration import read_canonical_parent
        task = read_canonical_parent(parts["root"], parts["identity"].task_id, parts["identity"].run_token)
        require(task is not None, "canonical root disappeared")
        return task

    def persist_task(self, parts, task):
        from herdr.canonical_case_claim import persist_task
        return persist_task(parts, task)

    def require_live_case(self, binding):
        from herdr.host_configuration import _read_configuration
        # Original root custody stays 0700/0600. Read only the root-published
        # nonsecret phase projection. The SDK gets no access to this directory.
        try:
            _read_configuration(META / "scope-fenced.json")
        except FileNotFoundError:
            pass
        else:
            raise Denied("irreversible original root expiry fence")
        row = _read_configuration(META / "case-phase.json")
        require(set(row) == {"schema", "state", "authority", "used", "revision", "projection_sha256"} and
            row["schema"] == "canonical-case-phase-projection-1" and
            row["projection_sha256"] == sha(canonical({k: v for k, v in row.items() if k != "projection_sha256"})),
            "root custody projection changed")
        state, authority, used = row["state"], row["authority"], row["used"]
        require(state["binding"] == used == binding and
            state["phase"] in {"ADMITTED", "ARMED", "PREPARED", "START_INTENT"} and
            sha(canonical(authority)) == binding["authority_sha256"] and
            authority["not_before"] <= time.time() < authority["deadline"] and
            self.boot_id() == binding["boot_id"], "case fenced, expired or changed")

    def validate_authority(self, authority, binding):
        from offline_case.case import validate_authority
        from offline_case.admission import NativeAdmission
        build = parse(pinned_bytes(BASE / "integration-manifest.json", root_owned=True), 262144)
        selector = NativeAdmission.from_configuration(build=build)
        info = os.statvfs("/")
        validate_authority(authority, build, now=int(time.time()),
            free=info.f_bavail * info.f_frsize, boot=self.boot_id())
        require(sha(canonical(authority)) == binding["authority_sha256"] and
                authority["host_selector_sha256"] == selector.selector_sha256,
                "root consumed authority differs from original selector")

    def resource_usage(self):
        from herdr.runtime import scheduler_resource_usage
        from herdr.scheduler import DynamicChildScheduler
        # This empty scheduler supplies no ROOT claim. The original queue/epoch
        # is the ROOT claim; telemetry is measured by the original host adapter.
        return scheduler_resource_usage(DynamicChildScheduler(), time.monotonic(), "")

    def pane_pid(self, pane):
        data = self.invoke(["pane", "process-info", "--pane", pane], timeout_seconds=10)
        pid = data["result"]["process_info"]["shell_pid"]
        require(type(pid) is int and pid > 0, "owned native shell unavailable")
        return pid

    def _wait_pane(self, pane, marker):
        until = time.monotonic() + 15
        while True:
            data = self.invoke(["pane", "process-info", "--pane", pane], timeout_seconds=10)
            if self.sandbox.pane_input_ready(data["result"]["process_info"], marker): break
            require(time.monotonic() < until, "owned shell not ready")
            time.sleep(.05)
        self.sandbox.verify_pane_prompt(self.invoke, pane, marker, timeout_seconds=10)

    def early_root_pane(self, task):
        from herdr.canonical_case_claim import task_session_identity
        _, marker = task_session_identity(task)
        self._start_native_server(task)
        # Same ordinary native server/workspace/pane route as the accepted
        # clean_envelope host_run. A shell pane supplies a real owned command IO.
        layout = self.invoke(["workspace", "create", "--cwd", task["workspace"],
            "--label", "Offline canonical ROOT", "--env", "HERDR_DURABLE_TASK_PANE=" + marker,
            "--no-focus"], timeout_seconds=15)["result"]
        control = layout["root_pane"]["pane_id"]
        self._wait_pane(control, marker)
        # Actual original ancestry guard runs under UID0 in the immediately
        # following closed ROOT-base effect, before any SDK/factory launch.
        worker = self.invoke(["tab", "create", "--workspace", layout["workspace"]["workspace_id"],
            "--cwd", task["workspace"], "--label", "Offline owned ROOT worker",
            "--env", "HERDR_DURABLE_TASK_PANE=" + marker, "--no-focus"], timeout_seconds=15)
        pane = worker["result"]["root_pane"]["pane_id"]
        require(pane != control, "root pane reused native control pane")
        self._wait_pane(pane, marker)
        return pane, marker

    def _start_native_server(self, task):
        from herdr.canonical_case_claim import attempt_journal, claimed_root_identity
        from herdr.host_configuration import _read_configuration
        from herdr.policy_launch import process_start_ticks
        root = Path(task["task_file"]).parent.parent
        journal = attempt_journal({"root": root, "identity": claimed_root_identity(task), "recovery": True})
        layout = _read_configuration(Path("/etc/herdr/offline-03414499dd0d1986/native-layout.json"))
        from offline_case.native_source import NATIVE_SHA256
        require(layout["native_sha256"] == NATIVE_SHA256 and
                sha(pinned_bytes(self.real_binary, maximum=32_000_000, root_owned=True)) == NATIVE_SHA256,
                "exact native executable source changed")
        # Source intent is consumed before creating the ONLY owned native server.
        # No attachment to a live host pane/session and no restart after loss.
        journal.publish_once("native-server-start-intent", {"session": SESSION,
            "native_sha256": layout["native_sha256"], "task_id": task["id"], "run_token": task["run_token"]})
        process = subprocess.Popen([str(self.real_binary), "--session", SESSION, "server"],
            cwd=task["workspace"], env=self.env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, close_fds=True)
        journal.publish_once("native-server-started", {"session": SESSION, "pid": process.pid,
            "start_ticks": process_start_ticks(process.pid)})
        until = time.monotonic() + 25
        while True:
            require(process.poll() is None and time.monotonic() < until, "owned native server unavailable")
            result = self.runner.run(["workspace", "list"], timeout_seconds=5)
            if result.returncode == 0: break
            time.sleep(.05)

    def child_pane(self, root, rec, launch, startup_challenge):
        marker = "child-" + rec.run_token
        from herdr.canonical_startup_observation import AuthenticatedStartupObservation
        launch.verify_spawn_source(lambda: self.pane_pid(root.pane),
            observation=AuthenticatedStartupObservation("child-parent-startup-source", startup_challenge))
        env = launch.environment()
        env["HERDR_DURABLE_TASK_PANE"] = marker
        args = ["pane", "split", "--pane", root.pane, "--direction", "right", "--cwd", str(rec.worktree_identity.rsplit("|", 1)[0])]
        args += [value for key, item in env.items() for value in ("--env", key + "=" + item)]
        args += ["--no-focus"]
        pane = self.invoke(args, timeout_seconds=15)["result"]["pane"]["pane_id"]
        require(pane != root.pane, "child pane reused ROOT")
        self._wait_pane(pane, marker)
        return pane

    def root_base_request(self, parts, binding, pane):
        from herdr.policy_launch import process_start_ticks
        task, identity = parts["task"], parts["identity"]
        pane_id, marker = pane
        return {"kind": "PUBLISH_ROOT_ROSTER", "role": "root", "binding": binding,
            "identity": identity.to_json(), "workspace": task["workspace"], "marker": marker,
            "pane_id": pane_id, "shell_pid": self.pane_pid(pane_id), "controller_pid": os.getpid(),
            "controller_start_ticks": process_start_ticks(os.getpid())}

    def roster_request(self, entry, parts, binding):
        from herdr.policy_launch import process_start_ticks
        return {"kind": "PUBLISH_ROOT_ROSTER", "role": "root", "binding": binding,
            "identity": entry.identity.to_json(), "workspace": str(entry.workspace),
            "marker": entry.marker, "pane_id": entry.pane, "shell_pid": self.pane_pid(entry.pane),
            "controller_pid": os.getpid(), "controller_start_ticks": process_start_ticks(os.getpid()),
            "plan_sha256": entry.launch.mount.private_mount_plan.sha256,
            "grant_sha256": entry.launch.grant.hash}

    def child_parent_source_request(self, root, binding):
        from herdr.policy_launch import process_start_ticks
        return {"kind": "VERIFY_NATIVE_SOURCE", "role": "root", "binding": binding,
            "identity": root.identity.to_json(), "pane_id": root.pane, "shell_pid": self.pane_pid(root.pane),
            "controller_pid": os.getpid(), "controller_start_ticks": process_start_ticks(os.getpid()),
            "plan_sha256": root.launch.mount.private_mount_plan.sha256,
            "grant_sha256": root.launch.grant.hash}

    def preparation_request(self, entry, ticket, binding):
        ticket.revalidate()
        return {"kind": "START_NATIVE_PREPARATION", "role": entry.role, "binding": binding,
            "identity": entry.identity.to_json(), "plan_sha256": ticket.plan.sha256,
            "grant_sha256": entry.launch.grant.hash, "pane_id": entry.pane,
            "shell_pid": self.pane_pid(entry.pane), "record_sha256": sha(canonical(ticket.record))}

    def _runtime_context(self, entry):
        from herdr.host_configuration import _read_configuration
        context = _read_configuration(META / (entry.role + ".json"))
        runtime = _read_configuration(META / (entry.role + ".runtime.json"))
        require(context["identity"] == entry.identity.to_json() and
            context["grant_sha256"] == entry.prepared_grant_sha256 and
            context["plan_sha256"] == entry.launch.mount.private_mount_plan.sha256 and
            runtime["context_sha256"] == sha(canonical(context)) and
            runtime["role"] == entry.role and runtime["unit"] == context["unit"],
            "root-observed original preparation context changed")
        return context, runtime

    def observe_prepared(self, entry):
        context, runtime = self._runtime_context(entry)
        attestation = {"authority": "agent-task-worker" if entry.role == "root" else "herdr-runtime",
            "kind": "native-preparation-v2", "task_id": entry.identity.task_id,
            "run_token": entry.identity.run_token, "fencing_token": entry.identity.fencing_token,
            "sandbox_pid": runtime["pid"], "pane_id": entry.pane, "marker": entry.marker,
            "agent_name": entry.identity.agent_id, "policy_sha256": sha(entry.policy.read_bytes()),
            "approved_profile": entry.launch.private_profile_snapshot.identity,
            "immutable_sources": entry.launch.mount.immutable_source_evidence()}
        if entry.role == "child":
            from herdr.owned_write_mounts import validate_owned_mount_evidence
            attestation.update(worktree_identity=entry.record.worktree_identity,
                ownership_sha256=entry.record.ownership.hash,
                owned_write_mounts=entry.pins.evidence())
        return runtime["pid"], attestation

    def verify_boundary(self, entry, pid):
        return self.sandbox.verify(pid, self.real_binary, entry.marker, policy=entry.policy,
            attempts=1, pinned_worktree=entry.launch.mount.private_workspace_pin,
            child_workspace_writable=False, policy_mount=entry.launch.mount,
            **({"owned_write_pins": entry.pins} if entry.pins is not None else {}),
            private_profile_snapshot=entry.launch.private_profile_snapshot)

    def preparation_proof(self, entry, binding):
        context, runtime = self._runtime_context(entry)
        # The original verifier checks actual capped FD/private paths and kernel
        # namespace. These are derived only after that decision, not input flags.
        require(self.verify_boundary(entry, runtime["pid"]), "root native preparation proof denied")
        return {"binding": binding, "sdk_imported": False,
                "setup_fds_closed": True, "setup_paths_hidden": True}

    def root_session(self, entry, task, proof):
        from herdr.canonical_case_claim import task_session_identity
        agent, marker = task_session_identity(task)
        return {"agent_name": agent, "session_name": marker, "pane_id": entry.pane,
            "pane_marker": marker, "coordinator_agent": entry.identity.parent_agent_id,
            "coordinator_pane_id": entry.pane, "owned_pane": True,
            "launch_identity": entry.identity.to_json(), "economic_delivery_attempted": False,
            "agent_start_attempted": False, "pane_split_started": True, "launch_intent_version": 1,
            "created_at": datetime.now(UTC).isoformat(), "sandbox_pid": entry.sandbox_pid,
            "sandbox_attestation": entry.attestation, "sandbox_verified": True, "invocation_policy": proof}

    def pin_child(self, workspace, expected):
        # The exact original PinnedWorktree is a held descriptor value, not a
        # pathname factory. Open/verify it before passing to canonical children.
        fd = os.open(workspace, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(fd)
            require(stat.S_ISDIR(info.st_mode), "child worktree not a directory")
            pin = self.sandbox.PinnedWorktree(Path(workspace), fd, info.st_dev, info.st_ino)
            require(pin.identity == expected, "original pinned child worktree changed")
            pin.verify()
            return pin
        except BaseException:
            os.close(fd)
            raise

    def child_environment(self, root, task):
        return {**self.env, "HERDR_ENV": "1", "HERDR_PANE_ID": root.pane,
            "HERDR_PROFILE": task["safety_profile"], "HERDR_HERMES_PROFILE": task["hermes_profile"]}

    def host_reference(self, entry):
        from herdr.host_reference_binding import derive_host_reference
        value = derive_host_reference(entry.launch.grant, entry.launch.private_profile_snapshot)
        require(type(value) is dict and len(value) == 13, "original thirteen-field opaque reference required")
        return value

    def unit_source(self, unit):
        require(unit == CASE, "foreign owned case unit")
        return sha(pinned_bytes(Path("/etc/systemd/system") / unit, root_owned=True))

    def root_unit_receipt(self, binding, claim):
        # Root publishes this via the SAME finite effect pump, not a caller tuple.
        from herdr.canonical_case_claim import root_metadata
        row = root_metadata("case-unit", binding)
        require(row["source_sha256"] == claim["source_sha256"] and row["unit"] == CASE,
                "root unit-bound receipt changed")
        return row

    def historical_closure(self, binding, roster):
        from herdr.canonical_case_claim import root_metadata
        row = root_metadata("closure", binding)
        require(row["roster_sha256"] == sha(canonical(roster)), "historical holder roster changed")
        return row["observation"]

    def require_historical_namespace_closed(self, binding, row, proof):
        from herdr.canonical_case_claim import root_metadata
        closed = root_metadata("closure", binding)
        role = row["role"]
        require(closed["namespaces"].get(role) == proof and
            closed["observation"]["complete"] is True, "historic namespace closure unproven")

    def verify_releases(self, parts, scheduler, roster):
        from herdr.launch_ownership import _read
        for row in roster:
            from herdr.security import InvocationIdentity
            identity = InvocationIdentity.from_dict(row["identity"])
            require(_read(parts["factory"].storage, identity) is None, "original launch ownership still held")
            if row["role"] != "child": continue
            require(scheduler is not None, "canonical child release ledger unavailable")
            rec = scheduler.record_for(identity.task_id)
            require(rec.attempt_state == "terminal" and rec.cleanup_complete and rec.lease is None,
                    "canonical child cleanup still held")
            entries = parts["admission_registry"]._read()
            require(not any(item["agent_id"] == identity.agent_id and item["task_id"] == identity.task_id
                and item["fencing_token"] == identity.fencing_token for item in entries),
                "original admission reservation still held")
            if rec.ownership_reservation:
                state = scheduler.ownership_registry.snapshot()
                found = state["reservations"].get(rec.ownership_reservation) or scheduler.ownership_registry.retired_reservation(rec.ownership_reservation)
                require(found is not None and found["state"] == "released", "original ownership reservation still held")
