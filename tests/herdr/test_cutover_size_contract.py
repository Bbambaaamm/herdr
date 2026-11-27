"""B01–B30: real transaction bytes and isolated deployment adapters."""
import base64
import json
import os
from pathlib import Path

import pytest

from test_cutover_transaction import host
from herdr.release import ReleaseError
from deploy.herdr.cutover import transaction_contract as t
from deploy.herdr.cutover import cutover as runtime

REAL_PIN_ARCHIVE = runtime.pin_archive


def realistic(host):
    host.degraded()
    host.c.SNAPSHOT.write_bytes(b'x' * 119973)
    host.c.BRIDGE.write_bytes(b'b' * 8192)
    for name in host.c.CONSUMERS:
        (host.c.CONSUMER_DIR / (name + '.yaml')).write_bytes(b'consumer: ' + name.encode())
    dropin = host.c.UNIT_DIR / 'agent-stack-watchdog.service.d/126-capacity-repair.conf'
    dropin.parent.mkdir(exist_ok=True)
    dropin.write_bytes(b'capacity-protected-baseline')
    return dropin


def test_B06_realistic_snapshot_promotion(host):
    realistic(host)
    assert host.apply()['status'] == 'success'
    backups = list(host.c.STATE_DIR.glob('*-baseline-authority.json'))
    assert len(backups) == 1 and backups[0].stat().st_size > 131072
    document = json.loads(backups[0].read_bytes())
    assert len(base64.b64decode(document['files'][str(host.c.SNAPSHOT)][0])) == 119973
    assert not (host.c.STATE_DIR / 'transaction.json').exists()


def test_B19_B20_large_backup_degraded_rollback(host):
    dropin = realistic(host)
    before = {p: host.c.snapshot_file(p) for p in (host.c.SNAPSHOT, host.c.BRIDGE, dropin)}
    host.failure['candidate'] = True
    with pytest.raises(ReleaseError, match='rollback_degraded'):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous
    for p, value in before.items():
        assert host.c.snapshot_file(p) == value
    assert not (host.c.STATE_DIR / 'transaction.json').exists()


def plan(host, target_size=None):
    c = host.c
    host.report['systemd_authority'] = c.capture_systemd_authority()
    contract = t.Contract(c.__dict__)
    backup = c.STATE_DIR / '1234567890123456789-baseline-authority.json'
    args = (host.previous, host.report, c.transaction_snapshots(), c.snapshot_units(), backup)
    result = contract.plan(*args)
    if target_size:
        authority = host.report['systemd_authority']
        row = authority['units'][host.c.UNITS[0]]
        row['Environment'] = []
        result = contract.plan(*args)
        deficit = target_size - len(result[1])
        count = (deficit + 4095)//4096
        characters = deficit - (3*count-1)
        for _ in range(count):
            length = min(4096, characters - 4*(count-len(row['Environment'])-1))
            row['Environment'].append('PAD='+'p'*(length-4))
            characters -= length
        result = contract.plan(*args)
        assert len(result[1]) == target_size
    return contract, backup, result


@pytest.mark.parametrize('size', [None, 131071, 131072, 131073, 178649],
                         ids=['B01', 'B02', 'B03', 'B04', 'B05'])
def test_exact_document_sizes_real_write_readback_restore_plan(host, size):
    contract, backup, (doc, raw, journal, journal_raw) = plan(host, size)
    host.c.atomic_write(backup, raw, 0o600)
    path = host.c.STATE_DIR / 'transaction.json'
    host.c.atomic_write(path, journal_raw, 0o600)
    assert contract.read(backup, expected_sha256=host.c.sha256(raw)) == doc
    assert contract.read(path, journal=True) == journal
    restored = contract.validate(doc)
    assert restored[host.c.SNAPSHOT][0] == host.c.SNAPSHOT.read_bytes()


def test_B07_B08_maximum_inputs(host):
    contract, backup, _ = plan(host)
    files = {Path(p): (b'x' * limit, 0o640, os.getuid(), os.getgid())
             for p, limit in contract.limits.items()}
    files[host.c.watchdog_fence_path()] = None
    files[host.c.UNIT_DIR/'agent-stack-watchdog.service.d/126-capacity-repair.conf'] = None
    doc, raw, _, journal = contract.plan(host.previous, host.report, files, {}, backup)
    assert len(doc['files']) == 17
    assert len(raw) < t.BACKUP_MAX and len(journal) < t.JOURNAL_MAX
    assert sum(len(v[0]) for v in doc['files'].values() if v) <= t.BASE64_MAX
    host.c.atomic_write(backup, raw, 0o600)
    assert contract.read(backup) == doc


@pytest.mark.parametrize('delta', [0, 1], ids=['B09_reader_at_ceiling', 'B10_reader_over_ceiling'])
def test_aggregate_reader_byte_ceiling(host, delta):
    path = host.c.STATE_DIR / 'boundary.json'
    path.write_bytes(b' ' * (t.BACKUP_MAX + delta))
    path.chmod(0o600)
    if delta:
        with pytest.raises(ReleaseError, match='file_size'):
            t.bounded_read(path, t.BACKUP_MAX, aggregate=True)
    else:
        assert len(t.bounded_read(path, t.BACKUP_MAX, aggregate=True)[0]) == t.BACKUP_MAX
        # The byte ceiling never substitutes for the document/schema gate.
        with pytest.raises(ReleaseError, match='invalid_json'):
            t.Contract(host.c.__dict__).read(path)


def test_B11_oversize_input_before_aggregate_write(host):
    host.c.SNAPSHOT.write_bytes(b'x' * (t.FILE_MAX + 1))
    with pytest.raises(ReleaseError, match='file_size'):
        host.apply()
    assert not list(host.c.STATE_DIR.glob('*-baseline-authority.json'))
    assert host.c.CURRENT.resolve() == host.previous


def test_B12_extra_capture_path_rejected(host):
    contract, _, (doc, _, _, _) = plan(host)
    doc['files']['/unapproved/path'] = None
    with pytest.raises(ReleaseError, match='files_set'):
        contract.serialize(doc)


def test_B13_growth_during_read(host, monkeypatch):
    original = t.os.read
    mutated = []
    def read(fd, count):
        data = original(fd, count)
        if data and not mutated:
            mutated.append(True)
            with host.c.SNAPSHOT.open('ab') as f:
                f.write(b'changed')
        return data
    monkeypatch.setattr(t.os, 'read', read)
    with pytest.raises(ReleaseError, match='file_changed'):
        t.bounded_read(host.c.SNAPSHOT, t.FILE_MAX)


@pytest.mark.parametrize('attack', ['symlink', 'hardlink'], ids=['B14_symlink', 'B14_hardlink'])
def test_link_attacks(host, attack):
    contract, backup, (_, raw, _, _) = plan(host)
    host.c.atomic_write(backup, raw, 0o600)
    other = backup.with_name('attacker.json')
    if attack == 'symlink':
        other.symlink_to(backup)
    else:
        os.link(backup, other)
    with pytest.raises((OSError, ValueError)):
        contract.read(other)


@pytest.mark.parametrize('attack', ['owner', 'mode'], ids=['B15_owner', 'B15_mode'])
def test_aggregate_authority(host, monkeypatch, attack):
    contract, backup, (_, raw, _, _) = plan(host)
    host.c.atomic_write(backup, raw, 0o600)
    if attack == 'owner':
        monkeypatch.setattr(t, 'ROOT_UID', os.getuid() + 1)
    else:
        backup.chmod(0o640)
    with pytest.raises(ReleaseError, match='aggregate_authority'):
        contract.read(backup)


def test_B16_hash_and_binding_mismatch(host):
    contract, backup, (_, raw, journal, journal_raw) = plan(host)
    host.c.atomic_write(backup, raw, 0o600)
    with pytest.raises(ReleaseError, match='hash_mismatch'):
        contract.read(backup, expected_sha256='0' * 64)
    journal['public_health'] = '503'
    path = host.c.STATE_DIR / 'transaction.json'
    host.c.atomic_write(path, contract.serialize(journal, journal=True), 0o600)
    with pytest.raises(ReleaseError, match='journal_backup_mismatch'):
        contract.read(path, journal=True)


@pytest.mark.parametrize('attack', ['base64', 'duplicate', 'json', 'nan', 'type', 'truncated'], ids=lambda x:'B17_'+x)
def test_corrupt_documents(host, attack):
    contract, backup, (doc, raw, _, _) = plan(host)
    if attack == 'base64':
        doc['files'][str(host.c.SNAPSHOT)][0] = '!!!!'
        raw = host.c.canonical_json(doc)
    elif attack == 'duplicate':
        raw = raw.replace(b'{', b'{"version":2,', 1)
    elif attack == 'json':
        raw = b'not JSON'
    elif attack == 'nan':
        raw = raw.replace(b'"version":2', b'"version":NaN')
    elif attack == 'type':
        raw = b'[]'
    else:
        raw = raw[:-5]
    host.c.atomic_write(backup, raw, 0o600)
    with pytest.raises(ReleaseError):
        contract.read(backup)


def test_B18_journal_readback_is_required(host, monkeypatch):
    original = host.c.atomic_write
    def write(path, data, *args):
        original(path, b'corrupted' if path.name == 'transaction.json' else data, *args)
    monkeypatch.setattr(host.c, 'atomic_write', write)
    with pytest.raises(ReleaseError, match='invalid_json'):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous
    assert (host.c.STATE_DIR / 'transaction.json').exists()


def test_B21_large_healthy_exercise(host):
    host.c.SNAPSHOT.write_bytes(b'x' * 119973)
    assert host.apply()['rollback_exercised'] is True


def test_B22_large_sigterm_rollback(host):
    realistic(host)
    host.failure['interrupt'] = True
    with pytest.raises(ReleaseError, match='rollback_degraded'):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous
    assert not (host.c.STATE_DIR / 'transaction.json').exists()


def test_B24_B25_prejournal_failure_and_safe_retry(host, monkeypatch):
    realistic(host)
    original = host.c.begin_transaction
    monkeypatch.setattr(host.c, 'begin_transaction', lambda *args: (_ for _ in ()).throw(ReleaseError('before_journal')))
    with pytest.raises(ReleaseError, match='before_journal'):
        host.apply()
    assert not (host.c.STATE_DIR / 'transaction.json').exists()
    assert host.c.CURRENT.resolve() == host.previous
    preparations = list(host.c.STATE_DIR.glob('*-preparation.json'))
    assert preparations and json.loads(preparations[0].read_bytes())['status'] == 'candidate_prepared'
    monkeypatch.setattr(host.c, 'begin_transaction', original)
    assert host.apply()['status'] == 'success'


def test_B26_capacity_rejects_before_write(host, monkeypatch):
    from types import SimpleNamespace
    monkeypatch.setattr(host.c.os, 'statvfs', lambda p: SimpleNamespace(f_bavail=1, f_frsize=4096, f_favail=100000))
    with pytest.raises(ReleaseError, match='capacity_insufficient'):
        host.c.verify_transaction_preparation(host.previous,
            {**host.report, 'systemd_authority': host.c.capture_systemd_authority()}, host.archive, 4096)
    assert not (host.c.STATE_DIR / 'transaction.json').exists()


def test_B27_preflight_planner_catches_oversize(host):
    host.c.SNAPSHOT.write_bytes(b'x' * (t.FILE_MAX + 1))
    with pytest.raises(ReleaseError, match='file_size'):
        host.c.verify_transaction_preparation(host.previous,
            {**host.report, 'systemd_authority': host.c.capture_systemd_authority()}, host.archive, 4096)
    assert not list(host.c.STATE_DIR.iterdir())


def test_B28_apply_recaptures_growth(host):
    report = {**host.report, 'systemd_authority': host.c.capture_systemd_authority()}
    result = host.c.verify_transaction_preparation(host.previous, report, host.archive, 4096)
    assert result['status'] == 'verified'
    host.c.SNAPSHOT.write_bytes(b'x' * (t.FILE_MAX + 1))
    with pytest.raises(ReleaseError, match='file_size'):
        host.apply()
    assert host.c.CURRENT.resolve() == host.previous


def test_B23_sigkill_preserves_journal_and_fence(host, monkeypatch):
    from test_cutover_transaction import test_T11_sigkill_retains_durable_journal
    realistic(host)
    test_T11_sigkill_retains_durable_journal(host, monkeypatch)


@pytest.mark.parametrize('attack', ['missing_unit','missing_consumer','missing_nginx','missing_override','fence','authority','external'])
def test_restore_plan_rejects_incomplete_authority(host, attack):
    realistic(host)
    contract, _, (doc, _, _, _) = plan(host)
    if attack=='missing_unit':
        doc['files'][str(host.c.UNIT_DIR/host.c.UNITS[0])]=None
    elif attack=='missing_consumer':
        doc['files'][str(host.c.CONSUMER_DIR/'herdr.yaml')]=None
    elif attack=='missing_nginx':
        doc['files'][str(host.c.NGINX_ROUTE)]=None
    elif attack=='missing_override':
        doc['files'][str(host.c.UNIT_DIR/'agent-stack-watchdog.service.d/126-capacity-repair.conf')]=None
    elif attack=='fence':
        doc['files'][str(host.c.watchdog_fence_path())]=['',0o644,os.getuid(),os.getgid()]
    elif attack=='authority':
        doc['systemd_authority']['host_policy']={}
    else:
        doc['systemd_authority']['external_runtimes']={}
    with pytest.raises(ReleaseError):
        contract.serialize(doc)


def test_corrupt_journal_at_rollback_retains_fence(host, monkeypatch):
    realistic(host)
    original = host.c.assert_candidate_ready
    def ready(*args):
        (host.c.STATE_DIR/'transaction.json').write_bytes(b'corrupt')
        raise ReleaseError('candidate_unready')
    monkeypatch.setattr(host.c,'assert_candidate_ready',ready)
    with pytest.raises(ReleaseError,match='rollback_incomplete'):
        host.apply()
    assert (host.c.STATE_DIR/'transaction.json').exists()
    assert host.c.watchdog_fence_path().exists()
    assert not host.c.watchdog_permit_path().exists()
    assert host.states['agent-stack-watchdog.service']=='inactive'


def test_archive_replaced_with_fifo_does_not_block(host, monkeypatch):
    from types import SimpleNamespace
    incoming = host.c.STATE_DIR.parent/'incoming'
    monkeypatch.setattr(host.c,'INCOMING_DIR',incoming)
    monkeypatch.setenv('SUDO_UID',str(os.getuid()))
    real_stat = Path.stat
    def owned(path,*args,**kwargs):
        value = real_stat(path,*args,**kwargs)
        return SimpleNamespace(st_uid=0,st_mode=0o40700) if path==incoming else value
    monkeypatch.setattr(Path,'stat',owned)
    real_open = os.open
    replaced = []
    def race(path,flags,*args,**kwargs):
        if Path(path)==host.archive and not replaced:
            replaced.append(True)
            host.archive.unlink()
            os.mkfifo(host.archive,0o600)
            # Fail immediately on an old reader rather than hanging the test.
            assert flags & os.O_NONBLOCK, 'root open could block on substituted FIFO'
        return real_open(path,flags,*args,**kwargs)
    monkeypatch.setattr(os,'open',race)
    with pytest.raises(ReleaseError,match='release_archive_changed'):
        REAL_PIN_ARCHIVE(host.archive)
    assert replaced and not list(incoming.glob('release-*.tar.gz'))
