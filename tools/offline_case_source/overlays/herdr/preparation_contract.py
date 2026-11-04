"""Shared v2 host-ticket/root-entry/existing-custody ABI. No new authority."""
from datetime import UTC, datetime
from .case_roster import Roster, ROSTER_PATH, SUFFIX, digest, canonical, require, exact

VERSION = "herdr-native-preparation-3"
REQUEST_KEYS = {"schema_version", "role", "roster_sha256", "identity_sha256", "plan_sha256"}


def native_argv(roster, role, identity_sha256=None):
    require(role in ("root", "child"), "unknown_preparation_role")
    helper = roster.document["preparer"]
    answer = [helper["python"], "-I", "-B", helper["entrypoint"], "--execute", role]
    if role == "child":
        from .case_roster import hex64
        if identity_sha256 is None and "child" in roster.roles: identity_sha256 = digest(roster.slot("child")["identity"])
        require(hex64(identity_sha256), "actual_dispatched_child_identity_required")
        answer += ["--identity-sha256", identity_sha256]
    return answer


def request_for(roster, role, plan_sha256, *, identity=None):
    if identity is None: identity = roster.slot(role)["identity"]
    return {"schema_version": VERSION, "role": role, "roster_sha256": roster.sha256,
        "identity_sha256": digest(identity), "plan_sha256": plan_sha256}


def validate_request(request, roster):
    exact(request, REQUEST_KEYS)
    require(request["schema_version"] == VERSION and request["role"] in ("root", "child")
        and request["roster_sha256"] == roster.sha256,
        "native_request_roster_or_role_changed")
    from .case_roster import hex64
    require(hex64(request["plan_sha256"]) and hex64(request["identity_sha256"]), "plan_digest_invalid")
    if request["role"] in roster.roles:
        require(request["identity_sha256"] == digest(roster.slot(request["role"])["identity"]), "native_identity_changed")
    return request["role"]


def derive_record(roster, role, *, identity, plan, argv, grant_hash, expires_at, approved_profile):
    """Exact selected prior plan/custody, subordinate to the frozen two-slot roster."""
    root = roster.slot("root")["identity"]
    require(role in ("root", "child") and (identity == roster.slot(role)["identity"] if role in roster.roles else
        identity["consumer"] == root["consumer"] and identity["parent_task_id"] == root["task_id"]
        and identity["parent_agent_id"] == root["agent_id"] and identity["task_id"] != root["task_id"]
        and identity["run_token"] != root["run_token"] and identity["fencing_token"] != root["fencing_token"])
        and plan["identity"] == identity and
        plan["argv_sha256"] == digest(argv), "original_plan_identity_or_argv_changed")
    expiry = datetime.fromisoformat(expires_at)
    require(expiry.tzinfo is not None and expiry > datetime.now(UTC), "original_grant_expired")
    require(roster.document["deadline"] <= expiry.timestamp(), "roster_exceeds_original_grant_deadline")
    return {"schema_version": VERSION, "roster_sha256": roster.sha256, "role": role,
        "identity": identity, "plan": plan, "argv": argv, "plan_sha256": digest(plan),
        "grant_sha256": grant_hash, "grant_expires_at": expires_at,
        "approved_profile": approved_profile, "native_argv": native_argv(roster, role, digest(identity))}


def validate_record(record, roster, request):
    exact(record, {"schema_version", "roster_sha256", "role", "identity", "plan", "argv",
        "plan_sha256", "grant_sha256", "grant_expires_at", "approved_profile", "native_argv"})
    role = validate_request(request, roster)
    expected = derive_record(roster, role, identity=record["identity"], plan=record["plan"],
        argv=record["argv"], grant_hash=record["grant_sha256"], expires_at=record["grant_expires_at"],
        approved_profile=record["approved_profile"])
    require(record == expected and record["plan_sha256"] == request["plan_sha256"],
            "native_response_record_changed")
    return record
