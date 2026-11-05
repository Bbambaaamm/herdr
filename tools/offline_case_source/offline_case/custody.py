"""Root-only subordinate attempt receipts; no grant or admission authority."""
import fcntl
import os
import stat
from pathlib import Path

from .case import NONCE, canonical, parse, require


ATTEMPT = "used-" + NONCE + ".json"


class RootCustody:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.fd = self.lockfd = None
        self.locked = False

    def __enter__(self):
        require(os.geteuid() == 0 and self.path.is_absolute() and
                ".." not in self.path.parts, "root custody required")
        fd = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            for index, part in enumerate(self.path.parts[1:]):
                flags = os.O_RDONLY if index == len(self.path.parts) - 2 else os.O_PATH
                nextfd = os.open(part, flags | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
                os.close(fd)
                fd = nextfd
                st = os.fstat(fd)
                require(st.st_uid == 0 and not st.st_mode & 0o022,
                        "custody ancestry writable")
            self.fd = fd
            self.lockfd = os.open("attempt.lock", os.O_RDWR | os.O_NOFOLLOW, dir_fd=fd)
            self._regular(self.lockfd, 0)
            fcntl.flock(self.lockfd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.locked = True
            return self
        except BaseException:
            if self.lockfd is not None:
                os.close(self.lockfd)
            os.close(fd)
            self.fd = self.lockfd = None
            raise

    def __exit__(self, *_):
        self.locked = False
        os.close(self.lockfd)
        os.close(self.fd)
        self.fd = self.lockfd = None

    def suspend(self):
        """Release the journal lock while the owned worker blocks.

        The independent cleanup unit can then fence the case at its deadline.
        No journal operation is permitted until resume has revalidated custody.
        """
        require(self.locked and self.lockfd is not None, "locked custody required")
        fcntl.flock(self.lockfd, fcntl.LOCK_UN)
        self.locked = False

    def resume(self):
        require(not self.locked and self.lockfd is not None, "suspended custody required")
        fcntl.flock(self.lockfd, fcntl.LOCK_EX)
        self.locked = True
        self._regular(self.lockfd, 0)
        require(self.consumed(None), "attempt marker lost during worker execution")

    def _regular(self, fd, minsize=1):
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and st.st_nlink == 1
                and st.st_mode & 0o077 == 0 and minsize <= st.st_size <= 65536,
                "unsafe custody file")
        return st

    def _read(self, name):
        require(self.locked and self.fd is not None and "/" not in name, "locked custody required")
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=self.fd)
        try:
            before = self._regular(fd)
            raw = os.read(fd, before.st_size + 1)
            after = os.fstat(fd)
            entry = os.stat(name, dir_fd=self.fd, follow_symlinks=False)
            require(len(raw) == before.st_size and
                    (before.st_dev, before.st_ino, before.st_mtime_ns, before.st_size) ==
                    (after.st_dev, after.st_ino, after.st_mtime_ns, after.st_size) ==
                    (entry.st_dev, entry.st_ino, entry.st_mtime_ns, entry.st_size),
                    "custody changed during read")
            return parse(raw)
        finally:
            os.close(fd)

    def authority(self):
        return self._read("authority.json")

    def state(self):
        try:
            state = self._read("state.json")
            require(type(state) is dict and state.get("binding") == self._read(ATTEMPT),
                    "attempt state differs from fixed nonce marker")
            return state
        except FileNotFoundError:
            # Recover from the fixed case nonce. The authority challenge may
            # have been replaced after a crash and cannot be a journal key.
            if self.consumed(None):
                binding = self._read(ATTEMPT)
                require(type(binding) is dict and binding.get("nonce") == NONCE,
                        "torn or foreign attempt marker")
                return {"phase": "CONSUMED", "binding": binding}
            return None

    def consumed(self, challenge):
        # Challenge is validated for callers but never selects the marker.
        require(self.locked and self.fd is not None and (challenge is None or
                (type(challenge) is str and len(challenge) == 64 and
                 all(c in "0123456789abcdef" for c in challenge))),
                "locked custody and exact challenge required")
        # A crash before exclusive publication can leave a pending receipt.
        # It is uncertainty, not permission to try again.
        if any(name.startswith(".pending-") for name in os.listdir(self.fd)):
            return True
        try:
            os.stat(ATTEMPT, dir_fd=self.fd,
                    follow_symlinks=False)
            return True
        except FileNotFoundError:
            return False

    def _publish(self, name, value, *, exclusive=False):
        require(self.locked and self.fd is not None and "/" not in name, "locked custody required")
        pending = ".pending-" + os.urandom(16).hex()
        fd = os.open(pending, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                     0o600, dir_fd=self.fd)
        try:
            raw = canonical(value)
            require(len(raw) <= 65536, "receipt oversized")
            require(os.write(fd, raw) == len(raw), "receipt write short")
            os.fsync(fd)
        finally:
            os.close(fd)
        if exclusive:
            os.link(pending, name, src_dir_fd=self.fd, dst_dir_fd=self.fd,
                    follow_symlinks=False)
            os.unlink(pending, dir_fd=self.fd)
        else:
            os.replace(pending, name, src_dir_fd=self.fd, dst_dir_fd=self.fd)
        os.fsync(self.fd)

    def consume(self, challenge, binding):
        require(type(challenge) is str and len(challenge) == 64 and
                all(c in "0123456789abcdef" for c in challenge), "invalid challenge")
        require(type(binding) is dict and binding.get("nonce") == NONCE and
                binding.get("challenge") == challenge, "attempt binding mismatch")
        require(not self.consumed(challenge), "attempt already consumed or torn")
        self._publish(ATTEMPT, binding, exclusive=True)

    def save(self, state):
        require(type(state) is dict and state.get("binding") == self._read(ATTEMPT),
                "attempt state differs from fixed nonce marker")
        from .root_effects import RootEffectPump
        pump = RootEffectPump(None, None)
        denied = state["phase"] in {"FINISHED", "FENCE_INTENT", "STOP_INTENT", "RETIRE_INTENT", "RETAINED_UNKNOWN", "RETIRED"}
        if denied:
            pump.publish_case_phase(state, self.authority(), self._read(ATTEMPT))
        self._publish("state.json", state)
        if not denied:
            pump.publish_case_phase(state, self.authority(), self._read(ATTEMPT))
