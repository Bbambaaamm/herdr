"""C01–C32 capacity policy, with nonuniform filesystem and memory adapters.

Real-file controller promotion/rollback/recovery remains in the rehearsal suite.
These tests deliberately do not represent physical mount/systemd acceptance.
"""
import ast
import hashlib
import os
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from deploy.herdr.cutover import filesystem_capacity as f, transaction_contract as t
from herdr.release import ReleaseError

G = 1024**3


@pytest.fixture
def model(tmp_path, monkeypatch):
    archive = tmp_path/'official.tar.gz'
    archive.write_bytes(b'x'*1507591)
    api = {k:tmp_path/k for k in ('STATE_DIR','INCOMING_DIR','RELEASES')}
    for p in api.values():p.mkdir()
    monkeypatch.setattr(f,'TEMP',tmp_path/'tmp')
    monkeypatch.setattr(f,'BACKUPS',tmp_path/'backups')
    monkeypatch.setattr(f,'OFFSITE',tmp_path/'offsite')
    for p in (f.TEMP,f.BACKUPS,f.OFFSITE):p.mkdir()
    config = dict(split={str(f.TEMP):42},free={2049:13608820736,42:2932469760},
                  inodes={},total={2049:80279486464,42:4061155328},memory=4*G,
                  mount_offset=0,table_revision=0)
    monkeypatch.setattr(f,'mounts',lambda:[{'revision':config['table_revision']}])
    def observer(path, table):
        key=config['split'].get(str(path),2049)
        return dict(path=str(path),existing=str(path),mount_id=key+config['mount_offset'],
            mountpoint=str(path) if key!=2049 else '/',mount_root='/',device=key,
            fsid=key,type='tmpfs' if key==42 else 'ext4',source='fixture',
            options='rw',super_options='rw',block_bytes=4096,
            total_bytes=config['total'].get(key,80*G),available_bytes=config['free'].get(key,20*G),
            free_inodes=config['inodes'].get(key,1000000),quota='verified')
    monkeypatch.setattr(f,'observe',observer)
    monkeypatch.setattr(f,'memory_headroom',lambda:dict(available_bytes=config['memory'],cgroup_headroom_bytes=[]))
    def run(**kwargs):return t.capacity(api,archive,5971968,**kwargs)
    return SimpleNamespace(archive=archive,api=api,config=config,run=run,observer=observer)


def test_C03_original_exact_RC10_red(model):
    # Exact baseline capacity function, same bytes as release commit. No checkout
    # switch and no mutation of the approved original installer.
    original=(Path(__file__).parent/'fixtures/rc10_transaction_capacity.py.txt').read_bytes()
    assert hashlib.sha256(original).hexdigest()=='56a88c90413bf4b79e66e1c5dfd2ec40fe4b4f9af33d086ba2b5dbd2b66f3fe0'
    source=original.decode()
    node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='capacity')
    class LegacyPath:
        def __init__(self,value):self.value=str(value)
        def glob(self,pattern):return []
        def exists(self):return True
        @property
        def parent(self):return self
        def __str__(self):return self.value
    def space(p):
        value=4061155328 if str(p)=='/tmp' else 13608820736
        return SimpleNamespace(f_bavail=value//4096,f_frsize=4096,f_favail=1000000)
    def need(ok,reason):
        if not ok:raise ReleaseError('transaction_'+reason)
    ns=dict(Path=LegacyPath,os=SimpleNamespace(statvfs=space),need=need,RESERVE_BYTES=t.RESERVE_BYTES)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<exact RC10 capacity>','exec'),ns)
    with pytest.raises(ReleaseError,match='transaction_capacity_insufficient'):
        ns['capacity'](model.api,model.archive,5971968)
    assert model.run()['status']=='verified'


@pytest.mark.parametrize('case', ['C01','C02','C04','C08','C09','C10','C11','C12','C13','C14'])
def test_topologies(model,case,monkeypatch):
    c=model.config
    if case=='C01':c['split']={};c['free'][2049]=20*G
    if case=='C08':c['split'][str(model.api['RELEASES'])]=801
    if case=='C09':
        for k in ('STATE_DIR','INCOMING_DIR'):c['split'][str(model.api[k])]=901
    if case=='C10':
        c['split'][str(f.BACKUPS)]=1001;c['split'][str(f.OFFSITE)]=1002
    if case=='C11':
        for i,p in enumerate([*model.api.values(),f.BACKUPS,f.OFFSITE],900):c['split'][str(p)]=i
    if case=='C14':
        model.api['STATE_DIR']=model.api['STATE_DIR']/'not-yet-created'
    if case=='C13':
        base=model.observer
        def bind(path,table):
            row=base(path,table)
            if path==model.api['INCOMING_DIR']:row.update(mount_id=999,mount_root='/bind-root')
            return row
        # Same allocation domain, different attested mount IDs and bind roots.
        monkeypatch.setattr(f,'observe',bind)
    report=model.run(); domains=report['filesystems']
    assert all(d['status']=='PASS' for d in domains)
    assert len(domains)==len({(r['device'],r['fsid']) for r in report['topology']})
    disk=next(d for d in domains if 'host' in d['roles'])
    assert disk['reserves']['host_policy']==13555990528
    if case!='C01':
        temp=next(d for d in domains if 'temporary' in d['roles'])
        assert temp['required_bytes']<4061155328
        assert 'host_policy' not in temp['reserves']


@pytest.mark.parametrize('case',['C05','C06','C07','C16','C17','C22','C27'])
def test_fail_closed(model,case):
    before=model.run()
    if case in ('C05','C16'):model.config['free'][2049]=10*G
    if case=='C06':model.config['free'][42]=4096
    if case=='C07':model.config['inodes'][42]=32767
    if case=='C17':(f.BACKUPS/'hermes-backup-auto-test.zip').write_bytes(b'')
    if case=='C17':
        # Sparse file changes backup admission without allocating test gigabytes.
        with open(f.BACKUPS/'hermes-backup-auto-test.zip','r+b') as stream:stream.truncate(G)
    if case=='C22':
        disk=next(d for d in before['filesystems'] if 'host' in d['roles'])
        model.config['free'][2049]=disk['required_bytes']-1
    if case=='C27':model.config['memory']=1
    with pytest.raises(f.CapacityError) as exc:model.run()
    assert exc.value.report['status']=='rejected'
    assert any(d['status']=='FAIL' and d['reasons'] for d in exc.value.report['filesystems'])


def test_C15_mount_drift(model):
    old=model.run()['topology'];model.config['mount_offset']=1
    with pytest.raises(ReleaseError,match='mount_topology_drift'):model.run(expected=old)


@pytest.mark.parametrize('case',['C18','C19','C20','C21','C23','C24','C25','C26','C32'])
def test_bounds_and_lifecycle(model,case):
    if case=='C18':
        with open(model.archive,'r+b') as stream:stream.truncate(64*f.MIB)
        model.config['free'][2049]=20*G
    if case=='C19':
        report=model.run(phase='temporary');domain=report['filesystems'][0]
        assert domain['allocations'][0]['inodes']==8194
        assert domain['maximum_concurrent_bytes']==256*f.MIB+8194*4096
    if case=='C20':
        assert (t.FILE_MAX,t.MARKER_MAX,t.FILE_COUNT,t.AUTHORITY_MAX,t.BACKUP_MAX,t.JOURNAL_MAX,t.EVIDENCE_MAX,t.RESERVE_BYTES)==(131072,4096,17,262144,3238168,3246360,524288,13558880)
    if case=='C21':
        for d in model.run()['filesystems']:
            key=42 if 'temporary' in d['roles'] else 2049
            model.config['free'][key]=d['required_bytes'];model.config['inodes'][key]=d['required_inodes']
    if case=='C23':assert model.run()['backup_preparation_peak_bytes']==2684354560
    if case in ('C24','C25'):
        existing=model.api['RELEASES']/'immutable-candidate';existing.mkdir()
        (existing/'retained').write_bytes(b'evidence')
        model.run();assert (existing/'retained').read_bytes()==b'evidence'
    if case=='C26':
        model.config['free'][42]=0
        with pytest.raises(f.CapacityError):model.run(phase='temporary')
        assert not list(f.TEMP.iterdir());return
    report=model.run()
    if case=='C32':
        model.config['split']={};model.config['free'][2049]=20*G
        d=model.run()['filesystems'][0]
        assert d['maximum_concurrent_bytes']==max(d['phase_allocations'].values())
        assert d['maximum_concurrent_bytes']<sum(a['bytes'] for a in d['allocations'])
    assert report['status']=='verified'


def test_C31_unverified_filesystem_and_quota(monkeypatch):
    row=dict(options='rw',super_options='prjquota')
    with pytest.raises(ReleaseError,match='project_quota_unverified'):
        f.quota_headroom(-1,row,20*G,1000000)


@pytest.mark.parametrize('result,valid',[(0,15),(0,0),(-1,0)])
def test_C31_enabled_quota_requires_valid_observation(monkeypatch,result,valid):
    class Query:
        def __call__(self,fd,command,identity,pointer):
            q=pointer._obj;q.valid=valid;q.bhard=1024;q.space=1024
            q.ihard=100;q.inodes=10
            return result
    monkeypatch.setattr(f.ctypes,'CDLL',lambda *a,**kw:SimpleNamespace(quotactl_fd=Query()))
    row=dict(options='rw',super_options='usrquota')
    if result==0 and valid==15:
        available,inodes,status=f.quota_headroom(-1,row,20*G,1000000)
        assert (available,inodes,status)==(1047552,90,'verified')
    else:
        with pytest.raises(ReleaseError,match='quota_'):
            f.quota_headroom(-1,row,20*G,1000000)


def test_temporary_memory_includes_verification_working_set(model):
    d=model.run(phase='temporary')['filesystems'][0]
    assert d['memory']['required_bytes']>d['maximum_concurrent_bytes']


@pytest.mark.parametrize('nested', [False, True])
def test_real_memory_observer_root_and_enclosing_limits(monkeypatch,nested):
    data={'/proc/meminfo':b'MemAvailable: 4194304 kB\n',
          '/proc/self/cgroup':b'0::/parent/child\n' if nested else b'0::/\n',
          '/cg/parent/child/memory.max':str(2*G).encode(),
          '/cg/parent/child/memory.current':str(G).encode(),
          '/cg/parent/memory.max':str(G).encode(),
          '/cg/parent/memory.current':str(G//2).encode()}
    def read(p,*args):
        if str(p) not in data:raise FileNotFoundError(str(p))
        return data[str(p)]
    monkeypatch.setattr(f,'bounded',read)
    monkeypatch.setattr(f,'mounts',lambda:[dict(type='cgroup2',root='/',mount='/cg')])
    observed=f.memory_headroom()
    assert observed['available_bytes']==(G//2 if nested else 4*G)
    assert len(observed['cgroup_headroom_bytes'])==(2 if nested else 0)


def test_C27_unreadable_limit_is_not_unlimited(monkeypatch):
    data={'/proc/meminfo':b'MemAvailable: 4194304 kB\n','/proc/self/cgroup':b'0::/child\n'}
    def read(p,*args):
        if str(p) not in data:raise PermissionError('isolated missing authority')
        return data[str(p)]
    monkeypatch.setattr(f,'bounded',read)
    monkeypatch.setattr(f,'mounts',lambda:[dict(type='cgroup2',root='/',mount='/cg')])
    with pytest.raises(PermissionError):f.memory_headroom()


@pytest.mark.skipif(os.name!='posix',reason='Linux descriptor-based observer')
def test_C14_actual_nearest_existing_ancestor_and_symlink(tmp_path):
    fd,existing=f.directory(tmp_path/'missing'/'child')
    try:assert existing==tmp_path and os.fstat(fd).st_ino==tmp_path.stat().st_ino
    finally:os.close(fd)
    (tmp_path/'alias').symlink_to(tmp_path,target_is_directory=True)
    with pytest.raises(OSError):f.directory(tmp_path/'alias'/'child')


@pytest.mark.skipif(os.name!='posix',reason='Linux mount observer')
def test_actual_observer_and_device_mismatch(tmp_path,monkeypatch):
    table=f.mounts()
    observed=f.observe(tmp_path,table)
    assert observed['available_bytes']>=0 and observed['path']==str(tmp_path)
    bad=[dict(r,device='0:0') for r in table]
    with pytest.raises(ReleaseError,match='mount_device_changed'):f.observe(tmp_path,bad)
    readonly=[dict(r,options='ro') for r in table]
    with pytest.raises(ReleaseError,match='read_only_filesystem'):f.observe(tmp_path,readonly)


def test_destination_block_size_is_per_entry(model,monkeypatch):
    small=model.run()
    observe=model.observer
    def large(path,table):
        r=observe(path,table)
        if path==model.api['RELEASES']:r.update(device=901,fsid=901,mount_id=901,block_bytes=65536)
        return r
    monkeypatch.setattr(f,'observe',large)
    d=next(d for d in model.run()['filesystems'] if 'release' in d['roles'])
    assert d['maximum_concurrent_bytes']+d['reserves']['approved_candidate_safety']>=3*(5971968+(65536-4096)*8194)


def test_C32_multiple_tmpfs_share_physical_memory(model,monkeypatch):
    observe=model.observer
    model.config['split'][str(f.BACKUPS)]=43
    model.config['split'][str(f.OFFSITE)]=44
    def tmpfs(path,table):
        r=observe(path,table)
        if r['device'] in (43,44):r['type']='tmpfs'
        return r
    monkeypatch.setattr(f,'observe',tmpfs)
    with pytest.raises(f.CapacityError) as exc:model.run()
    assert any('memory_headroom' in d['reasons'] for d in exc.value.report['filesystems'])


def test_C18_archive_one_byte_over_ceiling(model):
    with open(model.archive,'r+b') as stream:stream.truncate(64*f.MIB+1)
    with pytest.raises(ReleaseError,match='archive_size'):model.run()


def test_C26_verifier_rejects_before_first_extraction(model,monkeypatch):
    from deploy.herdr.cutover import cutover as c
    called=[]
    monkeypatch.setattr(c,'_verify_archive',lambda *a,**kw:called.append(True))
    model.config['free'][42]=0
    with pytest.raises(f.CapacityError):c.verify_archive(model.archive)
    assert not called and not list(f.TEMP.iterdir())


@pytest.mark.skipif(os.name!='posix',reason='Linux stable descriptors and fsync')
@pytest.mark.parametrize('corrupt',[False,True])
def test_cross_filesystem_evidence_transfer(tmp_path,monkeypatch,corrupt):
    from deploy.herdr.cutover import cutover as c
    source=tmp_path/'source.tar.gz';source.write_bytes(b'original evidence');source.chmod(0o400)
    target=tmp_path/'state'/'retained.tar.gz';target.parent.mkdir()
    real_lstat,real_fstat=Path.lstat,os.fstat
    class SourceInfo:
        def __init__(self,s):self.s=s;self.st_uid=0;self.st_dev=s.st_dev+1
        def __getattr__(self,k):return getattr(self.s,k)
    def lstat(p,*a,**kw):
        s=real_lstat(p,*a,**kw)
        return SourceInfo(s) if Path(p)==source else s
    def fstat(fd):
        s=real_fstat(fd)
        return SourceInfo(s) if os.readlink('/proc/self/fd/'+str(fd))==str(source) else s
    monkeypatch.setattr(Path,'lstat',lstat);monkeypatch.setattr(os,'fstat',fstat)
    if corrupt:
        monkeypatch.setattr(c,'digest_file',lambda p:'0'*64)
        with pytest.raises(ReleaseError,match='evidence_archive_readback'):c.retain_archive(source,target)
        assert source.read_bytes()==b'original evidence' and not target.exists()
    else:
        c.retain_archive(source,target)
        assert not source.exists() and target.read_bytes()==b'original evidence'
        assert target.stat().st_mode&0o777==0o400
    assert not list(target.parent.glob('.archive-*'))

