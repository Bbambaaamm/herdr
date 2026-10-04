"""Host startup environment controls for trusted native/Python bootstrap."""
from __future__ import annotations
import os

# Clear before the first native executable, including the pane shell and FD
# launcher. Unsetting only in the shim would be too late for its /bin/sh loader.
STARTUP_CONTROLS=(
    "LD_ASSUME_KERNEL","LD_AUDIT","LD_BIND_NOT","LD_BIND_NOW","LD_DEBUG","LD_DEBUG_OUTPUT",
    "LD_DYNAMIC_WEAK","LD_HWCAP_MASK","LD_LIBRARY_PATH","LD_ORIGIN_PATH","LD_POINTER_GUARD",
    "LD_PRELOAD","LD_PROFILE","LD_PROFILE_OUTPUT","LD_SHOW_AUXV","LD_TRACE_LOADED_OBJECTS",
    "LD_VERBOSE","LD_WARN","LD_USE_LOAD_BIAS","LD_PREFER_MAP_32BIT_EXEC","LD_TRACE_PRELINKING",
    "GLIBC_TUNABLES","GCONV_PATH","LOCPATH","NLSPATH","BASH_ENV","ENV",
)

def sanitize_environment(environment):
    return {key:value for key,value in environment.items()
            if key not in STARTUP_CONTROLS and not key.startswith("LD_")}

def require_clean_environment(environment):
    if any(name in STARTUP_CONTROLS or name.startswith("LD_") for name in environment):
        raise ValueError("unsafe native-loader/startup environment")


def process_environment(pid):
    """Read a bounded exact process environment; duplicates are ambiguous."""
    from pathlib import Path
    if type(pid) is not int or pid <= 0:
        raise ValueError("invalid startup process")
    with Path(f"/proc/{pid}/environ").open("rb") as stream:
        raw=stream.read(262145)
    if len(raw)>262144:
        raise ValueError("startup environment exceeds bound")
    result={}
    for item in raw.split(b"\0"):
        if not item: continue
        if b"=" not in item: raise ValueError("malformed startup environment")
        key,value=item.split(b"=",1)
        name=key.decode("utf-8",errors="strict")
        if name in result: raise ValueError("ambiguous startup environment")
        result[name]=value.decode("utf-8",errors="strict")
    return result

def require_clean_spawn_source(pane_shell_pid):
    """Before pane creation, check the trusted spawn parent's ancestry.

    The OS host and terminal server are trusted authorities. An inherited
    loader directive in any ancestor blocks creating a managed pane; this
    function never edits a running server or restarts a service.
    """
    from pathlib import Path
    if type(pane_shell_pid) is not int or pane_shell_pid <= 0:
        raise ValueError("invalid pane startup source")
    shell=Path(f"/proc/{pane_shell_pid}/stat").read_text().rsplit(")",1)[1].split()
    pid=int(shell[1])
    visited=set()
    for _ in range(32):
        if pid<=0 or pid in visited: raise ValueError("invalid startup parent chain")
        # PID 1 is the trusted OS service authority, not a worker-controlled
        # spawn backend. Its environment may be intentionally unreadable.
        if pid==1: return
        visited.add(pid)
        before=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()
        require_clean_environment(process_environment(pid))
        after=Path(f"/proc/{pid}/stat").read_text().rsplit(")",1)[1].split()
        if before[19]!=after[19] or before[1]!=after[1]:
            raise ValueError("startup parent process changed")
        pid=int(before[1])
    raise ValueError("startup parent chain exceeds bound")
