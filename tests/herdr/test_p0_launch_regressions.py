"""Current-HEAD regressions: bootstrap provenance, teardown and durable sources."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr.policy_launch import PreparedPolicyLaunch, SecurityError, validate_policy_evidence
from herdr.host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE
from tests.herdr.test_policy_launch import mount, grant, proof_scheduler, attest_proof


def private_evidence(proof):
    from herdr.private_profile_namespace import profile_identity
    result = json.loads(json.dumps(proof))
    result["approved_profile"] = profile_identity("quantlab", {"config.yaml": "a" * 64, ".env": "b" * 64})
    from tests.policy_launch_fakes import immutable_sources_fixture
    result["immutable_sources"] = immutable_sources_fixture(result)
    return result


@pytest.mark.parametrize("failure", ["stage", "bootstrap", "code", "runtime", "ownership"])
def test_every_resource_closes_after_independent_teardown_failure(tmp_path, monkeypatch, failure):
    from herdr.policy_launch import _LIVE_PREPARED_LAUNCHES, _launch_key
    workspace = tmp_path / "work"
    workspace.mkdir()
    item = mount(tmp_path)
    launch = PreparedPolicyLaunch(item, grant(workspace), object(), "test")
    released = []
    def broken(label):
        released.append(label)
        if label == failure:
            raise SecurityError("first failure: " + label)
    if failure == "stage":
        monkeypatch.setattr(item.stage, "_same_inode", lambda: broken("stage"))
    for label, tree in zip(("code", "runtime", "runtime2"), (item.code, *item.runtime)):
        if label == failure:
            monkeypatch.setattr(tree, "verify", lambda label=label: broken(label))
    item.bootstrap = SimpleNamespace(cleanup_after_pane_closed=lambda: broken("bootstrap"))
    launch._ownership = SimpleNamespace(cleanup_after_pane_closed=lambda: broken("ownership"))
    launch.private_profile_snapshot = SimpleNamespace(close=lambda: released.append("profile"))
    _LIVE_PREPARED_LAUNCHES[_launch_key(launch.identity)] = launch
    with pytest.raises(SecurityError, match="first failure: " + failure):
        launch.cleanup_after_pane_closed()
    assert item.stage.fd == -1
    assert all(tree.fd == -1 for tree in (item.code, *item.runtime))
    assert {"bootstrap", "ownership", "profile"} <= set(released)
    assert _launch_key(launch.identity) not in _LIVE_PREPARED_LAUNCHES
    assert launch._private_key is None
    # Closed trees do not reverify dead FDs on an idempotent retry.
    for tree in (item.code, *item.runtime):
        tree.cleanup_after_pane_closed()


def test_bootstrap_shim_executes_original_approved_policy_inode():
    root = Path(__file__).resolve().parents[2]
    shim = (root / SHIM_SOURCE).read_text()
    assert "/run/herdr/policy-code/" + STAGE1_SOURCE in shim
    assert "exec /usr/bin/python3 -I -S /run/herdr-bootstrap/" not in shim
    source = (root / STAGE1_SOURCE).read_text()
    assert 'STAGE1_PATH = Path("/run/herdr/policy-code/' + STAGE1_SOURCE + '")' in source


def test_host_broker_admits_only_the_original_policy_stage1_path(tmp_path, monkeypatch):
    from herdr import host_bootstrap
    from herdr.policy_launch import CODE_TARGET
    selected = []
    monkeypatch.setattr(host_bootstrap, "_DurableBootstrapAuthority",
                        lambda **kwargs: selected.append(kwargs) or object())
    fd = os.open(tmp_path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        launch = SimpleNamespace(mount=SimpleNamespace(code=SimpleNamespace(target=CODE_TARGET)))
        host_bootstrap.HostBootstrap(launch, object(), {}, object(), tmp_path / "s", fd)
        assert selected[0]["stage1_path"] == str(CODE_TARGET / STAGE1_SOURCE)
    finally:
        os.close(fd)


def test_legacy_private_launch_cannot_recover_as_immutable(tmp_path):
    from herdr.security import InvocationIdentity
    _, _, _, proof = proof_scheduler(tmp_path)
    private = private_evidence(proof)
    identity = InvocationIdentity.from_dict(private["identity"])
    assert validate_policy_evidence(private, identity=identity) == private
    del private["immutable_sources"]
    with pytest.raises(SecurityError, match="bounded policy evidence"):
        validate_policy_evidence(private, identity=identity)


def test_child_source_identity_is_durable_and_cannot_be_rotated_in_replay(tmp_path):
    from herdr.scheduler import DynamicChildScheduler, AuditLog, SchedulerError
    scheduler, record, marker, evidence = proof_scheduler(tmp_path)
    proof = private_evidence(evidence)
    assert attest_proof(scheduler, record, marker, proof)
    for field in ("approved_profile", "immutable_sources"):
        assert record.execution_sandbox_attestation[field] == proof[field]
    recovered = DynamicChildScheduler(audit_log=AuditLog(tmp_path / "proof-events"))
    recovered.replay()
    assert recovered._tasks[record.id].execution_sandbox_attestation == record.execution_sandbox_attestation
    path = tmp_path / "proof-events"
    events = [json.loads(line) for line in path.read_text().splitlines()]
    event = next(row for row in events if row["event"] == "execution_sandbox_attested")
    event["attestation"]["approved_profile"]["manifest_sha256"] = "0" * 64
    path.write_text("".join(json.dumps(row) + "\n" for row in events))
    with pytest.raises(SchedulerError, match="invocation policy"):
        DynamicChildScheduler(audit_log=AuditLog(path)).replay()
