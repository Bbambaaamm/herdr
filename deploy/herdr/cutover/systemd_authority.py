"""Closed effective-systemd authority for the existing cutover transaction.

No commands from this module start services or execute the inspected programs.
Only the measured #126 RC6 exception may be reconciled, never arbitrary drop-ins.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import stat

from herdr.release import ReleaseError, canonical_json

WATCHDOG = "agent-stack-watchdog.service"
CAPACITY_DROPIN = "126-capacity-repair.conf"
CAPACITY_EXEC = "/opt/herdr/operations/capacity-repair-20261123/agent-stack-watchdog"
RC6 = "8d8ad50375557b7ac77348e6475cb455682f4a9a"
SOURCE_DROPINS = {
    "agent-platform-export.service": "09cba797e1a7e32f2d5d7552029fdba0a68af09adee28ced76c5cd9e9e784f5c",
    "agent-platform-herdr.service": "ff3151c4de83460048520673f0a7f5e7d637397d267bf7205f5b0155bf815153",
}
PROPERTIES = (
    "FragmentPath", "DropInPaths", "LoadState", "Transient", "NeedDaemonReload",
    "ExecStart", "ExecStartPre", "ExecStartPost", "ExecStop", "ExecStopPost",
    "ExecReload", "ExecCondition", "Environment", "EnvironmentFiles",
    "PassEnvironment", "UnsetEnvironment", "WorkingDirectory", "User", "Group",
    "RootDirectory", "RootImage", "PAMName", "ExecSearchPath",
)
COMMANDS = tuple(name for name in PROPERTIES if name.startswith("Exec") and name != "ExecSearchPath")


def need(ok, reason):
    if not ok:
        raise ReleaseError(reason)


def stamp(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def facts(path: Path):
    """Bounded no-follow reads; retain hashes/metadata, never operational content."""
    before = path.lstat()
    row = dict(uid=before.st_uid, gid=before.st_gid, mode=stat.S_IMODE(before.st_mode))
    if stat.S_ISLNK(before.st_mode):
        row["link"] = os.readlink(path)
    elif stat.S_ISDIR(before.st_mode):
        row["directory"] = True
    else:
        need(stat.S_ISREG(before.st_mode) and before.st_nlink == 1
             and before.st_size <= 32 * 1024**2, "unsafe_runtime_dependency")
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC)
        try:
            need(stamp(os.fstat(fd)) == stamp(before), "runtime_dependency_changed")
            digest, total = hashlib.sha256(), 0
            while chunk := os.read(fd, 65536):
                total += len(chunk)
                need(total <= before.st_size, "runtime_dependency_grew")
                digest.update(chunk)
            need(total == before.st_size and stamp(os.fstat(fd)) == stamp(before),
                 "runtime_dependency_changed")
            row["sha256"] = digest.hexdigest()
        finally:
            os.close(fd)
    need(stamp(path.lstat()) == stamp(before), "runtime_dependency_changed")
    return row


def safe_ancestors(path):
    for parent in path.parents:
        s = parent.lstat()
        need(stat.S_ISDIR(s.st_mode) and s.st_uid in (0, 1001)
             and not s.st_mode & 0o022, "unsafe_runtime_ancestor")


def inventory(root, *, observations=None, content_observations=None):
    safe_ancestors(root)
    paths = [root]
    for path in root.rglob("*"):
        need(len(paths) < 1024, "runtime_inventory_limit")
        paths.append(path)
    identities = {p: stamp(p.lstat()) for p in paths}
    if observations is not None:
        observations.update(identities)
    rows = {}
    for path in paths:
        row = facts(path)
        # The two explicitly approved historical source trees have no symlinks.
        need("link" not in row and not row["mode"] & 0o022, "unsafe_runtime_tree")
        rows[path.relative_to(root).as_posix()] = row
        if content_observations is not None:
            content_observations[path] = row
    checked = {root}
    for path in root.rglob("*"):
        need(len(checked) < 1024, "runtime_inventory_limit")
        checked.add(path)
    need(set(paths) == checked
         and all(stamp(p.lstat()) == value for p, value in identities.items()),
         "runtime_inventory_changed")
    # Coarse filesystem timestamp ticks can hide a same-size rewrite between
    # two lstat calls. Re-read bounded content, not only inode timestamps, when
    # closing the inventory. This does not authorize later runtime mutation.
    need(all(facts(p) == rows[p.relative_to(root).as_posix()] for p in paths),
         "runtime_inventory_changed")
    need(all(stamp(p.lstat()) == value for p, value in identities.items()),
         "runtime_inventory_changed")
    safe_ancestors(root)
    return {"entries": len(rows), "sha256": hashlib.sha256(canonical_json(rows)).hexdigest()}


def unit_directives(path):
    from deploy.herdr.cutover.transaction_contract import bounded_read, FILE_MAX
    result, section = {}, ""
    for line in bounded_read(path, FILE_MAX)[0].decode("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if line.startswith("["):
            section = line
        elif section == "[Service]" and "=" in line:
            key, value = line.split("=", 1)
            if not value:
                result[key] = []
            else:
                result.setdefault(key, []).append(value)
    return result


def commands(value):
    if not value:
        return []
    records = re.findall(r"\{ path=([^;]+) ; argv\[\]=([^;]+) ; ignore_errors=([^;]+) ;[^}]*\}", value)
    need(records and len(records) == value.count("{ path=")
         and value.count("}") == len(records), "invalid_effective_command")
    result = []
    for path, argv, ignored in records:
        args = shlex.split(argv.strip())
        need(args and path.strip() == args[0] and ignored.strip() == "no",
             "unsafe_effective_command")
        result.append(args)
    return result


class SystemdAuthority:
    def __init__(self, api, *, unit_search_roots=None):
        self.api = api
        self.units = api["UNITS"]
        self.unit_dir = api["UNIT_DIR"]
        self.dropin = self.unit_dir / (WATCHDOG + ".d") / CAPACITY_DROPIN
        self.search_roots = tuple(unit_search_roots) if unit_search_roots is not None else (
            self.unit_dir, Path("/run/systemd/system"),
            Path("/usr/local/lib/systemd/system"), Path("/usr/lib/systemd/system"))
        self.observed = {}
        self.contents = {}
        self.absent = set()
        self.policy_path = api.get("HOST_POLICY_PATH", Path("/etc/herdr/host-policy.json"))

    def observe(self, path):
        value = stamp(path.lstat())
        need(path not in self.observed or self.observed[path] == value, "authority_changed_during_capture")
        self.observed[path] = value
        row = facts(path)
        need(path not in self.contents or self.contents[path] == row,
             "authority_changed_during_capture")
        self.contents[path] = row
        return row

    def verify_observations(self):
        need(all(facts(path) == value for path, value in self.contents.items()),
             "authority_changed_during_capture")
        need(all(stamp(path.lstat()) == value for path, value in self.observed.items()),
             "authority_changed_during_capture")
        need(all(not os.path.lexists(path) for path in self.absent),
             "authority_appeared_during_capture")

    def approved_dependencies(self):
        descriptor = json.loads((self.api["ROOT"] / "deploy/herdr/cutover/capacity-repair-authority.json").read_bytes())
        identities = {name: stamp(Path(name).lstat()) for name in descriptor["files"]}
        for name, expected in descriptor["files"].items():
            path = Path(name)
            safe_ancestors(path)
            need(self.observe(path) == expected, "capacity_dependency_drift:" + name)
            if "link" in expected:
                need(str(path.resolve(strict=True)) == expected["link"], "capacity_symlink_drift")
        for name, expected in descriptor["trees"].items():
            need(inventory(Path(name), observations=self.observed,
                           content_observations=self.contents) == expected,
                 "capacity_runtime_tree_drift:" + name)
        need(all(stamp(Path(name).lstat()) == value for name, value in identities.items()),
             "capacity_dependency_changed")
        self.verify_observations()
        return descriptor

    def external_dependencies(self):
        descriptor = json.loads((self.api["ROOT"] / "deploy/herdr/cutover/external-runtime-authority.json").read_bytes())
        identities = {name: stamp(Path(name).lstat()) for name in descriptor}
        for name, expected in descriptor.items():
            safe_ancestors(Path(name))
            need(self.observe(Path(name)) == expected, "external_runtime_drift:" + name)
        need(all(stamp(Path(name).lstat()) == value for name, value in identities.items()),
             "external_runtime_changed")
        self.verify_observations()
        return descriptor

    def capture(self, *, allow_capacity=True, allow_fence=False):
        self.observed = {}
        self.contents = {}
        self.absent = set()
        permit = self.api["watchdog_permit_path"]()
        present = os.path.lexists(permit)
        need(allow_fence or not present,
             "orphan_watchdog_start_permit")
        if not present:
            self.absent.add(permit)
        rows, drops = {}, {}
        capacity = os.path.lexists(self.dropin)
        if capacity:
            need(allow_capacity and self.api["verify_tree"](self.api["CURRENT"].resolve())["commit"] == RC6,
                 "capacity_override_wrong_baseline")
            dependencies = self.approved_dependencies()
        else:
            dependencies = None
        for unit in self.units:
            text = self.api["run"]("/usr/bin/systemctl", "show", unit,
                                   "--property=" + ",".join(PROPERTIES))
            loaded = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
            need(loaded.get("FragmentPath") == str(self.unit_dir / unit)
                 and loaded.get("LoadState") == "loaded"
                 and loaded.get("Transient") == "no"
                 and loaded.get("NeedDaemonReload") == "no", "unsafe_effective_unit:" + unit)
            approved = {}
            if unit in SOURCE_DROPINS:
                path = self.unit_dir / (unit + ".d") / "sources.conf"
                row = self.observe(path)
                need(row == dict(uid=0, gid=0, mode=0o644, sha256=SOURCE_DROPINS[unit]),
                     "source_dropin_drift:" + unit)
                approved[str(path)] = row
            if unit == WATCHDOG and capacity:
                approved[str(self.dropin)] = self.observe(self.dropin)
            fence = self.api["watchdog_fence_path"]()
            if unit == WATCHDOG and os.path.lexists(fence):
                need(allow_fence, "unfinished_watchdog_fence")
                row = self.observe(fence)
                need(row == dict(uid=0, gid=0, mode=0o644,
                    sha256=hashlib.sha256(self.api["watchdog_fence_bytes"]()).hexdigest()),
                    "watchdog_fence_drift")
                need((self.api["STATE_DIR"] / "transaction.json").is_file(), "watchdog_fence_without_journal")
                approved[str(fence)] = row
            need(set(shlex.split(loaded.get("DropInPaths", ""))) == set(approved),
                 "unknown_effective_dropin:" + unit)
            # Detect pending/unloaded, shadowed and /run overrides as well.
            stem, kind = unit.rsplit(".", 1)
            folders = {unit + ".d", kind + ".d"}
            for index, char in enumerate(stem):
                if char == "-":
                    folders.add(stem[:index + 1] + "." + kind + ".d")
            for prefix in self.search_roots:
                for name in folders:
                    folder = prefix / name
                    if not os.path.lexists(folder):
                        self.absent.add(folder)
                        continue
                    safe_ancestors(folder)
                    directory = self.observe(folder)
                    need(directory.get("directory") is True and directory["uid"] == 0
                         and not directory["mode"] & 0o022, "unsafe_dropin_directory")
                    # systemd only loads *.conf; backups such as sources.conf.tmp
                    # are not activation authority and are never removed here.
                    need(all(str(p) in approved for p in folder.glob("*.conf")),
                         "unknown_disk_dropin:" + unit)
            base = self.unit_dir / unit
            need(self.observe(base)["uid"] == 0 and not base.lstat().st_mode & 0o022,
                 "unsafe_unit_fragment")
            directives = unit_directives(base)
            normalized = {}
            for key in COMMANDS:
                expected = [shlex.split(x) for x in directives.get(key, [])]
                if unit == WATCHDOG and key == "ExecStart" and capacity:
                    expected = [[CAPACITY_EXEC]]
                normalized[key] = commands(loaded.get(key, ""))
                need(normalized[key] == expected, "effective_command_drift:" + unit + ":" + key)
            for key in ("WorkingDirectory", "User", "Group"):
                normalized[key] = loaded.get(key, "")
                need(normalized[key] == "".join(directives.get(key, [])), "effective_property_drift:" + key)
            normalized["Environment"] = sorted(shlex.split(loaded.get("Environment", "")))
            need(normalized["Environment"] == sorted(
                item for line in directives.get("Environment", []) for item in shlex.split(line)),
                "effective_environment_drift")
            for key in ("EnvironmentFiles", "PassEnvironment", "UnsetEnvironment", "RootDirectory",
                        "RootImage", "PAMName", "ExecSearchPath"):
                need(not loaded.get(key), "unexpected_effective_property:" + key)
            normalized["fragment"] = self.observe(base)
            normalized["dropins"] = {k: v for k, v in approved.items() if k != str(fence)}
            rows[unit] = normalized
            drops.update(approved)
        policy = self.observe(self.policy_path)
        need(policy["uid"] == 0 and not policy["mode"] & 0o022, "unsafe_host_policy")
        external = self.external_dependencies()
        self.verify_observations()
        return dict(version=1, mode="capacity_rc6" if capacity else "standard",
                    units=rows, dependencies=dependencies, host_policy=policy,
                    external_runtimes=external)

    def verify(self, authority, *, allow_fence=False):
        need(self.capture(allow_fence=allow_fence) == authority, "effective_systemd_authority_changed")

    def reconcile(self, authority, *, fenced=False):
        self.verify(authority, allow_fence=fenced)
        self.api["ensure_watchdog_fence"]()
        self.verify(authority, allow_fence=True)
        if authority["mode"] == "capacity_rc6":
            self.api["remove_regular_file"](self.dropin)
            self.api["run"]("/usr/bin/systemctl", "daemon-reload")
        candidate = self.capture(allow_capacity=False, allow_fence=True)
        need(candidate["host_policy"] == authority["host_policy"], "host_policy_changed")
        return candidate

    def restore_check(self, authority):
        self.verify(authority)


def verify_release_runtime(root):
    """Require the reviewed #126 maintenance and release-relative dispatch closure."""
    pins = {
        "agent-stack-watchdog": "826be65434c24755f738d002a74cd40e3cd6be37258feb72927dcae6960654cc",
        "hermes-maintenance": "cfee75d96071891deecfa01176f52515019086c34ae5a7e8d2c44949c0a11a9a",
    }
    binary = root / "agent-stack/bin"
    for name, digest in pins.items():
        need(facts(binary / name).get("sha256") == digest, "candidate_capacity_contract_drift:" + name)
    # These approved scripts derive BIN/WORKER from their own immutable __file__.
    for name in ("agent-stack-ensure", "agent-stack-recovery", "agent-task-dispatcher",
                 "agent-task-worker", "agent-durable-bridge", "agent-github-intake"):
        path = binary / name
        row = facts(path)
        need(row["uid"] == 0 and not row["mode"] & 0o022 and "sha256" in row,
             "unsafe_candidate_runtime:" + name)
