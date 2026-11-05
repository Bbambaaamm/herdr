"""One closed root-owned SOURCE candidate roster for root + one child.

The roster narrows an already authorized case. It is not an issuer, grant,
signature, observed runtime assurance or permission to execute this source.
"""
from dataclasses import dataclass
import hashlib
import json
import re

NONCE = "03414499dd0d1986968b2393d44275d0"
SUFFIX = NONCE[:16]
VERSION = "herdr-offline-roster-2"
ROSTER_PATH = "/etc/herdr/offline-" + SUFFIX + "/roster.json"
CONTEXT_ROOT = "/var/lib/herdr-offline-observer-" + SUFFIX + "/contexts"
CHILD_PATH = CONTEXT_ROOT + "/child-slot.json"
SOCKET_PATH = "/run/herdr-offline-" + SUFFIX + "/observer.sock"
OBSERVER_LABEL = "herdr-offline-observer-" + SUFFIX
CONTROLLER_LABEL = "herdr-offline-controller-" + SUFFIX
PREP_LABEL = "herdr-offline-prep-" + SUFFIX
WORKER_LABEL = "herdr189-reference-lifetime"
WORKER_SOURCE = "42c8d021a856eb5e9c59b9f335695f296ea17b91eb3a04044ca6ef0e7bdf6d62"
MAX_BYTES = 1048576


class Denied(ValueError): pass
def require(ok, code):
    if not ok: raise Denied(code)
def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode()
def digest(value): return hashlib.sha256(canonical(value)).hexdigest()
def hex64(value): return type(value) is str and re.fullmatch("[0-9a-f]{64}", value) is not None
def exact(value, keys): require(type(value) is dict and set(value) == set(keys), "closed_roster_schema_required")
def positive(value): return type(value) is int and value > 0


def decode(raw):
    require(type(raw) is bytes and 0 < len(raw) <= MAX_BYTES, "bounded_roster_required")
    def unique(rows):
        value = {}
        for k, v in rows:
            require(k not in value, "duplicate_roster_key"); value[k] = v
        return value
    return json.loads(raw, object_pairs_hook=unique,
        parse_constant=lambda _x: (_ for _ in ()).throw(Denied("nonfinite_roster")))


@dataclass(frozen=True)
class Roster:
    raw: bytes
    child_raw: bytes | None = None

    @classmethod
    def parse(cls, raw, identity_type):
        doc = decode(raw)
        exact(doc, {"schema", "nonce", "case_binding", "not_before", "deadline", "host_policy_sha256",
            "controller", "observer", "preparer", "slots", "worker_source_sha256"})
        require(doc["schema"] == VERSION and doc["nonce"] == NONCE and
            type(doc["not_before"]) is int and type(doc["deadline"]) is int and
            0 < doc["deadline"] - doc["not_before"] <= 1800 and hex64(doc["host_policy_sha256"])
            and doc["worker_source_sha256"] == WORKER_SOURCE, "invalid_case_roster")
        binding = doc["case_binding"]
        exact(binding, {"nonce", "challenge", "boot_id", "authority_sha256", "build_sha256"})
        require(binding["nonce"] == NONCE and type(binding["boot_id"]) is str and binding["boot_id"]
            and all(hex64(binding[k]) for k in ("challenge", "authority_sha256", "build_sha256")),
            "invalid_case_binding")
        controller = doc["controller"]
        exact(controller, {"uid", "gid", "pid", "start_ticks", "exe_sha256", "cgroup",
                           "profile", "source_sha256", "loaded_sha256"})
        require(controller["uid"] == controller["gid"] == 1001 and
            positive(controller["pid"]) and positive(controller["start_ticks"]) and
            hex64(controller["exe_sha256"]) and type(controller["cgroup"]) is str and
            re.fullmatch(r"/system\.slice/[A-Za-z0-9_.@:-]+\.service", controller["cgroup"])
            and controller["profile"] == CONTROLLER_LABEL and hex64(controller["source_sha256"])
            and hex64(controller["loaded_sha256"]),
            "invalid_original_controller_binding")
        for key, label in (("observer", OBSERVER_LABEL), ("preparer", PREP_LABEL)):
            value = doc[key]
            exact(value, {"profile", "source_sha256", "loaded_sha256", "entrypoint", "files", "python", "python_sha256"})
            require(value["profile"] == label and all(hex64(value[k]) for k in
                ("source_sha256", "loaded_sha256", "python_sha256")) and
                type(value["entrypoint"]) is str and value["entrypoint"].startswith("/opt/agent-platform/herdr-offline-" + SUFFIX + "/")
                and type(value["python"]) is str and value["python"].startswith("/opt/") and
                type(value["files"]) is dict and 1 <= len(value["files"]) <= 16 and
                all(type(k) is str and re.fullmatch(r"[a-z_]+\.py", k) and hex64(v) for k, v in value["files"].items()),
                "invalid_immutable_helper_binding")
        require(type(doc["slots"]) is dict and set(doc["slots"]) in ({"root"}, {"root", "child"}),
                "root_initial_or_closed_two_slot_roster_required")
        identities = {}
        for role in (role for role in ("root", "child") if role in doc["slots"]):
            slot = doc["slots"][role]
            exact(slot, {"identity", "workspace", "unit", "stdio", "marker"})
            identity = identity_type.from_dict(slot["identity"])
            identities[role] = identity
            require(slot["unit"] == "herdr-offline-" + role + "-" + SUFFIX + ".service"
                and type(slot["workspace"]) is str and slot["workspace"].startswith("/home/agentops/tmp/hermes-")
                and "/../" not in slot["workspace"] and "//" not in slot["workspace"]
                and slot["workspace"].endswith("/workspace"), "invalid_exact_slot")
            require(type(slot["marker"]) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", slot["marker"]),
                    "fixed_case_pane_marker_required")
            exact(slot["stdio"], {"0", "1", "2"})
            for number in ("0", "1", "2"):
                stream = slot["stdio"][number]
                exact(stream, {"path", "device", "inode", "rdev"})
                require(type(stream["path"]) is str and re.fullmatch(r"/dev/pts/[0-9]+", stream["path"]) and
                    all(type(stream[k]) is int and stream[k] >= 0 for k in ("device", "inode", "rdev")),
                    "invalid_root_pinned_stdio")
            require(len({slot["stdio"][n]["path"] for n in ("0", "1", "2")}) == 1,
                    "one_exact_owned_terminal_required")
        if "child" in identities:
            a, b = identities["root"], identities["child"]
            require(a.consumer == b.consumer and a.task_id != b.task_id and a.agent_id != b.agent_id
                and a.run_token != b.run_token and a.fencing_token != b.fencing_token
                and b.parent_task_id == a.task_id and b.parent_agent_id == a.agent_id,
                "root_child_lineage_or_fence_changed")
        return cls(canonical(doc))

    @property
    def document(self): return decode(self.raw)
    @property
    def sha256(self): return hashlib.sha256(self.raw).hexdigest()
    @property
    def roles(self):
        return tuple(role for role in ("root", "child") if role in self.document["slots"] or role == "child" and self.child_raw is not None)
    def slot(self, role):
        require(role in ("root", "child"), "unknown_roster_role")
        if role == "child" and self.child_raw is not None: return decode(self.child_raw)["slot"]
        require(role in self.document["slots"], "canonical_child_not_yet_appended")
        return self.document["slots"][role]
    def role_for(self, identity):
        selected = [role for role in self.roles if self.slot(role)["identity"] == identity.to_json()]
        require(len(selected) == 1, "identity_not_in_admitted_roster")
        return selected[0]
    def projection_sha256(self, role):
        self.slot(role)
        return hashlib.sha256(self.child_raw).hexdigest() if role == "child" and self.child_raw is not None else None
    def live(self, *, now, boot_id):
        doc = self.document
        require(type(now) in (int, float) and doc["not_before"] <= now < doc["deadline"]
            and boot_id == doc["case_binding"]["boot_id"], "roster_expired_or_boot_changed")
        return self

    def with_child(self, raw, identity_type, *, root_context):
        """Parse a root-owned append receipt; never changes ROOT base digest."""
        require(set(self.document["slots"]) == {"root"} and self.child_raw is None, "child_append_once_required")
        extension = decode(raw)
        exact(extension, {"schema", "root_roster_sha256", "root_context_sha256", "slot", "grant_sha256",
            "parent_grant_sha256", "parent_bundle_sha256", "plan_sha256", "original_request_sha256", "original_peer"})
        require(extension["schema"] == "herdr-canonical-child-projection-3" and
            extension["root_roster_sha256"] == self.sha256 and extension["root_context_sha256"] == digest(root_context)
            and root_context["roster_sha256"] == self.sha256 and root_context["role"] == "root"
            and root_context["identity"] == self.slot("root")["identity"] and
            all(hex64(extension[k]) for k in ("grant_sha256", "parent_grant_sha256", "parent_bundle_sha256",
                "plan_sha256", "original_request_sha256")) and
            extension["original_peer"] == [self.document["controller"]["pid"], 1001, 1001,
                self.document["controller"]["start_ticks"]], "canonical_child_append_binding_changed")
        # Reuse the complete original slot+lineage validator. This temporary
        # composed view is NOT substituted for the immutable authority digest.
        complete = self.document; complete["slots"]["child"] = extension["slot"]
        type(self).parse(canonical(complete), identity_type)
        return type(self)(self.raw, canonical(extension))


def load_roster(read_json, identity_type):
    from pathlib import Path
    base = Roster.parse(canonical(read_json(Path(ROSTER_PATH))), identity_type)
    if "child" in base.roles: return base
    try: child = read_json(Path(CHILD_PATH))
    except FileNotFoundError: return base
    return base.with_child(canonical(child), identity_type,
        root_context=read_json(Path(CONTEXT_ROOT) / "root.json"))


def capture_context(roster, role, request, peer):
    """Call ONLY after existing issuer _validate and _host_peer succeeded.

    Captures exact prior authority as data. It creates no authority, private
    key or signature and does not assert any runtime-isolation boolean.
    """
    slot, doc = roster.slot(role), roster.document
    proposal = request["proposal"]
    require(proposal["plan"]["identity"] == slot["identity"] and
        request["grant"]["identity"] == slot["identity"] and
        request["grant"]["workspace_root"] == slot["workspace"] and
        request["policy_sha256"] == doc["host_policy_sha256"] and
        peer[0] == doc["controller"]["pid"] and peer[1] == peer[2] == 1001 and
        peer[3] == doc["controller"]["start_ticks"], "canonical_original_custody_differs")
    return {"schema": "herdr-observer-context-2", "roster_sha256": roster.sha256, "role": role,
        "slot_sha256": digest(slot), "child_projection_sha256": roster.projection_sha256(role),
        "identity": slot["identity"], "workspace": slot["workspace"], "unit": slot["unit"],
        "grant_sha256": proposal["grant_sha256"], "grant_expires_at": request["grant"]["expires_at"],
        "parent_grant_hash": request["grant"].get("parent_grant_hash"),
        "parent_grant": request["parent_grant"],
        "plan": proposal["plan"], "plan_sha256": digest(proposal["plan"]),
        "approved_profile": proposal["approved_profile"], "argv": proposal["argv"],
        "original_request_sha256": digest(request), "original_peer": list(peer)}
