"""Proposed trusted prep implementation. Import is inert; execution is not authorized.

The existing Herdr ApprovedPrivateMountPlan is necessary but insufficient:
the future root case must ALSO approve these preparer bytes, its exact argv,
profile/transition and runtime. No plan is issued or signed in this module.
The SDK worker profile is entered after all namespace and mount operations.
"""
from __future__ import annotations
from dataclasses import dataclass
import ctypes
import hashlib
import os
from pathlib import PurePosixPath
import re
import stat
import struct
import fcntl
import select
import signal
import socket

PROFILE = "herdr189-reference-lifetime"
UID = GID = 1001
MS_RDONLY, MS_NOSUID, MS_NODEV, MS_NOEXEC = 1, 2, 4, 8
MS_REMOUNT, MS_BIND, MS_REC, MS_PRIVATE = 32, 4096, 16384, 1 << 18
CLONE_NEWNS, CLONE_NEWPID, CLONE_NEWNET = 0x20000, 0x20000000, 0x40000000
CLONE_NEWIPC, CLONE_NEWUTS, CLONE_NEWUSER = 0x08000000, 0x04000000, 0x10000000


class Denied(RuntimeError):
    pass


def require(condition, code):
    if not condition:
        raise Denied(code)


def path(value):
    require(type(value) is str and value.startswith("/") and "\0" not in value,
            "absolute_path_required")
    p = PurePosixPath(value)
    require(str(p) == value and all(x not in (".", "..") for x in p.parts),
            "canonical_path_required")
    return p


@dataclass(frozen=True)
class Mount:
    target: str
    fd: int | None
    readonly: bool
    kind: str
    device: int | None = None
    inode: int | None = None


@dataclass(frozen=True)
class Recipe:
    mounts: tuple[Mount, ...]
    directories: tuple[str, ...]
    readonly_directories: tuple[str, ...]
    cwd: str
    environment: dict[str, str]
    argv: tuple[str, ...]
    plan_sha256: str


def recipe_from_approved(plan, descriptors, argv, *, identity, api, system_fds):
    """Consume the actual typed authority and exact approved argv, never a bool.

    system_fds are independently held/pinned host runtime files. Literal
    --ro-bind paths in the accepted grammar are not reopened during setup.
    Exact command interpretation is source-advisory pending issuer compatibility.
    """
    require(isinstance(plan, api.ApprovedPrivateMountPlan), "typed_existing_plan_required")
    require(plan.identity == identity and plan.authorize(descriptors, argv)["authority_sha256"]
            == plan.sha256, "existing_plan_binding_changed")
    require(type(argv) is list and argv[0] == "/usr/bin/bwrap" and argv.count("--") == 1,
            "accepted_bwrap_grammar_required")
    end = argv.index("--")
    require(argv[end + 1:] == ["/bin/bash", "--noprofile", "--norc", "-i"],
            "accepted_waiting_shell_required")
    entries = {row["fd"]: row for row in descriptors}
    require(len(entries) == len(descriptors) <= 96, "ambiguous_descriptors")
    mounts, directories, readonly_dirs, env, used = [], [], [], {}, set()
    cwd = None
    seen_targets = {}
    arity = {"--tmpfs": 1, "--dir": 1, "--dev": 1, "--proc": 1,
             "--chdir": 1, "--remount-ro": 1, "--setenv": 2, "--unsetenv": 1,
             "--ro-bind": 2, "--bind-fd": 2, "--ro-bind-fd": 2, "--ro-bind-data": 2,
             "--unshare-pid": 0, "--die-with-parent": 0,
             "--disable-userns": 0, "--cap-drop": 1}
    index = 1
    required = set()
    while index < end:
        op = argv[index]
        require(op in arity and index + arity[op] < end, "unsupported_mount_operation")
        values = argv[index + 1:index + arity[op] + 1]
        required.add(op)
        index += arity[op] + 1
        if op in {"--unshare-pid", "--die-with-parent", "--disable-userns", "--unsetenv"}:
            continue
        if op == "--cap-drop":
            require(values == ["ALL"], "complete_capability_drop_required")
        elif op == "--setenv":
            require(values[0] not in env, "duplicate_environment")
            env[values[0]] = values[1]
        elif op == "--chdir":
            require(cwd is None, "duplicate_cwd")
            cwd = str(path(values[0]))
        elif op == "--dir":
            directories.append(str(path(values[0])))
        elif op == "--remount-ro":
            readonly_dirs.append(str(path(values[0])))
        else:
            target = values[-1]
            path(target)
            # The accepted private resolver may first bind the literal system
            # resolver, then cover it with its sealed snapshot. No other stack
            # (including a reversed resolver stack) has an authority meaning.
            previous = seen_targets.get(target)
            resolver_overlay = (previous == "--ro-bind" and op == "--ro-bind-data"
                and target in system_fds and target in getattr(api, "RESOLVER_TARGETS", ())
                and any(row["fd"] == int(values[0]) and
                        row["kind"] == "sealed-resolver-data" and row["target"] == target
                        for row in descriptors)) if values[0].isdigit() else False
            require(previous is None or resolver_overlay, "stacked_mount_rejected")
            seen_targets[target] = op
            if op in {"--tmpfs", "--dev", "--proc"}:
                mounts.append(Mount(target, None, False, op[2:]))
            elif op == "--ro-bind":
                require(values[0] == target and target in system_fds,
                        "unheld_literal_system_file")
                info = system_fds[target]
                require(info["sha256"] == api.approved_system_files[target]
                        and api.fd_sha256(info["fd"]) == info["sha256"],
                        "system_runtime_bytes_changed")
                mounts.append(Mount(target, info["fd"], True, "file",
                                    info["device"], info["inode"]))
            else:
                require(values[0].isdigit(), "descriptor_token_invalid")
                number = int(values[0]); row = entries.get(number)
                require(row is not None and number not in used and row["target"] == target,
                        "unapproved_descriptor")
                used.add(number)
                require(row["kind"] in {"directory", "file", "socket", "reserved-result",
                        "sealed-profile-data", "sealed-resolver-data"}, "descriptor_kind_invalid")
                require((op == "--ro-bind-data") == row["kind"].startswith("sealed-"),
                        "sealed_descriptor_mode_changed")
                mounts.append(Mount(target, number, op != "--bind-fd", row["kind"],
                                    row["device"], row["inode"]))
    require(used == set(entries) and cwd and mounts and mounts[0] == Mount("/", None, False, "tmpfs")
            and {"--unshare-pid", "--die-with-parent", "--disable-userns", "--cap-drop"} <= required
            and readonly_dirs[-1:] == ["/"], "incomplete_private_plan")
    require(set(system_fds) == set(api.SYSTEM_RUNTIME_FILES), "exact_system_runtime_required")
    return Recipe(tuple(mounts), tuple(directories), tuple(readonly_dirs), cwd, env,
                  tuple(argv[end + 1:]), plan.sha256)


def prepare_and_exec(recipe, ops, *, root, identity_environment, safe_environment,
                     filter_program, filter_sha256, prep_profile):
    """Concrete sequence over injected syscalls; no SDK import or host authority.

    Must run in a separately admitted, root, single-threaded disposable prep
    process. The host supervisor retains FDs/authority and independently kills
    its owned cgroup on failure. Returning is always an execution error.
    """
    require(isinstance(recipe, Recipe), "typed_recipe_required")
    require(re.fullmatch(r"[0-9a-f]{64}", filter_sha256 or "") and
            hashlib.sha256(filter_program).hexdigest() == filter_sha256,
            "fixed_filter_binding_changed")
    require(ops.euid() == 0 and ops.threads() == 1, "single_threaded_root_prep_required")
    require(re.fullmatch(r"herdr-offline-prep-[0-9a-f]{16}", prep_profile or "") and
            ops.label() == prep_profile + " (enforce)", "exact_trusted_prep_profile_required")
    path(root)
    require(root != "/" and recipe.cwd != "/", "private_root_required")
    ops.verify_stdio()
    # Verify all mount sources before any namespace/mount operation. The
    # approved plan revalidation in the host is repeated before process start.
    for item in recipe.mounts:
        if item.fd is not None:
            info = ops.fstat(item.fd)
            expected_kind = stat.S_ISDIR(info.st_mode) if item.kind == "directory" else (
                stat.S_ISSOCK(info.st_mode) if item.kind == "socket" else stat.S_ISREG(info.st_mode))
            require(expected_kind and (info.st_dev, info.st_ino) == (item.device, item.inode),
                    "held_mount_source_changed")
    ops.unshare(CLONE_NEWNS | CLONE_NEWPID | CLONE_NEWNET | CLONE_NEWIPC | CLONE_NEWUTS)
    ops.mount(None, "/", None, MS_REC | MS_PRIVATE, None)
    # The child is PID1 of the new private PID namespace. Parent must wait and
    # propagate its status; it never reaches worker bootstrap or model code.
    ops.fork_namespace_init()
    ops.create_private_root(root)
    resolver_literals = set()
    for item in recipe.mounts:
        target = root if item.target == "/" else root + item.target
        if item.kind == "tmpfs":
            ops.target(target, directory=True)
            private_write = item.target == "/tmp" or any(
                item.target.endswith("/" + name) for name in ("sessions", "cache", "logs", "pastes"))
            settings = "mode=700,uid=1001,gid=1001" if private_write else "mode=755"
            ops.mount("tmpfs", target, "tmpfs", MS_NOSUID | MS_NODEV, settings + ",size=268435456")
        elif item.kind == "proc":
            ops.target(target, directory=True)
            ops.mount("proc", target, "proc", MS_NOSUID | MS_NODEV | MS_NOEXEC, None)
        elif item.kind == "dev":
            ops.private_devices(target)
        else:
            replace_resolver = item.kind == "sealed-resolver-data" and item.target in resolver_literals
            if replace_resolver:
                ops.replace_resolver(target)
            else:
                ops.target(target, directory=item.kind == "directory")
            if item.kind.startswith("sealed-"):
                ops.copy_sealed_file(item.fd, target)
                ops.mount(target, target, None, MS_BIND, None)
            else:
                ops.mount("/proc/self/fd/" + str(item.fd), target, None, MS_BIND, None)
            if item.readonly:
                ops.mount(None, target, None, MS_BIND | MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV, None)
            if item.target in ("/etc/resolv.conf", "/run/systemd/resolve/stub-resolv.conf",
                               "/run/systemd/resolve/resolv.conf") and item.kind == "file":
                resolver_literals.add(item.target)
    for target in recipe.directories:
        ops.target(root + target, directory=True)
    for target in recipe.readonly_directories:
        ops.mount(None, root if target == "/" else root + target,
                  None, MS_REMOUNT | MS_RDONLY | MS_NOSUID | MS_NODEV, None)
    # pivot_root discards every host-root pathname, including old cwd aliases.
    # No host-backed directory FD survives this point or enters the worker.
    ops.pivot_to(root)
    ops.chdir(recipe.cwd)
    ops.close_except({0, 1, 2})
    env = dict(safe_environment)
    env.update(recipe.environment)
    env.update(identity_environment)
    require(env.get("HOME") == "/home/agentops" and
            all(type(k) is str and type(v) is str and "\0" not in k + v for k, v in env.items())
            and not any(k.startswith(("LD_", "PYTHONPATH", "PYTHONHOME")) for k in env),
            "unsafe_worker_environment")
    ops.setgroups([])
    # A distinct root parent in the original user namespace writes maps.
    # The worker cannot self-map host UID 1001 after CLONE_NEWUSER.
    ops.map_worker_userns(UID, GID)
    parent_fd = ops.parent_fence_begin()
    ops.close_except({0, 1, 2, parent_fd})
    ops.drop_bounding_capabilities()
    ops.setresgid(GID)
    ops.setresuid(UID)
    ops.clear_capabilities()
    # Credential changes clear PDEATHSIG. Re-arm it after the final change,
    # then check the pidfd captured before fork to close the death race.
    ops.parent_fence_finish(parent_fd)
    # This is a direct transition from the future approved prep domain into
    # the EXISTING fixed worker domain, after the last privileged operation.
    ops.change_profile(PROFILE)
    ops.no_new_privileges()
    ops.verify_parent_fence()
    ops.install_filter(filter_program)
    ops.verify_worker_identity(UID, GID, PROFILE)
    ops.verify_stdio()
    ops.execve(recipe.argv[0], list(recipe.argv), env)
    raise Denied("exec_returned")


class LinuxOps:
    """Actual Linux syscall implementation, constructed only by explicit execute.

    No permissive fallback. A real case needs a reviewed temporary prep profile
    allowing setup plus ONE transition to PROFILE; the worker receives none of
    those setup rights. This class never loads a profile or edits issuer policy.
    """
    def __init__(self):
        require(os.name == "posix" and os.uname().machine == "x86_64", "linux_x86_64_required")
        self.libc = ctypes.CDLL(None, use_errno=True)
        self.libc.syscall.restype = ctypes.c_long

    def checked(self, name, *args):
        result = getattr(self.libc, name)(*args)
        if result < 0:
            raise OSError(ctypes.get_errno(), "trusted preparation syscall failed")
        return result

    def euid(self): return os.geteuid()
    def threads(self): return len(os.listdir("/proc/self/task"))
    def label(self): return self._read("/proc/self/attr/current", 1024).decode().strip()
    def fstat(self, fd): return os.fstat(fd)
    def verify_stdio(self):
        for fd in (0, 1, 2):
            info = os.fstat(fd)
            mode = fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE
            require(stat.S_ISCHR(info.st_mode) and os.major(info.st_rdev) == 1
                    and os.minor(info.st_rdev) == 3 and
                    mode == (os.O_RDONLY if fd == 0 else os.O_WRONLY),
                    "exact_null_stdio_required")
    def unshare(self, flags): self.checked("unshare", flags)
    def mount(self, source, target, kind, flags, data):
        enc = lambda x: None if x is None else os.fsencode(x)
        self.checked("mount", enc(source), enc(target), enc(kind), ctypes.c_ulong(flags), enc(data))

    @staticmethod
    def _read(name, limit):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            raw = os.read(fd, limit + 1)
            require(len(raw) <= limit, "kernel_metadata_limit")
            return raw
        finally: os.close(fd)

    def fork_namespace_init(self):
        original_parent = os.getpid()
        parent_fd = os.pidfd_open(original_parent)
        pid = os.fork()
        if pid:
            try:
                _, status = os.waitpid(pid, 0)
                os._exit(os.waitstatus_to_exitcode(status) if os.WIFEXITED(status) else 128 + os.WTERMSIG(status))
            finally: os.close(parent_fd)
        self.checked("prctl", 1, signal.SIGKILL, 0, 0, 0)
        poller = select.poll(); poller.register(parent_fd, select.POLLIN | select.POLLHUP | select.POLLERR)
        require(not poller.poll(0), "namespace_preparer_parent_died")
        os.close(parent_fd)

    def map_worker_userns(self, uid, gid):
        require((uid, gid) == (UID, GID) and os.geteuid() == 0,
                "root_parent_mapping_required")
        parent, worker = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM | socket.SOCK_CLOEXEC)
        pid = os.fork()
        if pid:
            worker.close()
            try:
                require(parent.recv(1) == b"U", "worker_userns_handshake_missing")
                for name, raw in (("setgroups", b"deny\n"), ("uid_map", b"1001 1001 1\n"),
                                  ("gid_map", b"1001 1001 1\n")):
                    fd = os.open(f"/proc/{pid}/{name}", os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
                    try: require(os.write(fd, raw) == len(raw), "parent_userns_mapping_incomplete")
                    finally: os.close(fd)
                parent.sendall(b"M")
            except BaseException:
                try: parent.sendall(b"E")
                except OSError: pass
                os.kill(pid, signal.SIGKILL)
                os.waitpid(pid, 0)
                raise
            finally: parent.close()
            _, status = os.waitpid(pid, 0)
            os._exit(os.waitstatus_to_exitcode(status) if os.WIFEXITED(status) else 128 + os.WTERMSIG(status))
        parent.close()
        try:
            self.unshare(CLONE_NEWUSER)
            worker.sendall(b"U")
            require(worker.recv(1) == b"M", "parent_userns_mapping_denied")
            require(self._read("/proc/self/uid_map", 256).split() == [b"1001", b"1001", b"1"]
                    and self._read("/proc/self/gid_map", 256).split() == [b"1001", b"1001", b"1"],
                    "worker_userns_mapping_changed")
        finally: worker.close()

    def parent_fence_begin(self):
        self._fence_parent = os.getppid()
        require(self._fence_parent > 0, "worker_parent_identity_missing")
        return os.pidfd_open(self._fence_parent)

    def parent_fence_finish(self, fd):
        self.checked("prctl", 1, signal.SIGKILL, 0, 0, 0)
        poller = select.poll(); poller.register(fd, select.POLLIN | select.POLLHUP | select.POLLERR)
        require(os.getppid() == self._fence_parent and not poller.poll(0),
                "worker_parent_died_or_replaced")
        os.close(fd)
        self.verify_stdio()
        require(sorted(int(name) for name in os.listdir("/proc/self/fd")
                       if name.isdecimal() and self._fd_open(int(name))) == [0, 1, 2],
                "worker_fd_closure_incomplete")

    def verify_parent_fence(self):
        value = ctypes.c_int(-1)
        self.checked("prctl", 2, ctypes.byref(value), 0, 0, 0)
        require(value.value == signal.SIGKILL and os.getppid() == self._fence_parent,
                "worker_parent_death_contract_lost")

    @staticmethod
    def _fd_open(fd):
        try: os.fstat(fd); return True
        except OSError: return False

    def create_private_root(self, root):
        # Exact new directory; no reuse of an uncertain previous attempt.
        os.mkdir(root, 0o700)
        os.chmod(root, 0o700)

    def replace_resolver(self, target):
        self.checked("umount2", os.fsencode(target), 2)
        info = os.lstat(target)
        require(stat.S_ISREG(info.st_mode) and info.st_uid == 0 and info.st_nlink == 1,
                "resolver_underlay_changed")

    def target(self, target, *, directory):
        # All destination components live on our private empty root. Every
        # component is no-follow so no mounted source can redirect creation.
        parent = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        parts = PurePosixPath(target).parts[1:]
        try:
            for component in parts[:-1] + (parts[-1:] if directory else ()):
                created = False
                try:
                    os.mkdir(component, 0o755, dir_fd=parent)
                    created = True
                except FileExistsError: pass
                if created: os.chmod(component, 0o755, dir_fd=parent, follow_symlinks=False)
                fd = os.open(component, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=parent)
                os.close(parent); parent = fd
            if not directory:
                fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                             0o600, dir_fd=parent)
                os.fchmod(fd, 0o600)
                os.close(fd)
        finally: os.close(parent)

    def private_devices(self, target):
        self.target(target, directory=True)
        self.mount("tmpfs", target, "tmpfs", MS_NOSUID, "mode=755,size=1048576")
        for name, mode, major, minor in (("null", 0o666, 1, 3), ("tty", 0o666, 5, 0), ("ptmx", 0o666, 5, 2)):
            os.mknod(target + "/" + name, stat.S_IFCHR | mode, os.makedev(major, minor))
            os.chmod(target + "/" + name, mode)
        self.target(target + "/pts", directory=True)
        self.mount("devpts", target + "/pts", "devpts", MS_NOSUID | MS_NOEXEC,
                   "newinstance,ptmxmode=0666,mode=0620,gid=1001")
        self.target(target + "/shm", directory=True)
        self.mount("tmpfs", target + "/shm", "tmpfs", MS_NOSUID | MS_NODEV, "mode=1777,size=16777216")

    def copy_sealed_file(self, fd, target):
        import fcntl
        require(fcntl.fcntl(fd, 1034) & 15 == 15, "sealed_file_required")
        info = os.fstat(fd)
        require(stat.S_ISREG(info.st_mode) and info.st_size <= 524288, "sealed_file_size")
        output = os.open(target, os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            offset = 0
            while offset < info.st_size:
                raw = os.pread(fd, min(65536, info.st_size - offset), offset)
                require(bool(raw) and os.write(output, raw) == len(raw), "sealed_copy_incomplete")
                offset += len(raw)
            os.fchmod(output, 0o444)
        finally: os.close(output)

    def pivot_to(self, root):
        # Linux pivot_root(".", ".") detaches the old root without a writable
        # old-root directory, including when the private root was remounted ro.
        os.chdir(root)
        require(self.libc.syscall(155, b".", b".") == 0, "pivot_root_failed")
        self.checked("umount2", b".", 2)
        os.chdir("/")

    def chdir(self, where): os.chdir(where)
    def close_except(self, kept):
        for name in os.listdir("/proc/self/fd"):
            if name.isdecimal() and int(name) not in kept:
                try: os.close(int(name))
                except OSError as exc:
                    if exc.errno != 9: raise

    def setgroups(self, groups): os.setgroups(groups)
    def write_self(self, name, raw):
        require(name in {"uid_map", "gid_map", "setgroups"}, "namespace_mapping_target")
        fd = os.open("/proc/self/" + name, os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try: require(os.write(fd, raw) == len(raw), "namespace_mapping_incomplete")
        finally: os.close(fd)
    def drop_bounding_capabilities(self):
        # Kernel currently supports <=64 capability numbers. Unknown future
        # extensions fail closed in the final CapBnd observation.
        for number in range(64):
            value = self.libc.prctl(23, number, 0, 0, 0)
            if value < 0:
                require(ctypes.get_errno() == 22, "capability_inventory_failed")
                break
            if value: self.checked("prctl", 24, number, 0, 0, 0)
    def setresgid(self, gid): os.setresgid(gid, gid, gid)
    def setresuid(self, uid): os.setresuid(uid, uid, uid)
    def clear_capabilities(self):
        class Header(ctypes.Structure): _fields_ = [("version", ctypes.c_uint32), ("pid", ctypes.c_int)]
        class Data(ctypes.Structure): _fields_ = [("effective", ctypes.c_uint32), ("permitted", ctypes.c_uint32), ("inheritable", ctypes.c_uint32)]
        header = Header(0x20080522, 0); values = (Data * 2)()
        self.checked("capset", ctypes.byref(header), ctypes.byref(values))
        self.checked("prctl", 47, 4, 0, 0, 0)  # clear ALL ambient capabilities
    def change_profile(self, profile):
        require(profile == PROFILE, "fixed_worker_profile_required")
        fd = os.open("/proc/self/attr/current", os.O_WRONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            raw = ("changeprofile " + profile).encode()
            require(os.write(fd, raw) == len(raw), "profile_transition_incomplete")
        finally: os.close(fd)
    def no_new_privileges(self): self.checked("prctl", 38, 1, 0, 0, 0)
    def install_filter(self, program):
        require(len(program) % 8 == 0 and 0 < len(program) <= 32768, "invalid_filter_program")
        class SockFilter(ctypes.Structure):
            _fields_ = [("code", ctypes.c_ushort), ("jt", ctypes.c_ubyte), ("jf", ctypes.c_ubyte), ("k", ctypes.c_uint32)]
        class SockFprog(ctypes.Structure):
            _fields_ = [("len", ctypes.c_ushort), ("filter", ctypes.POINTER(SockFilter))]
        filters = (SockFilter * (len(program) // 8))(*(SockFilter(*row) for row in struct.iter_unpack("=HBBI", program)))
        value = SockFprog(len(filters), filters)
        self.checked("prctl", 22, 2, ctypes.byref(value), 0, 0)
    def verify_worker_identity(self, uid, gid, profile):
        fields = dict(line.split(":", 1) for line in self._read("/proc/self/status", 65536).decode().splitlines() if ":" in line)
        require(os.getresuid() == (uid,) * 3 and os.getresgid() == (gid,) * 3 and os.getgroups() == []
                and all(fields[k].strip() == "0000000000000000" for k in ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb"))
                and fields["NoNewPrivs"].strip() == "1" and fields["Seccomp"].strip() == "2"
                and self.label() == profile + " (enforce)", "worker_transition_unproven")
    def execve(self, executable, argv, env): os.execve(executable, argv, env)
