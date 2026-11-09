"""Narrow metadata backend for actual bootstrap/retained/ownership readers.

Every PID must be the root-mapper-recorded init, its ONE measured stage-one
child, or the later canonical bootstrap continuation. No general proc/file
service and no target mutation is provided.
"""
import errno
import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import stat
import time
from .case_roster import CONTEXT_ROOT, SUFFIX, canonical, digest, require

VERSION = "herdr-offline-metadata-2"


def stat_data(info):
    return {name: getattr(info, name) for name in dir(info) if name.startswith("st_")
            and type(getattr(info, name)) in (int, float)}


def layout_metadata(context):
    """Closed metadata-only names derived from the ALREADY authorized plan.

    Directory construction/absence checks are needed by the actual accepted
    sandbox verifier, not only by the credential decision. No new file-body
    read is granted by this layout.
    """
    targets = {"/", "/proc", "/dev", "/home/agentops"}
    targets.update(item["target"] for item in context["plan"]["descriptors"])
    argv = context["argv"]; end = argv.index("--"); i = 1
    arity = {"--tmpfs": 1, "--dir": 1, "--dev": 1, "--proc": 1, "--remount-ro": 1,
        "--chdir": 1, "--setenv": 2, "--unsetenv": 1, "--ro-bind": 2,
        "--bind-fd": 2, "--ro-bind-fd": 2, "--ro-bind-data": 2,
        "--unshare-user": 0, "--unshare-pid": 0, "--die-with-parent": 0, "--disable-userns": 0, "--cap-drop": 1}
    while i < end:
        operation = argv[i]; require(operation in arity and i + arity[operation] < end, "closed_layout_grammar_required")
        values = argv[i + 1:i + 1 + arity[operation]]; i += 1 + arity[operation]
        if operation in {"--tmpfs", "--dir", "--dev", "--proc", "--remount-ro", "--ro-bind",
                         "--bind-fd", "--ro-bind-fd", "--ro-bind-data"}: targets.add(values[-1])
    for item in tuple(targets):
        p = PurePosixPath(item)
        require(p.is_absolute() and str(p) == item and ".." not in p.parts, "canonical_layout_target_required")
        targets.update(str(parent) for parent in p.parents)
    home = "/home/agentops"
    profile = home + "/.hermes/profiles/" + context["approved_profile"]["name"]
    runtime = {"sessions", "cache", "logs", "pastes", "cron", "memories", "pairing", "hooks",
               "image_cache", "audio_cache", "skills"}
    targets.update({profile + "/" + n for n in runtime | {"auth.json", "config.yaml", ".env", "herdr-sdk-policy.json"}})
    targets.update({home + "/" + n for n in {".cache", ".ssh", ".aws", ".gnupg", ".kube", ".config"}})
    lists = {home + "/.hermes": {"profiles", "hermes-agent"},
        home + "/.hermes/profiles": {context["approved_profile"]["name"]},
        home + "/.config": {"herdr"}, home + "/.config/herdr": set(),
        profile: runtime | {"config.yaml", ".env", "herdr-sdk-policy.json"}}
    # The accepted sandbox.verify requires this exact runtime mask to be
    # empty. It is not an inventory/content reader for the host release.
    if "/opt/agent-platform" in targets: lists["/opt/agent-platform"] = set()
    targets.update(lists)
    return targets, lists


class MetadataOps:
    def __init__(self, observer): self.observer, self.pending = observer, {}
    def runtime(self, role):
        return self.observer.read_json(Path(CONTEXT_ROOT) / (role + ".runtime.json"))
    def sdk_phase(self, role):
        from .prep_entry import protected_bytes
        base = Path("/var/lib/herdr-offline-controller-" + SUFFIX) / "observer-phases"
        # Host-only canonical projection, written exclusively by the actual
        # authenticated BootstrapContinuation sink. Never read a prompt/log.
        path = base / (role + ".json")
        directory = os.open(base, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            info = os.fstat(directory)
            require(info.st_uid == 1001 and not info.st_mode & 0o077, "private_controller_phase_store_required")
            fd = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
            try:
                before = os.fstat(fd)
                require(stat.S_ISREG(before.st_mode) and before.st_uid == 1001 and before.st_nlink == 1
                    and stat.S_IMODE(before.st_mode) == 0o400 and 0 < before.st_size <= 65536,
                    "canonical_sdk_projection_required")
                raw = os.read(fd, 65537); after = os.fstat(fd)
                stamp = lambda s: (s.st_dev, s.st_ino, s.st_size, s.st_mtime_ns, s.st_ctime_ns)
                require(len(raw) == before.st_size and stamp(before) == stamp(after), "sdk_projection_changed")
                from .case_roster import decode
                return decode(raw)
            finally: os.close(fd)
        finally: os.close(directory)
    def locate(self, pid):
        ops = self.observer; roster = ops.roster()
        for role in roster.roles:
            try: context = ops.context(role); runtime = self.runtime(role)
            except FileNotFoundError: continue
            require(runtime["roster_sha256"] == roster.sha256 and runtime["context_sha256"] == digest(context)
                and runtime["role"] == role and runtime["namespace"].startswith("pid:["), "native_runtime_record_changed")
            slot = roster.slot(role)
            # Membership first: no read of an arbitrary caller-selected PID.
            base = Path("/sys/fs/cgroup/system.slice") / slot["unit"]
            names = ops.read_bounded(base / "cgroup.procs", 65536).split()
            if str(pid).encode() not in names: continue
            snapshot = ops.target(pid, slot, context)
            require(snapshot["uid"] == snapshot["gid"] == 1001 and
                snapshot["label"] == "herdr189-reference-lifetime (enforce)" and
                ops.identity_environment(pid, slot["identity"], slot["marker"]), "exact_worker_identity_required")
            if pid == runtime["pid"]:
                require(snapshot["start_ticks"] == runtime["start_ticks"], "native_init_replaced")
                return roster, role, context, runtime, snapshot
            try: phase = self.sdk_phase(role)
            except FileNotFoundError: phase = None
            if phase is not None:
                require(phase["roster_sha256"] == roster.sha256 and phase["context_sha256"] == digest(context)
                    and phase["identity"] == slot["identity"] and phase["init_pid"] == runtime["pid"]
                    and phase["init_start_ticks"] == runtime["start_ticks"], "canonical_sdk_phase_changed")
                continuation = phase["continuation"]
                from herdr.host_bootstrap import validate_continuation
                from herdr.security import InvocationIdentity
                validate_continuation(continuation, identity=InvocationIdentity.from_dict(slot["identity"]),
                                      bundle_sha256=phase["bundle_sha256"])
                require(pid == continuation["peer_pid"] and snapshot["start_ticks"] == continuation["process_start_ticks"],
                        "sdk_pid_not_canonical_continuation")
                return roster, role, context, runtime, snapshot
            # Before stage2 confirmation the existing authority needs facts
            # about its actual stage1 peer. Only ONE direct child of this init
            # with the exact independent stage1 interpreter/argv is admissible.
            from herdr.bootstrap_authority import inspect_peer
            peer = inspect_peer(pid)
            require(peer.ppid == runtime["pid"] and peer.start_ticks == snapshot["start_ticks"],
                    "pending_bootstrap_not_owned_init_child")
            fixed = self.pending.get(role)
            if fixed is not None:
                require(fixed == (pid, peer.start_ticks), "bootstrap_candidate_already_consumed")
                return roster, role, context, runtime, snapshot
            from herdr.host_bootstrap import STAGE1_SOURCE
            expected = "/run/herdr/policy-code/" + STAGE1_SOURCE
            require(expected in peer.argv and peer.argv[0] in {"/usr/bin/python3", "/usr/bin/python3.14"},
                    "pending_peer_is_not_exact_stage1")
            self.pending[role] = (pid, peer.start_ticks)
            return roster, role, context, runtime, snapshot
        raise PermissionError(errno.EACCES, "target is outside recorded native identities")

    def view_source(self, pid, suffix, context, operation):
        require(suffix.startswith("/root/"), "approved_target_view_required")
        logical = "/" + suffix[len("/root/"):]
        require(str(PurePosixPath(logical)) == logical and ".." not in PurePosixPath(logical).parts,
                "canonical_target_view_required")
        entries = context["plan"]["descriptors"]
        candidates = [item for item in entries if logical == item["target"] or
            item["kind"] == "directory" and logical.startswith(item["target"].rstrip("/") + "/")]
        require(bool(candidates), "target_path_not_in_original_plan")
        entry = max(candidates, key=lambda item: len(item["target"]))
        # Workspace/results are metadata-only. Never read project payloads or
        # result/model output through a privileged observer.
        require(not (logical == context["workspace"] or logical.startswith(context["workspace"].rstrip("/") + "/"))
                and entry["kind"] != "reserved-result",
                "workspace_and_results_have_no_privileged_content_reader")
        rest = logical[len(entry["target"]):]
        if entry["kind"] == "directory":
            policy = self.observer.read_json(Path("/etc/herdr/host-policy.json"))
            require(digest(policy) == self.observer.roster().document["host_policy_sha256"], "original_policy_changed")
            definitions = [policy["code"], *policy["runtime"]]
            inventory = next((row["files"] for row in definitions if row["target"] == entry["target"]), None)
            if inventory is None:
                require(entry["target"] == "/run/herdr-bootstrap", "unlisted_directory_content_reader")
                inventory = {name: None for name in ("hermes", "agent-hermes-policy-stage1", "immutable-trees.json")}
            selected = rest.lstrip("/")
            require(not selected or selected in inventory or any(name.startswith(selected.rstrip("/") + "/") for name in inventory)
                or selected == "no-bytecode-cache", "unlisted_immutable_source_member")
            if operation == "read": require(selected in inventory, "immutable_file_content_only")
            if operation == "list":
                prefix = selected.rstrip("/") + "/" if selected else ""
                expected_names = {name[len(prefix):].split("/", 1)[0] for name in inventory if name.startswith(prefix)}
                actual_names = {item.name for item in Path(f"/proc/{pid}" + suffix).iterdir()}
                require(actual_names == expected_names, "immutable_directory_inventory_changed")
        else:
            require(not rest and entry["kind"] in {"sealed-profile-data", "sealed-resolver-data", "file"},
                    "unlisted_file_content_reader")
        source = entry["source"] + rest
        require(source.startswith("/proc/" + str(context["original_peer"][0]) + "/fd/"), "original_source_owner_changed")
        return Path(f"/proc/{pid}" + suffix), source

    def operation(self, pid, suffix, op, context, slot):
        ops = self.observer
        base = Path(f"/proc/{pid}" + suffix)
        if op == "locate": return {}
        if suffix == "" and op in {"stat", "lstat"}:
            return {"stat": stat_data(base.stat() if op == "stat" else base.lstat())}
        if suffix in {"/stat", "/mountinfo", "/environ", "/cmdline", "/status", "/cgroup", "/attr/current"}:
            require(op == "read", "closed_proc_metadata_operation_required")
            raw = ops.read_bounded(base, 1048576 if suffix == "/mountinfo" else 262144)
            if suffix == "/environ":
                from herdr.policy_launch import IDENTITY_ENV
                safe = {name.encode() for name in IDENTITY_ENV.values()} | {
                    b"HERDR_DURABLE_TASK_PANE", b"HERDR_DURABLE_SANDBOX", b"HERDR_POLICY_STAGE1_PROOF_SHA256"}
                pairs = [part.split(b"=", 1) for part in raw.rstrip(b"\0").split(b"\0")]
                require(all(len(pair) == 2 for pair in pairs) and len({k for k, _ in pairs}) == len(pairs), "malformed_env")
                from herdr.credential_isolation import _SAFE_ENV, _SECRET_VALUE
                stage = {"HERDR_VERIFIED_PYTHON_FD", "HERDR_VERIFIED_STAGE2_FD", "HERDR_BOOTSTRAP_AUTH_FD"}
                require(all(k.decode("ascii") in _SAFE_ENV | stage and not _SECRET_VALUE.search(v) for k, v in pairs),
                        "unsafe_metadata_environment")
                raw = b"\0".join(k + b"=" + v for k, v in pairs if k in safe) + b"\0"
            elif suffix == "/stat":
                # The verifier needs only numeric kernel fields, not comm.
                raw = str(pid).encode() + b" (herdr-worker)" + raw.rsplit(b")", 1)[1]
            elif suffix == "/status":
                allowed = {b"State", b"Pid", b"PPid", b"NSpid", b"Uid", b"Gid", b"CapInh", b"CapPrm", b"CapEff",
                           b"CapBnd", b"CapAmb", b"NoNewPrivs", b"Seccomp", b"Seccomp_filters"}
                raw = b"\n".join(line for line in raw.splitlines() if line.split(b":", 1)[0] in allowed) + b"\n"
            elif suffix == "/cmdline":
                # Fixed startup-only argv. Never proxy a prompt/tool command.
                parts = raw.rstrip(b"\0").split(b"\0")
                constants = {b"-I", b"-S", b"-B", b"-X", b"-p", b"chat", b"--toolsets", b"none",
                    b"--max-turns", b"1", b"--run-budget", b"900", b"600", context["approved_profile"]["name"].encode(),
                    b"/usr/bin/python3", b"/usr/bin/python3.14", b"/run/herdr/policy-code/agent-stack/bin/agent-hermes-policy-stage1",
                    b"pycache_prefix=/run/herdr/policy-code/no-bytecode-cache"}
                require(all(p in constants or re.fullmatch(rb"/proc/self/fd/[0-9]+", p) for p in parts),
                        "noncanonical_bootstrap_argv")
            return {"text": raw.decode("utf-8", "strict")}
        if suffix.startswith("/ns/"):
            require(op == "readlink" and suffix[4:] in {"pid", "mnt", "net", "user", "cgroup", "time"}, "namespace_kind_invalid")
            return {"link": os.readlink(base)}
        if suffix == "/exe":
            require(op in {"stat", "lstat"}, "executable_metadata_only")
            return {"stat": stat_data(base.stat())}
        if op == "terminal":
            require(suffix == "", "fixed_terminal_operation_required")
            import importlib.util, sys
            from herdr import policy_launch
            file = Path(policy_launch.__file__).resolve().parents[1] / "agent-stack/bin/agent_durable_sandbox.py"
            spec = importlib.util.spec_from_file_location("root_exact_terminal_reader", file)
            module = importlib.util.module_from_spec(spec); sys.modules[spec.name] = module; spec.loader.exec_module(module)
            return {"ready": module._terminal_input_ready(pid, slot["marker"])}
        if suffix.startswith("/root"):
            require(op in {"stat", "lstat", "read", "list"}, "readonly_view_operation_required")
            # Exact plan targets (incl root/workspace) may be stat'ed, never
            # used as an arbitrary file-content oracle.
            logical = suffix[len("/root"):] or "/"
            targets, lists = layout_metadata(context)
            if op in {"stat", "lstat"} and logical in targets:
                return {"stat": stat_data(base.stat() if op == "stat" else base.lstat())}
            if op == "list" and logical in lists:
                names = {item.name for item in base.iterdir()}
                require(names <= lists[logical], "unexpected_private_layout_member")
                return {"names": sorted(names)}
            actual, source = self.view_source(pid, suffix, context, op)
            if op in {"stat", "lstat"}: return {"stat": stat_data(actual.stat() if op == "stat" else actual.lstat())}
            if op == "read": return {"stat": stat_data(actual.stat()), "local_source": source}
            require(op == "list", "unsupported_view_operation")
            names = [entry.name for entry in actual.iterdir()]
            require(len(names) <= 4096, "view_directory_bound")
            return {"names": names}
        raise PermissionError(errno.EACCES, "unlisted metadata field")


def process_metadata(raw, peer, metadata):
    from .case_roster import decode, exact
    query = decode(raw); exact(query, {"v", "op", "pid", "suffix"})
    require(query["v"] == VERSION and query["op"] in {"locate", "read", "readlink", "stat", "lstat", "list", "terminal"}
        and type(query["pid"]) is int and query["pid"] > 0 and type(query["suffix"]) is str and
        len(query["suffix"]) <= 4096 and "\0" not in query["suffix"] and
        all(p not in (".", "..") for p in query["suffix"].split("/")), "invalid_metadata_query")
    ops = metadata.observer; roster = ops.roster()
    roster.live(now=ops.now(), boot_id=ops.boot_id()); ops.case_live(roster)
    require(peer == (roster.document["controller"]["pid"], 1001, 1001) and ops.controller() == roster.document["controller"],
            "exact_original_controller_required")
    ops.verify_observer(roster.document["observer"])
    selected, role, context, runtime, before = metadata.locate(query["pid"])
    require(selected.sha256 == roster.sha256, "metadata_roster_changed")
    rows = ops.mount_rows(query["pid"]); ops.original_plan(context).verify_mounted(query["pid"], rows)
    try:
        data = {"start_ticks": before["start_ticks"]} if query["op"] == "locate" else \
            metadata.operation(query["pid"], query["suffix"], query["op"], context, roster.slot(role))
    except FileNotFoundError: data = {"errno": errno.ENOENT}
    after = ops.target(query["pid"], roster.slot(role), context)
    require(after == before and ops.roster().sha256 == roster.sha256, "metadata_process_changed")
    return {"v": VERSION, "request_sha256": hashlib.sha256(raw).hexdigest(), "roster_sha256": roster.sha256,
        "context_sha256": digest(context), "role": role, "identity_sha256": digest(roster.slot(role)["identity"]),
        "pid": query["pid"], "start_ticks": before["start_ticks"], "observer_pid": ops.self_pid(), "data": data}
