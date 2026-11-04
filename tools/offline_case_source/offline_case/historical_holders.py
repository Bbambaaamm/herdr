"""Root-only historical scope and complete holder observation after fencing.

This does not call live observer admission or reissue an expired grant. All
scope derives from the root-owned original custody context and exact unit
receipt. Missing/inaccessible/changing metadata raises: UNKNOWN stays retained.
"""
from pathlib import Path
import os
import re
import stat

from .case import CASE, NONCE, require, sha, canonical

SUFFIX = NONCE[:16]


def observe_closed(binding, roster, namespaces, io, read_metadata):
    require(type(roster) is list and len(roster) <= 2 and type(namespaces) is dict and
            set(namespaces) == {"root", "child"}, "closed historical role inventory required")
    boot = io.read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip()
    require(boot == binding["boot_id"], "historic boot changed")
    roles, namespace_ids, private_paths = set(), set(), set()
    unit_names = {CASE}
    allowed_custodians = set()
    for row in roster:
        role = row["role"]
        require(role in {"root", "child"} and role not in roles and row["binding"] == binding,
                "foreign or duplicate historical role")
        roles.add(role)
        context = read_metadata(role)
        runtime = read_metadata(role + ".runtime")
        unit = "herdr-offline-" + role + "-" + SUFFIX + ".service"
        unit_names.add(unit)
        if runtime is None:
            require(context is None and row["sandbox_pid"] is None and namespaces[role] is None,
                    "partial native custody is unknown")
            # Original command/plan never delivered to a started root process.
            require(io.run("/usr/bin/systemctl", "show", unit, "--property=ActiveState", "--value",
                           timeout=10).strip() == "inactive", "unbound role may still be active")
            continue
        require(context is not None and context["identity"] == row["identity"] and
            context["grant_sha256"] == row["prepared_grant_sha256"] and context["plan_sha256"] == row["plan_sha256"] and
            runtime["context_sha256"] == sha(canonical(context)) and runtime["unit"] == unit,
            "historic custody context changed")
        owned = read_metadata(role + "-unit")
        require(owned is not None and owned["binding"] == binding and
            owned["value"]["runtime"] == runtime and owned["value"]["cgroup"] == context["cgroup_identity"],
            "original stable role unit receipt missing")
        group = Path("/sys/fs/cgroup/system.slice") / unit
        if io.exists(group):
            require(tuple(context["cgroup_identity"]) == io.identity(group), "historical role cgroup replaced")
            require(io.read(group / "cgroup.procs", 65536).strip() == b"" and
                io.read(group / "cgroup.events", 4096).splitlines().count(b"populated 0") == 1,
                "role cgroup not empty")
        proof = namespaces[role]
        require(type(proof) is dict and proof["pid"] == runtime["pid"] and
            proof["start_ticks"] == runtime["start_ticks"] and
            proof["namespace"] == runtime["namespace"] and
            proof["context_sha256"] == sha(canonical(context)), "captured namespace lifetime changed")
        namespace_ids.add(runtime["namespace"])
        # Root-owned context captures original source descriptors. Scope private
        # per-launch directories only; public immutable runtime/source trees do
        # not become forever-held merely because the trusted host reads them.
        for entry in context["plan"]["descriptors"]:
            source = entry["source"]
            match = re.fullmatch(r"/proc/([1-9][0-9]*)/fd/([0-9]+)", source)
            require(match is not None, "original source descriptor spelling changed")
            allowed_custodians.add((int(match[1]), context["original_peer"][3]))
            if entry["kind"] in {"reserved-result", "sealed-profile-data", "sealed-resolver-data", "socket"}:
                private_paths.add(entry["target"])
        private_paths.add("/run/herdr-policy")
        private_paths.add("/run/herdr-bootstrap")

    case_group = Path("/sys/fs/cgroup/system.slice") / CASE
    case_receipt = read_metadata("case-unit")
    if io.exists(case_group):
        require(case_receipt is not None and case_receipt["binding"] == binding and
            tuple(case_receipt["value"]["cgroup"]) == io.identity(case_group), "case group not original")
        require(io.read(case_group / "cgroup.procs", 65536).strip() == b"" and
            io.read(case_group / "cgroup.events", 4096).splitlines().count(b"populated 0") == 1,
            "original case cgroup not empty")

    def scan():
        with os.scandir("/proc") as entries:
            pids = sorted(int(entry.name) for entry in entries if entry.name.isdecimal())
        require(len(pids) <= 8192, "global holder inventory bound exceeded")
        holders, identities = [], []
        for pid in pids:
            base = Path("/proc") / str(pid)
            before = io.process_start_ticks(pid)
            group = io.read(base / "cgroup", 65536).decode().splitlines()
            label = io.read(base / "attr/current", 4096).strip()
            namespace = os.readlink(base / "ns/pid")
            maps = io.read(base / "maps", 8388608)
            mounts = io.read(base / "mountinfo", 8388608)
            links = []
            with os.scandir(base / "fd") as entries:
                for count, fd in enumerate(entries, 1):
                    require(count <= 4096, "global descriptor inventory bound exceeded")
                    # Read while the iterator is alive. For the scanner's own
                    # PID its uniquely owned enumeration FD is then still open;
                    # it names public /proc/PID/fd, never a private case object.
                    # No ENOENT is ignored for this or any foreign descriptor.
                    value = os.readlink(fd.path)
                    os.stat(fd.path)
                    links.append(value)
            after = io.process_start_ticks(pid)
            require(before == after and before > 0, "holder PID changed during scan")
            identities.append((pid, before))
            trusted_custodian = (pid, before) in allowed_custodians
            owns_unit = any(line == "0::/system.slice/" + unit for line in group for unit in unit_names)
            keeps_namespace = namespace in namespace_ids or any(link in namespace_ids for link in links)
            private_reference = any(name.encode() in value for name in private_paths for value in (maps, mounts))
            private_fd = any(link == name or link.startswith(name.rstrip("/") + "/")
                             for link in links for name in private_paths)
            if owns_unit or keeps_namespace or label == b"herdr189-reference-lifetime (enforce)" or (
                    not trusted_custodian and (private_reference or private_fd)):
                holders.append((pid, before))
        return tuple(identities), tuple(holders)

    first, second = scan(), scan()
    require(first == second and not first[1], "incomplete, changing or held private namespace inventory")
    observation = {"fenced": True, "case_cgroup_empty": True, "descendants": [],
        "fds": [], "maps": [], "profile_holders": [], "complete": True, "boot_id": boot}
    return {"roster_sha256": sha(canonical(roster)), "namespaces": namespaces, "observation": observation,
            "process_inventory_sha256": sha(canonical(first[0]))}
