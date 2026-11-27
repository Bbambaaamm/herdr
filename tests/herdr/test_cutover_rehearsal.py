"""B29: isolated real-file deployment, OS/systemd/network adapters only.

No live systemd or model calls. The archive, controller, manifests, pin/install,
preflight, authority capture, documents, readiness and rollback are real.
"""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import shutil
import socket
import stat
import tarfile
import time
from types import SimpleNamespace

import pytest

from deploy.herdr.cutover import cutover as c, systemd_authority as s
from herdr import release
from agent_platform_dashboard import production_contract as pc, observability
from agent_platform_dashboard.production_credentials import material
from test_systemd_authority import manager


@pytest.fixture
def rehearsal(tmp_path, monkeypatch, manager):
    root = tmp_path / 'isolated-host'
    root.mkdir(mode=0o700)
    for name, relative in dict(RELEASES='releases', STATE_DIR='state/deployments',
                               INCOMING_DIR='state/incoming', CONSUMER_DIR='consumers',
                               LEGACY='legacy').items():
        p = root / relative
        p.mkdir(parents=True, mode=0o700)
        monkeypatch.setattr(c, name, p)
    (root/'state').chmod(0o700)
    for name in ('PUBLIC_STATE', 'BRIDGE', 'SNAPSHOT', 'NGINX_ROUTE', 'NGINX_LOCATION_COMMON',
                 'WEB_CONFIG', 'CURRENT', 'DEPLOYMENT_LOCK', 'WATCHDOG_LOCK'):
        monkeypatch.setattr(c, name, root / name.lower())
    monkeypatch.setattr(c, 'UNIT_DIR', manager.units)
    monkeypatch.setattr(c, 'HOST_POLICY_PATH', manager.api['HOST_POLICY_PATH'], raising=False)
    manager.capacity()
    source = Path(__file__).resolve().parents[2]
    stage = root / 'payload'
    stage.mkdir()
    # Copy only the closed production payload, never host data or credentials.
    for relative in release.PAYLOAD_PATHS:
        src, dest = source / relative, stage / relative
        if not src.exists():
            continue
        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_dir():
            shutil.copytree(src, dest, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        else:
            shutil.copyfile(src, dest)
    binary = b'isolated external binary fixture' * 2
    dependency = dict(name='herdr', version='0.9.1', size=len(binary), sha256=release.sha256(binary))
    (c.LEGACY / 'herdr').write_bytes(binary)
    (c.LEGACY / 'DEPLOYED_GIT_SHA').write_text('fixture-legacy')
    c.NGINX_ROUTE.write_bytes(b'authenticated-route')
    external = root / 'external'
    external.mkdir()
    entries = {}
    for name in ('herdr', 'hermes', 'majak', 'quantlab', 'agent-codex-usage-export',
                 'hermes-offsite-prepare', 'hermes-offsite-sync'):
        p = external / name
        p.write_bytes(b'never executed: ' + name.encode())
        entries[str(p)] = s.facts(p)
    contract_dir = stage / 'deploy/herdr/cutover'
    (contract_dir / 'external-runtime-authority.json').write_bytes(release.canonical_json(entries))
    (contract_dir / 'capacity-repair-authority.json').write_bytes(release.canonical_json({
        'files': {str(manager.authority.dropin): s.facts(manager.authority.dropin)}, 'trees': {}}))
    hashes = {c.UNIT_DIR / name: release.sha256((c.UNIT_DIR / name).read_bytes()) for name in c.UNITS}
    hashes[c.NGINX_ROUTE] = release.sha256(c.NGINX_ROUTE.read_bytes())
    (contract_dir / 'legacy-quantlab-staging-01.sha256').write_text(
        ''.join(digest + '  ' + str(path) + '\n' for path, digest in hashes.items()))

    def tree(tag, commit, parent):
        target = parent / (tag + '-' + commit[:12])
        shutil.copytree(stage, target)
        policies = {name+'.yaml': (target/'configs/consumers'/(name+'.yaml')).read_bytes() for name in c.CONSUMERS}
        metadata = dict(schema_version=1, tag=tag, commit=commit, commit_time=1,
                        config_contract_sha256=release.consumer_digest(policies),
                        external_dependency=dependency, payload_manifest_sha256='0'*64)
        (target/'RELEASE.json').write_bytes(release.canonical_json(metadata))
        manifest = release.file_manifest(target)
        metadata['payload_manifest_sha256'] = release.sha256(manifest)
        (target/'RELEASE.json').write_bytes(release.canonical_json(metadata))
        (target/'MANIFEST.sha256').write_bytes(manifest)
        assert release.verify_tree(target) == metadata
        return target, metadata

    previous, old = tree('v0.3.0-router-v5-p1d-rc6', s.RC6, c.RELEASES)
    controller, candidate = tree('v0.3.0-router-v5-p1d-rc10', 'b'*40, c.INCOMING_DIR)
    for name in c.CONSUMERS:
        shutil.copyfile(previous/'configs/consumers'/(name+'.yaml'), c.CONSUMER_DIR/(name+'.yaml'))
    archive = root/'candidate.tar.gz'
    with tarfile.open(archive, 'w:gz') as out:
        out.add(controller, arcname=controller.name)
    for p in [controller, *controller.rglob('*')]:
        p.chmod(0o555 if p.is_dir() or p.parent.name == 'bin' else 0o444)
    monkeypatch.setattr(c, 'ROOT', controller)
    monkeypatch.setattr(c, 'IMMUTABLE_PREFLIGHT_ROOTS', (c.INCOMING_DIR,))
    c.CURRENT.symlink_to(previous)
    document = c.deployed_document(old, old['config_contract_sha256'], int(time.time()))
    c.PUBLIC_STATE.write_bytes(release.canonical_json(document))
    c.PUBLIC_STATE.chmod(0o640)
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock = root/'herdr.sock'
    listener.bind(str(sock))
    listener.listen()
    monkeypatch.setattr(c, 'HERDR_SOCKET', sock)
    auth = root/'auth.json'
    auth.write_bytes(release.canonical_json(material('x'*32, b's'*16)))
    auth.chmod(0o600)
    c.WEB_CONFIG.write_bytes(release.canonical_json(dict(version=1, snapshot=str(c.SNAPSHOT), auth=str(auth))))

    # Label only ownership at the isolated OS boundary. Preserve the real
    # size/inode/link/mode/timestamps and every no-follow read/write operation.
    class Info:
        def __init__(self, value, path):
            self.value = value
            telemetry = str(path) in (str(c.BRIDGE), str(c.SNAPSHOT))
            self.st_uid, self.st_gid = (1001, 982) if telemetry else (0, 0)
        def __getattr__(self, name):
            return getattr(self.value, name)
        def __getitem__(self, index):
            return self.value[index]
    real_stat, real_lstat, real_fstat = os.stat, os.lstat, os.fstat
    monkeypatch.setattr(os, 'stat', lambda path, *a, **kw: Info(real_stat(path,*a,**kw), path))
    monkeypatch.setattr(os, 'lstat', lambda path,*a,**kw: Info(real_lstat(path,*a,**kw), path))
    monkeypatch.setattr(os, 'fstat', lambda fd: Info(real_fstat(fd), os.readlink('/proc/self/fd/'+str(fd))))
    monkeypatch.setattr(os, 'chown', lambda *a,**kw: None)
    monkeypatch.setattr(os, 'geteuid', lambda: 0)
    monkeypatch.setenv('SUDO_UID', '0')
    monkeypatch.setattr(os, 'statvfs', lambda p: SimpleNamespace(f_bavail=100*1024**3//4096, f_frsize=4096, f_favail=1000000))
    from capacity_fixture import install
    install(monkeypatch, root)
    monkeypatch.setattr(c, 'root_owned_readonly', lambda p: p in root.parents or not p.stat().st_mode & 0o022)
    monkeypatch.setattr(c.transactions, 'aggregate_ancestors', lambda p: None)
    monkeypatch.setattr(c.socket, 'gethostname', lambda: c.HOST)
    monkeypatch.setattr(c, 'pwd', SimpleNamespace(getpwnam=lambda _: SimpleNamespace(pw_uid=1001)))
    monkeypatch.setattr(c, 'grp', SimpleNamespace(getgrnam=lambda _: SimpleNamespace(gr_gid=982)))
    monkeypatch.setattr(c, 'WATCHDOG_STABILITY_SECONDS', 0.01)
    real_replace = os.replace
    def privileged_replace(src, dest):
        # Linux root may move an immutable directory between parents. Emulate
        # that permission at the OS boundary, retaining the final real mode.
        directory = Path(src).is_dir()
        mode = stat.S_IMODE(Path(src).stat().st_mode) if directory else None
        if directory:
            Path(src).chmod(0o700)
        try:
            return real_replace(src, dest)
        finally:
            if directory:
                (Path(dest) if Path(dest).exists() else Path(src)).chmod(mode)
    monkeypatch.setattr(os, 'replace', privileged_replace)
    states = {name:'active' for name in c.UNITS}
    states.update({'agent-platform-web.service':'failed', 'agent-platform-export.service':'inactive',
                   'agent-platform-herdr.service':'failed'})
    fail = {'candidate':False}
    events = []

    def publish():
        now = int(time.time())
        agents = [dict(agent=p+'-hermes',status='idle') for p in pc.PROFILES]
        c.BRIDGE.write_bytes(release.canonical_json(dict(version=1,observed_at=now,profiles=list(pc.PROFILES),agents=agents)))
        c.BRIDGE.chmod(0o640)
        model = pc.unavailable(now)
        deployed = json.loads(c.PUBLIC_STATE.read_bytes())
        for row in model['sources']:
            if row['kind'] in ('herdr','router','release'):
                rows = ([a for a in agents if a['agent'].startswith(row['profile'])] if row['kind']=='herdr'
                        else [{k:deployed[k] for k in ('tag','commit','config_sha256','deployed_at')}] if row['kind']=='release' else [])
                row.update(status='available',reason='ok',rows=rows,data_at=now)
        model['observability'] = observability.build(model)
        raw = pc.encode(model)
        require_size = 119973
        assert len(raw) <= require_size
        c.SNAPSHOT.write_bytes(raw + b' '*(require_size-len(raw)))
        c.SNAPSHOT.chmod(0o640)
        assert pc.decode(c.SNAPSHOT.read_bytes()) == model

    def run(*args, check=True):
        events.append(args)
        if args[0] in ('/usr/bin/pgrep','/usr/sbin/nginx'):
            return ''
        assert args[0] == '/usr/bin/systemctl', args
        action = args[1]
        if action == 'is-active':
            return states[args[2]]
        if action in ('start','stop'):
            for name in args[2:]:
                states[name] = 'active' if action=='start' else 'inactive'
                if action=='start' and name=='agent-platform-export.service':
                    publish()
                    states['agent-platform-herdr.service']='inactive'
                if action=='start' and name=='agent-platform-web.service' and fail['candidate']:
                    raise release.ReleaseError('injected_rehearsal_candidate_failure')
            return ''
        if action == 'show':
            if '--property=Result' in args:
                return 'success'
            if 'MainPID' in args:
                return 'ActiveState=active\nSubState=running\nMainPID=123\nNRestarts=0'
            if 'ProtectKernelTunables' in args:
                return '\n'.join(p+'=yes' for p in args if p not in ('-p',) and p[0].isupper())
            name = args[2]
            path = c.UNIT_DIR/name
            directives = s.unit_directives(path)
            dropins = sorted(path.parent.glob(name+'.d/*.conf'))
            for p in dropins:
                for key, values in s.unit_directives(p).items():
                    directives[key] = values
            row = dict(FragmentPath=str(path),LoadState='loaded',Transient='no',NeedDaemonReload='no',
                       DropInPaths=' '.join(map(str,dropins)),Environment=' '.join(directives.get('Environment',[])))
            row.update({k:''.join(directives.get(k,[])) for k in ('User','Group','WorkingDirectory')})
            for key in s.COMMANDS:
                row[key] = ' '.join('{ path='+line.split()[0]+' ; argv[]='+line+' ; ignore_errors=no ; }'
                                    for line in directives.get(key,[]))
            return '\n'.join(k+'='+v for k,v in row.items())
        assert action in ('daemon-reload','reset-failed','reload'), args
        return ''
    monkeypatch.setattr(c, 'run', run)
    real_authority = s.SystemdAuthority
    class IsolatedAuthority(real_authority):
        def __init__(self, api):
            super().__init__(api,unit_search_roots=(c.UNIT_DIR,root/'empty-run',root/'empty-vendor'))
    monkeypatch.setattr(c, 'SystemdAuthority', IsolatedAuthority)
    def http(url):
        if url.endswith('165/'):
            return '307'
        if '127.0.0.1' in url:
            return '401' if states['agent-platform-web.service']=='active' else '000'
        return '401' if c.NGINX_ROUTE.read_bytes()==b'authenticated-route' else '503'
    monkeypatch.setattr(c, 'http_status', http)
    publish()
    try:
        yield SimpleNamespace(archive=archive, release=candidate, previous=previous,
                              fail=fail, events=events, states=states, root=root,
                              tree=tree, publish=publish, stage=stage)
    finally:
        listener.close()
        # Only this test's newly created private directories, for pytest cleanup.
        for p in [root, *root.rglob('*')]:
            if p.is_dir() and not p.is_symlink():
                p.chmod(0o700)


@pytest.mark.parametrize('fail_candidate',[False,True],ids=['B29_promotion','B29_rollback'])
def test_B29_complete_isolated_deployment(rehearsal, fail_candidate):
    r = rehearsal
    preflight = c.preflight(r.archive,'fixture-legacy')
    domains = preflight['transaction_contract']['capacity']['filesystems']
    assert len({d['identity'] for d in domains}) == 2
    assert next(d for d in domains if d['type']=='tmpfs')['required_bytes'] < 4061155328
    assert next(d for d in domains if 'host' in d['roles'])['reserves']['host_policy'] >= 12*1024**3
    assert preflight['transaction_contract']['status']=='verified'
    assert preflight['transaction_contract']['authority_backup_serialized_bytes']>131072
    assert preflight['systemd_authority']['mode']=='capacity_rc6'
    assert len(preflight['systemd_authority']['units'])==6
    assert len(preflight['systemd_authority']['external_runtimes'])==7
    r.fail['candidate']=fail_candidate
    confirmation = preflight['release']['tag']+'-'+preflight['release']['commit'][:12]
    if fail_candidate:
        with pytest.raises(release.ReleaseError,match='rollback_degraded'):
            c.apply(r.archive,'fixture-legacy',confirmation)
        assert c.CURRENT.resolve()==r.previous
        assert (c.UNIT_DIR/'agent-stack-watchdog.service.d/126-capacity-repair.conf').exists()
    else:
        result = c.apply(r.archive,'fixture-legacy',confirmation)
        assert result['status']=='success'
        assert release.verify_tree(c.CURRENT.resolve())==r.release
        assert c.assert_candidate_ready(c.CURRENT.resolve(),c.read_trusted_public_state(c.PUBLIC_STATE)) is None
    assert not (c.STATE_DIR/'transaction.json').exists()
    assert not c.watchdog_fence_path().exists()
    assert not c.watchdog_permit_path().exists()
    assert list(c.STATE_DIR.glob('*-baseline-authority.json'))
    assert list(c.STATE_DIR.glob('*-preparation.json'))


def test_C24_C25_real_existing_candidate_after_prejournal_failure(rehearsal,monkeypatch):
    r=rehearsal
    report=c.preflight(r.archive,'fixture-legacy')
    confirmation=report['release']['tag']+'-'+report['release']['commit'][:12]
    original=c.begin_transaction
    def fail(*a,**kw):raise release.ReleaseError('isolated_before_journal')
    monkeypatch.setattr(c,'begin_transaction',fail)
    with pytest.raises(release.ReleaseError,match='isolated_before_journal'):
        c.apply(r.archive,'fixture-legacy',confirmation)
    target=c.RELEASES/confirmation
    assert release.verify_tree(target)==r.release
    assert c.CURRENT.resolve()==r.previous
    assert not (c.STATE_DIR/'transaction.json').exists()
    assert list(c.STATE_DIR.glob('*-preparation.json'))
    retained=list(c.INCOMING_DIR.glob('release-*.tar.gz'))
    assert retained
    monkeypatch.setattr(c,'begin_transaction',original)
    assert c.apply(r.archive,'fixture-legacy',confirmation)['status']=='success'
    assert all(p.exists() for p in retained)


def test_B30_historical_recovery_real_preflight_and_apply(rehearsal, monkeypatch):
    """Private fixture pins replace historical artifact pins, never host gates."""
    import sqlite3
    from agent_platform_dashboard.production_sources import ROUTER_COLUMNS
    r = rehearsal
    (c.UNIT_DIR/'agent-stack-watchdog.service.d/126-capacity-repair.conf').unlink()
    c.NGINX_LOCATION_COMMON.write_bytes(b'isolated authenticated location include')
    manifest = r.stage/'deploy/herdr/cutover/legacy-quantlab-staging-01.sha256'
    manifest.write_text(manifest.read_text()+c.sha256(c.NGINX_LOCATION_COMMON.read_bytes())+'  '+str(c.NGINX_LOCATION_COMMON)+'\n')
    previous, old = r.tree(c.RECOVERY_RC8_TAG,c.RECOVERY_RC8_COMMIT,c.RELEASES)
    controller, target = r.tree(c.RECOVERY_TARGET_TAG,c.RECOVERY_TARGET_COMMIT,c.INCOMING_DIR)
    archive = r.root/'recovery.tar.gz'
    with tarfile.open(archive,'w:gz') as out:
        out.add(controller,arcname=controller.name)
    for p in [controller,*controller.rglob('*')]:
        p.chmod(0o555 if p.is_dir() or p.parent.name=='bin' else 0o444)
    monkeypatch.setattr(c,'ROOT',controller)
    monkeypatch.setattr(c,'RECOVERY_TARGET_ARCHIVE_SHA256',c.digest_file(archive))
    monkeypatch.setattr(c,'RECOVERY_TARGET_CONFIG_SHA256',target['config_contract_sha256'])
    monkeypatch.setattr(c,'RECOVERY_TARGET_PAYLOAD_MANIFEST_SHA256',target['payload_manifest_sha256'])
    monkeypatch.setattr(c,'BOOTSTRAP_VERSIONED_UNIT_HASHES',{
        (c.RECOVERY_RC8_TAG,c.RECOVERY_RC8_COMMIT):{
            name:c.digest_file(c.UNIT_DIR/name) for name in c.UNITS}})
    c.CURRENT.unlink()
    c.CURRENT.symlink_to(previous)
    c.PUBLIC_STATE.write_bytes(c.canonical_json(c.deployed_document(old,old['config_contract_sha256'],int(time.time()))))
    r.publish()
    model = pc.decode(c.SNAPSHOT.read_bytes())
    for source in model['sources']:
        if source['kind']=='router':
            source.update(status='unavailable',reason='source_failed',rows=[])
    c.SNAPSHOT.write_bytes(c.canonical_json(model))
    databases = {}
    for profile in pc.PROFILES:
        path = r.root/(profile+'.sqlite')
        with sqlite3.connect(path) as db:
            db.execute('CREATE TABLE requests ('+','.join(name+(' INTEGER' if name=='id' else ' TEXT') for name in sorted(ROUTER_COLUMNS))+')')
            for index in range(51):
                db.execute('INSERT INTO requests (id,task_id,actual_model,provider) VALUES (?,?,?,?)',
                           (index,str(index),'fixture-model','fixture-provider'))
        databases[profile] = path
    monkeypatch.setattr(c,'RECOVERY_ROUTER_DATABASES',databases)
    r.states['agent-stack-watchdog.service']='inactive'
    preflight = c.preflight(archive,'fixture-legacy',allow_degraded_rc8=True)
    assert preflight['recovery_mode']=='rc8_router_overflow'
    assert preflight['transaction_contract']['status']=='verified'
    result = c.recovery_apply(archive,'fixture-legacy',target['tag']+'-'+target['commit'][:12])
    assert result['status']=='success' and not result['rollback_exercised']
    assert c.CURRENT.resolve().name==controller.name
