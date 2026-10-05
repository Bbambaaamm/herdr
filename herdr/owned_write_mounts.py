"""Host-pinned finite write mounts for one admitted child ownership contract."""
from __future__ import annotations
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from .child_ownership import ChildOwnership, OwnershipError, require

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

    def verify(self):
        require(not self._closed,"owned_write_pins_closed")
        self.worktree.verify()
        for chain in self._chains.values():
            parent=self.worktree.fd
            for key,fd,device,inode,kind in chain:
                named=os.stat(key.rsplit("/",1)[-1],dir_fd=parent,follow_symlinks=False)
                held=os.fstat(fd)
                require((named.st_dev,named.st_ino)==(held.st_dev,held.st_ino)==(device,inode)
                        and held.st_uid==os.geteuid() and not held.st_mode&0o022
                        and ((kind=="directory" and stat.S_ISDIR(held.st_mode)) or
                             (kind=="file" and stat.S_ISREG(held.st_mode) and held.st_nlink==1)),
                        "owned_write_binding_changed")
                parent=fd

    def descriptors(self):
        self.verify()
        return [{"source":f"/proc/{os.getpid()}/fd/{item.fd}","fd":item.fd,
                 "device":item.device,"inode":item.inode,"kind":item.kind,"target":item.target}
                for item in self.mounts]

    def verify_mounted(self,pid,modes):
        self.verify()
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
