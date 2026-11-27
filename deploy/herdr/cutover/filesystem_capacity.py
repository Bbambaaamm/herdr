"""One phase-aware admission policy for cutover, including pre-verification I/O.

Mount IDs attest topology, not independent storage. Proven same-device/fsid
mounts share one capacity budget. Unknown quota/subvolume semantics fail closed.
No environment-selected temporary location or maintenance action is used here.
"""
from __future__ import annotations

import ctypes
import errno
import json
import os
from pathlib import Path
import re
import stat
import sys

from herdr.release import DEFAULT_ARCHIVE_LIMITS, ReleaseError

GIB = 1024**3
MIB = 1024**2
TEMP = Path('/tmp')
BACKUPS = Path('/home/agentops/backups/hermes')
OFFSITE = Path('/home/agentops/backups/hermes-offsite')
HOST = Path('/')
INODES = 32768
TEMP_MARGIN = 64*MIB
MEMORY_MARGIN = 128*MIB
MAX_BLOCK = 65536


class CapacityError(ReleaseError):
    def __init__(self, report):
        self.report = report
        super().__init__('transaction_capacity_insufficient:' +
                         json.dumps(report, sort_keys=True, separators=(',', ':')))


def require(ok, reason):
    if not ok:
        raise ReleaseError('transaction_capacity_' + reason)


def bounded(path, limit=2*MIB):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        chunks = bytearray()
        while len(chunks) <= limit:
            chunk = os.read(fd, min(65536, limit+1-len(chunks)))
            if not chunk:
                break
            chunks.extend(chunk)
        require(len(chunks) <= limit, 'observation_limit')
        return bytes(chunks)
    finally:
        os.close(fd)


def unescape(value):
    return re.sub(r'\\([0-7]{3})', lambda m: chr(int(m[1], 8)), value)


def mounts():
    rows = []
    for line in bounded('/proc/self/mountinfo').decode().splitlines():
        p = line.split(); i = p.index('-')
        require(len(rows) < 8192 and len(p) >= i+4, 'mountinfo_shape')
        rows.append(dict(id=int(p[0]), device=p[2], root=unescape(p[3]),
                         mount=unescape(p[4]), options=p[5], type=p[i+1],
                         source=unescape(p[i+2]), super_options=p[i+3]))
    require(bool(rows), 'mountinfo_empty')
    return rows


def directory(path):
    """Pin nearest existing ancestor without following substituted symlinks."""
    path = Path(path)
    require(path.is_absolute() and '..' not in path.parts, 'path')
    fd = os.open('/', os.O_RDONLY | os.O_DIRECTORY)
    existing = Path('/')
    try:
        for name in path.parts[1:]:
            try:
                nxt = os.open(name, os.O_RDONLY | os.O_DIRECTORY |
                              os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            except FileNotFoundError:
                break
            os.close(fd); fd = nxt; existing /= name
        return os.dup(fd), existing
    finally:
        os.close(fd)


class _Dqblk(ctypes.Structure):
    _fields_ = [(name, ctypes.c_uint64) for name in (
        'bhard', 'bsoft', 'space', 'ihard', 'isoft', 'inodes', 'btime', 'itime'
    )] + [('valid', ctypes.c_uint32)]


def _read_quota(fd, kind, identity):
    """Read one Linux if_dqblk from the already pinned filesystem."""
    require(sys.platform == 'linux' and os.uname().machine == 'x86_64',
            'quota_architecture_unsupported')
    require(sys.byteorder == 'little' and ctypes.sizeof(ctypes.c_void_p) == 8
            and ctypes.sizeof(ctypes.c_long) == 8 and ctypes.sizeof(ctypes.c_int) == 4
            and ctypes.sizeof(_Dqblk) == 72 and ctypes.alignment(_Dqblk) == 8
            and all(getattr(_Dqblk, name).offset == i * 8
                    for i, (name, _) in enumerate(_Dqblk._fields_)), 'quota_abi_unsupported')
    require(0 <= fd <= 0x7fffffff, 'quota_invalid_descriptor')
    require(kind in (0, 1) and 0 <= identity <= 0xffffffff, 'quota_invalid_argument')
    libc = ctypes.CDLL(None, use_errno=True)
    args = [ctypes.c_int(fd), ctypes.c_uint(0x80000700 | kind), ctypes.c_uint(identity)]
    value = _Dqblk()
    wrapper = getattr(libc, 'quotactl_fd', None)
    if wrapper is not None:
        wrapper.argtypes = [ctypes.c_int, ctypes.c_uint, ctypes.c_uint, ctypes.POINTER(_Dqblk)]
        wrapper.restype = ctypes.c_int
        result = wrapper(*args, ctypes.byref(value))
    else:
        syscall = getattr(libc, 'syscall', None)
        require(syscall is not None, 'quota_syscall_unavailable')
        syscall.argtypes = [ctypes.c_long]  # fixed argument of variadic libc syscall
        syscall.restype = ctypes.c_long
        # arch/x86/entry/syscalls/syscall_64.tbl, native LP64 (exclude x32).
        result = syscall(443, *args, ctypes.byref(value))
    if result != 0:
        error = ctypes.get_errno()
        reason = errno.errorcode.get(error, 'UNKNOWN')
        raise ReleaseError(f'quota_query_failed:{reason}:{error}')
    require(value.valid & 15 == 15, 'quota_fields_unverified')
    return value


def quota_headroom(fd, row, available, inodes):
    """Read-only Linux quota query; enabled but unreadable quotas are NO-GO.

    Bound both root-written installation data and agentops telemetry/backup
    writes. Group bounds are conservative; no quota capability is changed.
    """
    options = set((row['options']+','+row['super_options']).split(','))
    names = {option.partition('=')[0] for option in options}
    if names & {'prjquota', 'pquota', 'pqnoenforce'}:
        require(False, 'project_quota_unverified')
    user = {'usrquota', 'uquota', 'quota', 'usrjquota', 'uqnoenforce', 'qnoenforce'}
    group = {'grpquota', 'gquota', 'grpjquota', 'gqnoenforce'}
    markers = {name for name in names if 'quota' in name or 'qnoenforce' in name
               or name == 'jqfmt'}
    require(not (markers - user - group - {'noquota', 'jqfmt'}), 'quota_options_unverified')
    require('jqfmt' not in names or bool(names & {'usrjquota', 'grpjquota'}),
            'quota_options_unverified')
    kinds = []
    if names & user:
        kinds.append((0, (0, 1001)))
    if names & group:
        kinds.append((1, (0, 982, 1001)))
    if not kinds:
        return available, inodes, 'not_enabled'
    for kind, identities in kinds:
        for identity in identities:
            value = _read_quota(fd, kind, identity)
            for limit in (value.bhard, value.bsoft):
                if limit:
                    available = min(available, max(0, limit*1024-value.space))
            for limit in (value.ihard, value.isoft):
                if limit:
                    inodes = min(inodes, max(0, limit-value.inodes))
    return available, inodes, 'verified'


def observe(path, table):
    fd, existing = directory(path)
    try:
        before = os.fstat(fd); v = os.fstatvfs(fd)
        candidates = [m for m in table if existing == Path(m['mount']) or
                      Path(m['mount']) in existing.parents]
        require(bool(candidates), 'mount_missing')
        depth = max(len(Path(m['mount']).parts) for m in candidates)
        candidates = [m for m in candidates if len(Path(m['mount']).parts) == depth]
        require(len(candidates) == 1, 'overmounted_path_unverified')
        row = candidates[0]
        require('ro' not in row['options'].split(',') and not v.f_flag & os.ST_RDONLY,
                'read_only_filesystem')
        require(row['device'] == f'{os.major(before.st_dev)}:{os.minor(before.st_dev)}',
                'mount_device_changed')
        require(row['type'] in {'ext4', 'xfs', 'tmpfs'}, 'filesystem_unverified')
        require(0 < v.f_frsize <= MAX_BLOCK and v.f_fsid != 0
                and v.f_bavail >= 0 and v.f_favail >= 0 and v.f_blocks >= 0,
                'allocation_geometry')
        available, free_inodes, quota = quota_headroom(
            fd, row, v.f_bavail*v.f_frsize, v.f_favail)
        after = os.fstat(fd)
        require((before.st_dev, before.st_ino) == (after.st_dev, after.st_ino),
                'directory_changed')
        again, _ = directory(path)
        try:
            named = os.fstat(again)
            require((before.st_dev, before.st_ino) == (named.st_dev, named.st_ino),
                    'named_directory_changed')
        finally:
            os.close(again)
        return dict(path=str(path), existing=str(existing), mount_id=row['id'],
                    mountpoint=row['mount'], mount_root=row['root'],
                    device=before.st_dev, fsid=v.f_fsid, type=row['type'],
                    source=row['source'], options=row['options'],
                    super_options=row['super_options'], block_bytes=v.f_frsize,
                    total_bytes=v.f_blocks*v.f_frsize, available_bytes=available,
                    free_inodes=free_inodes, quota=quota)
    finally:
        os.close(fd)


def memory_headroom():
    """Available physical memory capped by every enclosing cgroup-v2 limit."""
    fields = bounded('/proc/meminfo', 65536).decode().splitlines()
    available = next(int(x.split()[1])*1024 for x in fields if x.startswith('MemAvailable:'))
    lines = bounded('/proc/self/cgroup', 65536).decode().splitlines()
    unified = [x[3:] for x in lines if x.startswith('0::')]
    require(len(unified) == 1 and '..' not in Path(unified[0]).parts,
            'memory_cgroup_unverified')
    # A cgroup namespace with a hidden ancestor cannot prove outer headroom.
    require(unified[0].startswith('/'), 'memory_cgroup_path')
    table = mounts()
    cg = [r for r in table if r['type'] == 'cgroup2' and r['root'] == '/']
    require(len(cg) == 1, 'memory_cgroup_mount_unverified')
    root = Path(cg[0]['mount'])
    current = root / unified[0].lstrip('/')
    limits = []
    while True:
        # The hierarchy root has no memory.max/current interface: its bound is
        # physical MemAvailable. Missing interfaces below it are unverified.
        if current == root:
            try:
                bounded(root/'memory.max',64)
            except FileNotFoundError:
                break
            # A mounted/namespace root exposing limits can hide tighter outer
            # ancestors. Do not declare that a complete hierarchy observation.
            require(False, 'memory_cgroup_root_namespace_unverified')
        maximum = bounded(current/'memory.max', 64).decode().strip()
        used = int(bounded(current/'memory.current', 64))
        if maximum != 'max':
            remaining = max(0, int(maximum)-used)
            available = min(available, remaining); limits.append(remaining)
        require(root in current.parents, 'memory_cgroup_escape')
        current = current.parent
    return dict(available_bytes=available, cgroup_headroom_bytes=limits)


def topology(rows):
    return [{k: r[k] for k in ('path','device','fsid','mount_id','mountpoint',
                              'mount_root','type','source','options','super_options')}
            for r in rows]


def backup_peak():
    candidates = []
    for p in BACKUPS.glob('hermes-backup-auto-*.zip'):
        require(len(candidates) < 4096, 'backup_inventory_limit')
        candidates.append(p)
    size = 512*MIB
    if candidates:
        newest = max(candidates, key=lambda p: p.lstat().st_mtime)
        s = newest.lstat()
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'backup_identity')
        size = max(size, s.st_size)
    return 3*size+GIB


def effective_previous(api):
    """Keep the same predecessor role before/after the legacy bootstrap link."""
    previous = api.get('CAPACITY_PREVIOUS')
    if previous is not None:
        return previous
    current = api.get('CURRENT')
    if current is not None and (current.exists() or current.is_symlink()):
        require(current.is_symlink(), 'current_not_symlink')
        return current.resolve(strict=True)
    return api.get('LEGACY')


def rollback_margin(api):
    """Retain the prior explicitly approved RC6-sized planning margin.

    The existing tree is already charged in statvfs. This is a named additional
    safety margin, never a claim that the tree must be copied or deleted.
    """
    previous = effective_previous(api)
    if previous is None:
        return 0
    require(previous == api.get('LEGACY') or previous.parent == api['RELEASES'],
            'rollback_path')
    total = previous.lstat().st_blocks*512
    count = 0
    for base, dirs, files in os.walk(previous, followlinks=False):
        for name in dirs+files:
            count += 1
            require(count <= 8194, 'rollback_inventory_limit')
            s = (Path(base)/name).lstat()
            require(stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode), 'rollback_object')
            total += s.st_blocks*512
    return total


def plan(api, archive, candidate_allocation, reserve, *, phase='transaction', expected=None):
    """Observe + admit, before each allocation. Existing bytes are not added again.

    phase=temporary admits the bounded extractor before any archive verification.
    The transaction model additionally retains the previously approved 2 archive /
    3 candidate conservative envelope; tmp verification copies are sequential.
    """
    info = archive.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
            and 0 < info.st_size <= 64*MIB, 'archive_size')
    require(type(candidate_allocation) is int and 0 <= candidate_allocation <= 320*MIB,
            'candidate_allocation')
    require(phase in {'temporary','transaction'}, 'phase')
    roles = {'temporary': TEMP}
    if phase == 'transaction':
        roles.update(host=HOST, state=api['STATE_DIR'], incoming=api['INCOMING_DIR'],
                     release=api['RELEASES'], backup=BACKUPS, offsite=OFFSITE)
        previous = effective_previous(api)
        if previous is not None:
            roles['rollback'] = previous
        for name in ('PUBLIC_STATE','BRIDGE','SNAPSHOT','NGINX_ROUTE','CONSUMER_DIR','UNIT_DIR'):
            if name in api:
                roles['runtime_'+name] = (api[name] if name.endswith('_DIR') else api[name].parent)
    table = mounts()
    rows = []
    for role, path in roles.items():
        try:
            rows.append(observe(path, table))
        except (OSError, ReleaseError, ValueError) as exc:
            raise CapacityError(dict(schema_version=2,status='rejected',phase=phase,
                filesystems=[dict(paths=[str(path)],roles=[role],status='FAIL',
                                  reasons=['filesystem_observation_unverified'],
                                  detail=str(exc))])) from exc
    require(mounts() == table, 'mount_topology_changed')
    identity = topology(rows)
    if expected is not None:
        require(identity == expected, 'mount_topology_drift')
    domains = {}; role_domain = {}
    for (role, path), row in zip(roles.items(), rows):
        key = (row['device'], row['fsid'])
        role_domain[role] = key
        if key not in domains:
            domains[key] = dict(identity=f'{key[0]}:{key[1]}', type=row['type'],
                paths=[], roles=[], mounts=[], total_bytes=row['total_bytes'],
                available_bytes=row['available_bytes'], free_inodes=row['free_inodes'],
                block_bytes=row['block_bytes'], allocations=[], reserves={})
        d = domains[key]
        require(d['type'] == row['type'] and d['block_bytes'] == row['block_bytes'],
                'capacity_domain_unverified')
        d['paths'].append(str(path)); d['roles'].append(role)
        d['mounts'].append(row['mount_id'])
        d['available_bytes'] = min(d['available_bytes'], row['available_bytes'])
        d['free_inodes'] = min(d['free_inodes'], row['free_inodes'])
    def allocation(role, name, size, count, phases):
        d = domains[role_domain[role]]; block = d['block_bytes']
        d['allocations'].append(dict(name=name, bytes=((size+block-1)//block)*block,
                                     inodes=count, phases=phases))
    limits = DEFAULT_ARCHIVE_LIMITS
    td = domains[role_domain['temporary']]
    # Extractor's created-object ceiling includes implicit parents (release.py).
    objects = limits.max_members+2
    temp_bytes = limits.max_total_bytes + objects*td['block_bytes']
    allocation('temporary','bounded_extraction',temp_bytes,objects,['verification'])
    td['reserves']['temporary_margin'] = TEMP_MARGIN
    peak = backup_peak() if phase == 'transaction' else 0
    existing = []
    if phase == 'transaction':
        pinned = api.get('CAPACITY_PINNED') is True
        allocation('incoming','pinned_archive',0 if pinned else info.st_size,0 if pinned else 1,
                   ['preparation','activation','rollback'])
        allocation('state','retained_archive',info.st_size,1,['activation','rollback'])
        release_block = domains[role_domain['release']]['block_bytes']
        # preflight's allocation metric is a 4-KiB envelope. Destination blocks
        # may be larger; bound every object rather than rounding the total once.
        destination_allocation = candidate_allocation + max(0,release_block-4096)*objects
        candidate_needed = True
        release = api.get('CAPACITY_RELEASE')
        if release:
            target = api['RELEASES']/(release['tag']+'-'+release['commit'][:12])
            require(target.parent == api['RELEASES'], 'candidate_path')
            if target.exists() or target.is_symlink():
                s = target.lstat()
                require(stat.S_ISDIR(s.st_mode) and s.st_uid == 0
                        and not s.st_mode & 0o022, 'existing_candidate_authority')
                require(api['verify_tree'](target) == release, 'existing_candidate_identity')
                candidate_needed = False
                existing.append(dict(path=str(target),accounting='already_in_measured_usage',
                                     identity='verified_existing_candidate'))
        allocation('release','candidate_installation',destination_allocation if candidate_needed else 0,
                   objects if candidate_needed else 0,
                   ['preparation','activation','rollback'])
        domains[role_domain['release']]['reserves']['approved_candidate_safety'] = 2*destination_allocation
        state_block = domains[role_domain['state']]['block_bytes']
        transaction_allocation = reserve + max(0,state_block-4096)*64
        allocation('state','transaction_documents_atomic_evidence',transaction_allocation,64,
                   ['preparation','activation','rollback'])
        # Preserve the complete #126 admission policy on the host root. If
        # backup paths are separate they ALSO need their own physical peak.
        host = domains[role_domain['host']]
        host['reserves']['host_policy'] = max(12*GIB,10*GIB+128*MIB+peak)
        margin = rollback_margin(api)
        if margin:
            # Policy conservatism applies on the existing rollback tree domain.
            # Normal deployment has RELEASES and previous on the same domain;
            # legacy layouts are separately validated before use.
            domains[role_domain['rollback']]['reserves']['approved_rollback_safety'] = margin
        for role in ('backup','offsite'):
            d = domains[role_domain[role]]
            if d is not host:
                # Full peak on each separated backup domain is conservative;
                # dedup if both backup paths share a domain.
                d['reserves']['backup_peak_and_safety'] = peak
        for role in roles:
            if role.startswith('runtime_'):
                d = domains[role_domain[role]]
                if role_domain[role] != role_domain['state']:
                    d['reserves']['runtime_atomic_restore'] = reserve + max(0,d['block_bytes']-4096)*64
    report = dict(schema_version=2, status='verified', phase=phase,
                  transaction_reserve_bytes=reserve, backup_preparation_peak_bytes=peak,
                  topology=identity, filesystems=list(domains.values()))
    report['existing_artifacts'] = [*existing,dict(path=str(archive),bytes=info.st_size,
        allocation_bytes=info.st_blocks*512,accounting='already_in_measured_usage')]
    tmpfs_domains = [d for d in domains.values() if d['type'] == 'tmpfs']
    # All tmpfs mounts consume a common physical/cgroup memory budget. Count
    # simultaneous pages across domains, including offsite/backup preparation,
    # but not the host's unspent disk floor or an already-existing rollback tree.
    tmpfs_future = max((sum(a['bytes'] for d in tmpfs_domains for a in d['allocations']
                           if p in a['phases']) for p in
                       ('verification','preparation','activation','rollback')),default=0)
    tmpfs_future += sum(value for d in tmpfs_domains for name,value in d['reserves'].items()
                        if name not in {'host_policy','approved_rollback_safety'})
    memory_required = tmpfs_future+64*MIB+64*MIB+4*reserve+MEMORY_MARGIN
    failed = False
    for d in domains.values():
        # Max across phases, sum only simultaneous allocations in each phase.
        phases = ('verification','preparation','activation','rollback')
        totals = {p:sum(a['bytes'] for a in d['allocations'] if p in a['phases']) for p in phases}
        inode_totals = {p:sum(a['inodes'] for a in d['allocations'] if p in a['phases']) for p in phases}
        d['phase_allocations'] = totals
        d['maximum_concurrent_bytes'] = max(totals.values())
        d['required_bytes'] = d['maximum_concurrent_bytes']+sum(d['reserves'].values())
        d['required_inodes'] = max(INODES,max(inode_totals.values())+64)
        d['headroom_bytes'] = d['available_bytes']-d['required_bytes']
        d['missing_bytes'] = max(0,-d['headroom_bytes'])
        d['physically_possible'] = d['total_bytes'] >= d['required_bytes']
        reasons = []
        if d['missing_bytes']: reasons.append('available_bytes')
        if d['free_inodes'] < d['required_inodes']: reasons.append('free_inodes')
        if d['type'] == 'tmpfs':
            # tmpfs future pages + max verifier read/file + bounded archive
            # parser/inventory + aggregate/base64/json working copies + guard.
            try:
                memory = memory_headroom()
                d['memory'] = dict(**memory,required_bytes=memory_required)
                if memory['available_bytes'] < memory_required: reasons.append('memory_headroom')
            except (OSError, ReleaseError, ValueError, StopIteration) as exc:
                d['memory'] = dict(status='unverified',detail=str(exc),required_bytes=memory_required)
                reasons.append('memory_observation_unverified')
        d['status'] = 'FAIL' if reasons else 'PASS'; d['reasons'] = reasons
        failed |= bool(reasons)
    # Scalar retained for compatibility ONLY: never an admission proof. See v2 domains.
    report['required_bytes'] = max(d['required_bytes'] for d in domains.values())
    report['observations'] = [dict(available_bytes=d['available_bytes'],free_inodes=d['free_inodes'],
                                    required_bytes=d['required_bytes'],identity=d['identity'])
                              for d in domains.values()]
    if failed:
        report['status'] = 'rejected'
        raise CapacityError(report)
    return report
