"""Historical publication files must never be promoted into new authority."""
import hashlib
import json
from pathlib import Path

import pytest
from herdr import runtime_reuse_audit as audit
from herdr.security import canonical_json_bytes
from herdr.runtime_publication import _manifest_sha256


def pair():
    trees = {name: {'source': f'/root/reviewed/{name}', 'target': f'/sandbox/{name}',
                    'files': {'a': hashlib.sha256(name.encode()).hexdigest()},
                    'executable_files': [], 'max_bytes': 2048,
                    'max_file_bytes': 2048} for name in ('code', 'hermes', 'python')}
    request = {'schema_version': 'herdr-runtime-publication-1', 'version': 'old-test',
               'destination': '/root/reviewed', 'trees': trees}
    record = {'schema_version': 'herdr-runtime-publication-1', 'version': 'old-test',
              'approval_sha256': hashlib.sha256(canonical_json_bytes(request)).hexdigest(),
              'trees': {name: {'source': f'/root/reviewed/old-test/{name}',
                               'manifest_sha256': _manifest_sha256(row['files'])}
                        for name, row in trees.items()}}
    return request, record


def test_legacy_digest_match_is_not_schema2_authority():
    req, rec = pair()
    out = audit.inspect_pair(req, rec, tree_presence=dict.fromkeys(rec['trees'], True))
    assert out['request_record_digest_match']
    assert out['historical_record_only']
    assert out['source_only_reuse_candidate']
    assert not out['current_record_contract_pass']
    assert not out['authorized_for_schema2']
    assert not out['can_publish_without_operator']


@pytest.mark.parametrize('attack', ['approval', 'manifest', 'version', 'no-hermes'])
def test_malformed_or_partial_history_is_not_usable(attack):
    req, rec = pair()
    presence = dict.fromkeys(rec['trees'], True)
    if attack == 'approval': rec['approval_sha256'] = '0' * 64
    if attack == 'manifest': rec['trees']['python']['manifest_sha256'] = '0' * 64
    if attack == 'version': rec['version'] = 'different'
    if attack == 'no-hermes': presence['hermes'] = False
    out = audit.inspect_pair(req, rec, tree_presence=presence)
    assert not out['source_only_reuse_candidate']
    assert not out['authorized_for_schema2']


def test_bad_shape_is_non_authoritative():
    req, rec = pair()
    assert not audit.inspect_pair(req, {'trees': {}}, tree_presence={})['source_only_reuse_candidate']
    assert not audit.inspect_pair([], rec, tree_presence={})['source_only_reuse_candidate']


def test_proposal_has_no_approval_or_unreviewed_hashes():
    root = Path(__file__).resolve().parents[2]
    proposal = json.loads((root / 'configs/rc6-runtime-publication.proposal.json').read_text())
    assert proposal['authorization_granted'] is False
    assert proposal['publication_allowed'] is False
    assert proposal['native_root_child_e2e_accepted'] is False
    assert all(value is None for value in proposal['candidate'].values())


def test_root_reader_and_missing_tree_do_not_generate_approval(monkeypatch, tmp_path):
    req, rec = pair()
    root = tmp_path / 'p0-test'
    root.mkdir()
    (root/'code').mkdir()
    request_path = tmp_path/'request.json'
    record_path = root/'publication.json'
    monkeypatch.setattr(audit, '_read_configuration',
                        lambda path: req if path == request_path else rec)
    out = audit.inspect_root_owned_pair(request_path, record_path)
    assert not out['source_only_reuse_candidate']
    assert not out['authorized_for_schema2']
