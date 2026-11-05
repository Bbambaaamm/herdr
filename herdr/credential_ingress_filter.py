"""Fixed x86_64 seccomp program for the credentialless private worker.

Bubblewrap installs this before the waiting shell exists. Seccomp filters are
inherited by fork/clone/exec and cannot be removed. The fixed host work socket
uses send/recv, never descriptor-passing sendmsg/recvmsg.
"""
from __future__ import annotations

import fcntl
import os
import platform
import struct


# Linux x86_64 syscall numbers. An unknown architecture fails closed.
DENIED_SYSCALLS = {
    "ptrace": 101, "sendmsg": 46, "recvmsg": 47, "sendmmsg": 307,
    "recvmmsg": 299, "open_by_handle_at": 304, "process_vm_readv": 310,
    "process_vm_writev": 311, "kcmp": 312, "bpf": 321,
    "mount": 165, "umount2": 166, "pivot_root": 155,
    "chroot": 161, "setns": 308, "unshare": 272,
    "userfaultfd": 323, "perf_event_open": 298,
    "open_tree": 428, "move_mount": 429, "fsopen": 430,
    "fsconfig": 431, "fsmount": 432, "fspick": 433,
    "pidfd_open": 434, "clone3": 435, "mount_setattr": 442,
    "io_uring_setup": 425,
    "io_uring_enter": 426, "io_uring_register": 427,
    "pidfd_getfd": 438,
}
_BPF_LD_W_ABS = 0x20
_BPF_JMP_JEQ_K = 0x15
_BPF_JMP_JGE_K = 0x35
_BPF_JMP_JSET_K = 0x45
_BPF_RET_K = 0x06
_AUDIT_ARCH_X86_64 = 0xC000003E
_X32_SYSCALL_BIT = 0x40000000
_FIRST_UNSUPPORTED_SYSCALL = 512
_SECCOMP_RET_KILL_PROCESS = 0x80000000
_SECCOMP_RET_ERRNO_EPERM = 0x00050001
_SECCOMP_RET_ALLOW = 0x7FFF0000


def filter_bytes() -> bytes:
    instructions = [
        (_BPF_LD_W_ABS, 0, 0, 4),
        (_BPF_JMP_JEQ_K, 1, 0, _AUDIT_ARCH_X86_64),
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        (_BPF_LD_W_ABS, 0, 0, 0),
        # x32 shares AUDIT_ARCH_X86_64. Reject its tagged numbers before
        # native comparisons, including x32-specific calls. Older kernels
        # also recognized untagged x32 numbers 512..547; reserve the entire
        # unsupported range rather than relying on the host kernel version.
        (_BPF_JMP_JSET_K, 0, 1, _X32_SYSCALL_BIT),
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
        (_BPF_JMP_JGE_K, 0, 1, _FIRST_UNSUPPORTED_SYSCALL),
        (_BPF_RET_K, 0, 0, _SECCOMP_RET_KILL_PROCESS),
    ]
    for number in sorted(DENIED_SYSCALLS.values()):
        instructions.extend(((_BPF_JMP_JEQ_K, 0, 1, number),
                             (_BPF_RET_K, 0, 0, _SECCOMP_RET_ERRNO_EPERM)))
    instructions.append((_BPF_RET_K, 0, 0, _SECCOMP_RET_ALLOW))
    return b"".join(struct.pack("=HBBI", *row) for row in instructions)


def fixed_filter_fd() -> int:
    if platform.machine() != "x86_64":
        raise RuntimeError("credential ingress filter architecture unsupported")
    fd = os.memfd_create("herdr-credential-ingress-filter",
                         os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        program = filter_bytes()
        if os.write(fd, program) != len(program):
            raise RuntimeError("credential ingress filter incomplete")
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS,
                    fcntl.F_SEAL_SEAL | fcntl.F_SEAL_SHRINK |
                    fcntl.F_SEAL_GROW | fcntl.F_SEAL_WRITE)
        os.lseek(fd, 0, os.SEEK_SET)
        os.set_inheritable(fd, True)
        return fd
    except BaseException:
        os.close(fd)
        raise
