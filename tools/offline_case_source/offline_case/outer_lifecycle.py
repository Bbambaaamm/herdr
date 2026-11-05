"""Current034 outer ROOT expiry adapter over original custody and Linux effects.

No authority issuer, daemon, SDK, provider or execution admission is introduced.
The original OS root deployment actor runs this finite expiry entry in its own
unconfined domain, after consuming the same source-bound case approval.
"""
from pathlib import Path
import os
import stat
import re
import time
import fcntl
from contextlib import contextmanager

from .case import (NONCE, CASE, OPERATOR, CLEANUP, TIMER, PROFILE, PREP, OBSERVER,
    HOST_PROFILE, OPERATOR_PROFILE, INSTALL_ROOT, Denied, require, canonical, parse, pinned_bytes, sha)
from .admission import HOST_UNIT
from .root_effects import CONTEXT, RootEffectPump, ROLE_UNITS
from .profile_observations import OWN_UNITS, OWN_PROFILES, LinuxView, observe_linux

ROOT = Path('/var/lib/herdr-offline-03414499dd0d1986')
BASE = Path(INSTALL_ROOT)
EXPIRY = 'herdr-offline-expire-03414499dd0d1986.service'
MONO = 'herdr-offline-expiry-monotonic-03414499dd0d1986'
COMMAND = ('/usr/bin/python3.14', '-I', '-B', '-c',
    'import sys; sys.path.insert(0,"/opt/agent-platform/herdr-offline-03414499dd0d1986"); from offline_case.outer_lifecycle import main; main()')


HOST_COMMAND_PINS = {"/usr/bin/systemctl":"6394f5e8df92878184de9d4dfb7ac242471cb09daf89d23be4e81ae17e9c03b2","/usr/bin/systemd-run":"03a68bafb0ebc0f5eff41cbdf3cbbdf126a3bb87e21140f9147bf78edce36d88","/usr/sbin/apparmor_parser":"11e9595527b8bb5b775709e4626ec69dc682585760ec7c6d0b045e759f1c0df2","/usr/bin/python3.14":"52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41"}


def verify_host_commands():
    for name, digest in HOST_COMMAND_PINS.items():
        info=Path(name).lstat()
        require(stat.S_ISREG(info.st_mode) and info.st_uid==info.st_gid==0 and
                stat.S_IMODE(info.st_mode)==0o755 and info.st_nlink==1 and
                sha(pinned_bytes(Path(name),root_owned=True))==digest,
                "immutable original OS command changed")


def read_consumed(build, *, reader=None, read_boot=None):
    """Same immutable original approval/nonce marker; expiration is NOT renewal."""
    reader = reader or pinned_bytes
    authority = parse(reader(ROOT/'authority.json', root_owned=True))
    used = parse(reader(ROOT/('used-'+NONCE+'.json'), root_owned=True))
    state = parse(reader(ROOT/'state.json', root_owned=True))
    boot = read_boot() if read_boot is not None else Path('/proc/sys/kernel/random/boot_id').read_text().strip()
    require(authority.get('schema') == 2 and authority.get('purpose') == 'SINGLE_OFFLINE_PHYSICAL_CASE' and
        authority.get('nonce') == NONCE and authority.get('build_sha256') == sha(canonical(build)) and
        type(used) is dict and set(used) == {'nonce','challenge','boot_id','authority_sha256','build_sha256'} and
        used['nonce'] == NONCE and used['challenge'] == authority['challenge'] and
        used['authority_sha256'] == sha(canonical(authority)) and used['build_sha256'] == sha(canonical(build)) and
        used['boot_id'] == authority['boot_id'] == boot and state.get('binding') == used,
        'foreign/missing consumed original case approval')
    require(type(authority.get('deadline')) is int and type(authority.get('not_before')) is int and
        0 < authority['deadline']-authority['not_before'] <= 1800, 'finite original case expiry required')
    from .case import validate_retirement_authority
    validate_retirement_authority(authority, build, boot=boot)
    return authority, used, state


@contextmanager
def expiry_guard():
    """Separate nonblocking expiry lock; never waits for supervisor custody."""
    directory=os.open(ROOT,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        info=os.fstat(directory)
        require(info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o700,'original root custody directory changed')
        fd=os.open('expiry.lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=directory)
        try:
            info=os.fstat(fd)
            require(stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_nlink==1 and
                    stat.S_IMODE(info.st_mode)==0o600,'expiry lock metadata changed')
            fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
            yield
        finally:os.close(fd)
    finally:os.close(directory)


def unit(io, name):
    require(name in {*OWN_UNITS, TIMER, EXPIRY, MONO+'.timer', MONO+'.service'}, 'foreign outer unit')
    raw = io.run('/usr/bin/systemctl','show',name,
        '--property=ActiveState,ControlGroup,MainPID,InvocationID,FragmentPath,LoadState','--no-pager',timeout=10)
    rows = raw.splitlines()
    require(len(rows) <= 16 and all('=' in row for row in rows), 'outer unit observation unavailable')
    result = dict(row.split('=',1) for row in rows)
    required={'ActiveState','LoadState'}
    if name.endswith('.service'):required |= {'ControlGroup','MainPID','InvocationID','FragmentPath'}
    require(len(result) == len(rows) and required <= set(result),
        'incomplete outer unit observation')
    return result


class OuterLifecycle:
    def __init__(self, build, io=None):
        from .native import LinuxEffects
        self.build, self.io = build, io or LinuxEffects()
        self.pump = RootEffectPump(build, None, self.io)

    def consumed(self):
        return read_consumed(self.build, read_boot=lambda:self.io.read(Path('/proc/sys/kernel/random/boot_id'),128).decode().strip())

    def arm(self, binding, deadline):
        verify_host_commands()
        authority, used, state = self.consumed()
        require(os.geteuid() == 0 and used == binding and authority['deadline'] == deadline and
                state['phase'] in {'CONSUMED','ARMED'}, 'foreign outer expiry arm')
        remaining = deadline-int(time.time())
        require(0 < remaining <= 1800 and unit(self.io,TIMER)['ActiveState'] == 'active',
                'original absolute wall expiry must preexist')
        record = {'binding':binding,'deadline':deadline,'remaining_seconds':remaining,
                  'monotonic_not_after':time.monotonic()+remaining,'unit':MONO}
        # Existing root metadata O_EXCL + fsync occurs before systemd timer IO.
        require(self.pump._read('expiry-intent') is None, 'expiry arm was already attempted; no resend')
        self.pump._metadata('expiry-intent',binding,record)
        self.io.run('/usr/bin/systemd-run','--unit='+MONO,'--on-active='+str(remaining)+'s',
            '--timer-property=AccuracySec=1s','--property=RuntimeMaxSec=120',
            '--property=Restart=on-failure','--property=RestartSec=5s',
            '--property=CapabilityBoundingSet=','--property=NoNewPrivileges=yes',
            '--property=RestrictNamespaces=yes','--property=RestrictAddressFamilies=AF_UNIX',
            '/usr/bin/systemctl','start',EXPIRY,timeout=15)
        require(unit(self.io,MONO+'.timer')['ActiveState'] == 'active', 'independent monotonic expiry uncertain')
        self.pump._metadata('expiry-armed',binding,record)
        return True

    def _stop_control(self, name, binding):
        props = unit(self.io,name)
        if props['ActiveState'] == 'inactive': return
        require(props['ActiveState'] in {'active','activating'} and props['MainPID'].isdecimal(), 'owned control state unknown')
        pid = int(props['MainPID']);require(pid>1,'control PID unknown')
        fragment = Path(props['FragmentPath'])
        require(fragment.is_absolute() and sha(pinned_bytes(fragment,root_owned=True)) == self.build['files']['units/'+name],
                'owned control source changed')
        if name == OPERATOR:
            matches=[]
            with os.scandir(CONTEXT) as entries:
                for entry in entries:
                    if entry.name.startswith('caller-') and entry.name.endswith('.json'):
                        row=parse(pinned_bytes(CONTEXT/entry.name,root_owned=True),4096)
                        if row['pid']==pid and row['cgroup']=='0::/system.slice/'+OPERATOR:matches.append(row)
            require(len(matches)==1 and matches[0]['boot_id']==binding['boot_id'] and
                    matches[0]['build_sha256']==binding['build_sha256'] and
                    self.io.process_start_ticks(pid)==matches[0]['start_ticks'], 'original root driver lifetime unproved')
        elif name == HOST_UNIT:
            roster=parse(pinned_bytes(Path('/etc/herdr/offline-03414499dd0d1986/roster.json'),root_owned=True),262144)
            c=roster['controller']
            require(roster['case_binding']==binding and c['pid']==pid and
                    self.io.process_start_ticks(pid)==c['start_ticks'] and c['profile']==HOST_PROFILE,
                    'original UID1001 controller lifetime unproved')
        else:raise Denied('unknown control stop')
        group=Path('/sys/fs/cgroup/system.slice')/name
        identity=self.io.identity(group)
        require(unit(self.io,name)==props,'owned control invocation changed before stop')
        self.io.stop_cgroup(group,identity)
        self.io.run('/usr/bin/systemctl','stop',name,timeout=30)
        require(unit(self.io,name)['ActiveState']=='inactive','owned control stop unknown')

    def ownership(self, binding):
        """Original root receipts plus stable inactive unit/cgroup observations."""
        receipts={}
        for name in OWN_UNITS:
            props=unit(self.io,name)
            require(props['ActiveState']=='inactive','all owned service lifetimes must end before unload')
            if props['LoadState'] != 'not-found':
                fragment=Path(props['FragmentPath'])
                expected=(self.build['files'].get('units/'+name))
                if expected is None:
                    # Role/observer source units were written O_EXCL from the
                    # actual ROOT roster. The root-owned control receipt pins it.
                    kind=('observer-control-unit' if 'observer-' in name else
                          ('root-unit' if name==ROLE_UNITS['root'] else 'child-unit'))
                    record=self.pump._read(kind)
                    require(record is not None and record['binding']==binding,'dynamic source receipt missing')
                    expected=record['value']['source_sha256']
                require(fragment.is_absolute() and sha(pinned_bytes(fragment,root_owned=True))==expected,
                        'inactive owned unit source changed')
            relative='system.slice/'+name;absolute='/sys/fs/cgroup/'+relative
            if not self.io.exists(Path(absolute)):
                receipts[name]={'binding':binding,'path':relative,'absent':True}
            else:
                # Once inactive, no thread can remain or migrate through this
                # cgroup. The original complete recursive observer rechecks its
                # stable device/inode before and after the entire empty walk.
                receipts[name]={'binding':binding,'path':relative,'identity':list(self.io.identity(Path(absolute)))}
        return receipts

    def observe(self, binding):
        scope=[]
        for role in ('root','child'):
            context=self.pump._read(role)
            runtime=self.pump._read(role+'.runtime')
            require((context is None)==(runtime is None),
                    'partial native lifetime cannot retire policy')
            if context is None:
                try:
                    pinned_bytes(CONTEXT/(role+'.mount.json'),root_owned=True)
                except FileNotFoundError:
                    continue
                raise Denied('orphaned native mount identity cannot retire policy')
            mount=parse(pinned_bytes(CONTEXT/(role+'.mount.json'),root_owned=True),65536)
            root='/run/herdr-offline-private-root-'+sha(canonical(context['identity']))[:16]
            require(type(mount) is dict and set(mount)=={'role','roster_sha256','context_sha256','unit',
                'private_root','mount_id','mount_ids','mount_namespace','pid','start_ticks','pid_namespace'} and
                mount['role']==role and mount['roster_sha256']==runtime['roster_sha256'] and
                mount['context_sha256']==runtime['context_sha256']==sha(canonical(context)) and
                mount['unit']==runtime['unit'] and mount['private_root']==root and
                type(mount['mount_id']) is int and mount['mount_id']>0 and
                type(mount['mount_ids']) is list and 0<len(mount['mount_ids'])<=4096 and
                all(type(item) is int and item>0 for item in mount['mount_ids']) and
                mount['mount_ids']==sorted(set(mount['mount_ids'])) and
                mount['mount_id'] in mount['mount_ids'] and
                mount['pid']==runtime['pid'] and mount['start_ticks']==runtime['start_ticks'] and
                mount['pid_namespace']==runtime['namespace'] and
                type(mount['mount_namespace']) is str and
                re.fullmatch(r'mnt:\[[1-9][0-9]*\]',mount['mount_namespace']),
                'recorded private mount identity changed')
            scope.append({'root':root,'mount_id':mount['mount_id'],'mount_ids':mount['mount_ids'],
                          'mount_namespace':mount['mount_namespace'],
                          'pid_namespace':mount['pid_namespace']})
        return observe_linux(binding,self.ownership(binding),fenced=True,
                             view=getattr(self.io,'view',None),private_scope=scope)

    def expire(self):
        with expiry_guard():
            return self._expire()

    def _expire(self):
        verify_host_commands()
        authority,binding,state=self.consumed()
        require(os.geteuid()==0 and self.io.read(Path('/proc/self/attr/current'),256).strip()==b'unconfined',
                'existing outer OS root actor required')
        # Irreversible deny-only root fence uses a separate custody path. It
        # does not wait for the running driver's supervisor/attempt lock.
        self.pump._metadata('scope-fenced',binding,{'binding':binding,'deadline':authority['deadline']})
        if state['phase']!='RETIRED':
            try:self._stop_control(OPERATOR,binding)
            except (OSError,Denied):pass
            try:self.io.run('/usr/bin/systemctl','start',CLEANUP,timeout=120)
            except (OSError,Denied):pass
            # A failed canonical host fence still cannot keep owned SDK workers
            # alive. No ownership or admission is released on this path.
            try:self.pump.stop_roles(binding)
            except (OSError,Denied):pass
            try:self._stop_control(HOST_UNIT,binding)
            except (OSError,Denied):pass
            authority,binding,state=self.consumed()
        require(state['phase']=='RETIRED','canonical cleanup is UNKNOWN; retain all policy')
        first=self.observe(binding);second=self.observe(binding)
        require(first==second and first['complete'] is True and first['holders']==[] and
                all(row=={'owned':True,'populated':False,'tasks':[]} for row in first['groups'].values()),
                'outer thread/stack holders or scope unknown')
        from .publisher import finalize_owned_policy
        result=finalize_owned_policy(self.build,authority,self.io)
        # Timer removal follows actual absence of all five profiles, never the
        # early per-launch RETIRED state. Original attempt is never reset.
        self.io.run('/usr/bin/systemctl','stop',TIMER,MONO+'.timer',timeout=15)
        return result


def main():
    from .case import validate_build
    build=parse(pinned_bytes(BASE/'integration-manifest.json',root_owned=True),262144)
    validate_build(build,BASE,baseline=BASE/'accepted-source',root_owned=True,installed=True)
    import sys
    sys.path[:0]=[str(BASE/'composed-core'),str(BASE/'composed-core/agent-stack/bin')]
    return OuterLifecycle(build).expire()
