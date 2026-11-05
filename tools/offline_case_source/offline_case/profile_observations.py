"""Linux retirement observations for the future admitted host broker.

No observation runs at import. The broker must hold its admission/attachment
fence across this call and unload. Missing or racing data is UNKNOWN, not empty.
Filesystem access is injectable; unit tests use a temporary synthetic tree.
"""
import os
from pathlib import Path
import re
from .case import require as need, PROFILE, PREP, OBSERVER, HOST_PROFILE, OPERATOR_PROFILE
OWN_PROFILES = (PROFILE, PREP, OBSERVER, HOST_PROFILE, OPERATOR_PROFILE)
OWN_UNITS = (
    "herdr-offline-03414499dd0d1986.service",
    "herdr-offline-root-03414499dd0d1986.service",
    "herdr-offline-child-03414499dd0d1986.service",
    "herdr-offline-observer-03414499dd0d1986.service",
    "herdr-offline-host-03414499dd0d1986.service",
    "herdr-offline-operator-03414499dd0d1986.service",
    "herdr-offline-cleanup-03414499dd0d1986.service")
PRIVATE_MARKERS = (
    '/opt/agent-platform/herdr-offline-03414499dd0d1986',
    '/run/herdr-bootstrap', '/run/herdr-policy', '/run/herdr/policy-code')


class LinuxView:
    def directories(self, path, numeric=False):
        result = []
        for child in Path(path).iterdir():
            if numeric and not child.name.isdecimal(): continue
            need(not child.is_symlink(), 'unexpected observation symlink')
            if child.is_dir(): result.append(child.name)
        return sorted(result)

    def text(self, path):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            data = bytearray()
            while len(data) <= 16777216:
                part = os.read(fd,65536)
                if not part: break
                data.extend(part)
            need(len(data) <= 16777216, 'observation oversized')
            return bytes(data).decode('utf-8', errors='strict')
        finally: os.close(fd)

    def identity(self, path):
        info = Path(path).lstat()
        need(Path(path).is_dir() and not Path(path).is_symlink(), 'not a cgroup directory')
        return [info.st_dev, info.st_ino]

    def links(self, directory):
        """Read every descriptor target while its enumeration FD is live."""
        with os.scandir(directory) as entries:
            targets = []
            for entry in entries:
                need(len(targets) < 4096 and entry.name.isdecimal(), 'descriptor inventory unknown')
                target = os.readlink(entry.path)
                os.stat(entry.path)
                targets.append((int(entry.name), target))
        return sorted(targets)

    def link(self, path):
        return os.readlink(path)

    def directory_mount_id(self, path, *, must_directory=True):
        """Follow a proc magic link while holding its target O_PATH FD."""
        fd=os.open(path,os.O_PATH|os.O_CLOEXEC)
        try:
            before=os.fstat(fd)
            if must_directory:
                need((before.st_mode & 0o170000)==0o040000,'directory target unknown')
            info=self.text('/proc/self/fdinfo/'+str(fd))
            found=re.findall(r'(?m)^mnt_id:\s*([0-9]+)$',info)
            after=os.fstat(fd)
            stable=lambda item:(item.st_dev,item.st_ino,item.st_mode,item.st_nlink)
            need(len(found)==1 and stable(before)==stable(after) and int(found[0])>0,
                 'directory mount identity unknown')
            return (int(found[0]),before.st_dev,before.st_ino)
        finally:os.close(fd)

    def map_mount_ids(self, directory):
        """Enumerate every file-backed mapping through held map_files targets."""
        with os.scandir(directory) as entries:
            rows=[]
            for entry in entries:
                need(len(rows)<16384 and re.fullmatch(r'[0-9a-f]+-[0-9a-f]+',entry.name),
                     'map file inventory unknown')
                rows.append((entry.name,self.directory_mount_id(entry.path,must_directory=False)))
        names=[name for name,_ in rows]
        need(len(names)==len(set(names)),'map file inventory ambiguous')
        return sorted(rows)


def integers(text):
    values = text.split()
    need(all(re.fullmatch('[1-9][0-9]*', s) for s in values), 'unknown task list')
    return sorted(set(int(s) for s in values))


def task_identity(text):
    # comm may contain spaces and parentheses; starttime is field 22.
    tail = text.rsplit(')', 1)
    need(len(tail) == 2 and len(tail[1].split()) >= 20, 'unknown task stat')
    return (text.split(' ', 1)[0], tail[1].split()[19])


def carries_profile(label):
    label = label.strip()
    if label == 'unconfined': return False
    need(label.endswith(' (enforce)') or label.endswith(' (complain)'), 'unknown process label')
    body = label.rsplit(' (',1)[0]
    # Stacked labels use //&; hats/child profiles use //. An own child is a
    # holder too. Exact component comparison avoids substring false positives.
    return any(part == profile or part.startswith(profile+'//')
               for part in body.split('//&') for profile in OWN_PROFILES)


def retained_private_reference(scope, maps, mounts, fds, fdinfo, namespaces, directory_links, directory_ids, map_ids):
    """Match recorded native mount IDs, paths and namespace FD identities."""
    for row in scope:
        root=row['root']; mount_ids=row['mount_ids']
        identities=(row['mount_namespace'],row['pid_namespace'])
        if any(namespace in identities for namespace in namespaces) or any(identity in content for content in (maps,mounts)
                                          for identity in identities):
            return True
        if any(root in content for content in (maps,mounts)):
            return True
        if any(root in target for target in directory_links):
            return True
        if any(identity[0] in mount_ids for identity in directory_ids):
            return True
        if any(identity[0] in mount_ids for _,identity in map_ids):
            return True
        for number,target in fds:
            if root in target or target in identities:
                return True
            info=fdinfo[number]
            found=re.findall(r'(?m)^mnt_id:\s*([0-9]+)$',info)
            need(len(found)==1,'descriptor mount identity unknown')
            if int(found[0]) in mount_ids:return True
    return False


def observe_linux(binding, ownership, *, fenced, view=None, proc='/proc', cgroups='/sys/fs/cgroup',
                  profiles='/sys/kernel/security/apparmor/profiles', private_scope=()):
    """Ownership comes only from broker's durable unit-creation receipts.

    Each receipt binds exact unit, cgroup relative path and device/inode under
    this boot. PID reuse, vanished tasks, inaccessible labels, and nonempty
    nested cgroups cannot produce a successful absence report.
    """
    view = view or LinuxView()
    result = dict(binding=binding, fenced=fenced, groups={}, holders=None, complete=False, loaded=None)
    try:
        need(fenced is True and set(ownership) == set(OWN_UNITS), 'scope ownership incomplete')
        need(type(private_scope) in (tuple,list) and len(private_scope)<=2 and all(
             type(row) is dict and set(row)=={'root','mount_id','mount_ids','mount_namespace','pid_namespace'} and
             type(row['root']) is str and re.fullmatch(r'/run/herdr-offline-private-root-[0-9a-f]{16}',row['root']) and
             type(row['mount_id']) is int and row['mount_id']>0 and
             type(row['mount_ids']) is list and 0<len(row['mount_ids'])<=4096 and
             all(type(value) is int and value>0 for value in row['mount_ids']) and
             row['mount_ids']==sorted(set(row['mount_ids'])) and row['mount_id'] in row['mount_ids'] and
             type(row['mount_namespace']) is str and re.fullmatch(r'mnt:\[[1-9][0-9]*\]',row['mount_namespace']) and
             type(row['pid_namespace']) is str and re.fullmatch(r'pid:\[[1-9][0-9]*\]',row['pid_namespace'])
             for row in private_scope), 'native private scope unknown')
        need(view.text(proc+'/sys/kernel/random/boot_id').strip() == binding['boot_id'], 'boot changed')
        for unit in OWN_UNITS:
            record = ownership[unit]
            need(record['binding'] == binding and set(record) in
                 ({'binding','path','identity'}, {'binding','path','absent'}), 'foreign unit ownership')
            path = record['path']
            need(type(path) is str and path and not path.startswith('/')
                 and all(p not in ('','.','..') for p in path.split('/')), 'invalid cgroup path')
            absolute = cgroups+'/'+path
            if set(record) == {'binding','path','absent'}:
                need(record['absent'] is True and not os.path.lexists(absolute),
                     'absent unit cgroup appeared')
                result['groups'][unit] = dict(owned=True, populated=False, tasks=[])
                continue
            need(view.identity(absolute) == record['identity'], 'cgroup replaced')
            tasks = []
            populated = False
            def walk(directory):
                nonlocal populated
                events = dict(line.split() for line in view.text(directory+'/cgroup.events').splitlines())
                need(events.get('populated') in ('0','1'), 'cgroup population unknown')
                populated |= events['populated'] == '1'
                tasks.extend(integers(view.text(directory+'/cgroup.procs')))
                tasks.extend(integers(view.text(directory+'/cgroup.threads')))
                for name in view.directories(directory): walk(directory+'/'+name)
            walk(absolute)
            need(view.identity(absolute) == record['identity'], 'cgroup changed while observing')
            result['groups'][unit] = dict(owned=True, populated=populated, tasks=sorted(set(tasks)))
        holders = []
        processes = view.directories(proc, numeric=True)
        for pid in processes:
            taskdir = proc+'/'+pid+'/task'
            threads = view.directories(taskdir, numeric=True)
            need(threads and all(t.isdecimal() for t in threads), 'thread inventory unknown')
            before_pid = task_identity(view.text(proc+'/'+pid+'/stat'))
            maps = view.text(proc+'/'+pid+'/maps')
            mounts = view.text(proc+'/'+pid+'/mountinfo')
            fds = view.links(proc+'/'+pid+'/fd')
            fdinfo={number:view.text(proc+'/'+pid+'/fdinfo/'+str(number)) for number,_ in fds} if private_scope else {}
            namespaces=(view.link(proc+'/'+pid+'/ns/mnt'),view.link(proc+'/'+pid+'/ns/pid')) if private_scope else ()
            directories=(view.link(proc+'/'+pid+'/cwd'),view.link(proc+'/'+pid+'/root')) if private_scope else ()
            directory_ids=(view.directory_mount_id(proc+'/'+pid+'/cwd'),view.directory_mount_id(proc+'/'+pid+'/root')) if private_scope else ()
            map_ids=view.map_mount_ids(proc+'/'+pid+'/map_files') if private_scope else ()
            if any(marker in content for marker in PRIVATE_MARKERS
                   for content in (maps, mounts, *(target for _, target in fds))) or \
                    retained_private_reference(private_scope,maps,mounts,fds,fdinfo,namespaces,directories,directory_ids,map_ids):
                holders.append({'pid':int(pid),'kind':'private-fd-map-or-mount'})
            for tid in threads:
                path = taskdir+'/'+tid
                before = task_identity(view.text(path+'/stat'))
                label = view.text(path+'/attr/current')
                thread_maps = view.text(path+'/maps')
                thread_mounts = view.text(path+'/mountinfo')
                thread_fds = view.links(path+'/fd')
                thread_fdinfo={number:view.text(path+'/fdinfo/'+str(number)) for number,_ in thread_fds} if private_scope else {}
                thread_namespaces=(view.link(path+'/ns/mnt'),view.link(path+'/ns/pid')) if private_scope else ()
                thread_directories=(view.link(path+'/cwd'),view.link(path+'/root')) if private_scope else ()
                thread_directory_ids=(view.directory_mount_id(path+'/cwd'),view.directory_mount_id(path+'/root')) if private_scope else ()
                thread_map_ids=view.map_mount_ids(path+'/map_files') if private_scope else ()
                if any(marker in content for marker in PRIVATE_MARKERS
                       for content in (thread_maps, thread_mounts,
                                       *(target for _, target in thread_fds))) or \
                        retained_private_reference(private_scope,thread_maps,thread_mounts,thread_fds,thread_fdinfo,thread_namespaces,thread_directories,thread_directory_ids,thread_map_ids):
                    holders.append({'pid':int(pid),'tid':int(tid),'kind':'private-thread-fd-map-or-mount'})
                need(before == task_identity(view.text(path+'/stat')), 'task changed during observation')
                need(thread_maps == view.text(path+'/maps') and
                     thread_mounts == view.text(path+'/mountinfo') and
                     thread_fds == view.links(path+'/fd') and
                     (not private_scope or (thread_namespaces==(view.link(path+'/ns/mnt'),view.link(path+'/ns/pid')) and
                      thread_directories==(view.link(path+'/cwd'),view.link(path+'/root')) and
                      thread_directory_ids==(view.directory_mount_id(path+'/cwd'),view.directory_mount_id(path+'/root')) and
                      thread_map_ids==view.map_mount_ids(path+'/map_files') and
                      thread_fdinfo=={number:view.text(path+'/fdinfo/'+str(number)) for number,_ in thread_fds})),
                     'thread descriptor or mapping changed during observation')
                if carries_profile(label): holders.append({'pid':int(pid),'tid':int(tid),'label':label.strip()})
            need(before_pid == task_identity(view.text(proc+'/'+pid+'/stat')) and
                 maps == view.text(proc+'/'+pid+'/maps') and
                 mounts == view.text(proc+'/'+pid+'/mountinfo') and
                 fds == view.links(proc+'/'+pid+'/fd') and
                 (not private_scope or (namespaces==(view.link(proc+'/'+pid+'/ns/mnt'),view.link(proc+'/'+pid+'/ns/pid')) and
                  directories==(view.link(proc+'/'+pid+'/cwd'),view.link(proc+'/'+pid+'/root')) and
                  directory_ids==(view.directory_mount_id(proc+'/'+pid+'/cwd'),view.directory_mount_id(proc+'/'+pid+'/root')) and
                  map_ids==view.map_mount_ids(proc+'/'+pid+'/map_files') and
                  fdinfo=={number:view.text(proc+'/'+pid+'/fdinfo/'+str(number)) for number,_ in fds})),
                 'process descriptor or mapping changed during observation')
            need(threads == view.directories(taskdir, numeric=True), 'thread inventory changed')
        need(processes == view.directories(proc, numeric=True), 'process inventory changed')
        loaded = {profile: [] for profile in OWN_PROFILES}
        for line in view.text(profiles).splitlines():
            need(line.endswith(' (enforce)') or line.endswith(' (complain)'), 'profile inventory unknown')
            name = line.rsplit(' (',1)[0]
            for profile in OWN_PROFILES:
                if name == profile or name.startswith(profile+'//'): loaded[profile].append(line)
        need(all(len(rows) <= 1 for rows in loaded.values()), 'ambiguous profile inventory')
        result.update(holders=holders, loaded={key:bool(rows) for key,rows in loaded.items()}, complete=True)
    except (OSError, ValueError, UnicodeError) as error:
        # Keep result schema closed. Broker separately logs the detailed error.
        result.update(holders=None, loaded=None, complete=False)
    return result
