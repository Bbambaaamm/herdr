"""Read-only root measurements over the ORIGINAL authenticated bootstrap.

This data never authorizes a host effect. WorkAuthority/reference/grant/budget
guards remain independent. A Python receipt is only a local input check.
Legacy direct observations remain unchanged outside the explicit v3 branch.
"""
from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
import re
import secrets
import time

from .case_roster import canonical, decode, digest, exact, hex64, require, load_roster, WORKER_LABEL, WORKER_SOURCE

MODE = "authenticated-root-kernel-v1"
PREFLIGHT = "herdr-bootstrap-confinement-preflight-1"
KERNEL_REQUEST = "herdr-bootstrap-kernel-request-1"
KERNEL_PROOF = "herdr-bootstrap-kernel-observation-1"
ENVELOPE = "herdr-stage2-authenticated-envelope-1"
MAX_RESPONSE = 32768
CAPS = ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")
NAMESPACES = ("pid", "mnt", "net", "user")
MODE_KEYS = {"mode", "role", "roster_sha256", "worker_source_sha256", "loaded_policy_sha256",
             "filter_program_sha256", "system_files_sha256"}
SESSION_KEYS = {"proof_sha256", "bundle_sha256", "stage1_sha256", "stage2_sha256", "python_sha256"}
FACT_KEYS = {"schema_version", "identity", "role", "host_pid", "private_pid", "start_ticks", "namespaces",
    "label", "uids", "gids", "capabilities", "no_new_privs", "seccomp", "seccomp_filters", "challenge",
    "grant_sha256", "bundle_sha256", "signed_attestation_sha256", "proof_sha256", "stage1_sha256",
    "stage2_sha256", "python_sha256", "profile_manifest_sha256", "roster_sha256", "context_sha256",
    "plan_sha256", "slot_sha256", "child_projection_sha256", "observed_source_sha256",
    "observed_loaded_sha256", "filter_program_sha256", "system_files", "issued_at_ns", "valid_until_ns"}


def validate_facts(value):
    exact(value, FACT_KEYS)
    from .security import InvocationIdentity
    require(value["schema_version"] == KERNEL_PROOF and value["role"] in ("root", "child")
        and InvocationIdentity.from_dict(value["identity"]).to_json() == value["identity"]
        and all(hex64(value[k]) for k in FACT_KEYS if k.endswith("sha256") and k != "child_projection_sha256")
        and hex64(value["challenge"]) and (value["child_projection_sha256"] is None
            if value["role"] == "root" else hex64(value["child_projection_sha256"])), "closed_kernel_facts_required")
    for key in ("host_pid", "private_pid", "start_ticks", "no_new_privs", "seccomp", "seccomp_filters", "issued_at_ns", "valid_until_ns"):
        require(type(value[key]) is int and value[key] > 0, "integer_kernel_fact_required")
    exact(value["namespaces"], NAMESPACES); exact(value["capabilities"], CAPS)
    require(all(type(value["namespaces"][k]) is str and re.fullmatch(k + r":\[[0-9]+\]", value["namespaces"][k]) for k in NAMESPACES)
        and all(type(v) is int and v == 0 for v in value["capabilities"].values())
        and all(type(value[k]) is list and len(value[k]) == 4 and all(type(n) is int and n == 1001 for n in value[k]) for k in ("uids", "gids"))
        and type(value["system_files"]) is dict and all(type(k) is str and hex64(v) for k, v in value["system_files"].items()),
        "typed_kernel_facts_required")
    return value


def status_values(raw):
    require(type(raw) is bytes and len(raw) <= 131072, "bounded_kernel_status_required")
    values = {}
    wanted = {"Uid", "Gid", "NSpid", "NoNewPrivs", "Seccomp", "Seccomp_filters", *CAPS}
    for line in raw.decode("ascii", "strict").splitlines():
        key, separator, value = line.partition(":")
        if separator and key in wanted:
            require(key not in values, "duplicate_kernel_status")
            values[key] = value.split()
    require(set(values) == wanted, "complete_kernel_status_required")
    numbers = {key: tuple(int(v, 16 if key in CAPS else 10) for v in row) for key, row in values.items()}
    require(numbers["Uid"] == numbers["Gid"] == (1001,) * 4 and
        all(numbers[key] == (0,) for key in CAPS) and numbers["NoNewPrivs"] == (1,) and
        numbers["Seccomp"] == (2,) and len(numbers["Seccomp_filters"]) == 1 and numbers["Seccomp_filters"][0] > 0
        and numbers["NSpid"] and all(n > 0 for n in numbers["NSpid"]), "worker_kernel_boundary_changed")
    return numbers


def start_ticks(raw, pid):
    require(type(raw) is bytes and len(raw) <= 16384 and raw.startswith(str(pid).encode() + b" (") and b") " in raw,
            "bounded_exact_process_stat_required")
    row = raw.rsplit(b") ", 1)[1].split()
    require(len(row) > 19 and row[0] not in {b"Z", b"X", b"x"}, "live_process_stat_required")
    ticks = int(row[19]); require(ticks > 0, "positive_process_start_required")
    return ticks


def _authenticated_host(raw, peer, observer):
    require(type(raw) is bytes and 0 < len(raw) <= 8192, "bounded_readonly_observer_request_required")
    roster = observer.roster(); roster.live(now=observer.now(), boot_id=observer.boot_id()); observer.case_live(roster)
    require(peer == (roster.document["controller"]["pid"], 1001, 1001) and
        observer.controller() == roster.document["controller"], "original_controller_peer_required")
    observer.verify_observer(roster.document["observer"])
    return roster


def measured_confinement():
    """Actual root reads; an expected digest is NEVER returned as observed."""
    from .credential_isolation import (_approved_confinement, _loaded_profile_sha256, CONFINEMENT_SOURCE)
    from .credential_ingress_filter import filter_bytes
    from .prep_entry import protected_bytes
    record = _approved_confinement()
    loaded = _loaded_profile_sha256()
    source = hashlib.sha256(protected_bytes(CONFINEMENT_SOURCE, 1048576)).hexdigest()
    program = hashlib.sha256(filter_bytes()).hexdigest()
    require(source == record["source_sha256"] == WORKER_SOURCE and loaded == record["loaded_sha256"]
        and program == record["filter_sha256"], "measured_confinement_differs_from_approval")
    # The filter source hash is an actual pinned program hash, not a claim of
    # reading active BPF bytes. Actual installed seccomp/NNP state is separate.
    return record, source, loaded, program


def process_preflight(raw, peer, observer):
    roster = _authenticated_host(raw, peer, observer)
    request = decode(raw); exact(request, {"v", "challenge"})
    require(request["v"] == PREFLIGHT and hex64(request["challenge"]), "invalid_preflight_request")
    record, source, loaded, program = measured_confinement()
    return {"v": PREFLIGHT, "request_sha256": hashlib.sha256(raw).hexdigest(), "challenge": request["challenge"],
        "roster_sha256": roster.sha256, "observer_pid": observer.self_pid(), "approval": record,
        "observed_source_sha256": source, "observed_loaded_sha256": loaded, "filter_program_sha256": program}


def host_preflight():
    """UID1001 gets root-only policy measurements, never SDK assurance/authority."""
    from .observer_client import LinuxClientOps
    client = LinuxClientOps(); roster = client.roster()
    query = {"v": PREFLIGHT, "challenge": secrets.token_hex(32)}; packet = canonical(query)
    answer = decode(client.exchange(packet, roster))
    exact(answer, {"v", "request_sha256", "challenge", "roster_sha256", "observer_pid", "approval",
                   "observed_source_sha256", "observed_loaded_sha256", "filter_program_sha256"})
    record = answer["approval"]
    require(answer["v"] == PREFLIGHT and answer["request_sha256"] == hashlib.sha256(packet).hexdigest()
        and answer["challenge"] == query["challenge"] and answer["roster_sha256"] == roster.sha256
        and answer["observer_pid"] == client.peer_pid and answer["observed_source_sha256"] == WORKER_SOURCE
        and answer["observed_source_sha256"] == record["source_sha256"]
        and answer["observed_loaded_sha256"] == record["loaded_sha256"]
        and answer["filter_program_sha256"] == record["filter_sha256"], "root_preflight_binding_changed")
    return answer


def mode_for_launch(launch):
    from .security import InvocationIdentity
    from .host_configuration import _read_configuration
    roster = load_roster(_read_configuration, InvocationIdentity)
    root = InvocationIdentity.from_dict(roster.slot("root")["identity"])
    identity = launch.identity
    role = "root" if identity == root else "child"
    require(role == "root" or identity.consumer == root.consumer and identity.parent_task_id == root.task_id
        and identity.parent_agent_id == root.agent_id and identity.run_token != root.run_token,
        "original_case_launch_required")
    measured = host_preflight()
    require(measured["roster_sha256"] == roster.sha256, "case_preflight_changed")
    return {"mode": MODE, "role": role, "roster_sha256": roster.sha256,
        "worker_source_sha256": measured["observed_source_sha256"], "loaded_policy_sha256": measured["observed_loaded_sha256"],
        "filter_program_sha256": measured["filter_program_sha256"], "system_files_sha256": digest(measured["approval"]["system_files"])}


def validate_mode(value):
    exact(value, MODE_KEYS)
    require(value["mode"] == MODE and value["role"] in ("root", "child") and
        all(hex64(value[k]) for k in MODE_KEYS - {"mode", "role"}) and
        value["worker_source_sha256"] == WORKER_SOURCE, "closed_self_observation_mode_required")
    return value


def process_kernel_request(raw, peer, observer):
    """Root-only facts before continuation, deliberately excludes FD/env True."""
    roster = _authenticated_host(raw, peer, observer)
    request = decode(raw)
    exact(request, {"v", "challenge", "identity", "pid", "start_ticks", "session", "grant_sha256",
                    "signed_attestation_sha256", "mode"})
    exact(request["session"], SESSION_KEYS); mode = validate_mode(request["mode"])
    require(request["v"] == KERNEL_REQUEST and hex64(request["challenge"]) and
        all(hex64(request["session"][k]) for k in SESSION_KEYS) and hex64(request["grant_sha256"])
        and hex64(request["signed_attestation_sha256"]) and type(request["pid"]) is int and request["pid"] > 0
        and type(request["start_ticks"]) is int and request["start_ticks"] > 0, "invalid_kernel_request")
    selected, role, context, runtime, before = observer.metadata().locate(request["pid"])
    require(selected.sha256 == roster.sha256 == mode["roster_sha256"] and role == mode["role"]
        and context["identity"] == request["identity"] and before["start_ticks"] == request["start_ticks"],
        "original_pending_bootstrap_peer_required")
    rows = observer.mount_rows(request["pid"]); observer.original_plan(context).verify_mounted(request["pid"], rows)
    from .security import InvocationIdentity, load_policy_bundle
    from .policy_launch import BUNDLE_TARGET
    target = Path(f"/proc/{request['pid']}/root") / str(BUNDLE_TARGET).lstrip("/")
    bundle = observer.read_bounded(target, 2097152)
    grant = load_policy_bundle(target, InvocationIdentity.from_dict(context["identity"]),
        expected_attestation_sha256=request["signed_attestation_sha256"])
    require(hashlib.sha256(bundle).hexdigest() == request["session"]["bundle_sha256"]
        and grant.hash == request["grant_sha256"] and grant.runtime_assurance.credentials_isolated is True
        and observer.read_bounded(target, 2097152) == bundle, "original_signed_bundle_changed")
    record, source, loaded, program = measured_confinement()
    require(source == mode["worker_source_sha256"] and loaded == mode["loaded_policy_sha256"]
        and program == mode["filter_program_sha256"] and digest(record["system_files"]) == mode["system_files_sha256"],
        "measured_policy_not_bootstrap_pinned")
    from .credential_isolation import _observed_system_runtime
    require(_observed_system_runtime(request["pid"], rows, record), "actual_private_runtime_changed")
    status = status_values(observer.read_bounded(Path(f"/proc/{request['pid']}/status"), 131072))
    require(status["NSpid"][0] == request["pid"] and len(status["NSpid"]) >= 2 and status["NSpid"][-1] > 1,
            "actual_private_stage2_pid_required")
    label = observer.read_bounded(Path(f"/proc/{request['pid']}/attr/current"), 256).decode().strip()
    require(label == WORKER_LABEL + " (enforce)", "worker_label_changed")
    # Session code/python pins are checked against the ROOT-approved inventories,
    # independently of the caller's request or a future continuation receipt.
    from .host_configuration import _read_configuration
    policy = _read_configuration(Path("/etc/herdr/host-policy.json"))
    require(digest(policy) == roster.document["host_policy_sha256"], "original_policy_changed")
    from .host_bootstrap import BOOTSTRAP_TARGET, STAGE1_SOURCE, STAGE2_SOURCE, PYTHON_TARGET, PYTHON_EXECUTABLE
    proof_path = Path(f"/proc/{request['pid']}/root") / str(BOOTSTRAP_TARGET).lstrip("/") / "immutable-trees.json"
    actual_proof = observer.read_bounded(proof_path, 65536)
    require(hashlib.sha256(actual_proof).hexdigest() == request["session"]["proof_sha256"]
        and decode(actual_proof)["self_observation"] == mode, "actual_immutable_bootstrap_proof_changed")
    python = next(tree for tree in policy["runtime"] if tree["target"] == str(PYTHON_TARGET))
    require(request["session"]["stage1_sha256"] == policy["code"]["files"][STAGE1_SOURCE]
        and request["session"]["stage2_sha256"] == policy["code"]["files"][STAGE2_SOURCE]
        and request["session"]["python_sha256"] == python["files"][PYTHON_EXECUTABLE], "session_source_pins_changed")
    now_ns = int(observer.now() * 1000000000)
    deadline = min(roster.document["deadline"], datetime.fromisoformat(grant.expires_at).timestamp(), observer.now() + 60)
    result = {"schema_version": KERNEL_PROOF, "identity": grant.identity.to_json(), "role": role,
        "host_pid": request["pid"], "private_pid": status["NSpid"][-1], "start_ticks": before["start_ticks"],
        "namespaces": before["namespaces"], "label": label, "uids": list(status["Uid"]), "gids": list(status["Gid"]),
        "capabilities": {k: status[k][0] for k in CAPS}, "no_new_privs": 1, "seccomp": 2,
        "seccomp_filters": status["Seccomp_filters"][0], "challenge": request["challenge"],
        "grant_sha256": grant.hash, "signed_attestation_sha256": grant.runtime_assurance.sandbox_attestation_sha256,
        **request["session"], "profile_manifest_sha256": context["approved_profile"]["manifest_sha256"],
        "roster_sha256": roster.sha256, "context_sha256": digest(context), "plan_sha256": context["plan_sha256"],
        "slot_sha256": context["slot_sha256"], "child_projection_sha256": context["child_projection_sha256"],
        "observed_source_sha256": source, "observed_loaded_sha256": loaded, "filter_program_sha256": program,
        "system_files": record["system_files"], "issued_at_ns": now_ns, "valid_until_ns": int(deadline * 1000000000)}
    require(observer.target(request["pid"], roster.slot(role), context) == before and
        measured_confinement() == (record, source, loaded, program) and observer.roster().sha256 == roster.sha256,
        "kernel_observation_changed")
    roster.live(now=observer.now(), boot_id=observer.boot_id()); observer.case_live(roster)
    validate_facts(result)
    return {"v": KERNEL_REQUEST, "request_sha256": hashlib.sha256(raw).hexdigest(), "observer_pid": observer.self_pid(), "observation": result}


def produce_for_bootstrap(owner, session, peer, challenge):
    """Only original verified pre-continuation hook calls; no SDK proof accepted."""
    from .observer_client import LinuxClientOps
    launch = owner.launch
    require(launch.sealed is not None and owner._claimed_peer == (peer.pid, peer.start_ticks)
        and session.peer_pid == peer.pid and session.peer_start_ticks == peer.start_ticks
        and session.expectation.identity == launch.identity.to_json(), "original_authenticated_bootstrap_required")
    mode = validate_mode(owner.proof["self_observation"])
    request = {"v": KERNEL_REQUEST, "challenge": challenge, "identity": launch.identity.to_json(),
        "pid": peer.pid, "start_ticks": peer.start_ticks,
        "session": {key: getattr(session.expectation, key) for key in SESSION_KEYS},
        "grant_sha256": launch.grant.hash,
        "signed_attestation_sha256": launch.grant.runtime_assurance.sandbox_attestation_sha256, "mode": mode}
    client = LinuxClientOps(); roster = client.roster(); packet = canonical(request)
    answer = decode(client.exchange(packet, roster))
    exact(answer, {"v", "request_sha256", "observer_pid", "observation"})
    require(answer["v"] == KERNEL_REQUEST and answer["request_sha256"] == hashlib.sha256(packet).hexdigest()
        and answer["observer_pid"] == client.peer_pid, "root_kernel_reply_peer_or_request_changed")
    observation = validate_facts(answer["observation"])
    require(observation["identity"] == launch.identity.to_json() and observation["host_pid"] == peer.pid
        and observation["start_ticks"] == peer.start_ticks and observation["challenge"] == challenge
        and observation["grant_sha256"] == launch.grant.hash and observation["role"] == mode["role"]
        and observation["roster_sha256"] == mode["roster_sha256"]
        and observation["observed_source_sha256"] == mode["worker_source_sha256"]
        and observation["observed_loaded_sha256"] == mode["loaded_policy_sha256"]
        and observation["filter_program_sha256"] == mode["filter_program_sha256"]
        and digest(observation["system_files"]) == mode["system_files_sha256"]
        and observation["signed_attestation_sha256"] == launch.grant.runtime_assurance.sandbox_attestation_sha256
        and observation["issued_at_ns"] <= time.time_ns() < observation["valid_until_ns"]
        and all(observation[key] == request["session"][key] for key in SESSION_KEYS), "root_kernel_session_binding_changed")
    return decode(canonical(observation))


def observe_self_from_bootstrap(observation, *, challenge, grant, bootstrap_proof, bundle_sha256, pid=None, now_ns=None):
    """Local additional check ONLY; never a host-effect authorization API."""
    try:
        from .credential_isolation import (_read_bounded, _process_tree, _capture_fd_links,
            evaluate_sdk_credentials, _observed_system_runtime, SYSTEM_RUNTIME_FILES)
        from .policy_launch import mount_rows
        from .credential_ingress_filter import filter_bytes
        pid = os.getpid() if pid is None else pid
        require(pid == os.getpid() and type(observation) is dict, "local_self_only")
        validate_facts(observation)
        mode = validate_mode(bootstrap_proof["self_observation"])
        require(bootstrap_proof["schema_version"] == "herdr-policy-bootstrap-3" and observation["schema_version"] == KERNEL_PROOF
            and observation["identity"] == grant.identity.to_json() == bootstrap_proof["identity"]
            and observation["role"] == mode["role"] and observation["roster_sha256"] == mode["roster_sha256"]
            and observation["challenge"] == challenge and hex64(challenge) and grant.is_active()
            and observation["grant_sha256"] == grant.hash and observation["bundle_sha256"] == bundle_sha256
            and observation["proof_sha256"] == digest(bootstrap_proof)
            and observation["profile_manifest_sha256"] == bootstrap_proof["approved_profile"]["manifest_sha256"]
            and observation["signed_attestation_sha256"] == grant.runtime_assurance.sandbox_attestation_sha256,
            "self_grant_bootstrap_binding_changed")
        require(observation["observed_source_sha256"] == mode["worker_source_sha256"] == WORKER_SOURCE
            and observation["observed_loaded_sha256"] == mode["loaded_policy_sha256"]
            and observation["filter_program_sha256"] == mode["filter_program_sha256"] == hashlib.sha256(filter_bytes()).hexdigest()
            and type(observation["system_files"]) is dict and set(observation["system_files"]) == SYSTEM_RUNTIME_FILES
            and digest(observation["system_files"]) == mode["system_files_sha256"], "self_measured_policy_binding_changed")
        now_ns = time.time_ns() if now_ns is None else now_ns
        require(type(now_ns) is int and type(observation["issued_at_ns"]) is int and type(observation["valid_until_ns"]) is int
            and observation["issued_at_ns"] <= now_ns < observation["valid_until_ns"]
            and 0 < observation["valid_until_ns"] - observation["issued_at_ns"] <= 60000000000,
            "self_kernel_observation_stale")
        require(type(observation["host_pid"]) is int and observation["host_pid"] > 0
            and observation["private_pid"] == pid and pid > 1 and type(observation["start_ticks"]) is int
            and observation["start_ticks"] > 0 and observation["label"] == WORKER_LABEL + " (enforce)"
            and observation["uids"] == observation["gids"] == [1001] * 4
            and observation["capabilities"] == {k: 0 for k in CAPS} and observation["no_new_privs"] == 1
            and observation["seccomp"] == 2 and type(observation["seccomp_filters"]) is int and observation["seccomp_filters"] > 0,
            "self_kernel_facts_invalid")
        exact(observation["namespaces"], NAMESPACES)
        before = _process_tree(pid); rows = mount_rows(pid)
        require(os.getresuid() == os.getresgid() == (1001,) * 3, "self_uid_gid_changed")
        require(start_ticks(_read_bounded(Path(f"/proc/{pid}/stat"), 16384), pid) == observation["start_ticks"], "self_start_changed")
        for member in before:
            local = status_values(_read_bounded(Path(f"/proc/{member}/status"), 131072))
            require(local["NSpid"][-1] == member and local["Seccomp_filters"][0] >= observation["seccomp_filters"], "self_pid_filter_changed")
            require(_read_bounded(Path(f"/proc/{member}/attr/current"), 256).decode().strip() == observation["label"]
                and all(os.readlink(f"/proc/{member}/ns/{name}") == observation["namespaces"][name] for name in NAMESPACES),
                "self_namespace_or_label_changed")
            require(_observed_system_runtime(member, rows, {"system_files": observation["system_files"]}) and
                evaluate_sdk_credentials(Path(f"/proc/{member}/root"), bootstrap_proof["approved_profile"], rows,
                    _read_bounded(Path(f"/proc/{member}/environ"), 262144), _capture_fd_links(member),
                    _read_bounded(Path(f"/proc/{member}/mountinfo"), 1048576), grant.workspace_root),
                "local_self_private_runtime_profile_fd_or_environment_changed")
        return before == _process_tree(pid) and start_ticks(_read_bounded(Path(f"/proc/{pid}/stat"), 16384), pid) == observation["start_ticks"]
    except Exception:
        return False
