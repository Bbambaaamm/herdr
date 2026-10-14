"""Compact proof bounds and real replay mode checks; root publication is doubled."""
from copy import deepcopy
import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

from herdr import policy_launch as launch
from herdr.host_bootstrap import SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE
from herdr.private_mount_plan import ApprovedPrivateMountPlan
from herdr.private_profile_namespace import profile_identity
from herdr.security import InvocationIdentity, SecurityError, canonical_json_bytes
from tests.policy_launch_fakes import policy_fixture, immutable_sources_fixture


@pytest.fixture
def emitted(tmp_path, monkeypatch):
    identity = InvocationIdentity('github:compact', 'parent', 'coordinator', 'coordinator-task', 'task', 'run', 1)
    proof = policy_fixture(identity, modern=True)
    profile = profile_identity('quantlab', {'config.yaml': '1' * 64, '.env': '2' * 64})
    seed = immutable_sources_fixture(proof)
    plan = ApprovedPrivateMountPlan(tmp_path / 'plan', identity, 'e' * 64, 1, 5)
    # Only root attachment/approval and bootstrap-file reading are doubles.
    monkeypatch.setattr(ApprovedPrivateMountPlan, 'read', classmethod(lambda cls, *args: plan))
    monkeypatch.setattr(ApprovedPrivateMountPlan, 'evidence', lambda self: seed['mount_plan'])
    from herdr import host_bootstrap
    monkeypatch.setattr(host_bootstrap, 'read_frozen_file', lambda *args: b'bootstrap fixture')
    names = [f'venv/lib/python3.11/site-packages/package_{index:03d}/native/runtime_loader_binary.so'
             for index in range(227)]
    trees = [SimpleNamespace(target=Path(target), path=Path(row['source']),
        source_digest=row['manifest_sha256'], executable_files=tuple(names),
        files=tuple(dict.fromkeys((SHIM_SOURCE, STAGE1_SOURCE, STAGE2_SOURCE), 'f' * 64).items()))
        for target, row in seed['trees'].items()]
    code = next(tree for tree in trees if tree.target == launch.CODE_TARGET)
    mount = SimpleNamespace(require_immutable_runtime=lambda: None, code=code,
        runtime=tuple(tree for tree in trees if tree is not code),
        private_mount_plan=plan, private_identity=identity)
    proof['approved_profile'] = profile
    proof['immutable_sources'] = launch.PolicyMount.immutable_source_evidence(mount)
    return SimpleNamespace(identity=identity, proof=proof, names=names, mount=mount)


def test_real_producer_compacts_large_runtime_inventory_without_raising_frame_limit(emitted):
    item = emitted
    assert item.proof['immutable_sources']['schema_version'] == 'herdr-immutable-sources-2'
    for source in item.proof['immutable_sources']['trees'].values():
        assert 'executable_files' not in source
        assert source['executable_inventory'] == {
            'count': 227, 'sha256': hashlib.sha256(canonical_json_bytes(sorted(item.names))).hexdigest()}
    compact_bytes = len(canonical_json_bytes(item.proof))
    assert compact_bytes < 8192
    assert launch.validate_policy_evidence(item.proof, identity=item.identity) == item.proof
    legacy = deepcopy(item.proof)
    legacy['immutable_sources']['schema_version'] = 'herdr-immutable-sources-1'
    for source in legacy['immutable_sources']['trees'].values():
        source.pop('executable_inventory'); source['executable_files'] = item.names
    assert len(canonical_json_bytes(legacy)) > 16384
    with pytest.raises(SecurityError, match='bounded policy evidence required'):
        launch.validate_policy_evidence(legacy, identity=item.identity)


def test_small_legacy_executable_inventory_still_validates(emitted):
    proof = deepcopy(emitted.proof)
    proof['immutable_sources']['schema_version'] = 'herdr-immutable-sources-1'
    for source in proof['immutable_sources']['trees'].values():
        source.pop('executable_inventory'); source['executable_files'] = ['entry.py']
    assert launch.validate_policy_evidence(proof, identity=emitted.identity) == proof


@pytest.mark.parametrize('fault', ['extra', 'missing-count', 'bad-sha', 'sha-type',
    'bool-count', 'negative-count', 'huge-count', 'string-count', 'null',
    'mixed', 'missing-inventory', 'wrong-version', 'legacy-with-compact', 'modern-with-list'])
def test_closed_compact_inventory_and_version_contract(emitted, fault):
    proof = deepcopy(emitted.proof)
    source = next(iter(proof['immutable_sources']['trees'].values()))
    inventory = source['executable_inventory']
    if fault == 'extra': inventory['extra'] = True
    elif fault == 'missing-count': inventory.pop('count')
    elif fault == 'bad-sha': inventory['sha256'] = 'g' * 64
    elif fault == 'sha-type': inventory['sha256'] = 1
    elif fault == 'bool-count': inventory['count'] = True
    elif fault == 'negative-count': inventory['count'] = -1
    elif fault == 'huge-count': inventory['count'] = 65537
    elif fault == 'string-count': inventory['count'] = '227'
    elif fault == 'null': source['executable_inventory'] = None
    elif fault == 'mixed': source['executable_files'] = ['entry.py']
    elif fault == 'missing-inventory': source.pop('executable_inventory')
    elif fault == 'wrong-version': proof['immutable_sources']['schema_version'] = 'unknown'
    elif fault == 'legacy-with-compact': proof['immutable_sources']['schema_version'] = 'herdr-immutable-sources-1'
    else:
        source.pop('executable_inventory'); source['executable_files'] = ['entry.py']
    with pytest.raises(SecurityError): launch.validate_policy_evidence(proof, identity=emitted.identity)


@pytest.mark.parametrize('fault', ['exec-to-ro', 'ro-to-exec', 'same-count-swap',
    'partial-mode', 'digest', 'count', 'rename'])
def test_cold_replay_recomputes_exact_executable_names_and_canonical_modes(tmp_path, monkeypatch, fault):
    source = tmp_path / 'retained'; source.mkdir()
    executable = source / 'entry.sh'; executable.write_bytes(b'stable executable'); executable.chmod(0o555)
    data = source / 'data.py'; data.write_bytes(b'stable data'); data.chmod(0o444)
    def manifest():
        return {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in source.iterdir()}
    inode = source.stat(); target = str(launch.CODE_TARGET)
    definition = {'source': str(source),
        'manifest_sha256': hashlib.sha256(canonical_json_bytes(manifest())).hexdigest(),
        'executable_inventory': launch._executable_inventory(['entry.sh'])}
    proof = {'identity': InvocationIdentity('github:compact', 'parent', 'coordinator', 'coordinator-task', 'task', 'run', 1).to_json(), 'tree_identities': {target: {'device': inode.st_dev, 'inode': inode.st_ino}},
        'immutable_sources': {'mount_plan': {'authority': '/unit-authority'}, 'executables': {},
            'trees': {target: definition}}}
    # Only root ownership/plan authority are doubles. Walking, content hashes,
    # inode checks and mode/inventory recomputation use actual Linux files.
    monkeypatch.setattr(ApprovedPrivateMountPlan, 'read', classmethod(lambda cls, *args:
        SimpleNamespace(evidence=lambda: proof['immutable_sources']['mount_plan'])))
    monkeypatch.setattr(launch, '_verify_root_owned_ancestry', lambda path: None)
    monkeypatch.setattr(launch, '_verify_immutable_entry', lambda info: None)
    launch.verify_retained_immutable_sources(proof)
    if fault == 'exec-to-ro': executable.chmod(0o444)
    elif fault == 'ro-to-exec': data.chmod(0o555)
    elif fault == 'same-count-swap': executable.chmod(0o444); data.chmod(0o555)
    elif fault == 'partial-mode': executable.chmod(0o544)
    elif fault == 'digest': definition['executable_inventory']['sha256'] = '0' * 64
    elif fault == 'count': definition['executable_inventory']['count'] += 1
    else:
        executable.rename(source / 'renamed.sh')
        definition['manifest_sha256'] = hashlib.sha256(canonical_json_bytes(manifest())).hexdigest()
    with pytest.raises(SecurityError, match='retained immutable executable'):
        launch.verify_retained_immutable_sources(proof)


def test_empty_executable_inventory_is_verified(tmp_path, monkeypatch):
    source = tmp_path / 'retained'; source.mkdir()
    file = source / 'data'; file.write_bytes(b'data'); file.chmod(0o444)
    inode = source.stat(); target = str(launch.CODE_TARGET)
    definition = {'source': str(source), 'manifest_sha256': hashlib.sha256(canonical_json_bytes(
        {'data': hashlib.sha256(b'data').hexdigest()})).hexdigest(),
        'executable_inventory': launch._executable_inventory([])}
    proof = {'identity': InvocationIdentity('github:compact', 'parent', 'coordinator', 'coordinator-task', 'task', 'run', 1).to_json(), 'tree_identities': {target: {'device': inode.st_dev, 'inode': inode.st_ino}},
        'immutable_sources': {'mount_plan': {'authority': '/unit-authority'}, 'executables': {},
            'trees': {target: definition}}}
    monkeypatch.setattr(ApprovedPrivateMountPlan, 'read', classmethod(lambda cls, *args:
        SimpleNamespace(evidence=lambda: proof['immutable_sources']['mount_plan'])))
    monkeypatch.setattr(launch, '_verify_root_owned_ancestry', lambda path: None)
    monkeypatch.setattr(launch, '_verify_immutable_entry', lambda info: None)
    launch.verify_retained_immutable_sources(proof)
    file.chmod(0o555)
    with pytest.raises(SecurityError, match='retained immutable executable'):
        launch.verify_retained_immutable_sources(proof)


def test_unknown_legacy_modes_keep_legacy_format_and_cannot_claim_compact(emitted):
    for tree in (emitted.mount.code, *emitted.mount.runtime):
        tree.executable_files = None
    sources = launch.PolicyMount.immutable_source_evidence(emitted.mount)
    assert sources['schema_version'] == 'herdr-immutable-sources-1'
    proof = deepcopy(emitted.proof); proof['immutable_sources'] = sources
    assert launch.validate_policy_evidence(proof, identity=emitted.identity) == proof
    proof['immutable_sources']['schema_version'] = 'herdr-immutable-sources-2'
    with pytest.raises(SecurityError):
        launch.validate_policy_evidence(proof, identity=emitted.identity)
