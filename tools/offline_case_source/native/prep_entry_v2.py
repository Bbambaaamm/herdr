"""Post-pin v2 root entry implementation; no import-time effects."""
import hashlib
import os
from pathlib import Path
import sys
import time
from case_roster import Roster, ROSTER_PATH, canonical, digest, require, load_roster
from preparation_contract import request_for, validate_record, native_argv


def verify_entrypoint(roster, role, *, executable, argv, entrypoint, identity_sha256=None):
    """Python strips interpreter flags from sys.argv; issuer checks full proc argv."""
    expected = native_argv(roster, role, identity_sha256)
    require(executable == expected[0] and entrypoint == expected[3] and
        type(argv) is list and argv == expected[3:], "exact_native_roster_entrypoint_required")


def run(role, protected_json, protected_bytes, reserve_once, *, identity_sha256=None):
    raw_roster = protected_json(Path(ROSTER_PATH))
    policy = protected_json(Path("/etc/herdr/host-policy.json"))
    require(digest(policy) == raw_roster["host_policy_sha256"], "current_original_host_policy_changed")
    code = policy["code"]; total = 0
    require(type(code["files"]) is dict and 1 <= len(code["files"]) <= 4096,
            "complete_original_plus_overlay_core_required")
    for relative, expected in code["files"].items():
        require(type(relative) is str and relative and not relative.startswith("/") and
            all(p not in ("", ".", "..") for p in relative.split("/")), "canonical_core_member_required")
        raw = protected_bytes(Path(code["source"]) / relative, 16777216); total += len(raw)
        require(total <= 201326592 and hashlib.sha256(raw).hexdigest() == expected, "approved_core_changed")
    sys.path.insert(0, code["source"])
    from herdr.security import InvocationIdentity
    from herdr import launch_plan_issuer as authority
    from herdr.private_mount_plan import ApprovedPrivateMountPlan
    from herdr.native_fd_handoff import _connect
    from herdr.credential_isolation import _approved_confinement, _loaded_profile_sha256, SYSTEM_RUNTIME_FILES
    from herdr.credential_ingress_filter import filter_bytes
    from herdr.policy_launch import IDENTITY_ENV
    from trusted_prepare import LinuxOps, recipe_from_approved, prepare_and_exec
    roster = load_roster(protected_json, InvocationIdentity)
    roster.live(now=time.time(), boot_id=Path("/proc/sys/kernel/random/boot_id").read_text().strip())
    doc = roster.document
    verify_entrypoint(roster, role, executable=sys.executable, argv=sys.argv,
                      entrypoint=str(Path(__file__).with_name("prep_entry.py")), identity_sha256=identity_sha256)
    require(_loaded_profile_sha256() == _approved_confinement()["loaded_sha256"], "worker_kernel_policy_unapproved")
    if role == "child" and "child" not in roster.roles:
        from case_roster import hex64
        require(hex64(identity_sha256), "actual_child_identity_digest_required")
        published = protected_json(authority.publication.AUTHORITY_ROOT / (identity_sha256 + ".json"))
        identity = InvocationIdentity.from_dict(published["identity"])
        require(digest(identity.to_json()) == identity_sha256, "original_published_child_identity_changed")
    else: identity = InvocationIdentity.from_dict(roster.slot(role)["identity"])
    key = digest(identity.to_json())
    plan = ApprovedPrivateMountPlan.read(authority.publication.AUTHORITY_ROOT / (key + ".json"), identity)
    request = request_for(roster, role, plan.sha256, identity=identity.to_json())
    reserve_once(key, roster.sha256)
    connection, peer = _connect(60)
    received = []; system_fds = {}
    try:
        with connection:
            packet = canonical(request)
            require(connection.send(packet) == len(packet), "native_request_uncertain")
            answer, received = authority._receive(connection, peer)
        require(set(answer) == set(request) | {"record", "context_sha256", "descriptor_count"} and
            all(answer[k] == v for k, v in request.items()), "native_response_unknown")
        record = validate_record(answer["record"], roster, request)
        observed_roster = load_roster(protected_json, InvocationIdentity)
        require(observed_roster.sha256 == roster.sha256 and role in observed_roster.roles and
            observed_roster.slot(role)["identity"] == identity.to_json(), "root_validated_role_projection_unavailable")
        roster = observed_roster; slot = roster.slot(role)
        entries = record["plan"]["descriptors"]
        require(answer["descriptor_count"] == len(entries) == len(received), "descriptor_count_changed")
        plan.authorize(entries, record["argv"])
        from case_roster import CONTEXT_ROOT
        context = protected_json(Path(CONTEXT_ROOT) / (role + ".json"))
        require(digest(context) == answer["context_sha256"] and context["roster_sha256"] == roster.sha256
            and context["slot_sha256"] == digest(slot) and context["child_projection_sha256"] == roster.projection_sha256(role),
                "same_authority_context_changed")
        ops = LinuxOps(deadline=doc["deadline"], expected_stdio=slot["stdio"], runtime_binding={
            "role": role, "roster_sha256": roster.sha256, "context_sha256": digest(context), "unit": slot["unit"]})
        require(ops.label() == doc["preparer"]["profile"] + " (enforce)", "exact_prep_label_required")
        ops.verify_stdio()
        approval = _approved_confinement()
        def hash_fd(fd):
            info = os.fstat(fd); require(0 <= info.st_size <= 16777216, "system_runtime_bound")
            h = hashlib.sha256(); offset = 0
            while offset < info.st_size:
                part = os.pread(fd, min(65536, info.st_size - offset), offset)
                require(bool(part), "system_runtime_short_read"); h.update(part); offset += len(part)
            return h.hexdigest()
        for target in sorted(SYSTEM_RUNTIME_FILES):
            source = Path(target).resolve(strict=True)
            raw = protected_bytes(source, 16777216)
            require(hashlib.sha256(raw).hexdigest() == approval["system_files"][target], "system_runtime_changed")
            fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
            info = os.fstat(fd)
            system_fds[target] = {"fd": fd, "device": info.st_dev, "inode": info.st_ino,
                                  "sha256": hash_fd(fd)}
        from types import SimpleNamespace
        api = SimpleNamespace(ApprovedPrivateMountPlan=ApprovedPrivateMountPlan, SYSTEM_RUNTIME_FILES=SYSTEM_RUNTIME_FILES,
            approved_system_files=approval["system_files"], fd_sha256=hash_fd)
        recipe = recipe_from_approved(plan, entries, record["argv"], identity=identity, api=api, system_fds=system_fds)
        from dataclasses import replace
        mapping = {entry["fd"]: fd for entry, fd in zip(entries, received)}
        original_descriptors = {(entry["fd"], entry["target"], entry["kind"]) for entry in entries}
        recipe = replace(recipe, mounts=tuple(replace(m, fd=mapping[m.fd])
            if (m.fd, m.target, m.kind) in original_descriptors else m for m in recipe.mounts))
        environment = {name: str(getattr(identity, field)) for field, name in IDENTITY_ENV.items()}
        environment["HERDR_DURABLE_TASK_PANE"] = slot["marker"]
        prepare_and_exec(recipe, ops, root="/run/herdr-offline-private-root-" + key[:16],
            identity_environment=environment, safe_environment={"HOME": "/home/agentops", "LANG": "C"},
            filter_program=filter_bytes(), filter_sha256=approval["filter_sha256"], prep_profile=doc["preparer"]["profile"])
    finally:
        for fd in [*received, *(row["fd"] for row in system_fds.values())]:
            try: os.close(fd)
            except OSError: pass
