"""Finite original-root lifecycle effect IO. No SDK/kernel/service/HTTP runs."""
import unittest, types, os, stat, json, hashlib, zipfile
from pathlib import Path, PurePosixPath
from contextlib import contextmanager, ExitStack
from unittest.mock import patch
import test_canonical_runtime as common
from offline_case import outer_lifecycle as outer, profile_observations as obs, publisher, case
from offline_case.root_effects import RootEffectPump, ROLE_UNITS
import offline_case.root_effects as root_effects
from offline_case.admission import HOST_UNIT
HERE=common.HERE;O=common.OVERLAY

def digest(b):return hashlib.sha256(b).hexdigest()
def canon(v):return case.canonical(v)

class LogicalPath(PurePosixPath):
    def lstat(self):return types.SimpleNamespace(st_mode=stat.S_IFREG|0o755,st_uid=0,st_gid=0,st_nlink=1)

class Fixture:
    def __init__(self):
        self.events=[];self.fail_cleanup=False;self.extra_label=None;self.journal={};self.mounts={}
        self.units={n:('inactive' if n==case.CLEANUP else 'active') for n in obs.OWN_UNITS}
        self.pids={n:700+i for i,n in enumerate(obs.OWN_UNITS)};self.ticks={pid:9000+pid for pid in self.pids.values()}
        self.groups={n:[10,i+100] for i,n in enumerate(obs.OWN_UNITS)}
        self.loaded=set(obs.OWN_PROFILES)
        self.source={}
        files={}
        for n in ('offline_case/driver.py','offline_case/payload.py','overlays/host-profile.apparmor','overlays/operator-profile.apparmor',
                  'overlays/worker-profile.apparmor','overlays/observer-profile.apparmor','overlays/trusted-preparation.apparmor'):
            b=(O/n).read_bytes();files[n]=digest(b);self.source['/etc/herdr/'+n.split('/')[-1]]=b
        self.source['/proc/sys/kernel/random/boot_id']=b'boot\n'
        self.unit_bytes={}
        for n in obs.OWN_UNITS:
            p=O/'units'/n;b=p.read_bytes() if p.exists() else ('fixture-own-unit:'+n).encode()
            self.unit_bytes[n]=b;self.source['/etc/systemd/system/'+n]=b
            if p.exists():files['units/'+n]=digest(b)
        self.build={'files':files}
        a={k:'a'*64 for k in case.AUTH_KEYS}
        a.update(schema=2,purpose='SINGLE_OFFLINE_PHYSICAL_CASE',nonce=case.NONCE,case_unit=case.CASE,
          cleanup_unit=case.CLEANUP,cleanup_timer=case.TIMER,profile=case.PROFILE,profile_source_sha256=case.PROFILE_SOURCE,
          observer=case.OBSERVER,observer_source_sha256=case.OBSERVER_SOURCE,preparer=case.PREP,prep_source_sha256=case.PREP_SOURCE,
          host_profile=case.HOST_PROFILE,host_profile_source_sha256=files['overlays/host-profile.apparmor'],
          operator_profile=case.OPERATOR_PROFILE,operator_source_sha256=files['overlays/operator-profile.apparmor'],
          baseline_sha256=case.BASELINE,baseline_state_sha256=case.BASELINE_STATE,executor=case.EXECUTOR,
          build_sha256=digest(canon(self.build)),driver_sha256=files['offline_case/driver.py'],payload_sha256=files['offline_case/payload.py'],
          boot_id='boot',not_before=case.DEADLINE-1800,deadline=case.DEADLINE,budget=case.BUDGET)
        self.authority=a
        self.binding={'nonce':case.NONCE,'challenge':a['challenge'],'boot_id':'boot','authority_sha256':digest(canon(a)),
                      'build_sha256':a['build_sha256']}
        self.state={'phase':'START_INTENT','binding':self.binding}
        self.metadata={}
        for role,n in ROLE_UNITS.items():
            value={'unit':n,'cgroup':self.groups[n],'invocation_id':'f'*32,'main_pid':self.pids[n],
                'main_start_ticks':self.ticks[self.pids[n]],'source_sha256':digest(self.unit_bytes[n])}
            self.metadata[role+'-unit']={'binding':self.binding,'value':value}
        n='herdr-offline-observer-03414499dd0d1986.service'
        self.metadata['observer-control-unit']={'binding':self.binding,'value':{'source_sha256':digest(self.unit_bytes[n])}}
        self.view=self.View(self)
        self.lifecycle=outer.OuterLifecycle(self.build,self)
        pump=self.lifecycle.pump
        pump._read=lambda name:self.metadata.get(name)
        def metadata(kind,binding,value):
            if kind in self.metadata:case.require(self.metadata[kind]['binding']==binding,'changed fixture metadata')
            else:self.metadata[kind]={'binding':binding,'value':value}
            self.events.append(('metadata',kind));return value
        pump._metadata=metadata
        self.lifecycle.consumed=lambda:outer.read_consumed(self.build,reader=self.read_pinned,read_boot=lambda:'boot')
        self.command_bytes={name:('fixture-command:'+name).encode() for name in outer.HOST_COMMAND_PINS}
    def read_pinned(self,p,**kwargs):
        name=str(p).replace('\\','/')
        if p.name=='authority.json':return canon(self.authority)
        if p.name=='state.json':return canon(self.state)
        if p.name=='used-'+case.NONCE+'.json':return canon(self.binding)
        if p.name.startswith('caller-'):
            n=case.OPERATOR;pid=self.pids[n]
            return canon({'pid':pid,'cgroup':'0::/system.slice/'+n,'boot_id':'boot','build_sha256':self.binding['build_sha256'],
                          'start_ticks':self.ticks[pid]})
        if p.name=='roster.json':
            pid=self.pids[HOST_UNIT]
            return canon({'case_binding':self.binding,'controller':{'pid':pid,'start_ticks':self.ticks[pid],'profile':case.HOST_PROFILE}})
        if p.suffix=='.json' and p.stem in self.metadata:return canon(self.metadata[p.stem])
        if name.endswith('.mount.json') and p.stem[:-6] in self.mounts:return canon(self.mounts[p.stem[:-6]])
        if name.startswith(str(root_effects.CONTEXT)+'/'):raise FileNotFoundError(name)
        if name in self.command_bytes:return self.command_bytes[name]
        if name in self.source:return self.source[name]
        raise AssertionError(name)
    def read(self,p,n):
        name=str(p).replace('\\','/')
        if name.endswith('/boot_id'):return b'boot\n'
        if name=='/proc/self/attr/current':return b'unconfined'
        if name=='/sys/kernel/security/apparmor/profiles':return self.view.text(name).encode()
        raise AssertionError(name)
    def exists(self,p):return False
    def identity(self,p):return tuple(self.groups[p.name])
    def process_start_ticks(self,pid):return self.ticks[pid]
    def loaded_profile_sha256(self,p):
        case.require(p in self.loaded,'profile absent');return 'a'*64
    def stop_cgroup(self,p,identity):
        case.require(tuple(self.groups[p.name])==tuple(identity),'foreign fixture cgroup')
        self.events.append(('kill',p.name))
    def run(self,*args,**kwargs):
        self.events.append(tuple(args))
        if args[0]=='/usr/bin/systemd-run':return ''
        if args[0]=='/usr/sbin/apparmor_parser':
            assert 'outer-policy-retirement-intent.json' in self.journal,'effect before original custody consume'
            name=Path(args[-1]).name
            mapping={'worker-profile.apparmor':case.PROFILE,'trusted-preparation.apparmor':case.PREP,
              'observer-profile.apparmor':case.OBSERVER,'host-profile.apparmor':case.HOST_PROFILE,'operator-profile.apparmor':case.OPERATOR_PROFILE}
            self.loaded.remove(mapping[name]);return ''
        assert args[0]=='/usr/bin/systemctl',args
        if args[1]=='show':
            n=args[2];state=self.units.get(n,'active' if n.endswith('.timer') else 'inactive')
            props={'ActiveState':state,'LoadState':'loaded','ControlGroup':'/system.slice/'+n,'MainPID':str(self.pids.get(n,0)) if state=='active' else '0',
                'InvocationID':'f'*32,'FragmentPath':'/etc/systemd/system/'+n}
            if '--value' in args:return props[next(x.split('=',1)[1] for x in args if x.startswith('--property='))]+'\n'
            return '\n'.join(k+'='+v for k,v in props.items())+'\n'
        if args[1]=='stop':
            for n in args[2:]:
                self.units[n]='inactive'
                if n==HOST_UNIT:self.units['herdr-offline-observer-03414499dd0d1986.service']='inactive' # actual BindsTo
            return ''
        if args[1]=='start' and args[2]==case.CLEANUP:
            self.units[case.CLEANUP]='active'
            if self.fail_cleanup:
                self.state['phase']='RETAINED_UNKNOWN';self.units[case.CLEANUP]='inactive';raise case.Denied('inert cleanup loss')
            self.lifecycle.pump.stop_roles(self.binding) # actual root-owned role stop API
            self.units[case.CASE]='inactive'
            self.run('/usr/bin/systemctl','stop',HOST_UNIT)
            self.state['phase']='RETIRED';self.units[case.CLEANUP]='inactive' # oneshot exits, no RemainAfterExit
            return ''
        raise AssertionError(args)
    class View:
        def __init__(self,f):
            self.f=f;self.racy=False;self.private_fd=None;self.private_map=None
            self.thread_private_fd=None;self.fd_mount_id=1;self.mount_namespace='mnt:[999]';self.pid_namespace='pid:[999]'
            self.cwd='/safe';self.root='/';self.thread_cwd='/safe';self.thread_root='/'
            self.cwd_mount_id=1;self.root_mount_id=1;self.thread_cwd_mount_id=1;self.thread_root_mount_id=1
            self.map_mount_id=1;self.thread_map_mount_id=1
        def directories(self,p,numeric=False):
            if p=='/proc':return ['999']+[str(self.f.pids[n]) for n,s in self.f.units.items() if s=='active' and n in self.f.pids]
            if p.endswith('/task'):return [p.split('/')[-2],'1000'] if self.f.extra_label else [p.split('/')[-2]]
            return []
        def text(self,p):
            if p.endswith('/boot_id'):return 'boot'
            if p=='/sys/kernel/security/apparmor/profiles':return '\n'.join(n+' (enforce)' for n in sorted(self.f.loaded))
            if p.endswith('/stat'):return p.split('/')[-2]+' (outer) '+' '.join(['S','1']+['0']*17+['44','0'])
            if p.endswith('/attr/current'):return self.f.extra_label if p.split('/')[-3]=='1000' else 'unconfined'
            if p.endswith('/maps'):return self.private_map or ''
            if p.endswith('/mountinfo'):return ''
            if '/fdinfo/' in p:return 'mnt_id: '+str(self.fd_mount_id)+'\n'
            raise AssertionError(p)
        def link(self,p):
            if p.endswith('/ns/pid'):return self.pid_namespace
            if p.endswith('/ns/mnt'):return self.mount_namespace
            if p.endswith('/cwd'):return self.thread_cwd if '/task/' in p else self.cwd
            if p.endswith('/root'):return self.thread_root if '/task/' in p else self.root
            raise AssertionError(p)
        def directory_mount_id(self,p):
            thread='/task/' in p
            if p.endswith('/cwd'):
                value=self.thread_cwd_mount_id if thread else self.cwd_mount_id
            elif p.endswith('/root'):
                value=self.thread_root_mount_id if thread else self.root_mount_id
            else:raise AssertionError(p)
            return (value,1,1)
        def map_mount_ids(self,p):
            value=self.thread_map_mount_id if '/task/' in p else self.map_mount_id
            return [('a-b',(value,1,1))]
        def links(self,p):
            if '/task/' in p and self.thread_private_fd:return [(7,self.thread_private_fd)]
            return [(3,self.private_fd)] if self.private_fd else []

class OuterTests(unittest.TestCase):
    def test_expiry_map_file_capability_is_outer_only(self):
        name='units/herdr-offline-expire-03414499dd0d1986.service'
        current=(O/name).read_bytes()
        self.assertEqual(current.count(b'CAP_CHECKPOINT_RESTORE'), 1)
        self.assertIn(b'CapabilityBoundingSet=CAP_SYS_PTRACE CAP_DAC_READ_SEARCH CAP_CHOWN CAP_MAC_ADMIN CAP_CHECKPOINT_RESTORE', current)
        for other in ('units/herdr-offline-03414499dd0d1986.service',
                      'units/herdr-offline-cleanup-03414499dd0d1986.service',
                      'units/herdr-offline-host-03414499dd0d1986.service',
                      'units/herdr-offline-operator-03414499dd0d1986.service',
                      'overlays/worker-profile.apparmor','overlays/host-profile.apparmor',
                      'overlays/observer-profile.apparmor','overlays/operator-profile.apparmor'):
            self.assertNotIn(b'CAP_CHECKPOINT_RESTORE', (O/other).read_bytes(), other)

    def test_actual_scanner_map_file_permission_race_and_foreign_holder(self):
        class Entries:
            def __init__(self,rows):self.rows=rows
            def __enter__(self):return iter(self.rows)
            def __exit__(self,*args):return False
        for state in ('missing_capability','permitted','foreign_mapping','malformed','racy'):
            with self.subTest(state=state),self.fixture() as f:
                self.native_scope(f)
                f.units={n:'inactive' for n in obs.OWN_UNITS}
                original=f.view.directory_mount_id
                calls=[]
                def mount_id(path,*,must_directory=True):
                    if '/map_files/' not in path:
                        return original(path)
                    calls.append(path)
                    self.assertFalse(must_directory)
                    if state=='missing_capability':raise PermissionError('map_files follow needs checkpoint restore')
                    if state=='foreign_mapping':return (52,9,80)
                    if state=='racy':return (1 if len(calls)%2 else 52,9,80)
                    return (1,9,80)
                f.view.directory_mount_id=mount_id
                f.view.map_mount_ids=types.MethodType(obs.LinuxView.map_mount_ids,f.view)
                def scan(path):
                    if str(path).endswith('/map_files'):
                        name='invalid' if state=='malformed' else 'a-b'
                        return Entries([types.SimpleNamespace(name=name,path=str(path)+'/'+name)])
                    return Entries([types.SimpleNamespace(name='caller-1.json')])
                with patch.object(obs.os,'scandir',side_effect=scan):
                    if state in ('malformed','racy'):
                        with self.assertRaises(case.Denied):f.lifecycle.observe(f.binding)
                    else:
                        result=f.lifecycle.observe(f.binding)
                        self.assertEqual(result['complete'],state!='missing_capability')
                        if state=='foreign_mapping':self.assertTrue(result['holders'])
                        if state=='permitted':self.assertEqual(result['holders'],[])
                if state!='malformed':self.assertTrue(calls)

    def test_cwd_mount_identity_uses_held_path_fd_and_closes_it(self):
        events=[]
        mode=stat.S_IFDIR|0o700
        info=types.SimpleNamespace(st_mode=mode,st_dev=9,st_ino=80,st_nlink=2)
        view=obs.LinuxView()
        with patch.object(obs.os,'open',side_effect=lambda path,flags:events.append(('open',path,flags)) or 37), \
             patch.object(obs.os,'fstat',side_effect=lambda fd:events.append(('fstat',fd)) or info), \
             patch.object(obs.os,'close',side_effect=lambda fd:events.append(('close',fd))), \
             patch.object(view,'text',side_effect=lambda path:events.append(('text',path)) or 'mnt_id: 51\n'):
            self.assertEqual(view.directory_mount_id('/proc/777/cwd'),(51,9,80))
        self.assertEqual(events[0][1],'/proc/777/cwd')
        self.assertTrue(events[0][2]&os.O_PATH)
        self.assertIn(('text','/proc/self/fdinfo/37'),events)
        self.assertEqual(events[-1],('close',37))

    def test_map_file_inventory_reads_held_target_mount_ids(self):
        view=obs.LinuxView();calls=[]
        class Entries:
            def __enter__(self):return iter([types.SimpleNamespace(name='a-b',path='/synthetic/map_files/a-b')])
            def __exit__(self,*args):return False
        with patch.object(obs.os,'scandir',return_value=Entries()), \
             patch.object(view,'directory_mount_id',side_effect=lambda path,**kw:calls.append((path,kw)) or (52,1,2)):
            self.assertEqual(view.map_mount_ids('/synthetic/map_files'),[('a-b',(52,1,2))])
        self.assertEqual(calls,[('/synthetic/map_files/a-b',{'must_directory':False})])

    def native_scope(self,f):
        identity={'task_id':'case-root'}
        context={'identity':identity}
        root='/run/herdr-offline-private-root-'+digest(canon(identity))[:16]
        runtime={'roster_sha256':'a'*64,'context_sha256':digest(canon(context)),
                 'unit':ROLE_UNITS['root'],'pid':777,'start_ticks':888,'namespace':'pid:[777]'}
        f.metadata['root']=context;f.metadata['root.runtime']=runtime
        f.mounts['root']={'role':'root','roster_sha256':runtime['roster_sha256'],
            'context_sha256':runtime['context_sha256'],'unit':runtime['unit'],
            'private_root':root,'mount_id':51,'mount_ids':[51,52],'mount_namespace':'mnt:[777]',
            'pid':777,'start_ticks':888,'pid_namespace':'pid:[777]'}
        return root
    @contextmanager
    def fixture(self):
        f=Fixture();stack=ExitStack()
        stack.enter_context(patch.object(outer,'Path',LogicalPath));stack.enter_context(patch.object(publisher,'Path',LogicalPath))
        stack.enter_context(patch.object(outer,'pinned_bytes',f.read_pinned));stack.enter_context(patch.object(case,'pinned_bytes',f.read_pinned))
        stack.enter_context(patch.object(root_effects,'pinned_bytes',f.read_pinned))
        stack.enter_context(patch.object(outer,'HOST_COMMAND_PINS',{p:digest(b) for p,b in f.command_bytes.items()}))
        stack.enter_context(patch.object(outer.os,'geteuid',lambda:0,create=True))
        stack.enter_context(patch.object(obs.os.path,'lexists',lambda p:False))
        @contextmanager
        def entries(p):yield iter([types.SimpleNamespace(name='caller-1.json')])
        stack.enter_context(patch.object(outer.os,'scandir',entries))
        import offline_case.custody as custody
        class Custody:
            def __init__(self,p):pass
            def __enter__(self):return self
            def __exit__(self,*args):pass
            def authority(self):return f.authority
            def consumed(self,challenge):
                a,b,s=outer.read_consumed(f.build,reader=f.read_pinned,read_boot=lambda:'boot');return b['challenge']==challenge
            def state(self):return f.state
            def _publish(self,name,value,exclusive=False):
                if name in f.journal:raise FileExistsError(name)
                f.journal[name]=value;f.events.append(('custody',name))
        stack.enter_context(patch.object(custody,'RootCustody',Custody))
        try:yield f
        finally:stack.close()
    def test_actual_consumed_approval_binding_rejects_foreign_marker_without_renewing_expired_time(self):
        f=Fixture();a,b,s=outer.read_consumed(f.build,reader=f.read_pinned,read_boot=lambda:'boot')
        self.assertEqual(a['deadline'],case.DEADLINE)
        f.binding['challenge']='9'*64
        with self.assertRaises(case.Denied):outer.read_consumed(f.build,reader=f.read_pinned,read_boot=lambda:'boot')
    def test_original_thread_and_stacked_profile_scan_finds_nonleader_holder(self):
        with self.fixture() as f:
            f.units={n:'inactive' for n in obs.OWN_UNITS};f.extra_label=case.PROFILE+'//&unpriv_bwrap (enforce)'
            result=f.lifecycle.observe(f.binding)
            self.assertTrue(result['complete']);self.assertEqual(result['holders'][0]['tid'],1000)
            self.assertTrue(obs.carries_profile(case.OPERATOR_PROFILE+'//hat (complain)'))
            self.assertFalse(obs.carries_profile('unrelated-'+case.PROFILE+' (enforce)'))
    def test_current_expiry_invokes_canonical_cleanup_then_original_publisher_after_real_lifetime_exit(self):
        with self.fixture() as f:
            result=f.lifecycle._expire()
            self.assertEqual(result,{'profiles_retired':5,'source_deleted':False});self.assertFalse(f.loaded)
            self.assertTrue(all(f.units[n]=='inactive' for n in obs.OWN_UNITS))
            self.assertEqual(f.events[0],('metadata','scope-fenced'))
            first_unload=next(i for i,e in enumerate(f.events) if e[0]=='/usr/sbin/apparmor_parser')
            self.assertLess(f.events.index(('custody','outer-policy-retirement-intent.json')),first_unload)
            self.assertIn(('/usr/bin/systemctl','start',case.CLEANUP),f.events)
            self.assertIn('outer-policy-retirement-complete.json',f.journal)
    def test_unknown_canonical_cleanup_still_stops_owned_roles_and_never_unloads(self):
        with self.fixture() as f:
            f.fail_cleanup=True
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertEqual(f.state['phase'],'RETAINED_UNKNOWN')
            self.assertTrue(all(f.units[n]=='inactive' for n in ROLE_UNITS.values()))
            self.assertFalse(any(e[0]=='/usr/sbin/apparmor_parser' for e in f.events));self.assertEqual(len(f.loaded),5)
    def test_late_stacked_holder_prevents_all_policy_mutation(self):
        with self.fixture() as f:
            f.extra_label=case.PREP+'//&other (enforce)'
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertFalse(any(e[0]=='/usr/sbin/apparmor_parser' for e in f.events))

    def test_late_private_fd_or_map_prevents_all_policy_mutation(self):
        for field in ('private_fd','private_map'):
            with self.subTest(field=field), self.fixture() as f:
                setattr(f.view,field,'/run/herdr-bootstrap/held-private-object')
                with self.assertRaises(case.Denied):f.lifecycle._expire()
                self.assertFalse(any(e[0]=='/usr/sbin/apparmor_parser' for e in f.events))

    def test_finalizer_own_custody_fd_does_not_block_private_holder_scan(self):
        with self.fixture() as f:
            f.view.private_fd='/var/lib/herdr-offline-03414499dd0d1986'
            result=f.lifecycle._expire()
            self.assertEqual(result['profiles_retired'],5)

    def test_nonleader_private_fd_prevents_policy_retirement(self):
        with self.fixture() as f:
            f.view.thread_private_fd='/run/herdr-policy/child-held'
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertFalse(any(e[0]=='/usr/sbin/apparmor_parser' for e in f.events))

    def test_recorded_private_mount_and_namespace_fd_retain_policy(self):
        for kind in ('path','mount_id','nested_mount_id','namespace_fd','namespace_process','pid_namespace_process','cwd','process_root','thread_cwd','thread_root','detached_cwd','detached_root','detached_thread_cwd','detached_thread_root','detached_nested_cwd','detached_nested_map','detached_thread_map'):
            with self.subTest(kind=kind),self.fixture() as f:
                root=self.native_scope(f)
                if kind=='path':f.view.private_fd=root+'/held'
                if kind=='mount_id':f.view.fd_mount_id=51;f.view.private_fd='/tmp/anonymous'
                if kind=='nested_mount_id':f.view.fd_mount_id=52;f.view.private_fd='/tmp/anonymous'
                if kind=='namespace_fd':f.view.private_fd='mnt:[777]'
                if kind=='namespace_process':f.view.mount_namespace='mnt:[777]'
                if kind=='pid_namespace_process':f.view.pid_namespace='pid:[777]'
                if kind=='cwd':f.view.cwd=root+'/current'
                if kind=='process_root':f.view.root=root
                if kind=='thread_cwd':f.view.thread_cwd=root+'/current'
                if kind=='thread_root':f.view.thread_root=root
                if kind=='detached_cwd':f.view.cwd_mount_id=51
                if kind=='detached_root':f.view.root_mount_id=51
                if kind=='detached_thread_cwd':f.view.thread_cwd_mount_id=51
                if kind=='detached_thread_root':f.view.thread_root_mount_id=51
                if kind=='detached_nested_cwd':f.view.cwd_mount_id=52
                if kind=='detached_nested_map':f.view.map_mount_id=52
                if kind=='detached_thread_map':f.view.thread_map_mount_id=52
                with self.assertRaises(case.Denied):f.lifecycle._expire()
                self.assertEqual(len(f.loaded),5)
                self.assertFalse(any(e[0]=='/usr/sbin/apparmor_parser' for e in f.events))

    def test_missing_or_torn_private_mount_receipt_is_unknown(self):
        with self.fixture() as f:
            self.native_scope(f);f.mounts.clear()
            with self.assertRaises((case.Denied,FileNotFoundError)):f.lifecycle._expire()
            self.assertEqual(len(f.loaded),5)
        with self.fixture() as f:
            self.native_scope(f);f.mounts['root']['mount_id']=None
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertEqual(len(f.loaded),5)
        with self.fixture() as f:
            self.native_scope(f);del f.metadata['root'];del f.metadata['root.runtime']
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertEqual(len(f.loaded),5)


    def test_wall_and_monotonic_expiry_arm_is_consumed_before_effect_and_never_resent(self):
        with self.fixture() as f, patch.object(outer.time,'time',lambda:case.DEADLINE-1500), patch.object(outer.time,'monotonic',lambda:100):
            f.state['phase']='CONSUMED'
            self.assertTrue(f.lifecycle.arm(f.binding,case.DEADLINE))
            command=next(e for e in f.events if e[0]=='/usr/bin/systemd-run')
            self.assertIn('--on-active=1500s',command)
            self.assertEqual(command[-3:],('/usr/bin/systemctl','start',outer.EXPIRY))
            self.assertLess(f.events.index(('metadata','expiry-intent')),f.events.index(command))
            with self.assertRaises(case.Denied):f.lifecycle.arm(f.binding,case.DEADLINE)
            self.assertEqual(sum(e[0]=='/usr/bin/systemd-run' for e in f.events),1)
            timer=(O/'units'/case.TIMER).read_text()
            self.assertIn('Unit='+outer.EXPIRY,timer)
    def test_original_thread_inventory_race_is_unknown_not_empty(self):
        with self.fixture() as f:
            f.units={n:'inactive' for n in obs.OWN_UNITS}
            original=f.view.directories;calls=[]
            def directories(path,numeric=False):
                if path.endswith('/task'):
                    calls.append(path);return ['999'] if len(calls)==1 else []
                return original(path,numeric)
            f.view.directories=directories
            with self.assertRaises(case.Denied):f.lifecycle.observe(f.binding)
    def test_os_command_mismatch_denies_before_expiry_fence_or_timer_effect(self):
        with self.fixture() as f:
            f.command_bytes['/usr/bin/systemctl']=b'changed immutable command'
            with self.assertRaises(case.Denied):f.lifecycle._expire()
            self.assertEqual(f.events,[])

if __name__=='__main__':unittest.main(verbosity=2)
