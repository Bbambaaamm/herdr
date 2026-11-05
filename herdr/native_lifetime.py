"""Additive native PID1 lifetime proof; legacy bwrap proof v2 is unchanged."""
import os
from pathlib import Path
import re
from .case_roster import ROSTER_PATH, CONTEXT_ROOT, Roster, canonical, digest, require, hex64, load_roster

KEYS = {"version", "kind", "pid", "start_ticks", "namespace", "init_pid", "init_start_ticks",
        "role", "roster_sha256", "context_sha256", "runtime_sha256", "preparer_source_sha256"}


def binding_for(pid):
    from herdr.security import InvocationIdentity
    from .prep_entry import protected_json
    roster = load_roster(protected_json, InvocationIdentity)
    selected = []
    for role in roster.roles:
        try: runtime = protected_json(Path(CONTEXT_ROOT) / (role + ".runtime.json"))
        except FileNotFoundError: continue
        if runtime["pid"] == pid:
            context = protected_json(Path(CONTEXT_ROOT) / (role + ".json"))
            require(runtime["roster_sha256"] == roster.sha256 and runtime["context_sha256"] == digest(context)
                and runtime["role"] == role and runtime["unit"] == roster.slot(role)["unit"]
                and context["slot_sha256"] == digest(roster.slot(role)) and
                context["child_projection_sha256"] == roster.projection_sha256(role), "native_runtime_binding_changed")
            selected.append((roster, role, context, runtime))
    require(len(selected) == 1, "pid_not_one_recorded_native_init")
    return selected[0]


def capture_namespace_lifetime(pid):
    from herdr.observed_proc import Path as ObservedPath
    from herdr.observed_proc import os as observed_os
    def _process_snapshot(selected):
        proc = ObservedPath(f"/proc/{selected}")
        before = (proc / "stat").read_bytes()
        require(len(before) <= 8192 and b") " in before, "native_snapshot_stat_bound")
        fields = before.rsplit(b") ", 1)[1].split()
        status = (proc / "status").read_bytes()
        require(len(status) <= 131072, "native_snapshot_status_bound")
        rows = {line.split(b":", 1)[0]: line.split()[1:] for line in status.splitlines() if b":" in line}
        exe = (proc / "exe").stat()
        result = {"pid": selected, "start_ticks": int(fields[19]), "ppid": int(fields[1]),
            "ids": tuple(map(int, rows[b"NSpid"])), "uids": tuple(map(int, rows[b"Uid"])),
            "cgroup": (proc / "cgroup").read_bytes(), "namespace": observed_os.readlink(proc / "ns/pid"),
            "mount_namespace": observed_os.readlink(proc / "ns/mnt"), "executable": (exe.st_dev, exe.st_ino)}
        require(fields[0] not in {b"Z", b"X", b"x"} and (proc / "stat").read_bytes() == before,
                "native_snapshot_changed")
        return result
    roster, role, context, runtime = binding_for(pid)
    observed = _process_snapshot(pid)
    # Our actual waiting shell is PID1, preserved by start_sandbox_agent.
    # Do not represent it as legacy bwrap or assume an executable by name.
    bash = Path("/bin/bash").stat()
    require(observed["ids"][-1] == 1 and len(observed["ids"]) >= 2 and
        observed["start_ticks"] == runtime["start_ticks"] and observed["namespace"] == runtime["namespace"]
        and observed["uids"] == (1001,) * 4 and observed["executable"] == (bash.st_dev, bash.st_ino)
        and observed["cgroup"] == ("0::/system.slice/" + roster.slot(role)["unit"] + "\n").encode()
        and ObservedPath(f"/proc/{pid}/attr/current").read_text().strip() == "herdr189-reference-lifetime (enforce)",
        "actual_native_namespace_init_unproven")
    require(_process_snapshot(pid) == observed, "native_init_changed_during_capture")
    return {"version": 3, "kind": "native-preparation-v2", "pid": pid, "start_ticks": observed["start_ticks"],
        "namespace": observed["namespace"], "init_pid": pid, "init_start_ticks": observed["start_ticks"],
        "role": role, "roster_sha256": roster.sha256, "context_sha256": digest(context),
        "runtime_sha256": digest(runtime), "preparer_source_sha256": digest(roster.document["preparer"]["files"])}


def validate_namespace_lifetime(value):
    require(type(value) is dict and set(value) == KEYS and value["version"] == 3
        and value["kind"] == "native-preparation-v2" and value["role"] in ("root", "child")
        and type(value["pid"]) is int and value["pid"] > 0 and value["init_pid"] == value["pid"]
        and type(value["start_ticks"]) is int and value["start_ticks"] > 0
        and value["init_start_ticks"] == value["start_ticks"]
        and type(value["namespace"]) is str and re.fullmatch(r"pid:\[[0-9]+\]", value["namespace"])
        and all(hex64(value[k]) for k in ("roster_sha256", "context_sha256", "runtime_sha256", "preparer_source_sha256")),
        "closed_native_namespace_proof_required")
    roster, role, context, runtime = binding_for(value["pid"])
    require(role == value["role"] and roster.sha256 == value["roster_sha256"]
        and digest(context) == value["context_sha256"] and digest(runtime) == value["runtime_sha256"]
        and digest(roster.document["preparer"]["files"]) == value["preparer_source_sha256"]
        and runtime["namespace"] == value["namespace"] and runtime["start_ticks"] == value["start_ticks"],
        "native_namespace_proof_not_canonical")
    return dict(value)


def namespace_exited(value):
    value = validate_namespace_lifetime(value)
    # Read ONLY the already captured historic init's numeric start/state.
    # This never falls back to a credential or general proc reader. Permission
    # errors are unknown; only actual ENOENT/reuse/zombie can prove exit.
    try:
        fd = os.open(f"/proc/{value['init_pid']}/stat", os.O_RDONLY | os.O_CLOEXEC)
        try: raw = os.read(fd, 8193)
        finally: os.close(fd)
    except (FileNotFoundError, ProcessLookupError): return True
    require(len(raw) <= 8192 and raw.startswith(str(value["pid"]).encode() + b" ("), "native_init_stat_unknown")
    fields = raw.rsplit(b") ", 1)[1].split()
    require(len(fields) >= 20, "native_init_stat_unknown")
    return int(fields[19]) != value["start_ticks"] or fields[0] == b"Z"
