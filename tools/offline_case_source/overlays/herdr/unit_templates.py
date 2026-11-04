"""Deterministic exact own-unit source templates; never invokes systemd."""
from .case_roster import SUFFIX, Roster, require
from .preparation_contract import native_argv


def word(value):
    # Paths in this source contract use no systemd expansion/whitespace. No
    # shell, environment substitution, specifiers or injected extra arguments.
    require(type(value) is str and value and all(c.isalnum() or c in "/_.:-" for c in value),
            "literal_systemd_word_required")
    return value


def render_units(roster):
    require(isinstance(roster, Roster), "typed_root_roster_required")
    doc = roster.document
    controller_unit = word(doc["controller"]["cgroup"].split("/")[-1])
    outputs = {}
    for role in roster.roles:
        slot = roster.slot(role)
        target = word(slot["stdio"]["0"]["path"])
        require(all(slot["stdio"][n]["path"] == target for n in ("0", "1", "2")), "one_owned_terminal_required")
        streams = ("StandardInput=null\nStandardOutput=null\nStandardError=null\n" if target == "/dev/null" else
            "StandardInput=tty\nStandardOutput=tty\nStandardError=tty\nTTYPath=" + target +
            "\nTTYReset=no\nTTYVHangup=no\nTTYVTDisallocate=no\n")
        command = " ".join(word(x) for x in native_argv(roster, role))
        outputs[slot["unit"]] = ("[Unit]\nDescription=Owned offline " + role + " preparation\n"
            "BindsTo=" + controller_unit + " herdr-offline-observer-" + SUFFIX + ".service\nAfter=" + controller_unit +
            " herdr-offline-observer-" + SUFFIX + ".service\nRequires=herdr-offline-observer-" + SUFFIX + ".service\n"
            "PartOf=herdr-offline-" + SUFFIX + ".service\nConditionPathExists=!/var/lib/herdr-offline-observer-" + SUFFIX + "/contexts/scope-fenced.json\n[Service]\nType=exec\nUser=root\nGroup=root\nSupplementaryGroups=1001\n"
            "ExecStart=" + command + "\nAppArmorProfile=" + doc["preparer"]["profile"] +
            "\nCapabilityBoundingSet=CAP_SYS_ADMIN CAP_SETUID CAP_SETGID CAP_SETPCAP CAP_MKNOD CAP_KILL\n"
            "AmbientCapabilities=\nNoNewPrivileges=no\nUMask=0077\nKillMode=control-group\n"
            "RuntimeMaxSec=1800\nTimeoutStartSec=45\nTimeoutStopSec=15\nSendSIGKILL=yes\n"
            "Restart=no\nDelegate=no\n" + streams)
    helper = doc["observer"]
    name = "herdr-offline-observer-" + SUFFIX + ".service"
    outputs[name] = ("[Unit]\nDescription=Owned readonly metadata observer\nBindsTo=" + controller_unit +
        "\nAfter=" + controller_unit + "\nPartOf=herdr-offline-" + SUFFIX + ".service\n"
        "[Service]\nType=exec\nUser=root\nGroup=root\nSupplementaryGroups=1001\n"
        "ExecStart=" + " ".join(word(x) for x in [helper["python"], "-I", "-B", helper["entrypoint"], "--serve"]) +
        "\nAppArmorProfile=" + helper["profile"] + "\nRuntimeDirectory=herdr-offline-" + SUFFIX +
        "\nRuntimeDirectoryMode=0755\nStateDirectory=herdr-offline-observer-" + SUFFIX +
        "\nStateDirectoryMode=0755\nCapabilityBoundingSet=CAP_SYS_PTRACE CAP_DAC_READ_SEARCH\n"
        "AmbientCapabilities=\nNoNewPrivileges=yes\nRestrictNamespaces=yes\nRestrictAddressFamilies=AF_UNIX\n"
        "RestrictSUIDSGID=yes\nLockPersonality=yes\nPrivateTmp=no\nPrivateDevices=no\n"
        "ProtectHome=no\nProtectSystem=no\nUMask=0077\nKillMode=control-group\n"
        "RuntimeMaxSec=1800\nTimeoutStopSec=10\nRestart=no\nDelegate=no\n"
        "StandardInput=null\nStandardOutput=null\nStandardError=null\n")
    return outputs


def render_pending_child(ticket, measured_stdio):
    """Actual dispatched host ticket -> one child unit before its root append.

    This is a rendering input, not a published roster or runtime assurance.
    The root custody independently measures the started unit's actual PTY.
    """
    from .native_ticket_v2 import NativePreparationTicket
    from .case_roster import canonical
    from herdr.security import InvocationIdentity
    require(isinstance(ticket, NativePreparationTicket) and ticket.role == "child" and
        set(ticket.roster.document["slots"]) == {"root"} and "child" not in ticket.roster.roles,
        "actual_dispatched_child_ticket_required")
    ticket.revalidate()
    preview = ticket.roster.document
    # Workspace is taken from the typed original host plan, never a future
    # made-up child identity. Its exact logical directory is selected by the
    # original workspace descriptor, not descriptor ordering.
    workspaces = [entry["target"] for entry in ticket.record["plan"]["descriptors"]
        if entry["kind"] == "directory" and entry["target"].startswith("/home/agentops/tmp/hermes-")
        and entry["target"].endswith("/workspace")]
    require(len(workspaces) == 1, "one_original_child_workspace_required")
    preview["slots"]["child"] = {"identity": ticket.identity.to_json(), "workspace": workspaces[0],
        "unit": "herdr-offline-child-" + SUFFIX + ".service", "stdio": measured_stdio,
        "marker": "child-" + ticket.identity.run_token}
    units = render_units(Roster.parse(canonical(preview), InvocationIdentity))
    return preview["slots"]["child"]["unit"], units[preview["slots"]["child"]["unit"]]
