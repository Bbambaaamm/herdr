"""Worker handoff to the accepted held-FD Hermes bootstrap.

The root host must seal this process before arming bootstrap. Stage one obtains
and holds the stage-two and interpreter descriptors; stage two authenticates
the opaque host reference and installs the accepted SDK guard.
"""
import os
import re

from .case import PROFILE, require


class LinuxWorkerView:
    """Read kernel state of this process immediately before SDK import."""
    def text(self, path):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            return os.read(fd, 65537).decode("utf-8", "strict")
        finally:
            os.close(fd)

    def fds(self):
        result = []
        for name in os.listdir("/proc/self/fd"):
            if name.isdecimal():
                try:
                    os.fstat(int(name))
                except OSError:
                    continue  # proc enumeration may include its own closed fd
                result.append(int(name))
        return sorted(result)

    def namespace(self, kind):
        return os.readlink("/proc/self/ns/" + kind)

    def identity(self):
        return os.getuid(), os.getgid()

    def home(self):
        return os.environ.get("HOME")


def verify_worker(view):
    """Local checks supplement the accepted host seal and retained observer."""
    status = {}
    for line in view.text("/proc/self/status").splitlines():
        if ":" in line:
            key, value = line.split(":", 1)
            require(key not in status, "duplicate kernel status")
            status[key] = value.strip()
    require(view.identity() == (1001, 1001), "wrong worker uid or gid")
    require(all(status.get(key) == "0000000000000000" for key in
                ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")),
            "worker retained capabilities")
    require(status.get("NoNewPrivs") == "1" and status.get("Seccomp") == "2" and
            status.get("Seccomp_filters", "0").isdecimal() and
            int(status.get("Seccomp_filters", "0")) >= 1,
            "worker privilege or seccomp state unknown")
    require(view.text("/proc/self/attr/current").strip() == PROFILE + " (enforce)",
            "worker AppArmor label not enforced")
    require(view.fds() == [0, 1, 2],
            "unexpected inherited worker descriptor")
    require(view.home() == "/home/agentops", "private HOME missing")
    for kind in ("pid", "mnt", "net", "user"):
        require(re.fullmatch(rf"{kind}:\[[1-9][0-9]*\]", view.namespace(kind)) is not None,
                "kernel namespace identity unavailable")
    return True


def main(*, view=None, environ=None, execve=None):
    """Exec the accepted immutable shim, which handles stage-one descriptors."""
    env = dict(os.environ if environ is None else environ)
    view = view or LinuxWorkerView()
    execve = execve or os.execve
    identity = {"HERDR_POLICY_CONSUMER", "HERDR_POLICY_AGENT_ID",
                "HERDR_POLICY_PARENT_AGENT_ID", "HERDR_POLICY_PARENT_TASK_ID",
                "HERDR_POLICY_TASK_ID", "HERDR_POLICY_RUN_TOKEN",
                "HERDR_POLICY_FENCING_TOKEN", "HERDR_POLICY_STAGE1_PROOF_SHA256"}
    safe = identity | {"HOME", "HERMES_HOME", "HERMES_MANAGED_DIR",
        "HERMES_SAFE_MODE", "HERMES_ENABLE_PROJECT_PLUGINS", "HERDR_DURABLE_SANDBOX",
        "HERDR_DURABLE_TASK_PANE", "PATH", "LANG", "LC_ALL", "TERM",
        "TMPDIR", "USER", "LOGNAME", "PYTHONNOUSERSITE"}
    require(identity <= set(env) and set(env) <= safe and
            all(type(v) is str and v and "\0" not in v for v in env.values()) and
            re.fullmatch(r"[0-9a-f]{64}", env["HERDR_POLICY_STAGE1_PROOF_SHA256"]),
            "unclean or incomplete accepted bootstrap environment")
    verify_worker(view)
    target = "/run/herdr-bootstrap/hermes"
    execve(target, [target, "-p", "quantlab", "chat"], env)
    raise RuntimeError("accepted stage-one bootstrap returned unexpectedly")


if __name__ == "__main__":
    main()
