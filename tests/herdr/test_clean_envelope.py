"""Portable source/preparation tests, NOT physical namespace/SDK acceptance.

Linux-only composition tests use real core datatypes but never start a worker,
open a model allowance, mount, acquire root or manufacture an accepted receipt.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

ROOT = Path(__file__).resolve().parents[2]


def load(name):
    path = ROOT / 'tests/physical' / (name + '.py')
    spec = importlib.util.spec_from_file_location('clean_test_' + name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


@pytest.fixture
def m():
    return load('clean_envelope')


@pytest.fixture
def bundle(m, monkeypatch):
    def tree(source):
        return {'source': source, 'files': {'entry.py': 'a' * 64}, 'executable_files': [],
                'max_bytes': 100, 'max_file_bytes': 100}
    # Component manifests only; this is not a physical source acceptance.
    for key in ('MAIN_MANIFEST', 'SDK_MANIFEST', 'PYTHON_MANIFEST'):
        monkeypatch.setattr(m, key, m.digest({'entry.py': 'a' * 64}))
    monkeypatch.setattr(m, 'CORE_PATCH', {'entry.py': 'a' * 64})
    monkeypatch.setattr(m, 'PATCH_MANIFEST', m.digest(m.CORE_PATCH))
    return {'version': 1, 'core_patch': {'baseline_main': m.MAIN, 'baseline_manifest_sha256': m.BASE_MAIN_MANIFEST,
        'files': dict(m.CORE_PATCH), 'manifest_sha256': m.PATCH_MANIFEST, 'source_sha': 'b' * 40}, 'source_main': m.MAIN, 'case_sha256': m.CASE, 'nonce': '1' * 32,
        'runtime': {'code': tree('/run/clean/code'), 'sdk': tree(m.SDK), 'python': tree(m.PYTHON),
                    'native': {'source': '/home/agentops/.local/bin/herdr', 'sha256': 'b' * 64, 'bytes': 10}},
        'harness': {**{name: 'c' * 64 for name in m.HARNESSES}, 'offline_case_inputs.json': m.CASE},
        'system': {path: 'd' * 64 for path in ('/usr/bin/bwrap', '/usr/bin/git', '/usr/bin/openssl', '/usr/sbin/ip', '/usr/bin/unshare')},
        'check_runtime': {'files': {'/usr/bin/git': '1' * 64, m.PY: '2' * 64},
                          'executables': ['/usr/bin/git', m.PY], 'runtime_aliases': [], 'bytes': 100},
        'caps': dict(m.CAPS), 'shared_before': {'unknown185': 'e' * 64}}


@pytest.fixture
def proposal(bundle):
    pilot = load('offline_pilot')
    return pilot.prepare_clean_inputs(ROOT / 'tests/physical/offline_case_inputs.json',
                                     bundle['case_sha256'], bundle['nonce'])


def test_fresh_proposal_binds_without_grant_queue_or_budget(m, bundle, proposal):
    before = deepcopy(proposal)
    assert m.validate_bundle(bundle) is bundle
    task = m.bind_proposal(bundle, proposal)
    assert task['id'].endswith(bundle['nonce']) and task['fencing_token'] == 1
    assert proposal == before
    assert not any(proposal[key] for key in ('authority_created', 'queue_written', 'budget_allocated'))


@pytest.mark.parametrize('field', ['source_main', 'case_sha256', 'nonce'])
def test_source_case_or_run_substitution_denied(m, bundle, proposal, field):
    altered = deepcopy(bundle); altered[field] = '0' * (32 if field == 'nonce' else 64)
    with pytest.raises(m.Denied):
        m.bind_proposal(altered, proposal)


@pytest.mark.parametrize('field,value', [('workspace', '/home/agentops/worktrees/pilot/workspace'),
    ('id', 'herdr-budget-bootstrap-20261007'), ('fencing_token', 7), ('attempts', 6), ('attempt_id', 3)])
def test_historical_or_attempt_state_is_never_an_input(m, bundle, proposal, field, value):
    proposal['task_seed'][field] = value
    with pytest.raises(m.Denied):
        m.bind_proposal(bundle, proposal)


@pytest.mark.parametrize('path', ['../escape', '/root/auth', 'a/../b', './case', 'a//b',
                                 'a\\b', 'a:b', '', 'a\0b'])
def test_manifest_path_escape_denied(m, path):
    with pytest.raises(m.Denied):
        m.relative(path)


@pytest.mark.parametrize('change', ['extra', 'code', 'sdk', 'python', 'native', 'harness', 'cap', 'system'])
def test_closed_composition_and_allowlist(m, bundle, change):
    if change == 'extra':
        bundle['historical_work'] = '/var/lib/old'
    elif change == 'code':
        bundle['runtime']['code']['source'] = '/opt/herdr/current'
    elif change in ('sdk', 'python'):
        bundle['runtime'][change]['source'] = '/home/agentops/.hermes'
    elif change == 'native':
        bundle['runtime']['native']['source'] = '/usr/local/bin/unpinned'
    elif change == 'harness':
        bundle['harness']['offline_case_inputs.json'] = '0' * 64
    elif change == 'cap':
        bundle['caps']['external_model_calls'] = 1
    else:
        bundle['system']['/etc/secret'] = '1' * 64
    with pytest.raises(m.Denied):
        m.validate_bundle(bundle)


def test_one_absolute_deadline_cannot_be_replaced_by_elapsed_restart(m, bundle):
    admission = {'version': 1, 'nonce': bundle['nonce'], 'bundle_sha256': m.digest(bundle),
                 'started_epoch': 1000, 'deadline_epoch': 2800}
    assert m.deadline_check(admission, now=1100) == 1700
    with pytest.raises(m.Denied):
        m.deadline_check(admission, now=2800)
    with pytest.raises(m.Denied):
        m.deadline_check(admission, now=999)
    admission['deadline_epoch'] += 1
    with pytest.raises(m.Denied):
        m.deadline_check(admission, now=1100)


def test_reader_digest_and_named_substitution(m, tmp_path, monkeypatch):
    path = tmp_path / 'case'; path.write_bytes(b'approved'); path.chmod(0o600)
    owner = path.stat().st_uid; sha = hashlib.sha256(b'approved').hexdigest()
    # POSIX temp ancestry is intentionally not root-protected. This component
    # substitutes the ancestry platform branch only; execution remains Linux-only.
    if os.name == 'posix':
        pytest.skip('strict administrator ancestry belongs to physical preparation')
    assert m.read_pin(path, sha, owner=owner) == b'approved'
    with pytest.raises(m.Denied):
        m.read_pin(path, '0' * 64, owner=owner)
    original = m.os.read
    def changed(fd, size):
        value = original(fd, size)
        if value and path.read_bytes() == b'approved':
            path.write_bytes(b'changed!')
        return value
    monkeypatch.setattr(m.os, 'read', changed)
    with pytest.raises(m.Denied):
        m.read_pin(path, sha, owner=owner)


def test_cli_cannot_run_root_path_on_windows_or_unprivileged_host(m, bundle, tmp_path):
    if sys.platform == 'linux' and os.geteuid() == 0:
        pytest.skip('do not execute privileged mode in source tests')
    with pytest.raises(m.Denied):
        m.outer('missing', '0' * 64, 'missing', 'missing', tmp_path)


def test_transport_forwards_real_host_result_for_both_roles(proposal):
    provider = load('offline_provider')
    delegate = {'cwd': proposal['task_seed']['workspace'] + '/.managed-child/workspace',
                'key': 'arithmetic-child', 'objective': 'arithmetic', 'role': 'writer', 'prompt': 'arithmetic'}
    fixture = provider.TeamFixture.for_proposal(proposal, delegate)
    tools = ['read_file', 'write_file', 'herdr_verify_work', 'herdr_submit_result']
    def request(parent=False, submission=None):
        return {'model': 'meituan/longcat-2.0:free', 'tools': [{'type': 'function', 'function': {'name': name}}
                for name in tools + (['herdr_delegate_child'] if parent else [])],
                'messages': [] if submission is None else [{'role': 'tool', 'content': json.dumps(
                    {'result': {'status': 'pass', 'submission': submission}})}]}
    result = fixture.answer(request(True))
    assert result['choices'][0]['message']['tool_calls'][0]['function']['name'] == 'herdr_delegate_child'
    assert not fixture.complete
    for parent in (False, True):
        for _ in range(3):
            fixture.answer(request(parent))
        expected = {'status': 'completed', 'evidence': [{'opaque': 'actual-host-fixture'}], 'summary': 'local'}
        response = fixture.answer(request(parent, expected))
        arguments = response['choices'][0]['message']['tool_calls'][0]['function']['arguments']
        assert json.loads(arguments) == expected
        fixture.answer(request(parent))
    assert fixture.complete and fixture.root.workspace != fixture.child.workspace


def test_failed_or_missing_verifier_never_becomes_submission(proposal):
    provider = load('offline_provider')
    fixture = provider.TeamFixture.for_proposal(proposal, {'cwd': proposal['task_seed']['workspace'] + '/child'})
    fixture.child.turn = 3
    request = {'tools': [{'type': 'function', 'function': {'name': name}} for name in proposal['tools']],
               'messages': [{'role': 'tool', 'content': '{"status":"failed"}'}]}
    with pytest.raises(ValueError, match='did_not_pass'):
        fixture.answer(request)
    assert not fixture.complete


@pytest.mark.skipif(sys.platform != 'linux', reason='real core datatypes require POSIX; no physical effects')
def test_real_grant_budget_and_work_datatypes(m, bundle, proposal, tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "agent-stack/bin"))
    from dataclasses import asdict
    from herdr.security import SecurityGrant
    from herdr.work_budget_configuration import parse_allocation
    from herdr.check_runner import CheckEnvironment
    from herdr.work_cycle import WorkPlan
    from herdr.work_planning import PlanArtifact
    from herdr.security import InvocationIdentity
    admission = {'version': 1, 'nonce': bundle['nonce'], 'bundle_sha256': m.digest(bundle),
        'started_epoch': time.time(), 'deadline_epoch': time.time() + 1800}
    grant = SecurityGrant.from_dict(m.root_grant(bundle, proposal, admission, {},
        dict(proposal['task_seed'], run_token='actual-prepared-run', fencing_token=1)))
    assert grant.credential_refs == (m.CREDENTIAL_REF,)
    assert grant.provider_routes[0].credential_refs == grant.credential_refs
    from herdr.work_lifetime import require_grant_lifetime
    from dataclasses import replace
    actual = replace(grant, expires_at=m.iso(time.time() + m.GRANT_TTL))
    require_grant_lifetime(actual, 153 + 900)
    with pytest.raises(Exception):
        require_grant_lifetime(replace(actual, expires_at=m.iso(time.time() + 900)), 153 + 900)
    assert not grant.runtime_assurance.sandbox_verified
    assert grant.runtime_assurance.sandbox_attestation_sha256 is None
    parent, child = m.budgets(bundle)
    from herdr.work_budget_configuration import model_request_ceiling
    quote = parent['model_quotes'][0]
    assert quote['api_mode'] == grant.provider_routes[0].api_mode
    assert model_request_ceiling(quote)
    env_data = m.check_environment(bundle)
    assert set(env_data.executables) == set(bundle['check_runtime']['executables'])
    pa, ca = parse_allocation(parent['allocation']), parse_allocation(child['allocation'])
    assert ca.parent_allocation_id == pa.allocation_id and ca.lineage_key == pa.lineage_key
    assert parent['model_quotes'] == child['model_quotes']
    assert pa.limits.max_cost_microusd == ca.limits.max_cost_microusd == 0
    workspace = tmp_path / 'workspace'; (workspace / '.git/hooks').mkdir(parents=True)
    (workspace / '.git/config').write_text('[core]\nrepositoryformatversion = 0\n')
    env = CheckEnvironment('component-only', (('/usr/bin/git', '1' * 64), (m.PY, '2' * 64)), ('/usr/bin/git', m.PY))
    definition = m.work_definition(proposal, proposal['task_seed'], '3' * 40, workspace,
                                   proposal['tools'], env, parent)
    from herdr.work_hygiene import LocalCommitPolicy
    hygiene = LocalCommitPolicy(**definition['hygiene'], environment=env)
    identity = InvocationIdentity.from_dict(proposal['root_identity'])
    plan = {key: value for key, value in definition.items() if key not in ('discovery_files', 'planning', 'hygiene', 'budget')}
    planning = deepcopy(definition['planning'])
    planning.update(version=1, identity=identity.to_json(), spec_sha256='4' * 64, base_sha='3' * 40,
        discovery={'version': 1, 'identity': identity.to_json(), 'base_sha': '3' * 40,
            'inspected_files': {'arithmetic.py': '5' * 64}, 'symbols': {'arithmetic.py': ['add']},
            'facts': ['Frozen arithmetic source'], 'evidence_refs': ['git-base:' + '3' * 40],
            'unknowns': [], 'expansion_reason': None})
    plan.update(version=3, identity=identity.to_json(), spec_sha256='4' * 64, grant_sha256=grant.hash,
                environment_sha256=env.hash, hygiene_sha256=hygiene.hash, planning=planning)
    assert WorkPlan.from_json(plan).budget_reference == pa.hash


def test_import_is_inert_and_has_no_sdk_or_historical_helper_calls(m, monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('source import may not start a process')
    monkeypatch.setattr(subprocess, 'Popen', forbidden)
    module = load('clean_envelope')
    assert module.CAPS['external_github_calls'] == 0
    assert module.CAPS['external_auth_calls'] == 0
    assert module.CAPS['external_model_calls'] == 0


@pytest.mark.parametrize('surface', ['policy', 'grant', 'profile', 'source'])
def test_binding_record_rejects_substituted_authority_digest(m, bundle, surface):
    admission = {'bundle_sha256': m.digest(bundle), 'deadline_epoch': 3000}
    policy = {'code': deepcopy(bundle['runtime']['code']), 'private_launch': {'profile': 'private'},
              'templates': {m.CONSUMER: {'expires_at': m.iso(3000)}}, 'storage': '/private/host'}
    binding = m.binding_record(policy, bundle, admission)
    m.require_binding(binding, policy, bundle, admission)
    if surface == 'source': policy['code']['files']['entry.py'] = '0' * 64
    elif surface == 'grant': policy['templates'][m.CONSUMER]['expires_at'] = m.iso(3001)
    elif surface == 'profile': policy['private_launch']['profile'] = 'foreign'
    else: policy['storage'] = '/home/agentops/foreign'
    with pytest.raises(m.Denied, match='binding changed'):
        m.require_binding(binding, policy, bundle, admission)


def test_sdk_import_follows_real_boundary_and_capability_drop(m):
    import ast
    tree = ast.parse(Path(m.__file__).read_bytes())
    function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'inner')
    called = [(node.lineno, node.func.id) for node in ast.walk(function)
              if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
    order = {name: min(line for line, called_name in called if called_name == name)
             for name in ('private_boundary', 'drop_setup_authority', 'configure_profile')}
    assert order['private_boundary'] < order['drop_setup_authority'] < order['configure_profile']
    source = ast.get_source_segment(Path(m.__file__).read_text(), function)
    assert 'init.py' not in source and 'preflight.py' not in source


def test_outer_has_no_host_home_or_credentials_mount(m):
    import ast
    tree = ast.parse(Path(m.__file__).read_bytes())
    outer = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'outer')
    text = ast.get_source_segment(Path(m.__file__).read_text(), outer)
    assert "'--ro-bind', '/', '/'" not in text
    assert "'--bind', '/home'" not in text
    assert "'--unshare-net'" in text and "'--unshare-ipc'" in text
    assert "'--remount-ro', '/'" in text and "'--user'" in text
    assert 'RLIMIT_FSIZE' in text and text.index('RLIMIT_FSIZE') < text.index('subprocess.Popen')


def test_source_counter_does_not_call_dispatch_or_sdk_during_cold_recovery(m):
    import ast
    tree = ast.parse(Path(m.__file__).read_bytes())
    for name in ('recover_original', 'recover_child'):
        function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == name)
        text = ast.get_source_segment(Path(m.__file__).read_text(), function)
        assert 'Popen' not in text and 'host_run(' not in text and "'--sdk'" not in text
        assert 'recover_' in text and 'verifier(' in text
    assert 'closed_at' not in ast.get_source_segment(Path(m.__file__).read_text(),
        next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'recover_original'))


def test_unit_caps_fail_closed_before_any_spawn(m, bundle, monkeypatch):
    class File:
        def __init__(self, text): self.text = text
        def read_text(self): return self.text
    class Paths:
        def __call__(self, value):
            if str(value) == '/proc/self/cgroup': return File('0::/system.slice/foreign.service\n')
            pytest.fail('wrong unit must stop before other file reads')
    monkeypatch.setattr(m, 'Path', Paths())
    monkeypatch.setattr(m, 'run', lambda *a, **kw: pytest.fail('wrong unit cannot start a process'))
    with pytest.raises(m.Denied, match='dedicated'):
        m.verify_unit(bundle)


@pytest.mark.parametrize('uid', [0, 1001])
def test_preparation_never_drops_groups_twice(m, monkeypatch, uid):
    from types import SimpleNamespace
    called = []
    monkeypatch.setattr(m.os, 'geteuid', lambda: uid, raising=False)
    monkeypatch.setattr(m.os, 'getegid', lambda: 1001, raising=False)
    monkeypatch.setattr(m.os, 'getgroups', lambda: [], raising=False)
    monkeypatch.setattr(m.subprocess, 'run', lambda *args, **kwargs: (
        called.append(kwargs) or SimpleNamespace(returncode=0, stdout=b'ok', stderr=b'')))
    assert m.run(['/usr/bin/git', 'init'], user=True) == b'ok'
    assert 'preexec_fn' not in called[0]
    if uid == 0:
        assert called[0]['user'] == called[0]['group'] == 1001 and called[0]['extra_groups'] == ()
    else:
        assert 'user' not in called[0] and 'group' not in called[0] and 'extra_groups' not in called[0]


def test_unresolved_core_contract_stops_before_materialization(m, monkeypatch):
    monkeypatch.setattr(m, 'EXECUTABLE_SOURCE_READY', False)
    monkeypatch.setattr(m, 'load_pin', lambda *a, **kw: pytest.fail('blocked draft cannot even read execution inputs'))
    with pytest.raises(m.Denied, match='snapshot/write partition'):
        m.outer(None, None, None, None, None)


def test_parent_runtime_roots_portable_source_component():
    import ast
    from types import SimpleNamespace
    source = ROOT / 'herdr/hermes_guard.py'
    node = next(n for n in ast.parse(source.read_bytes()).body
                if isinstance(n, ast.FunctionDef) and n.name == '_runtime_file_roots')
    from pathlib import PurePosixPath
    scope = {'Path': PurePosixPath}
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), 'exec'), scope)
    rule = SimpleNamespace(allowed_roots=('/work/parent',))
    rules = {'read_file': rule, 'write_file': rule}
    assurance = SimpleNamespace(sandbox_verified=True,
                               writable_roots=('/work/parent/own.py', '/work/parent-other/foreign'))
    grant = SimpleNamespace(runtime_assurance=assurance)
    assert scope[node.name](grant, rules) == {'/work/parent', '/work/parent/own.py'}
    assert rule.allowed_roots == ('/work/parent',)
    assurance.sandbox_verified = False
    assert scope[node.name](grant, rules) == {'/work/parent'}
    assert scope[node.name](grant, {}) == set()


def _portable_security_scope():
    """Actual security datatypes with inert fixture constructors; no OS authority."""
    import ast
    from dataclasses import replace
    from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training
    from herdr.security import (InvocationIdentity, ProviderRoute, ToolRule, RiskClass, ProcessPolicy,
                                NetworkAccess, RuntimeAssurance, SecurityGrant, SecurityError)
    source = ROOT / 'tests/herdr/test_security.py'
    names = {'identity', 'scope', 'route', 'grant', 'assurance', '_parent_and_disjoint_child',
             'test_parent_own_leaf_never_implicitly_authorizes_disjoint_child_leaf',
             'test_only_revalidated_host_context_admits_exact_disjoint_child_leaf'}
    nodes = [n for n in ast.parse(source.read_bytes()).body if isinstance(n, ast.FunctionDef) and n.name in names]
    namespace = dict(locals()); namespace['pytest'] = pytest
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def test_portable_actual_security_keeps_default_physical_denial(tmp_path):
    _portable_security_scope()['test_parent_own_leaf_never_implicitly_authorizes_disjoint_child_leaf'](tmp_path)


@pytest.mark.parametrize('fault', [None, 'parent', 'child', 'stale', 'callback', 'extra-write', 'untyped'])
def test_portable_actual_security_host_delegation_contract(tmp_path, fault):
    _portable_security_scope()['test_only_revalidated_host_context_admits_exact_disjoint_child_leaf'](tmp_path, fault)


def test_actual_seal_records_revalidated_delegation_after_mounted_check(tmp_path):
    """Seal control-flow component; process, signing and mount boundaries are doubles."""
    import ast
    import io
    from types import SimpleNamespace
    from dataclasses import replace
    from herdr.security import DelegatedWriteAuthority, SecurityError, canonical_json_bytes
    namespace = _portable_security_scope()
    parent, child = namespace['_parent_and_disjoint_child'](tmp_path)
    source = ROOT / 'herdr/policy_launch.py'
    cls = next(n for n in ast.parse(source.read_bytes()).body if isinstance(n, ast.ClassDef) and n.name == 'PolicyMount')
    method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == 'seal')
    events = []
    env = {'agent_id': 'HERDR_AGENT_ID', 'task_id': 'HERDR_TASK_ID', 'run_token': 'HERDR_RUN_TOKEN'}
    raw = b'\0'.join((key + '=' + str(getattr(child.identity, field))).encode() for field, key in env.items())
    class ProcPath:
        def __init__(self, value): assert value == '/proc/123/environ'
        def open(self, mode): assert mode == 'rb'; return io.BytesIO(raw)
    def require(ok, reason):
        if not ok: raise SecurityError(reason)
    scope = dict(Path=ProcPath, SecurityGrant=namespace['SecurityGrant'], InvocationIdentity=namespace['InvocationIdentity'],
                 _require=require, replace=replace, canonical_json_bytes=canonical_json_bytes, IDENTITY_ENV=env)
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), scope)
    authority = DelegatedWriteAuthority(parent.hash, child.identity, 'c' * 64, 'd' * 64, 'e' * 64,
        child.runtime_assurance.writable_roots,
        lambda *a: events.append('revalidate') or child.runtime_assurance.writable_roots,
        lambda *a: events.append('durable-audit'))
    fake = SimpleNamespace(observed_assurance=lambda *a: child.runtime_assurance,
        stage=SimpleNamespace(seal=lambda *a, **k: events.append('signed') or 'sealed'),
        verify_mounted=lambda *a: events.append('mounted'))
    actual, sealed = scope['seal'](fake, 123, child, identity=child.identity,
        attestation={'task_id': child.identity.task_id, 'run_token': child.identity.run_token, 'sandbox_pid': 123},
        tools=child.scope.tools, permissions=child.scope.permissions,
        private_key=object(), key_id='fixture', parent=parent, delegated_writes=authority)
    assert actual.hash == child.hash and sealed == 'sealed'
    assert events == ['revalidate', 'signed', 'mounted', 'revalidate', 'durable-audit']
    events.clear()
    def fail(*a): raise RuntimeError('audit unavailable')
    authority = replace(authority, record_sealed=fail)
    with pytest.raises(RuntimeError, match='audit unavailable'):
        scope['seal'](fake, 123, child, identity=child.identity,
            attestation={'task_id': child.identity.task_id, 'run_token': child.identity.run_token, 'sandbox_pid': 123},
            tools=child.scope.tools, permissions=child.scope.permissions,
            private_key=object(), key_id='fixture', parent=parent, delegated_writes=authority)


def _portable_work_plan_scope():
    import ast
    import re
    from dataclasses import dataclass, asdict
    from enum import StrEnum
    from contextlib import contextmanager
    import json
    from pathlib import PurePosixPath
    from herdr.security import InvocationIdentity, canonical_json_bytes, canonical_digest
    source = ROOT / 'herdr/work_cycle.py'
    names = {'FileScope', 'ValidationCheck', 'WorkMode', 'WorkPlan', 'SnapshotPartition', 'relative', 'require'}
    nodes = [n for n in ast.parse(source.read_bytes()).body
             if isinstance(n, (ast.ClassDef, ast.FunctionDef)) and n.name in names]
    namespace = dict(locals(), Path=PurePosixPath, canonical=canonical_json_bytes, digest=canonical_digest,
                     _SHA=re.compile(r'^[0-9a-f]{64}$'), _GIT=re.compile(r'^[0-9a-f]{40}$'), WorkContractError=ValueError)
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(source), 'exec'), namespace)
    return namespace


def test_portable_original_delegation_plan_and_audit_cold_binding():
    import ast
    from dataclasses import replace
    from types import SimpleNamespace
    n = _portable_work_plan_scope()
    plan = n['WorkPlan'](n['InvocationIdentity']('github:org/repo', 'agent', 'parent', 'parent-task', 'task', 'run', 1),
        'spec-1', 'a'*64, 'policy-1', 'b'*40, (n['FileScope']('own.py'),), ('behavior',),
        (n['ValidationCheck']('test', ('/usr/bin/python3', 'check.py'), ('behavior',)),), 'c'*64, 'd'*64, 'e'*64)
    assert plan.to_json()['version'] == 1 and 'delegated_seal_sha256' not in plan.to_json()
    assert n['WorkPlan'].from_json(plan.to_json()).hash == plan.hash
    event = {'event': 'host_delegated_write_sealed', 'identity': plan.identity.to_json(),
             'grant_sha256': plan.grant_sha256, 'spec_sha256': plan.spec_sha256}
    new = replace(plan, delegated_seal_sha256=n['digest'](event))
    assert new.to_json()['version'] == 4 and n['WorkPlan'].from_json(new.to_json()).hash == new.hash
    source = ROOT/'herdr/work_cycle.py'
    cls = next(v for v in ast.parse(source.read_bytes()).body if isinstance(v, ast.ClassDef) and v.name == 'WorkCycle')
    method = next(v for v in cls.body if isinstance(v, ast.FunctionDef) and v.name == '_verify_delegated_seal')
    exec(compile(ast.Module(body=[method], type_ignores=[]), str(source), 'exec'), n)
    rows = []
    cycle = SimpleNamespace(plan=new, audit_log=SimpleNamespace(replay=lambda: rows))
    with pytest.raises(ValueError, match='original delegated seal'): n[method.name](cycle)
    rows.append(event); n[method.name](cycle)
    rows[0] = {**event, 'grant_sha256': 'f'*64}
    with pytest.raises(ValueError, match='original delegated seal'): n[method.name](cycle)


def test_portable_partition_is_exact_original_domain_not_prefix_ignore():
    n=_portable_work_plan_scope()
    identity=n['InvocationIdentity']('github:org/repo','agent','parent','parent-task','task','run',1)
    data={'version':1,'admission_sha256':'a'*64,'identity':identity.to_json(),'spec_sha256':'b'*64,
          'grant_sha256':'e'*64,'sandbox_attestation_sha256':'f'*64,'parent_writable_roots':['/work/root/own.py'],
          'root':{'path':'/work/root','device':1,'inode':2,'mount_id':3},
          'children':[{'path':'.managed/child','device':1,'inode':4,'mount_id':3,
                       'key':'child','spec_sha256':'c'*64,'ownership_sha256':'d'*64}]}
    partition=n['SnapshotPartition'].from_json(data)
    partition.require_binding(identity,'b'*64,(n['FileScope']('own.py'),))
    assert partition.contains('.managed/child') and partition.contains('.managed/child/own.py')
    assert not partition.contains('.managed/child-other/own.py') and not partition.contains('ignored.bin')
    data['children'][0]['path']='foreign'
    assert partition.contains('.managed/child') # Constructor captured canonical immutable bytes.
    with pytest.raises(ValueError):partition.require_binding(identity,'0'*64,(n['FileScope']('own.py'),))
    with pytest.raises(ValueError):partition.require_binding(identity,'b'*64,(n['FileScope']('.managed/child/own.py'),))


@pytest.mark.parametrize('fault',['traversal','absolute','duplicate','mount','bool-inode','bad-ownership','parent-rw','child-rw'])
def test_portable_partition_denies_forged_or_ambiguous_shape(fault):
    n=_portable_work_plan_scope();identity=n['InvocationIdentity']('github:org/repo','agent','p','pt','task','run',1)
    data={'version':1,'admission_sha256':'a'*64,'identity':identity.to_json(),'spec_sha256':'b'*64,
          'grant_sha256':'e'*64,'sandbox_attestation_sha256':'f'*64,'parent_writable_roots':['/work/root/own.py'],
          'root':{'path':'/work/root','device':1,'inode':2,'mount_id':3},
          'children':[{'path':'.managed/child','device':1,'inode':4,'mount_id':3,
                       'key':'child','spec_sha256':'c'*64,'ownership_sha256':'d'*64}]}
    row=data['children'][0]
    if fault=='traversal':row['path']='.managed/../child'
    elif fault=='absolute':row['path']='/child'
    elif fault=='duplicate':data['children'].append(dict(row,key='second'))
    elif fault=='mount':row['mount_id']=5
    elif fault=='bool-inode':row['inode']=True
    elif fault=='bad-ownership':row['ownership_sha256']='bad'
    elif fault=='parent-rw':data['parent_writable_roots']=['/work/root']
    elif fault=='child-rw':data['parent_writable_roots']=['/work/root/.managed/child/owned.py']
    with pytest.raises(ValueError):n['SnapshotPartition'].from_json(data)


@pytest.mark.parametrize('field',['baseline_main','baseline_manifest_sha256','files','manifest_sha256','source_sha'])
def test_composed_runtime_never_claims_unchanged_baseline_or_unpinned_patch(m,bundle,field):
    bad=deepcopy(bundle)
    bad['core_patch'][field]={'entry.py':'0'*64} if field=='files' else 'wrong'
    with pytest.raises(m.Denied,match='core patch binding'):m.validate_bundle(bad)
