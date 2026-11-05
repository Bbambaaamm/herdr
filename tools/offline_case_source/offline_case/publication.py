"""Deterministic prospective publication using an EXISTING approved runtime.

No downloader/installer/SDK execution or activation exists here. Source freeze
must call render_host_unit with the exact reviewed protected host policy, then
hash the returned bytes as the final unit. Missing runtime selection denies.
The original immutable entrypoint independently freezes BOTH full inventories.
"""
from pathlib import PurePosixPath
from .case import HOST_PROFILE, require, canonical, sha
from .admission import HOST_UNIT, HOST_ENTRY, HOST_TARGET
OPERATOR_PROFILE = "herdr-offline-operator-03414499dd0d1986"

PYTHON_TARGET = "/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu"
PYTHON_EXECUTABLE = "bin/python3.11"


def existing_runtime(policy):
    require(type(policy) is dict and policy.get("schema_version") == 2 and policy.get("host_uid") == 1001
        and type(policy.get("runtime")) is list and len(policy["runtime"]) == 2,
        "original protected private runtime selection required")
    matches = [row for row in policy["runtime"] if row.get("target") == PYTHON_TARGET]
    require(len(matches) == 1, "one original CP311 runtime required")
    row = matches[0]
    require(set(row) == {"source", "target", "files", "executable_files", "max_bytes", "max_file_bytes"}
        and type(row["files"]) is dict and PYTHON_EXECUTABLE in row["files"]
        and PYTHON_EXECUTABLE in row["executable_files"], "complete approved CP311 inventory required")
    source = PurePosixPath(row["source"])
    require(source.is_absolute() and ".." not in source.parts and str(source) == row["source"]
        and str(source).startswith("/opt/") and all(c.isalnum() or c in "/_.:-" for c in str(source)),
        "existing immutable CP311 installation required")
    digest = row["files"][PYTHON_EXECUTABLE]
    require(type(digest) is str and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest),
            "existing interpreter digest unavailable")
    return {"executable": str(source / PYTHON_EXECUTABLE), "executable_sha256": digest,
            "runtime_inventory_sha256": sha(canonical(row))}


def render_host_unit(policy):
    selected = existing_runtime(policy)
    command = " ".join((selected["executable"], "-I", "-B", HOST_ENTRY.as_posix(), HOST_TARGET))
    return ("[Unit]\nDescription=Finite canonical offline host\n"
        "Before=herdr-offline-operator-03414499dd0d1986.service\n"
        "[Service]\nType=exec\nUser=1001\nGroup=1001\n"
        "AppArmorProfile=" + HOST_PROFILE + "\nExecStart=" + command + "\n"
        "RuntimeMaxSec=1800\nTimeoutStopSec=30\nRestart=no\nDelegate=no\nKillMode=control-group\n"
        "CapabilityBoundingSet=\nAmbientCapabilities=\nNoNewPrivileges=yes\n"
        "RestrictAddressFamilies=AF_UNIX\nUMask=0077\n"
        "RuntimeDirectory=herdr-offline-host-03414499dd0d1986\nRuntimeDirectoryMode=0750\n"
        "StandardInput=null\nStandardOutput=null\nStandardError=null\n").encode()


def verify_existing_runtime(policy):
    """Original immutable inventory verifier, read-only attachment then close."""
    from herdr.host_configuration import _tree
    selected = existing_runtime(policy)
    roots = tuple(row["workspace_root"] for row in policy["templates"].values())
    for row in policy["runtime"]:
        tree = _tree(row, immutable=True).freeze(None, roots)
        tree.close()  # Closes held descriptors; never deletes an installed tree.
    return selected


def source_runtime_outputs(policy):
    """Pure source build result; integration freezes these exact final bytes."""
    selected = existing_runtime(policy)
    return {"runtime-binding.json": canonical({"schema": "existing-approved-runtime-1",
                "host_policy_sha256": sha(canonical(policy)), **selected}),
            "units/" + HOST_UNIT: render_host_unit(policy),
            "overlays/operator-profile.apparmor": render_operator_profile(policy),
            "units/herdr-offline-operator-03414499dd0d1986.service": render_operator_unit(cleanup=False),
            "units/herdr-offline-cleanup-03414499dd0d1986.service": render_operator_unit(cleanup=True)}


def render_operator_unit(*, cleanup):
    action = "--cleanup" if cleanup else "--execute"
    command = "/usr/bin/python3.14 -I -B -c 'import sys; sys.path.insert(0,\"/opt/agent-platform/herdr-offline-03414499dd0d1986\"); from offline_case.driver import main; main([\"" + action + "\"])'"
    return ("[Unit]\nDescription=Finite offline root " + ("cleanup" if cleanup else "operator") +
        "\nRequires=herdr-offline-cleanup-03414499dd0d1986.timer\nAfter=herdr-offline-cleanup-03414499dd0d1986.timer"
        "\n[Service]\nType=oneshot\nUser=root\nGroup=root\nAppArmorProfile=" + OPERATOR_PROFILE +
        "\nRuntimeMaxSec=1800\nTimeoutStartSec=1800\nTimeoutStopSec=30\nRestart=no\nDelegate=no\n"
        "KillMode=control-group\nCapabilityBoundingSet=CAP_SYS_PTRACE CAP_DAC_READ_SEARCH CAP_CHOWN\n"
        "AmbientCapabilities=\nNoNewPrivileges=yes\nRestrictNamespaces=yes\nPrivateNetwork=yes\n"
        "PrivateDevices=yes\nPrivateTmp=yes\nProtectSystem=strict\nProtectHome=read-only\n"
        "ReadWritePaths=/var/lib/herdr-offline-03414499dd0d1986 "
        "/var/lib/herdr-offline-observer-03414499dd0d1986/contexts "
        "/etc/herdr/offline-03414499dd0d1986 /run/systemd/system "
        "-/sys/fs/cgroup/system.slice/herdr-offline-03414499dd0d1986.service "
        "-/sys/fs/cgroup/system.slice/herdr-offline-root-03414499dd0d1986.service "
        "-/sys/fs/cgroup/system.slice/herdr-offline-child-03414499dd0d1986.service\n"
        "SystemCallArchitectures=native\nExecStart=" + command + "\n").encode()


def render_operator_profile(policy):
    existing_runtime(policy)
    roots = []
    for row in policy["runtime"]:
        source = PurePosixPath(row["source"])
        require(source.is_absolute() and str(source).startswith("/opt/") and ".." not in source.parts and
                all(c.isalnum() or c in "/_.:-" for c in str(source)), "exact operator runtime root required")
        roots += ["  " + str(source) + "/ r,", "  " + str(source) + "/** mr,"]
    prefix = "/opt/agent-platform/herdr-offline-03414499dd0d1986"
    lines = ["#include <tunables/global>", "profile " + OPERATOR_PROFILE + " flags=(attach_disconnected) {",
        "  #include <abstractions/base>", "  capability sys_ptrace,", "  capability dac_read_search,", "  capability chown,",
        "  network unix stream,", "  deny capability sys_admin,", "  deny mount,", "  deny userns,",
        "  ptrace (read) peer=**,",
        "  deny change_profile,", "  /usr/bin/python3.14 rix,", "  /usr/bin/systemctl rix,\n  /usr/bin/systemd-run rix,",
        "  /usr/lib/python3.14/ r,", "  /usr/lib/python3.14/** r,",
        "  /usr/lib/x86_64-linux-gnu/** mr,", "  /lib/x86_64-linux-gnu/** mr,",
        "  /run/systemd/private rw,", "  /run/dbus/system_bus_socket rw,",
        "  /proc/ r,", "  /proc/[0-9]*/ r,", "  /proc/[0-9]*/{stat,status,cgroup,maps,mountinfo} r,",
        "  /proc/[0-9]*/{attr/current,exe,cmdline,environ} r,", "  /proc/[0-9]*/fd/ r,", "  /proc/[0-9]*/fd/* r,",
        "  /proc/[0-9]*/ns/{pid,mnt,net,user} r,", "  /proc/sys/kernel/random/boot_id r,",
        "  /proc/self/ r,", "  /proc/self/{stat,status,cgroup,cmdline,mountinfo} r,",
        "  /proc/self/attr/current r,", "  /proc/self/fd/ r,", "  /proc/self/fd/* r,",
        "  /sys/kernel/security/apparmor/profiles r,",
        "  /sys/kernel/security/apparmor/policy/profiles/ r,",
        "  /sys/kernel/security/apparmor/policy/profiles/*/ r,",
        "  /sys/kernel/security/apparmor/policy/profiles/*/{name,raw_data} r,",
        "  " + prefix + "/ r,", "  " + prefix + "/offline_case/ r,", "  " + prefix + "/offline_case/** r,",
        "  " + prefix + "/composed-core/ r,", "  " + prefix + "/composed-core/** r,", "  " + prefix + "/composed-core/herdr/ r,",
        "  " + prefix + "/composed-core/herdr/** r,", "  " + prefix + "/composed-core/agent-stack/bin/ r,",
        "  " + prefix + "/composed-core/agent-stack/bin/** r,", "  " + prefix + "/native/ r,",
        "  " + prefix + "/native/** r,", "  " + prefix + "/observer/ r,", "  " + prefix + "/observer/** r,",
        "  " + prefix + "/accepted-source/ r,", "  " + prefix + "/accepted-source/** r,",
        "  " + prefix + "/{*.json,core_bridge.py} r,", "  " + prefix + "/overlays/ r,",
        "  " + prefix + "/overlays/** r,", "  " + prefix + "/units/ r,", "  " + prefix + "/units/* r,",
        "  /etc/herdr/ r,", "  /etc/herdr/*.json r,", "  /etc/herdr/*.apparmor r,",
        "  /etc/herdr/offline-03414499dd0d1986/ r,", "  /etc/herdr/offline-03414499dd0d1986/* r,",
        "  /etc/herdr/offline-03414499dd0d1986/roster.json w,",
        "  /etc/herdr/launch-plans/ r,", "  /etc/herdr/launch-plans/*.json r,",
        "  /etc/systemd/system/herdr-offline*-03414499dd0d1986.* r,",
        "  /run/systemd/system/ r,", "  /run/systemd/system/herdr-offline-{root,child,observer}-03414499dd0d1986.service rw,",
        "  /run/herdr-offline-host-03414499dd0d1986/control.sock rw,",
        "  /var/lib/herdr-offline-03414499dd0d1986/ rw,", "  /var/lib/herdr-offline-03414499dd0d1986/* rwk,",
        "  /var/lib/herdr-offline-observer-03414499dd0d1986/contexts/ rw,",
        "  /var/lib/herdr-offline-observer-03414499dd0d1986/contexts/*.json r,",
        "  /var/lib/herdr-offline-observer-03414499dd0d1986/contexts/{case-phase,.phase-*,effect-*,root-roster,root-unit,child-unit,case-unit,closure,historical-observation,expiry-intent,expiry-armed,scope-fenced,observer-control-unit,root-startup-source,child-parent-startup-source}.json rw,",
        "  /var/lib/herdr-offline-observer-03414499dd0d1986/contexts/.phase-[0-9]* rw,",
        "  /var/lib/herdr-offline-observer-03414499dd0d1986/contexts/caller-[0-9]*.json rw,",
        "  /sys/fs/cgroup/system.slice/herdr-offline*-03414499dd0d1986.service/ r,",
        "  /sys/fs/cgroup/system.slice/herdr-offline*-03414499dd0d1986.service/{cgroup.procs,cgroup.events} r,",
        "  /sys/fs/cgroup/system.slice/herdr-offline*-03414499dd0d1986.service/cgroup.kill w,",
        *roots, "}"]
    return ("\n".join(lines) + "\n").encode()


def render_native_layout(policy, files, authority):
    """Exact data proposal for ORIGINAL root approval; no signer or publication.

    Existing loaded-profile measurements must come from the separately approved
    case authority. This function cannot invent them or accept a test boolean.
    """
    selected = existing_runtime(policy)
    base = "/opt/agent-platform/herdr-offline-03414499dd0d1986"
    helpers = {}
    for role, directory, profile, source, entry, measurement in (
        ("observer", "observer", "herdr-offline-observer-03414499dd0d1986", "observer-profile.apparmor", "observer_entry.py", "observer_compiled_sha256"),
        ("preparer", "native", "herdr-offline-prep-03414499dd0d1986", "trusted-preparation.apparmor", "prep_entry.py", "prep_compiled_sha256")):
        names = {name.removeprefix(directory + "/"): value for name, value in files.items()
                 if name.startswith(directory + "/") and name.endswith(".py")}
        require(entry in names and 1 <= len(names) <= 16 and type(authority.get(measurement)) is str
                and len(authority[measurement]) == 64, "original helper source/measurement required")
        helpers[role] = {"profile": profile, "source_sha256": files["overlays/" + source],
            "loaded_sha256": authority[measurement], "entrypoint": base + "/" + directory + "/" + entry,
            "files": names, "python": selected["executable"], "python_sha256": selected["executable_sha256"]}
    from .native_source import NATIVE_SHA256
    return {"schema": "canonical-offline-native-layout-1", **helpers,
        "controller_source_sha256": files["overlays/host-profile.apparmor"], "native_sha256": NATIVE_SHA256}


def propose_sdk_profile_inputs(approved, config_raw, sdk_policy_raw):
    """Pure unissued update through ORIGINAL profile/projection hash algorithms.

    No profile, policy or installed SDK is changed. The resulting identity must
    receive a new approval from the existing authority before any execution.
    """
    from herdr.policy_launch import ApprovedProfile
    from herdr.private_profile_namespace import profile_identity, private_sdk_policy
    from dataclasses import asdict
    from .case import parse
    require(isinstance(approved, ApprovedProfile) and
            sha(config_raw) == approved.files['config.yaml'] and
            sha(sdk_policy_raw) == approved.files['herdr-sdk-policy.json'] and
            approved.files['.env'] == sha(b''), 'original empty credentialless profile input required')
    config = parse(config_raw)
    require(type(config.get('model')) is dict and config['model'].get('provider') == 'nous',
            'original protected Nous readiness route required')
    config['updates'] = {**config.get('updates', {}), 'check': False}
    config['display'] = {**config.get('display', {}), 'interface': 'classic'}
    new_config = canonical(config)
    files = dict(approved.files); files['config.yaml'] = sha(new_config)
    proposed = profile_identity(approved.name, files)
    policy = private_sdk_policy(proposed, sdk_policy_raw, new_config, credentialless=True)
    return {'status': 'DATA_ONLY_UNISSUED_PROFILE_UPDATE', 'config.yaml': new_config,
        'previous_profile': approved.identity, 'proposed_profile': proposed,
        'private_sdk_projection': asdict(policy), 'approval_required': True,
        'installed_SDK_changed': False}
