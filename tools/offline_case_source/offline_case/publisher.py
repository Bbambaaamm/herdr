"""Deterministic future source publisher for the single offline case.

Import and planning are read only. Publication requires a separately approved
root staging operation and refuses every occupied destination. It does not
activate policy, start units, issue authority, or run the SDK.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path


def _executable(name):
    # The extensionless entry chain must retain execute permission even when
    # the transport archive stores every member as 0444.
    return (name.startswith("agent-stack/bin/") or
            name.startswith("agent-stack/policy-bin/")) and Path(name).suffix == ""


def expected_modes(build):
    from .case import COMPOSED_CORE
    executable = {COMPOSED_CORE + "/" + name for name in build["core_files"]
                  if _executable(name)}
    executable.update(target for name, target in build["install_targets"].items()
                      if name == "overlays/agent-stack/bin/offline-case-host-entry")
    return {"data": 0o444, "executable": 0o555,
            "executable_targets": sorted(executable)}


def publication_entries(build, source_root):
    """Return the closed byte/mode/destination plan after source validation."""
    from .case import (INSTALL_ROOT, COMPOSED_CORE, pinned_bytes, require, sha,
                       validate_build, parse, BASELINE_INDEX)
    source_root = Path(source_root)
    from .case import canonical
    require(pinned_bytes(source_root / "integration-manifest.json", root_owned=True) == canonical(build),
            "published manifest differs from validated build")
    from .publication import verify_existing_runtime, render_host_unit
    from .admission import HOST_POLICY, HOST_UNIT
    policy = parse(pinned_bytes(HOST_POLICY, maximum=4194304, root_owned=True), 4194304)
    verify_existing_runtime(policy)
    require(pinned_bytes(source_root / "units" / HOST_UNIT, root_owned=True) == render_host_unit(policy),
            "freeze the exact existing-runtime host unit before publication")
    baseline = source_root / "accepted-source"
    validate_build(build, source_root, baseline=baseline, root_owned=True)
    index_raw = pinned_bytes(source_root / "accepted-source-index.json", root_owned=True)
    require(sha(index_raw) == BASELINE_INDEX, "accepted source index changed")
    from .runtime_inputs import checked_indices
    _, runtime_index = checked_indices(source_root, root_owned=True)
    modes = build["installed_modes"]
    executable = set(modes["executable_targets"])
    entries = {}

    def add(source, target, digest):
        target = Path(target)
        require(target.is_absolute() and ".." not in target.parts,
                "publication destination changed")
        raw = pinned_bytes(source, root_owned=True)
        require(sha(raw) == digest, "publication source changed")
        mode = modes["executable"] if str(target) in executable else modes["data"]
        old = entries.get(target)
        require(old is None or old[1:] == (digest, mode),
                "duplicate publication destination differs")
        entries[target] = (source, digest, mode)

    for name, digest in build["core_files"].items():
        add(source_root / "composed-core" / name, COMPOSED_CORE + "/" + name, digest)
    for name, digest in build["files"].items():
        add(source_root / name, build["install_targets"][name], digest)
        # Preserve the immutable source tree used by validate_build and root
        # metadata. Operational aliases (units/profiles) are additional copies.
        if build["install_targets"][name] != INSTALL_ROOT + "/" + name:
            add(source_root / name, INSTALL_ROOT + "/" + name, digest)
    for name, row in runtime_index["files"].items():
        add(baseline / name, INSTALL_ROOT + "/accepted-source/" + name, row["sha256"])
    for name, target in build["metadata_install_targets"].items():
        add(source_root / name, target, sha(pinned_bytes(source_root / name, root_owned=True)))
    from .native_source import NATIVE_RELATIVE, NATIVE_TARGET, NATIVE_SHA256, native_source_bytes
    native_source_bytes(source_root, root_owned=True)
    require(NATIVE_TARGET not in entries, "native publication target duplicated")
    entries[NATIVE_TARGET] = (source_root / NATIVE_RELATIVE, NATIVE_SHA256, 0o555)
    require(executable <= {str(path) for path in entries}, "executable source missing")
    return tuple((source, target, digest, mode)
                 for target, (source, digest, mode) in sorted(entries.items()))


def _parent_fd(path):
    """Create only missing root-owned ancestors, never follow an existing link."""
    from .case import require
    fd = os.open("/", os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        for component in path.parts[1:-1]:
            try:
                child = os.open(component, os.O_PATH | os.O_DIRECTORY |
                                os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            except FileNotFoundError:
                os.mkdir(component, 0o755, dir_fd=fd)
                os.chmod(component, 0o755, dir_fd=fd, follow_symlinks=False)
                child = os.open(component, os.O_PATH | os.O_DIRECTORY |
                                os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
            info = os.fstat(child)
            require(stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and
                    not info.st_mode & 0o022, "publication parent unsafe")
            os.close(fd); fd = child
        # fsync needs a readable descriptor; only this exact root-owned
        # destination directory is opened for read after traversal.
        final = os.open(".", os.O_RDONLY | os.O_DIRECTORY |
                        os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=fd)
        os.close(fd)
        return final
    except BaseException:
        os.close(fd)
        raise


def publish_source(build, source_root):
    """Root-only, no-replace source installation; never an execution grant.

    An interrupted copy leaves occupied destinations and requires manual
    reconciliation. This function never retries or overwrites partial data.
    """
    from .case import require, pinned_bytes, sha
    require(os.geteuid() == 0, "root source publisher required")
    entries = publication_entries(build, source_root)
    require(all(not os.path.lexists(target) for _, target, _, _ in entries),
            "publication destination already occupied")
    for source, target, digest, mode in entries:
        parent = _parent_fd(target)
        try:
            from .native_source import NATIVE_RELATIVE, NATIVE_TARGET, native_source_bytes
            raw = native_source_bytes(source_root, root_owned=True) if (source, target) == (Path(source_root) / NATIVE_RELATIVE, NATIVE_TARGET) else pinned_bytes(source, root_owned=True)
            require(sha(raw) == digest, "publication source changed before copy")
            fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         os.O_NOFOLLOW | os.O_CLOEXEC, 0o400, dir_fd=parent)
            try:
                require(os.write(fd, raw) == len(raw), "publication write uncertain")
                os.fchmod(fd, mode)
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(parent)
        finally:
            os.close(parent)
    for _, target, digest, mode in entries:
        item = target.lstat()
        require(stat.S_ISREG(item.st_mode) and item.st_uid == 0 and
                item.st_nlink == 1 and stat.S_IMODE(item.st_mode) == mode and
                sha(pinned_bytes(target, maximum=32_000_000, root_owned=True)) == digest,
                "installed source byte, owner, or executable mode changed")
    return len(entries)


def plan_owned_policy_retirement(build, authority, io):
    """Closed proposal for the EXISTING root publisher after all own units exit.

    This deliberately cannot run inside any profile it proposes to retire. It
    never unloads policy or deletes source. Actual outer deployment approval and
    activation are separate; CaseDriver.RETIRED means per-launch retirement only.
    """
    from .case import (require, canonical, sha, parse, pinned_bytes, NONCE, CASE,
                       OPERATOR, CLEANUP, TIMER, HOST_PROFILE, PROFILE, OBSERVER, PREP,
                       OPERATOR_PROFILE, INSTALL_ROOT)
    from .admission import HOST_UNIT
    require(os.geteuid() == 0 and io.read(Path("/proc/self/attr/current"), 256).strip() == b"unconfined",
            "existing outer root publisher required; own driver cannot finalize itself")
    require(authority["nonce"] == NONCE and authority["build_sha256"] == sha(canonical(build)) and
            io.read(Path("/proc/sys/kernel/random/boot_id"), 128).decode().strip() == authority["boot_id"],
            "foreign source deployment or boot")
    state = parse(pinned_bytes(Path("/var/lib/herdr-offline-03414499dd0d1986/state.json"), root_owned=True))
    require(state["phase"] == "RETIRED" and state["binding"]["authority_sha256"] == sha(canonical(authority)),
            "original per-launch retirement must precede outer policy proposal")
    from .outer_lifecycle import OuterLifecycle, read_consumed, verify_host_commands
    verify_host_commands()
    original, used, actual = read_consumed(build, read_boot=lambda:io.read(Path("/proc/sys/kernel/random/boot_id"),128).decode().strip())
    require(original == authority and actual["phase"] == "RETIRED", "immutable consumed original case marker changed")
    rows = ((PROFILE, "worker-profile.apparmor", "compiled_profile_sha256"),
            (PREP, "trusted-preparation.apparmor", "prep_compiled_sha256"),
            (OBSERVER, "observer-profile.apparmor", "observer_compiled_sha256"),
            (HOST_PROFILE, "host-profile.apparmor", "host_compiled_sha256"),
            (OPERATOR_PROFILE, "operator-profile.apparmor", "operator_compiled_sha256"))
    outer = OuterLifecycle(build, io)
    first = outer.observe(used);second = outer.observe(used)
    require(first == second and first["complete"] is True and first["fenced"] is True and first["holders"] == [] and
            all(row == {"owned":True,"populated":False,"tasks":[]} for row in first["groups"].values()),
            "complete stable thread/stack/cgroup absence required")
    units = tuple(first["groups"])
    commands = []
    for profile, filename, loaded in rows:
        source = Path("/etc/herdr") / filename
        require(sha(pinned_bytes(source, root_owned=True)) == build["files"]["overlays/" + filename] and
                io.loaded_profile_sha256(profile) == authority[loaded], "owned profile bytes/loaded identity changed")
        commands.append(["/usr/sbin/apparmor_parser", "-R", str(source)])
    return {"kind": "DATA_ONLY_OUTER_ORIGINAL_ROOT_PUBLISHER_RETIREMENT_PROPOSAL", "nonce": NONCE,
        "build_sha256": sha(canonical(build)), "units_confirmed_inactive": list(units),
        "holder_inventory_sha256": sha(canonical(first)), "commands": commands,
        "executed": False, "source_deletion": False}


def finalize_owned_policy(build, authority, io):
    """Existing outer root publisher extension, never a worker/driver endpoint.

    Mirrors original concrete_host.LinuxHost.unload_profile's fresh observation
    and absence checks, extending only the exact case profile set. The original
    RootCustody consumed attempt and source-bound authority remain mandatory.
    An outer reviewed expiry actor must call this AFTER owned lifetimes exit;
    the active operator cannot call it. No old nonce/two-unit authority is used.
    """
    from .case import require, canonical, sha
    from .custody import RootCustody
    root = Path("/var/lib/herdr-offline-03414499dd0d1986")
    with RootCustody(root) as custody:
        require(custody.authority() == authority and custody.consumed(authority["challenge"]) and
                custody.state()["phase"] == "RETIRED" and authority["purpose"] == "SINGLE_OFFLINE_PHYSICAL_CASE",
                "original consumed case approval required for outer retirement")
        proposal = plan_owned_policy_retirement(build, authority, io)
        # RootCustody O_EXCL/fsync publication occurs before any unload. A torn
        # outcome is retained and is never permission to resend the sequence.
        custody._publish("outer-policy-retirement-intent.json", proposal, exclusive=True)
        try:
            for index, command in enumerate(proposal["commands"], 1):
                for unit in proposal["units_confirmed_inactive"]:
                    require(io.run("/usr/bin/systemctl", "show", unit, "--property=ActiveState", "--value", timeout=10).strip()
                            == "inactive", "owned lifetime restarted before unload")
                from .outer_lifecycle import OuterLifecycle
                observation = OuterLifecycle(build, io).observe(custody.state()["binding"])
                require(observation["complete"] is True and observation["holders"] == [] and
                        all(not r["populated"] and r["tasks"] == [] for r in observation["groups"].values()),
                        "thread/stack holder appeared before unload")
                io.run(command[0], "--remove", "--skip-cache", command[2], timeout=30)
                label = {"worker-profile.apparmor": "herdr189-reference-lifetime",
                    "trusted-preparation.apparmor": "herdr-offline-prep-03414499dd0d1986",
                    "observer-profile.apparmor": "herdr-offline-observer-03414499dd0d1986",
                    "host-profile.apparmor": "herdr-offline-controller-03414499dd0d1986",
                    "operator-profile.apparmor": "herdr-offline-operator-03414499dd0d1986"}[Path(command[2]).name]
                lines = io.read(Path("/sys/kernel/security/apparmor/profiles"), 1048576).decode().splitlines()
                require(not any(line.startswith(label + " (") for line in lines), "own profile absence unconfirmed")
                after = OuterLifecycle(build, io).observe(custody.state()["binding"])
                require(after["complete"] is True and after["holders"] == [] and after["loaded"].get(label) is False,
                        "complete after-unload absence unconfirmed")
                custody._publish("outer-policy-retired-" + str(index) + ".json",
                    {"proposal_sha256": sha(canonical(proposal)), "profile": label}, exclusive=True)
            custody._publish("outer-policy-retirement-complete.json",
                {"proposal_sha256": sha(canonical(proposal)), "profiles": 5}, exclusive=True)
        except BaseException:
            custody._publish("outer-policy-retirement-unknown.json",
                {"proposal_sha256": sha(canonical(proposal)), "state": "RETAINED_UNKNOWN"}, exclusive=True)
            raise
        return {"profiles_retired": 5, "source_deleted": False}
