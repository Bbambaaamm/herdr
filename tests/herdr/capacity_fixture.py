"""Safe OS adapters with distinct disk/tmpfs observations; no planner stubs."""
from pathlib import Path
from deploy.herdr.cutover import filesystem_capacity as f


def install(monkeypatch, root, *, observer=None):
    temporary = root/'capacity-tmp'
    temporary.mkdir(exist_ok=True)
    backups = root/'capacity-backups'; backups.mkdir(exist_ok=True)
    offsite = root/'capacity-offsite'; offsite.mkdir(exist_ok=True)
    monkeypatch.setattr(f, 'TEMP', temporary)
    monkeypatch.setattr(f, 'BACKUPS', backups)
    monkeypatch.setattr(f, 'OFFSITE', offsite)
    monkeypatch.setattr(f, 'mounts', lambda: [{'fixture':'staging disk2049/tmpfs42'}])
    def observe(path, table):
        temp = Path(path) == temporary
        # Preserve tests that lower statvfs capacity at the OS boundary.
        space = f.os.statvfs(path if Path(path).exists() else root)
        available = min(space.f_bavail*space.f_frsize, 2932469760) if temp else space.f_bavail*space.f_frsize
        return dict(path=str(path),existing=str(path),mount_id=42 if temp else 1,
            mountpoint=str(temporary) if temp else '/',mount_root='/',
            device=42 if temp else 2049,fsid=42 if temp else 2049,
            type='tmpfs' if temp else 'ext4',source='tmpfs' if temp else '/dev/sda1',
            options='rw',super_options='rw',block_bytes=4096,
            total_bytes=4061155328 if temp else 80*1024**3,
            available_bytes=available,free_inodes=space.f_favail,quota='verified')
    monkeypatch.setattr(f,'observe',observer or observe)
    monkeypatch.setattr(f,'memory_headroom',lambda:dict(available_bytes=4*1024**3,cgroup_headroom_bytes=[]))

