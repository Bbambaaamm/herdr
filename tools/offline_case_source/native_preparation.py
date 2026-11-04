"""Proposed additive Herdr core handoff; no old-path changes or new issuer.

Integrate as herdr/native_preparation.py in a separately inventoried candidate
overlay. The ordinary ApprovedPrivateMountPlan and issuer checks remain
mandatory. A missing exact future root case/preparer approval denies.
"""
from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
from pathlib import Path
import re

APPROVAL = Path("/etc/herdr/native-preparation.json")
VERSION = "herdr-native-preparation-1"
WORKER = "herdr189-reference-lifetime"
WORKER_SOURCE = "a77ac0c2e44d51912df674de35c5175c16ef927a7178ebe1f6f3375822b3e4fb"
TOKEN = object()


def require(ok, reason):
    if not ok: raise RuntimeError(reason)


def canonical(value):
    import json
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode()


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


@dataclass(frozen=True)
class NativePreparationTicket:
    identity: object
    plan: object
    descriptors: tuple
    argv: tuple
    record: dict
    approval_sha256: str
    _construction: object

    def __post_init__(self):
        require(self._construction is TOKEN, "host_admitted_preparation_ticket_required")

    @classmethod
    def admit(cls, launch, *, case_binding, native_argv, api, now=None):
        """Pure validation over actual accepted types and stable root input reads.

        api is imported from the exact pinned accepted core by the host. Unit
        fixtures inject only its filesystem/time boundaries, not grant booleans.
        This never extends expiry, publishes plans, signs or contacts an issuer.
        """
        require(isinstance(launch, api.PreparedPolicyLaunch) and launch.sealed is None
                and launch.private_profile_snapshot is not None,
                "prepared_unsealed_private_launch_required")
        plan = launch.mount.private_mount_plan
        require(isinstance(plan, api.ApprovedPrivateMountPlan), "existing_approved_plan_required")
        descriptors = launch.mount.private_mount_request["descriptors"]
        argv = launch.mount.private_mount_argv
        plan.authorize(descriptors, argv)
        record = api.read_root_configuration(APPROVAL)
        keys = {"schema_version", "case_binding", "identity", "plan_sha256", "argv_sha256",
                "native_argv", "host_policy_sha256", "preparer", "worker", "filter_sha256",
                "not_before", "expires_at", "argv"}
        require(type(record) is dict and set(record) == keys and record["schema_version"] == VERSION,
                "closed_native_preparation_approval_required")
        require(record["case_binding"] == case_binding and record["identity"] == launch.identity.to_json()
                and record["plan_sha256"] == plan.sha256 and record["argv_sha256"] == digest(argv)
                and record["native_argv"] == native_argv and record["argv"] == argv,
                "native_preparation_binding_changed")
        require(type(native_argv) is list and len(native_argv) >= 5
                and native_argv[0] == str(api.native_python)
                and native_argv[1:3] == ["-I", "-B"] and native_argv[4] == "--execute"
                and all(type(x) is str and "\0" not in x for x in native_argv),
                "literal_isolated_native_entrypoint_required")
        issuer, policy = api.current_issuer_policy()
        require(record["host_policy_sha256"] == digest(policy)
                and issuer["host_policy_sha256"] == digest(policy),
                "original_host_policy_changed")
        # Reuse the existing authority's COMPLETE normal physical grant and
        # descriptor checks. The native preparer interprets the approved mount
        # recipe; this does not widen or replace the issuer's command grammar.
        launch.verify_private_handoff()
        require(launch.grant.is_active(), "active_original_grant_required")
        require(record["worker"] == {"profile": WORKER, "source_sha256": WORKER_SOURCE},
                "fixed_worker_boundary_required")
        prep = record["preparer"]
        require(type(prep) is dict and set(prep) == {"entrypoint", "sha256", "profile", "profile_source_sha256", "loaded_sha256", "python_sha256", "files"}
                and prep["entrypoint"] == native_argv[3] and
                re.fullmatch(r"herdr-offline-prep-[0-9a-f]{16}", prep["profile"] or "")
                and prep["profile"] != WORKER,
                "exact_separate_trusted_preparer_required")
        source = Path(prep["entrypoint"])
        require(source.is_absolute() and source.parent == api.native_source_directory,
                "immutable_native_preparer_location_required")
        for field in (prep["sha256"], prep["profile_source_sha256"], prep["loaded_sha256"], prep["python_sha256"], record["filter_sha256"]):
            require(type(field) is str and re.fullmatch(r"[0-9a-f]{64}", field), "preparation_digest_invalid")
        require(api.immutable_sha256(source) == prep["sha256"] and
                api.immutable_sha256(api.native_source_directory / "overlays/trusted-preparation.apparmor")
                == prep["profile_source_sha256"] and
                api.immutable_sha256(api.native_python) == prep["python_sha256"] and
                api.loaded_profile_sha256(prep["profile"]) == prep["loaded_sha256"] and
                hashlib.sha256(api.filter_bytes()).hexdigest() == record["filter_sha256"],
                "preparation_source_or_filter_changed")
        clock = datetime.now(UTC) if now is None else now
        start, expiry = (datetime.fromisoformat(record[k]) for k in ("not_before", "expires_at"))
        require(start.tzinfo is not None and expiry.tzinfo is not None and
                start <= clock < expiry <= datetime.fromisoformat(launch.grant.expires_at),
                "native_preparation_expired")
        return cls(launch.identity, plan, tuple(descriptors), tuple(argv), record, digest(record), TOKEN)

    def revalidate(self, api):
        require(digest(api.read_root_configuration(APPROVAL)) == self.approval_sha256,
                "native_preparation_approval_changed")
        self.plan.authorize(list(self.descriptors), list(self.argv))
        return self


def issuer_compatibility_request(launch, *, case_binding, native_argv):
    """DATA ONLY exact request for the existing root operator, never issuance.

    Existing issuer policy must explicitly approve the new immutable entrypoint
    and host cgroup before this can operate. Do not catch that policy's denial.
    This is an additive contract: old approved bwrap argv remains unchanged.
    """
    return {"schema_version": VERSION, "authority": "EXISTING_HERDR_ROOT_OPERATOR_ONLY",
            "status": "UNISSUED", "case_binding": case_binding,
            "identity": launch.identity.to_json(),
            "plan_sha256": launch.mount.private_mount_plan.sha256,
            "argv_sha256": digest(launch.mount.private_mount_argv),
            "native_argv": native_argv}
