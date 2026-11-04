"""Derive a nonsecret SDK identity in the authenticated host bootstrap.

The host uses its sealed full profile.  It sends only the exact selected pool
reference; the raw credential remains available solely to host_model_transport.
"""
import json
import os

from .private_profile_namespace import profile_identity
from .security import PolicyDenied


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate protected profile key")
        result[key] = value
    return result


def derive_host_reference(grant, snapshot):
    if not grant.is_active() or grant.runtime_assurance.credentials_isolated is not True:
        raise PolicyDenied("host_reference_observed_grant_required")
    sdk_files = snapshot.sdk_files
    files = {item.relative: item for item in snapshot.files}
    if ("auth.json" not in files or len(grant.provider_routes) != 1
            or len(grant.credential_refs) != 1):
        raise PolicyDenied("host_reference_single_canonical_route_required")
    route = grant.provider_routes[0]
    if (route.provider != "nous" or route.base_url != "https://inference-api.nousresearch.com/v1"
            or route.api_mode != "chat_completions"
            or tuple(route.credential_refs) != tuple(grant.credential_refs)):
        raise PolicyDenied("host_reference_canonical_route_required")
    auth = files["auth.json"]
    auth.verify()
    try:
        store = json.loads(os.pread(auth.fd, auth.size, 0), object_pairs_hook=_unique_object)
        rows = store["credential_pool"]["nous"]
        if type(rows) is not list or len(rows) != 1 or type(rows[0]) is not dict:
            raise ValueError()
        entry_id = rows[0]["id"]
        if type(entry_id) is not str or not entry_id or "pool:nous:" + entry_id != grant.credential_refs[0]:
            raise ValueError()
        config = files["config.yaml"]
        config.verify()
        settings = json.loads(os.pread(config.fd, config.size, 0), object_pairs_hook=_unique_object)
        model = settings["model"]["default"]
        if type(model) is not str or not model.endswith(":free"):
            raise ValueError()
    except (KeyError, TypeError, ValueError, UnicodeError) as exc:
        raise PolicyDenied("host_reference_protected_selection_invalid") from exc
    projection = profile_identity(snapshot.name,
        {item.relative: item.sha256 for item in sdk_files})
    identity = grant.identity
    return {
        "provider": "nous", "entry_id": entry_id,
        "credential_ref": grant.credential_refs[0], "endpoint": route.base_url,
        "api_mode": route.api_mode, "model": model,
        "profile_sha256": snapshot.identity["manifest_sha256"],
        "projection_sha256": projection["manifest_sha256"],
        "grant_hash": grant.hash, "workspace": grant.workspace_root,
        "fence": str(identity.fencing_token), "lineage": identity.parent_task_id,
        "tag": "host_reference",
    }
