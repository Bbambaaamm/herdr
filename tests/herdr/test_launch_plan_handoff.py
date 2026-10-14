"""Live FD handoff in disposable files; root records/runtime checks are doubles."""
from dataclasses import replace
from datetime import UTC, datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import threading
import time

import pytest

from herdr import host_configuration, launch_plan_handoff as handoff, private_mount_plan
from herdr.policy_launch import PreparedPolicyLaunch
from herdr.private_mount_plan import PinnedLaunchPath, request_for
from herdr.result_submission import reserve_empty_result, reservation_binding, ResultSlot
from herdr.security import SecurityError, canonical_json_bytes
from tests.herdr.test_policy_launch import grant
from tests.herdr.test_private_profile_fd_bridge import fixture_snapshot
from tests.herdr.test_private_host_composition import private_config


@pytest.fixture
def live(tmp_path, monkeypatch):
    proposals = tmp_path / "proposals"; proposals.mkdir(mode=0o700)
    plans = tmp_path / "plans"; plans.mkdir()
    workspace = tmp_path / "workspace"; workspace.mkdir()
    approved = replace(grant(workspace), expires_at=(datetime.now(UTC) + timedelta(minutes=5)).isoformat())
    result = reserve_empty_result(tmp_path / "result.json", approved.identity, "fixture-result")
    slot = ResultSlot.bind(result, approved.identity, "fixture-result")
    work = PinnedLaunchPath(workspace, directory=True)
    output = PinnedLaunchPath(result, directory=False, expected=(slot.device, slot.inode),
                             reservation=reservation_binding(slot))
    _, inputs, profile = fixture_snapshot(tmp_path)
    mount = SimpleNamespace(private_mount_plan=None, private_mount_request=None, private_mount_argv=None,
                            private_workspace_pin=work, private_result_pin=output,
                            require_immutable_runtime=lambda: None)
    launch = PreparedPolicyLaunch(mount, approved, None, "fixture")
    launch.private_profile_snapshot = profile
    launch.private_plan_handoff = handoff.LaunchPlanHandoff(proposals, 2)
    launch._private_handoff_verify = lambda: True
    state = {"time": 0.0, "sleep": None, "fault": None}
    def sleep(seconds):
        state["time"] += seconds
        if state["sleep"] is not None: state["sleep"]()
    monkeypatch.setattr(handoff, "time", SimpleNamespace(monotonic=lambda: state["time"], sleep=sleep))
    monkeypatch.setattr(handoff, "AUTHORITY_ROOT", plans)
    monkeypatch.setattr(private_mount_plan, "AUTHORITY_ROOT", plans)
    # Only root configuration reads and immutable root attachment are doubles.
    # Real sealed memfds, reservation xattrs, pinned FDs and file/fsync/rename remain.
    monkeypatch.setattr(host_configuration, "_read_configuration", lambda path: json.loads(Path(path).read_bytes()))
    calls = []
    def builder():
        calls.append("build")
        descriptors = [work.descriptor(), output.descriptor(), *profile.fd_descriptors()]
        argv = ["/usr/bin/bwrap", "--unshare-net", "--bind-fd", str(work.fd), str(work.logical),
                "--bind-fd", str(output.fd), str(output.logical), *profile.mount_arguments(),
                "--", "/bin/bash", "--noprofile", "--norc", "-i"]
        if state["fault"] is not None: state["fault"](descriptors, argv)
        mount.private_mount_request = request_for(launch.identity, descriptors, argv)
        mount.private_mount_argv = argv
        if mount.private_mount_plan is None: raise RuntimeError("durable_private_mount_plan_unapproved")
        mount.private_mount_plan.authorize(descriptors, argv)
        return argv
    def approve():
        target = plans / (hashlib.sha256(canonical_json_bytes(launch.identity.to_json())).hexdigest() + ".json")
        target.write_bytes(canonical_json_bytes(mount.private_mount_request))
        return target
    try:
        yield SimpleNamespace(launch=launch, state=state, builder=builder, approve=approve,
                              proposals=proposals, plans=plans, work=work, output=output,
                              profile=profile, inputs=inputs, calls=calls)
    finally:
        profile.close(); work.close(); output.close()


def test_worker_waits_for_independent_plan_then_consumes_exact_live_fds(live):
    live.state["sleep"] = live.approve
    argv = live.launch.prepare_private_command(live.builder)
    assert argv == live.launch.mount.private_mount_argv
    assert len(live.calls) >= 4
    assert live.launch.mount.private_mount_plan is not None
    proposal = next(live.proposals.glob("*.json"))
    raw = proposal.read_bytes(); record = json.loads(raw)
    assert record["schema_version"] == handoff.VERSION
    assert record["owner_pid"] == os.getpid()
    assert record["grant_sha256"] == live.launch.grant.hash
    assert record["approved_profile"] == live.profile.identity
    assert record["plan"] == live.launch.mount.private_mount_request
    assert all(body not in raw for body in live.inputs.values())
    assert proposal.stat().st_mode & 0o777 == 0o400
    assert live.work.fd >= 0 and live.output.fd >= 0


def test_separate_operator_publisher_releases_waiting_worker_with_real_file_operations(live, monkeypatch):
    from herdr import launch_plan_publication as publication
    monkeypatch.setattr(handoff, "time", time)
    live.launch.private_plan_handoff.timeout_seconds = 3
    approvals = live.proposals.parent / "approvals"; approvals.mkdir()
    monkeypatch.setattr(publication, "APPROVAL_ROOT", approvals)
    monkeypatch.setattr(publication, "AUTHORITY_ROOT", live.plans)
    monkeypatch.setattr(publication, "_verify_root_owned_ancestry", lambda path: None)
    class OperatorOS:
        def __getattr__(self, name):
            return (lambda: 0) if name == "geteuid" else getattr(os, name)
    # Scope the root-UID double to the publisher; the waiting worker retains
    # its actual UID for the real result reservation ownership check.
    monkeypatch.setattr(publication, "os", OperatorOS())
    monkeypatch.setattr(publication, "_root_owner", lambda info: None)
    errors = []
    def operator():
        try:
            deadline = time.monotonic() + 3
            while not list(live.proposals.glob("*.json")):
                if time.monotonic() >= deadline: raise AssertionError("proposal unavailable")
                time.sleep(0.01)
            proposal = next(live.proposals.glob("*.json"))
            record = json.loads(proposal.read_bytes())
            # This fixture operator independently checks the expected grant,
            # profile and actual held source FDs; it models trusted approval.
            assert record["grant_sha256"] == live.launch.grant.hash
            assert record["approved_profile"] == live.profile.identity
            assert record["plan"]["descriptors"] == [live.work.descriptor(), live.output.descriptor(), *live.profile.fd_descriptors()]
            now = datetime.now(UTC)
            ticket = {"schema_version": publication.TICKET_VERSION, "plan": record["plan"],
                      "argv": record["argv"], "not_before": (now - timedelta(seconds=1)).isoformat(),
                      "expires_at": (now + timedelta(minutes=1)).isoformat()}
            selected = approvals / proposal.name
            selected.write_bytes(canonical_json_bytes(ticket))
            assert publication.publish_approved_launch_plan(selected, publish=True)["published"] is True
        except BaseException as exc: errors.append(exc)
    thread = threading.Thread(target=operator)
    thread.start()
    try:
        assert live.launch.prepare_private_command(live.builder)[0] == "/usr/bin/bwrap"
    finally:
        thread.join(timeout=4)
    assert not thread.is_alive() and errors == []


@pytest.mark.parametrize("fault", ["deadline", "grant", "proposal"])
def test_drift_during_final_bound_builder_denies_before_pane(live, fault):
    live.state["sleep"] = live.approve
    def builder():
        result = live.builder()
        if fault == "deadline": live.state["time"] = 2.0
        elif fault == "grant": live.launch.grant = replace(live.launch.grant, grant_id="late-grant")
        else:
            proposal = next(live.proposals.glob("*.json")); proposal.chmod(0o600); proposal.write_text("{}")
        return result
    with pytest.raises(SecurityError): live.launch.prepare_private_command(builder)


def test_missing_approval_times_out_without_self_publication_and_preserves_proposal(live):
    with pytest.raises(SecurityError, match="timed out"):
        live.launch.prepare_private_command(live.builder)
    assert list(live.plans.iterdir()) == []
    assert len(list(live.proposals.glob("*.json"))) == 1
    assert live.launch.mount.private_mount_plan is None
    assert live.work.fd >= 0 and live.output.fd >= 0


def test_existing_proposal_is_never_overwritten_or_reused_after_restart(live):
    with pytest.raises(SecurityError, match="timed out"):
        live.launch.prepare_private_command(live.builder)
    path = next(live.proposals.glob("*.json")); old = path.read_bytes()
    with pytest.raises(FileExistsError): live.launch.prepare_private_command(live.builder)
    assert path.read_bytes() == old
    assert len(list(live.proposals.glob(".proposal-*"))) == 1


@pytest.mark.parametrize("fault", ["grant", "grant-replaced", "profile-replaced", "authority", "result-content", "result-path", "closed-profile", "runtime"])
def test_late_authority_or_physical_drift_denies_even_if_plan_arrives(live, fault):
    def attack():
        live.approve()
        if fault == "grant":
            live.launch.grant = replace(live.launch.grant, expires_at="2020-01-01T00:00:00+00:00")
        elif fault == "grant-replaced": live.launch.grant = replace(live.launch.grant, grant_id="different-grant")
        elif fault == "profile-replaced": live.profile.name = "different"
        elif fault == "authority": live.launch._private_handoff_verify = lambda: False
        elif fault == "result-content": live.output.logical.write_bytes(b"forged-result")
        elif fault == "result-path":
            live.output.logical.rename(live.output.logical.with_suffix(".old"))
            live.output.logical.write_bytes(b"")
        elif fault == "closed-profile": live.profile.close()
        else:
            def denied(): raise SecurityError("root runtime changed")
            live.launch.mount.require_immutable_runtime = denied
    live.state["sleep"] = attack
    with pytest.raises((SecurityError, RuntimeError, OSError, ValueError)): live.launch.prepare_private_command(live.builder)
    assert live.launch.mount.private_mount_plan is None
    assert len(list(live.proposals.glob("*.json"))) == 1


@pytest.mark.parametrize("fault", ["bytes", "replace", "symlink", "hardlink", "mode", "directory"])
def test_same_uid_proposal_tampering_is_a_denial_and_never_an_approval(live, fault):
    def attack():
        path = next(live.proposals.glob("*.json"))
        if fault == "bytes": path.chmod(0o600); path.write_text("{}")
        elif fault == "replace":
            path.rename(path.with_suffix(".old")); path.write_text("{}")
        elif fault == "symlink":
            path.rename(path.with_suffix(".old")); path.symlink_to(path.with_suffix(".old"))
        elif fault == "hardlink": os.link(path, path.with_suffix(".alias"))
        elif fault == "mode": path.chmod(0o600)
        else:
            live.proposals.rename(live.proposals.with_name("old-proposals"))
            live.proposals.mkdir(mode=0o700)
        live.approve()
    live.state["sleep"] = attack
    with pytest.raises((SecurityError, OSError)): live.launch.prepare_private_command(live.builder)
    assert live.launch.mount.private_mount_plan is None


@pytest.mark.parametrize("fault", ["argv", "descriptor", "secret-env", "command"])
def test_changed_command_or_descriptor_cannot_use_arriving_approval(live, fault):
    def attack():
        live.approve()
        def changed(entries, argv):
            if fault == "argv": argv.insert(1, "--new-session")
            elif fault == "descriptor": entries[0]["inode"] += 1
            elif fault == "secret-env": argv[1:1] = ["--setenv", "API_TOKEN", "do-not-persist"]
            else: argv[-1] = "execute-another-command"
        live.state["fault"] = changed
    live.state["sleep"] = attack
    with pytest.raises(SecurityError): live.launch.prepare_private_command(live.builder)
    assert live.launch.mount.private_mount_plan is None
    assert b"do-not-persist" not in next(live.proposals.glob("*.json")).read_bytes()


def test_malformed_root_record_is_not_polled_or_treated_as_missing(live):
    def attack(): live.approve().write_text("{}")
    live.state["sleep"] = attack
    with pytest.raises(SecurityError, match="identity mismatch"):
        live.launch.prepare_private_command(live.builder)
    assert live.state["time"] == 0.2


def test_plan_for_different_fence_cannot_release_this_worker(live):
    def attack():
        target = live.approve(); value = json.loads(target.read_bytes())
        value["identity"]["fencing_token"] += 1
        target.write_bytes(canonical_json_bytes(value))
    live.state["sleep"] = attack
    with pytest.raises(SecurityError, match="identity mismatch"):
        live.launch.prepare_private_command(live.builder)


def test_approval_arriving_at_deadline_is_denied(live):
    live.state["sleep"] = lambda: (live.state.update(time=2.0), live.approve())
    with pytest.raises(SecurityError, match="timed out"):
        live.launch.prepare_private_command(live.builder)
    assert live.launch.mount.private_mount_plan is None


def test_unrelated_builder_error_never_publishes_proposal(live):
    def fail(): raise RuntimeError("unrelated")
    with pytest.raises(RuntimeError, match="unrelated"): live.launch.prepare_private_command(fail)
    assert list(live.proposals.iterdir()) == []


@pytest.mark.parametrize("value", [0, 61, True, 0.5, "30", None])
def test_handoff_requires_finite_integer_deadline(tmp_path, value):
    tmp_path.chmod(0o700)
    with pytest.raises(SecurityError, match="finite"): handoff.LaunchPlanHandoff(tmp_path, value)


@pytest.mark.parametrize("fault", ["symlink", "mode", "missing"])
def test_handoff_rejects_invalid_proposal_directory(tmp_path, fault):
    path = tmp_path / "proposals"
    if fault != "missing": path.mkdir(mode=0o700)
    if fault == "mode": path.chmod(0o755)
    elif fault == "symlink":
        path.rename(tmp_path / "real"); path.symlink_to(tmp_path / "real", target_is_directory=True)
    with pytest.raises((SecurityError, OSError)): handoff.LaunchPlanHandoff(path, 30)


def test_only_closed_trusted_host_configuration_enables_handoff(tmp_path, monkeypatch):
    raw, _, _, _ = private_config(tmp_path, monkeypatch)
    proposals = tmp_path / "proposals"; proposals.mkdir(mode=0o700)
    assert host_configuration.build_host_policy_factory().private_plan_handoff is None
    raw["private_launch"]["plan_handoff"] = {"proposal_directory": str(proposals), "timeout_seconds": 30}
    factory = host_configuration.build_host_policy_factory()
    assert isinstance(factory.private_plan_handoff, handoff.LaunchPlanHandoff)
    assert factory.private_plan_handoff.directory == proposals
    raw["private_launch"]["plan_handoff"]["worker_approval"] = True
    with pytest.raises(SecurityError, match="closed host"):
        host_configuration.build_host_policy_factory()


def test_handoff_proposals_cannot_live_under_admitted_workspace(tmp_path, monkeypatch):
    raw, workspace, _, _ = private_config(tmp_path, monkeypatch)
    proposals = workspace / "proposals"; proposals.mkdir(mode=0o700)
    raw["private_launch"]["plan_handoff"] = {"proposal_directory": str(proposals), "timeout_seconds": 30}
    with pytest.raises(SecurityError, match="admitted write roots"):
        host_configuration.build_host_policy_factory()


def test_successful_automatic_publication_has_a_bounded_binding_window(live, monkeypatch):
    from herdr.launch_plan_issuer import AutomaticLaunchPlanClient
    client = AutomaticLaunchPlanClient("a" * 64, 2)
    live.launch.private_plan_handoff.automatic_issuer = client
    budgets = []
    def issue(launch, published, *, deadline):
        budgets.append(deadline)
        launch._private_issuer_reconciliation_deadline = deadline + live.launch.private_plan_handoff.timeout_seconds
        # Successful publication consumes the setup/issuer budget. A fresh,
        # finite binding phase is needed for this already committed identity.
        live.state["time"] = deadline
        live.approve()
    monkeypatch.setattr(client, "issue", issue)
    assert live.launch.prepare_private_command(live.builder)[0] == "/usr/bin/bwrap"
    assert budgets == [2.0]
    assert live.launch._private_handoff_state[1] == 4.0
    live.state["time"] = 4.0
    with pytest.raises(SecurityError, match="timed out"):
        live.launch.private_plan_handoff.verify_bound(live.launch)
    assert len(list(live.plans.iterdir())) == 1


def test_unresolved_automatic_exchange_blocks_with_retained_identity(live, monkeypatch):
    from herdr.launch_plan_issuer import AutomaticLaunchPlanClient
    client = AutomaticLaunchPlanClient("a" * 64, 2)
    live.launch.private_plan_handoff.automatic_issuer = client
    calls = []
    def issue(*args, **kwargs):
        calls.append(True)
        raise TimeoutError("ambiguous automatic exchange")
    monkeypatch.setattr(client, "issue", issue)
    with pytest.raises(handoff.LaunchPlanReconciliationRequired):
        live.launch.prepare_private_command(live.builder)
    assert len(calls) == 1 and len(list(live.proposals.glob("*.json"))) == 1
    assert not list(live.plans.glob("*.json"))
    retained = next(live.proposals.glob("*.json")).read_bytes()
    with pytest.raises(handoff.LaunchPlanReconciliationRequired, match="retained proposal"):
        live.launch.prepare_private_command(live.builder)
    assert len(calls) == 1 and next(live.proposals.glob("*.json")).read_bytes() == retained


@pytest.mark.parametrize("check", ["proposal", "live"])
def test_retained_proposal_validation_failure_blocks_before_exchange(live, monkeypatch, check):
    from herdr.launch_plan_issuer import AutomaticLaunchPlanClient
    client = AutomaticLaunchPlanClient("a" * 64, 2)
    live.launch.private_plan_handoff.automatic_issuer = client
    monkeypatch.setattr(client, "issue", lambda *args, **kwargs: pytest.fail("invalid proposal contacted issuer"))
    method = "_verify_proposal" if check == "proposal" else "_live"
    original = getattr(live.launch.private_plan_handoff, method)
    def withdrawn(*args):
        if list(live.proposals.glob("*.json")):
            raise SecurityError("retained proposal authority withdrawn")
        return original(*args)
    monkeypatch.setattr(live.launch.private_plan_handoff, method, withdrawn)
    with pytest.raises(handoff.LaunchPlanReconciliationRequired):
        live.launch.prepare_private_command(live.builder)
    assert len(list(live.proposals.glob("*.json"))) == 1
    assert not list(live.plans.glob("*.json"))
