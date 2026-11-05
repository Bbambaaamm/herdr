"""Host-pinned finite write mounts for one admitted child ownership contract."""
from __future__ import annotations
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from .child_ownership import ChildOwnership, OwnershipError, require

def _mount_id(fd):
    """Read the held FD's kernel mount identity, including same-device binds."""
    descriptor=os.open(f"/proc/self/fdinfo/{fd}",os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC)
    try:
        raw=os.read(descriptor,4097)
    finally:os.close(descriptor)
    require(len(raw)<=4096,"owned_mount_info_bound")
    values=[line.partition(b":")[2].strip() for line in raw.splitlines()
            if line.startswith(b"mnt_id:")]
    require(len(values)==1 and 1<=len(values[0])<=20 and values[0].isdigit(),
            "owned_mount_identity_unavailable")
    result=int(values[0])
    require(0<result<2**64,"owned_mount_identity_unavailable")
    return result

def _require_owned_name(name):
    require(name not in {".git",".herdr"} and not name.startswith(".herdr-"),
            "owned_control_path_denied")

@dataclass(frozen=True)
class WriteMount:
    key: str
    kind: str
    target: str
    fd: int
    device: int
    inode: int
    created: bool

class OwnedWritePins:
    MAX_DESCRIPTORS = 512
    def __init__(self, ownership, worktree, *, create_files=False):
        require(isinstance(ownership,ChildOwnership),"typed_child_ownership")
        require(type(create_files) is bool,"owned_write_creation_policy")
        worktree.verify()
        root=os.fstat(worktree.fd)
        require(stat.S_ISDIR(root.st_mode) and (root.st_dev,root.st_ino)==
                (worktree.device,worktree.inode),"owned_worktree_binding")
        self.worktree=worktree
        self._root_mount_id=_mount_id(worktree.fd)
        self.ownership_sha256=ownership.hash
        self._opened={}
        self._chains={}
        self._closed=False
        self.mounts=()
        mounts=[]
        try:
            for scope in ownership.write_scope:
                if scope.kind=="resource":continue
                parts=scope.key.split("/")
                require(len(parts)<=16 and not any(x in {".git",".herdr"} or
                        x.startswith(".herdr-") for x in parts),"owned_control_path_denied")
                parent=worktree.fd
                chain=[]
                for index,part in enumerate(parts):
                    key="/".join(parts[:index+1])
                    kind=scope.kind if index==len(parts)-1 else "directory"
                    created=False
                    if key in self._opened:
                        fd=self._opened[key]
                    else:
                        require(len(self._opened)<self.MAX_DESCRIPTORS,"owned_descriptor_bound")
                        flags=os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC
                        if kind=="directory":flags|=os.O_DIRECTORY
                        try:fd=os.open(part,flags,dir_fd=parent)
                        except FileNotFoundError:
                            require(kind=="file" and index==len(parts)-1 and create_files,
                                    "owned_target_missing")
                            fd=os.open(part,os.O_RDWR|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,
                                       0o600,dir_fd=parent)
                            os.fsync(fd)
                            directory_fd=os.open(".",os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC,dir_fd=parent)
                            try:os.fsync(directory_fd)
                            finally:os.close(directory_fd)
                            created=True
                        self._opened[key]=fd
                    info=os.fstat(fd)
                    self._require_same_mount(fd,info)
                    require(info.st_uid==os.geteuid() and not info.st_mode&0o022,
                            "owned_target_untrusted")
                    require((kind=="directory" and stat.S_ISDIR(info.st_mode)) or
                            (kind=="file" and stat.S_ISREG(info.st_mode) and info.st_nlink==1),
                            "owned_target_kind")
                    chain.append((key,fd,info.st_dev,info.st_ino,kind))
                    parent=fd
                final=chain[-1]
                mount=WriteMount(scope.key,scope.kind,str(worktree.logical/scope.key),
                                 final[1],final[2],final[3],created)
                # A declared directory already includes declared descendants.
                if not any(old.kind=="directory" and
                           (scope.key==old.key or scope.key.startswith(old.key+"/")) for old in mounts):
                    mounts=[old for old in mounts if not (scope.kind=="directory" and old.key.startswith(scope.key+"/"))]
                    mounts.append(mount)
                self._chains[scope.key]=tuple(chain)
            self.mounts=tuple(mounts)
            self.verify()
        except BaseException:
            self.close()
            raise

    @property
    def roots(self):
        return tuple(item.target for item in self.mounts)

    def _require_same_mount(self,fd,info):
        require(info.st_dev==self.worktree.device and _mount_id(fd)==self._root_mount_id,
                "owned_mount_crossing_denied")

    def verify(self):
        require(not self._closed,"owned_write_pins_closed")
        self.worktree.verify()
        for chain in self._chains.values():
            parent=self.worktree.fd
            for key,fd,device,inode,kind in chain:
                flags=os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC
                if kind=="directory":flags|=os.O_DIRECTORY
                fresh=os.open(key.rsplit("/",1)[-1],flags,dir_fd=parent)
                try:
                    named=os.fstat(fresh)
                    self._require_same_mount(fresh,named)
                finally:os.close(fresh)
                held=os.fstat(fd)
                self._require_same_mount(fd,held)
                require((named.st_dev,named.st_ino)==(held.st_dev,held.st_ino)==(device,inode)
                        and held.st_uid==os.geteuid() and not held.st_mode&0o022
                        and ((kind=="directory" and stat.S_ISDIR(held.st_mode)) or
                             (kind=="file" and stat.S_ISREG(held.st_mode) and held.st_nlink==1)),
                        "owned_write_binding_changed")
                parent=fd
        for item in self.mounts:
            if item.kind=="directory":
                self._verify_directory_tree(item.fd)

    def _verify_directory_tree(self,fd):
        remaining=4096
        device=self.worktree.device
        def visit(directory,depth):
            nonlocal remaining
            require(depth<=16,"owned_directory_depth_bound")
            with os.scandir(directory) as entries:
                for entry in entries:
                    remaining-=1
                    require(remaining>=0,"owned_directory_entry_bound")
                    _require_owned_name(entry.name)
                    info=os.stat(entry.name,dir_fd=directory,follow_symlinks=False)
                    require(info.st_dev==device and info.st_uid==os.geteuid()
                            and not info.st_mode&0o022,"owned_directory_entry_untrusted")
                    if stat.S_ISDIR(info.st_mode):
                        child=os.open(entry.name,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC,
                                      dir_fd=directory)
                        try:
                            held=os.fstat(child)
                            self._require_same_mount(child,held)
                            require((held.st_dev,held.st_ino)==(info.st_dev,info.st_ino),
                                    "owned_directory_entry_changed")
                            visit(child,depth+1)
                        finally:os.close(child)
                    else:
                        require(stat.S_ISREG(info.st_mode) and info.st_nlink==1,
                                "owned_directory_hardlink_or_special")
                        target=os.open(entry.name,os.O_PATH|os.O_NOFOLLOW|os.O_CLOEXEC,dir_fd=directory)
                        try:
                            held=os.fstat(target)
                            self._require_same_mount(target,held)
                            require((held.st_dev,held.st_ino)==(info.st_dev,info.st_ino)
                                    and stat.S_ISREG(held.st_mode) and held.st_nlink==1,
                                    "owned_directory_entry_changed")
                        finally:os.close(target)
        opened=os.open(".",os.O_RDONLY|os.O_DIRECTORY|os.O_CLOEXEC,dir_fd=fd)
        try:visit(opened,0)
        finally:os.close(opened)

    def descriptors(self):
        self.verify()
        return [{"source":f"/proc/{os.getpid()}/fd/{item.fd}","fd":item.fd,
                 "device":item.device,"inode":item.inode,"kind":item.kind,"target":item.target}
                for item in self.mounts]

    def evidence(self):
        self.verify()
        return [{"key":item.key,"kind":item.kind,"device":item.device,"inode":item.inode}
                for item in self.mounts]

    def verify_mounted(self,pid,modes):
        self.verify()
        verify_owned_mount_evidence(self.worktree.logical,self.evidence(),pid,modes)
        root=Path(f"/proc/{pid}/root")
        for item in self.mounts:
            mounted=(root/item.target.lstrip("/")).stat()
            require((mounted.st_dev,mounted.st_ino)==(item.device,item.inode)
                    and "rw" in modes.get(item.target,set()),"owned_write_mount_mismatch")

    def close(self):
        if not self._closed:
            self._closed=True
            for fd in self._opened.values():os.close(fd)
            self._opened.clear()

    def __enter__(self):return self
    def __exit__(self,*_):self.close()


def validate_owned_mount_evidence(ownership, rows):
    require(isinstance(ownership,ChildOwnership) and isinstance(rows,list) and len(rows)<=64,
            "owned_mount_evidence_bound")
    expected={}
    for scope in ownership.write_scope:
        if scope.kind=="resource":
            continue
        if any(kind=="directory" and (scope.key==key or scope.key.startswith(key+"/"))
               for key,kind in expected.items()):
            continue
        if scope.kind=="directory":
            expected={key:kind for key,kind in expected.items() if not key.startswith(scope.key+"/")}
        expected[scope.key]=scope.kind
    found={}
    for row in rows:
        require(isinstance(row,dict) and set(row)=={"key","kind","device","inode"}
                and isinstance(row["key"],str) and row["key"] not in found
                and expected.get(row["key"])==row["kind"]
                and all(type(row[name]) is int and 0<=row[name]<2**64 for name in ("device","inode"))
                and row["inode"]>0,"owned_mount_evidence_schema")
        found[row["key"]]=dict(row)
    require(set(found)==set(expected),"owned_mount_evidence_scope")
    return tuple(found.values())


def verify_owned_mount_evidence(workspace, rows, pid, modes):
    workspace=Path(workspace)
    require(workspace.is_absolute() and type(pid) is int and pid>0,"owned_mount_process")
    targets={str(workspace/row["key"]) for row in rows}
    for name,flags in modes.items():
        path=Path(name)
        if workspace in path.parents:
            require(name in targets and "__stacked__" not in flags,"owned_unexpected_mount")
    root=Path(f"/proc/{pid}/root")
    for row in rows:
        target=workspace/row["key"]
        info=(root/str(target).lstrip("/")).stat()
        require((info.st_dev,info.st_ino)==(row["device"],row["inode"])
                and ((row["kind"]=="file" and stat.S_ISREG(info.st_mode)) or
                     (row["kind"]=="directory" and stat.S_ISDIR(info.st_mode)))
                and "rw" in modes.get(str(target),set()),"owned_write_mount_mismatch")
