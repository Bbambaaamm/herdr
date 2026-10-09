"""Invocation-time security contract for Herdr issue #76.

This module is deliberately provider/runtime neutral.  It turns an admitted
capability scope into an immutable, authenticated invocation grant and enforces
the parts which can be decided without trusting model-produced content.

The physical sandbox remains an execution-runtime responsibility.  Process
tools therefore require an explicit RuntimeAssurance proving that the actual
sandbox/network/credential boundary is no broader than the grant.
"""
from __future__ import annotations

import hashlib
import base64
import json
import os
import re
import stat
import socket
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from urllib.parse import urlsplit
from typing import Any, Callable, Iterable, Mapping, Sequence

from herdr.capability import CapabilityScope, DataClass, Egress, Retention, Training

SECURITY_GRANT_VERSION = "herdr.security-grant.v1"
SIGNED_ENVELOPE_VERSION = "herdr.signed-grant.v2"
POLICY_BUNDLE_VERSION = "herdr.policy-bundle.v1"
_MAX_POLICY_BYTES = 256 * 1024
_MAX_ARG_DEPTH = 16
_MAX_ARG_ITEMS = 4096
_MAX_ARG_STRING = 256 * 1024
_TOKEN = re.compile(r"^[A-Za-z0-9._:/@+-]{1,256}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_V4A_SINGLE_HEADER = re.compile(
    r"^\*\*\*\s*(Update|Add|Delete)\s+File:\s*(.+?)\s*$"
)
_V4A_MOVE_HEADER = re.compile(
    r"^\*\*\*\s*Move\s+File:\s*(.+?)\s*->\s*(.+?)\s*$"
)
_V4A_ANY_FILE_HEADER = re.compile(
    r"^\*\*\*\s*(?:Update|Add|Delete|Move)\s+File:"
)
_SECRET_KEY = re.compile(
    r"(?:^|_)(?:password|passwd|secret|api_key|apikey|access_key|access_token|"
    r"refresh_token|private_key|client_secret|authorization|credential)(?:$|_)",
    re.IGNORECASE,
)
_SECRET_VALUE = tuple(
    re.compile(pattern)
    for pattern in (
        r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----",
        r"\bghp_[A-Za-z0-9]{20,}\b",
        r"\bgithub_pat_[A-Za-z0-9_]{20,}\b",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
        r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
        r"\bAKIA[0-9A-Z]{16}\b",
        r"\bAIza[0-9A-Za-z_-]{20,}\b",
    )
)
APPROVAL_SOCKET = Path("/run/herdr-policy/approval.sock")


def _credential_ref(value: Any, name: str) -> str:
    ref = _token(value, name)
    if any(pattern.search(ref) for pattern in _SECRET_VALUE):
        raise SecurityError(f"{name} contains secret material")
    if not re.fullmatch(r"pool:[A-Za-z0-9._-]+:[A-Za-z0-9._-]+", ref):
        raise SecurityError(f"{name} must be an opaque pool identity")
    return ref


def _credential_refs(values: Any, name: str) -> tuple[str, ...]:
    return tuple(_credential_ref(value, name) for value in _tuple_tokens(values, name))


class SecurityError(ValueError):
    """Malformed or unauthenticated security contract."""


class PolicyDenied(PermissionError):
    """Fail-closed invocation denial with a stable, audit-safe reason."""

    def __init__(self, reason: str, detail: str = "") -> None:
        self.reason = _token(reason, "denial reason")
        self.detail = detail[:512]
        super().__init__(f"{reason}: {self.detail}" if self.detail else reason)


class RiskClass(StrEnum):
    READ = "read"
    WORKSPACE_WRITE = "workspace_write"
    DELEGATION = "delegation"
    RESULT_SUBMISSION = "result_submission"
    PROCESS = "process"
    EXTERNAL_SIDE_EFFECT = "external_side_effect"
    CREDENTIAL_USE = "credential_use"
    PHYSICAL = "physical"


class NetworkAccess(StrEnum):
    NONE = "none"
    PROVIDER_ONLY = "provider_only"
    GLOBAL = "global"


_NETWORK_ORDER = {
    NetworkAccess.NONE: 0,
    NetworkAccess.PROVIDER_ONLY: 1,
    NetworkAccess.GLOBAL: 2,
}
_EGRESS_ORDER = {value: index for index, value in enumerate(Egress)}
_RETENTION_ORDER = {value: index for index, value in enumerate(Retention)}
_TRAINING_ORDER = {value: index for index, value in enumerate(Training)}


def _token(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _TOKEN.fullmatch(value):
        raise SecurityError(f"{name} must be a safe nonempty identifier")
    return value


def _sha256(value: Any, name: str) -> str:
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise SecurityError(f"{name} must be lowercase sha256")
    return value


def _int(value: Any, name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum or value > (1 << 63) - 1:
        raise SecurityError(f"{name} must be a bounded integer >= {minimum}")
    return value


def _tuple_tokens(value: Any, name: str) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise SecurityError(f"{name} must be an array")
    parsed = tuple(sorted(_token(item, name) for item in value))
    if len(parsed) != len(set(parsed)):
        raise SecurityError(f"{name} contains duplicates")
    return parsed


def _utc(value: Any, name: str) -> datetime:
    if not isinstance(value, str) or len(value) > 64:
        raise SecurityError(f"{name} must be an ISO-8601 UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise SecurityError(f"{name} must be an ISO-8601 UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != UTC.utcoffset(parsed):
        raise SecurityError(f"{name} must be an ISO-8601 UTC timestamp")
    return parsed


def _enum(typ: type[StrEnum], value: Any, name: str) -> StrEnum:
    try:
        return typ(value)
    except (TypeError, ValueError) as exc:
        raise SecurityError(f"invalid {name}") from exc


def canonical_json_bytes(value: Mapping[str, Any]) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SecurityError("policy is not canonical-json serializable") from exc


def canonical_digest(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


@dataclass(frozen=True)
class InvocationIdentity:
    consumer: str
    agent_id: str
    parent_agent_id: str
    parent_task_id: str
    task_id: str
    run_token: str
    fencing_token: int

    def __post_init__(self) -> None:
        for name in ("consumer", "agent_id", "parent_agent_id", "parent_task_id", "task_id", "run_token"):
            _token(getattr(self, name), name)
        _int(self.fencing_token, "fencing_token", minimum=1)

    def to_json(self) -> dict[str, Any]:
        return {
            "consumer": self.consumer,
            "agent_id": self.agent_id,
            "parent_agent_id": self.parent_agent_id,
            "parent_task_id": self.parent_task_id,
            "task_id": self.task_id,
            "run_token": self.run_token,
            "fencing_token": self.fencing_token,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "InvocationIdentity":
        _exact_keys(raw, {"consumer", "agent_id", "parent_agent_id", "parent_task_id", "task_id", "run_token", "fencing_token"})
        return cls(**dict(raw))


@dataclass(frozen=True)
class RuntimeAssurance:
    """Host-produced evidence about the *physical* child boundary.

    writable_roots are the paths actually mounted writable inside the child,
    not paths the model requested. credentials_isolated means raw provider/tool
    credential files and credential-bearing env are absent from tool-spawned
    processes; a broker/reference may still be used by the parent runtime.
    """
    sandbox_verified: bool
    sandbox_attestation_sha256: str | None
    network_access: NetworkAccess
    writable_roots: tuple[str, ...]
    credentials_isolated: bool

    def __post_init__(self) -> None:
        if type(self.sandbox_verified) is not bool or type(self.credentials_isolated) is not bool:
            raise SecurityError("runtime assurance booleans must be explicit")
        object.__setattr__(self, "network_access", _enum(NetworkAccess, self.network_access, "network_access"))
        if not isinstance(self.writable_roots, (tuple, list)):
            raise SecurityError("runtime writable_roots must be an array")
        roots = tuple(sorted(str(Path(root).expanduser().resolve(strict=False)) for root in self.writable_roots))
        object.__setattr__(self, "writable_roots", roots)
        if self.sandbox_verified:
            _sha256(self.sandbox_attestation_sha256, "sandbox_attestation_sha256")
        elif self.sandbox_attestation_sha256 is not None:
            raise SecurityError("unverified sandbox cannot carry an attestation digest")
        if (self.writable_roots or self.network_access != NetworkAccess.NONE) and not self.sandbox_verified:
            raise SecurityError("unverified runtime cannot assert writable/network capability")

    def to_json(self) -> dict[str, Any]:
        return {
            "sandbox_verified": self.sandbox_verified,
            "sandbox_attestation_sha256": self.sandbox_attestation_sha256,
            "network_access": self.network_access.value,
            "writable_roots": list(self.writable_roots),
            "credentials_isolated": self.credentials_isolated,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "RuntimeAssurance":
        _exact_keys(
            raw,
            {
                "sandbox_verified", "sandbox_attestation_sha256", "network_access",
                "writable_roots", "credentials_isolated",
            },
        )
        return cls(**dict(raw))


@dataclass(frozen=True)
class ToolRule:
    tool: str
    risk: RiskClass
    allowed_arg_keys: tuple[str, ...]
    path_fields: tuple[str, ...] = ()
    allowed_roots: tuple[str, ...] = ()
    credential_ref_fields: tuple[str, ...] = ()
    requires_process: bool = False
    requires_sandbox: bool = False
    result_slot: Any = None

    def __post_init__(self) -> None:
        _token(self.tool, "tool")
        object.__setattr__(self, "risk", _enum(RiskClass, self.risk, "risk"))
        for name in ("allowed_arg_keys", "path_fields", "credential_ref_fields"):
            object.__setattr__(self, name, _tuple_tokens(getattr(self, name), name))
        if not set(self.path_fields) <= set(self.allowed_arg_keys):
            raise SecurityError("path_fields must be allowed arguments")
        if not set(self.credential_ref_fields) <= set(self.allowed_arg_keys):
            raise SecurityError("credential_ref_fields must be allowed arguments")
        if not isinstance(self.allowed_roots, (tuple, list)):
            raise SecurityError("allowed_roots must be an array")
        roots = tuple(sorted(str(Path(root).expanduser().resolve(strict=False)) for root in self.allowed_roots))
        if self.path_fields and not roots:
            raise SecurityError("path-constrained rule requires at least one root")
        if any(not Path(root).is_absolute() for root in roots):
            raise SecurityError("tool roots must be absolute")
        object.__setattr__(self, "allowed_roots", roots)
        if self.result_slot is not None:
            from .result_submission import ResultSlot
            if not isinstance(self.result_slot, ResultSlot) or self.tool != "herdr_submit_result":
                raise SecurityError("result slot requires the submission tool")
        if type(self.requires_process) is not bool or type(self.requires_sandbox) is not bool:
            raise SecurityError("tool runtime requirements must be booleans")

    def to_json(self) -> dict[str, Any]:
        return {
            **({"result_slot": self.result_slot.to_json()} if self.result_slot is not None else {}),
            "tool": self.tool,
            "risk": self.risk.value,
            "allowed_arg_keys": list(self.allowed_arg_keys),
            "path_fields": list(self.path_fields),
            "allowed_roots": list(self.allowed_roots),
            "credential_ref_fields": list(self.credential_ref_fields),
            "requires_process": self.requires_process,
            "requires_sandbox": self.requires_sandbox,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ToolRule":
        raw = dict(raw)
        slot = raw.pop("result_slot", None)
        if slot is not None:
            from .result_submission import ResultSlot
            slot = ResultSlot.from_dict(slot)
        _exact_keys(
            raw,
            {
                "tool", "risk", "allowed_arg_keys", "path_fields", "allowed_roots",
                "credential_ref_fields", "requires_process", "requires_sandbox",
            },
        )
        return cls(**raw, result_slot=slot)


@dataclass(frozen=True)
class ProcessPolicy:
    enabled: bool
    tools: tuple[str, ...]
    max_network: NetworkAccess
    writable_roots: tuple[str, ...] = ()
    require_credentials_isolated: bool = True

    def __post_init__(self) -> None:
        if type(self.enabled) is not bool or type(self.require_credentials_isolated) is not bool:
            raise SecurityError("process policy booleans must be explicit")
        if self.enabled and not self.require_credentials_isolated:
            raise SecurityError("enabled process policy must require credential isolation")
        object.__setattr__(self, "tools", _tuple_tokens(self.tools, "process tools"))
        object.__setattr__(self, "max_network", _enum(NetworkAccess, self.max_network, "max_network"))
        if not isinstance(self.writable_roots, (tuple, list)):
            raise SecurityError("process writable_roots must be an array")
        roots = tuple(sorted(str(Path(root).expanduser().resolve(strict=False)) for root in self.writable_roots))
        object.__setattr__(self, "writable_roots", roots)
        if not self.enabled and (self.tools or self.writable_roots or self.max_network != NetworkAccess.NONE):
            raise SecurityError("disabled process policy cannot grant process capabilities")

    def is_subset_of(self, parent: "ProcessPolicy") -> bool:
        return (
            (not self.enabled or parent.enabled)
            and set(self.tools) <= set(parent.tools)
            and _NETWORK_ORDER[self.max_network] <= _NETWORK_ORDER[parent.max_network]
            and _roots_subset(self.writable_roots, parent.writable_roots)
            and (not parent.require_credentials_isolated or self.require_credentials_isolated)
        )

    def to_json(self) -> dict[str, Any]:
        return {
            "enabled": self.enabled,
            "tools": list(self.tools),
            "max_network": self.max_network.value,
            "writable_roots": list(self.writable_roots),
            "require_credentials_isolated": self.require_credentials_isolated,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProcessPolicy":
        _exact_keys(
            raw,
            {"enabled", "tools", "max_network", "writable_roots", "require_credentials_isolated"},
        )
        return cls(**dict(raw))


@dataclass(frozen=True)
class ProviderRoute:
    provider: str
    base_url: str
    api_mode: str
    regions: tuple[str, ...]
    data_classes: tuple[DataClass, ...]
    max_egress: Egress
    max_retention: Retention
    training: Training
    credential_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _token(self.provider, "provider")
        _token(self.api_mode, "api_mode")
        if not isinstance(self.base_url, str) or len(self.base_url) > 2048:
            raise SecurityError("provider base_url invalid")
        endpoint = urlsplit(self.base_url)
        if endpoint.scheme != "https" or not endpoint.hostname or endpoint.username or endpoint.password or endpoint.fragment:
            raise SecurityError("provider base_url must be an HTTPS endpoint without credentials")
        object.__setattr__(self, "regions", _tuple_tokens(self.regions, "provider regions"))
        if not isinstance(self.data_classes, (tuple, list)):
            raise SecurityError("provider data_classes must be an array")
        try:
            classes = tuple(sorted((DataClass(item) for item in self.data_classes), key=str))
        except ValueError as exc:
            raise SecurityError("invalid provider data class") from exc
        if len(classes) != len(set(classes)):
            raise SecurityError("provider data_classes contains duplicates")
        object.__setattr__(self, "data_classes", classes)
        object.__setattr__(self, "max_egress", _enum(Egress, self.max_egress, "max_egress"))
        object.__setattr__(self, "max_retention", _enum(Retention, self.max_retention, "max_retention"))
        object.__setattr__(self, "training", _enum(Training, self.training, "training"))
        refs = _credential_refs(self.credential_refs, "provider credential_refs")
        object.__setattr__(self, "credential_refs", refs)

    def to_json(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "base_url": self.base_url,
            "api_mode": self.api_mode,
            "regions": list(self.regions),
            "data_classes": [item.value for item in self.data_classes],
            "max_egress": self.max_egress.value,
            "max_retention": self.max_retention.value,
            "training": self.training.value,
            "credential_refs": list(self.credential_refs),
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ProviderRoute":
        _exact_keys(
            raw,
            {"provider", "base_url", "api_mode", "regions", "data_classes", "max_egress", "max_retention", "training", "credential_refs"},
        )
        return cls(**dict(raw))


@dataclass(frozen=True)
class ApprovalEvidence:
    approval_id: str
    identity: InvocationIdentity
    tool: str
    args_sha256: str

    def __post_init__(self) -> None:
        _token(self.approval_id, "approval_id")
        if not isinstance(self.identity, InvocationIdentity):
            raise SecurityError("approval identity must be typed")
        _token(self.tool, "approval tool")
        _sha256(self.args_sha256, "args_sha256")

    def to_json(self) -> dict[str, Any]:
        return {
            "approval_id": self.approval_id,
            "identity": self.identity.to_json(),
            "tool": self.tool,
            "args_sha256": self.args_sha256,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "ApprovalEvidence":
        _exact_keys(raw, {"approval_id", "identity", "tool", "args_sha256"})
        return cls(
            approval_id=raw["approval_id"],
            identity=InvocationIdentity.from_dict(raw["identity"]),
            tool=raw["tool"],
            args_sha256=raw["args_sha256"],
        )


@dataclass(frozen=True)
class SecurityGrant:
    grant_id: str
    workspace_root: str
    identity: InvocationIdentity
    scope: CapabilityScope
    tool_rules: tuple[ToolRule, ...]
    process: ProcessPolicy
    runtime_assurance: RuntimeAssurance
    provider_routes: tuple[ProviderRoute, ...]
    credential_refs: tuple[str, ...]
    approvals: tuple[ApprovalEvidence, ...]
    approval_required_for: tuple[RiskClass, ...]
    issued_at: str
    expires_at: str
    parent_grant_hash: str | None = None
    schema_version: str = SECURITY_GRANT_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != SECURITY_GRANT_VERSION:
            raise SecurityError("unsupported security grant schema")
        _token(self.grant_id, "grant_id")
        if not isinstance(self.workspace_root, str) or not Path(self.workspace_root).is_absolute():
            raise SecurityError("workspace_root must be absolute")
        object.__setattr__(self, "workspace_root", str(Path(self.workspace_root).resolve(strict=False)))
        if self.parent_grant_hash is not None:
            _sha256(self.parent_grant_hash, "parent_grant_hash")
        if not isinstance(self.identity, InvocationIdentity) or not isinstance(self.scope, CapabilityScope):
            raise SecurityError("grant identity/scope must be typed")
        for name, values, typ in (
            ("tool_rules", self.tool_rules, ToolRule),
            ("provider_routes", self.provider_routes, ProviderRoute),
            ("approvals", self.approvals, ApprovalEvidence),
        ):
            if not isinstance(values, (tuple, list)) or any(not isinstance(item, typ) for item in values):
                raise SecurityError(f"{name} must contain {typ.__name__}")
            object.__setattr__(self, name, tuple(values))
        if not isinstance(self.process, ProcessPolicy):
            raise SecurityError("process policy must be typed")
        if not isinstance(self.runtime_assurance, RuntimeAssurance):
            raise SecurityError("runtime assurance must be host-produced and typed")
        object.__setattr__(self, "credential_refs", _credential_refs(self.credential_refs, "credential_refs"))
        if not isinstance(self.approval_required_for, (tuple, list)):
            raise SecurityError("approval_required_for must be an array")
        risks = tuple(sorted((_enum(RiskClass, value, "approval risk") for value in self.approval_required_for), key=str))
        if len(risks) != len(set(risks)):
            raise SecurityError("duplicate approval risk")
        object.__setattr__(self, "approval_required_for", risks)
        issued, expires = _utc(self.issued_at, "issued_at"), _utc(self.expires_at, "expires_at")
        if expires <= issued:
            raise SecurityError("grant expires_at must be after issued_at")
        rule_names = [rule.tool for rule in self.tool_rules]
        if len(rule_names) != len(set(rule_names)):
            raise SecurityError("duplicate tool rule")
        if set(rule_names) != set(self.scope.tools):
            raise SecurityError("tool rules must exactly cover the granted tool set")
        built_in_risk = {"read_file": RiskClass.READ, "search_files": RiskClass.READ,
                         "write_file": RiskClass.WORKSPACE_WRITE, "patch": RiskClass.WORKSPACE_WRITE,
                         "terminal": RiskClass.PROCESS, "execute_code": RiskClass.PROCESS,
                         "herdr_delegate_child": RiskClass.DELEGATION,
                         "herdr_submit_result": RiskClass.RESULT_SUBMISSION,
                         "herdr_verify_work": RiskClass.READ,
                         "herdr_external_knowledge": RiskClass.READ}
        for rule in self.tool_rules:
            if rule.tool in {"read_file", "search_files", "write_file", "patch"}:
                required = () if rule.tool == "patch" else ("path",)
                if not set(required) <= set(rule.path_fields) or not rule.allowed_roots or not _roots_subset(rule.allowed_roots, (self.workspace_root,)):
                    raise SecurityError("file tool paths must be workspace-scoped")
                if rule.tool == "patch" and "path" in rule.allowed_arg_keys and "path" not in rule.path_fields:
                    raise SecurityError("patch path argument must be constrained")
            if rule.tool == "herdr_delegate_child" and (
                    not rule.requires_sandbox or rule.requires_process
                    or set(rule.allowed_arg_keys) - {"key", "role", "objective", "prompt", "tool", "permission", "cwd", "ownership"}):
                raise SecurityError("delegation requires narrow sandboxed bridge rule")
            if rule.tool == "herdr_submit_result":
                if (not rule.requires_sandbox or rule.requires_process or rule.path_fields
                        or rule.credential_ref_fields or set(rule.allowed_arg_keys) != {"status","evidence","summary"}
                        or not rule.allowed_roots):
                    raise SecurityError("result submission requires a narrow sandboxed rule")
                if rule.result_slot is not None:
                    if (not _roots_subset((rule.result_slot.path,),rule.allowed_roots)
                            or rule.result_slot.identity_sha256 != canonical_digest(self.identity.to_json())):
                        raise SecurityError("result slot identity/root mismatch")
            if rule.tool == "herdr_verify_work" and (
                    not rule.requires_sandbox or rule.requires_process or rule.path_fields
                    or rule.credential_ref_fields or set(rule.allowed_arg_keys) not in ({"request_id"}, {"request_id", "handoff"})):
                raise SecurityError("work verification requires a closed sandboxed rule")
            if rule.tool == "herdr_external_knowledge" and (
                    not rule.requires_sandbox or rule.requires_process or rule.path_fields
                    or rule.credential_ref_fields
                    or set(rule.allowed_arg_keys) != {"provider_id", "query", "sources", "conversation_id"}):
                raise SecurityError("external knowledge requires a closed sandboxed read rule")
            if rule.risk == RiskClass.PROCESS and (not rule.requires_process or not rule.requires_sandbox):
                raise SecurityError("process tool requires process policy and sandbox")
            if rule.tool in built_in_risk and rule.risk != built_in_risk[rule.tool]:
                raise SecurityError("built-in tool risk cannot be reclassified")
        mandatory_gates = {
            RiskClass.EXTERNAL_SIDE_EFFECT,
            RiskClass.CREDENTIAL_USE,
            RiskClass.PHYSICAL,
        }
        required_gates = {rule.risk for rule in self.tool_rules if rule.risk in mandatory_gates}
        if not required_gates <= set(self.approval_required_for):
            raise SecurityError("high-risk side-effect approval gate missing")
        route_names = [route.provider for route in self.provider_routes]
        if len(route_names) != len(set(route_names)):
            raise SecurityError("duplicate provider route")
        if set(route_names) != set(self.scope.providers):
            raise SecurityError("provider routes must exactly cover granted providers")
        if any(not set(route.credential_refs) <= set(self.credential_refs) for route in self.provider_routes):
            raise SecurityError("provider route uses an ungranted credential reference")
        if any(approval.identity != self.identity for approval in self.approvals):
            raise SecurityError("approval identity differs from grant identity")
        if any(approval.tool not in set(rule_names) for approval in self.approvals):
            raise SecurityError("approval references an ungranted tool")

    @property
    def hash(self) -> str:
        return canonical_digest(self.to_json())

    def is_active(self, at: datetime | None = None) -> bool:
        now = at or datetime.now(UTC)
        return _utc(self.issued_at, "issued_at") <= now < _utc(self.expires_at, "expires_at")

    def require_subset_of(self, parent: "SecurityGrant") -> None:
        self.require_logical_subset_of(parent)
        observed,ceiling=self.runtime_assurance,parent.runtime_assurance
        network_order={NetworkAccess.NONE:0,NetworkAccess.PROVIDER_ONLY:1,NetworkAccess.GLOBAL:2}
        parent_result = next((rule for rule in parent.tool_rules
            if rule.risk == RiskClass.RESULT_SUBMISSION and rule.result_slot is not None), None)
        delegated_slots = ()
        if parent_result is not None:
            delegated_slots = tuple(rule.result_slot.path for rule in self.tool_rules
                if rule.risk == RiskClass.RESULT_SUBMISSION and rule.result_slot is not None
                and rule.tool == parent_result.tool
                and _roots_subset((rule.result_slot.path,), parent_result.allowed_roots))
        # This exception names only a host-bound result inode, never its directory.
        # Normal path/process writes still obey the parent's physical ceiling.
        allowed_writes = (*ceiling.writable_roots, *delegated_slots)
        if (network_order[observed.network_access]>network_order[ceiling.network_access]
                or not _roots_subset(observed.writable_roots,allowed_writes)
                or ceiling.credentials_isolated and not observed.credentials_isolated
                or ceiling.sandbox_verified and not observed.sandbox_verified):
            raise SecurityError("child runtime assurance escalates above parent")

    def require_logical_subset_of(self, parent: "SecurityGrant") -> None:
        """Compare an unsealed host proposal; never replace observed launch checks."""
        if not isinstance(parent, SecurityGrant):
            raise SecurityError("typed parent grant required")
        if self.parent_grant_hash != parent.hash:
            raise SecurityError("child parent grant hash mismatch")
        if (
            self.identity.consumer != parent.identity.consumer
            or self.identity.parent_agent_id != parent.identity.agent_id
            or self.identity.parent_task_id != parent.identity.task_id
        ):
            raise SecurityError("child parent identity mismatch")
        self.scope.require_subset_of(parent.scope)
        if (_utc(self.issued_at, "issued_at") < _utc(parent.issued_at, "issued_at")
                or _utc(self.expires_at, "expires_at") > _utc(parent.expires_at, "expires_at")):
            raise SecurityError("child lifetime exceeds parent interval")
        if not self.process.is_subset_of(parent.process):
            raise SecurityError("child process policy escalates above parent")
        if not _path_within(Path(self.workspace_root), Path(parent.workspace_root)):
            raise SecurityError("child workspace escalates above parent")
        parent_rules = {rule.tool: rule for rule in parent.tool_rules}
        for child_rule in self.tool_rules:
            parent_rule = parent_rules.get(child_rule.tool)
            if parent_rule is None:
                raise SecurityError("child tool rule missing from parent")
            if (child_rule.result_slot is not None and parent_rule.result_slot is not None
                    and child_rule.result_slot.max_bytes > parent_rule.result_slot.max_bytes):
                raise SecurityError("child result bound exceeds parent")
            if not set(child_rule.allowed_arg_keys) <= set(parent_rule.allowed_arg_keys):
                raise SecurityError("child tool argument ceiling escalates above parent")
            required_path_fields = set(parent_rule.path_fields)
            if not required_path_fields <= set(child_rule.path_fields):
                raise SecurityError("child weakens parent path constraint")
            if not _roots_subset(child_rule.allowed_roots, parent_rule.allowed_roots):
                raise SecurityError("child filesystem ceiling escalates above parent")
            if not set(parent_rule.credential_ref_fields) <= set(child_rule.credential_ref_fields):
                raise SecurityError("child weakens parent credential constraint")
            if parent_rule.requires_process and not child_rule.requires_process:
                raise SecurityError("child weakens parent process requirement")
            if parent_rule.requires_sandbox and not child_rule.requires_sandbox:
                raise SecurityError("child weakens parent sandbox requirement")
            if child_rule.risk != parent_rule.risk:
                raise SecurityError("child cannot reclassify parent tool risk")
        if not set(self.credential_refs) <= set(parent.credential_refs):
            raise SecurityError("child credential references escalate above parent")
        parent_routes = {route.provider: route for route in parent.provider_routes}
        for route in self.provider_routes:
            ceiling = parent_routes.get(route.provider)
            if ceiling is None or not _route_subset(route, ceiling):
                raise SecurityError("child provider route escalates above parent")
        child_risks = {rule.risk for rule in self.tool_rules}
        if not set(self.approval_required_for) >= (set(parent.approval_required_for) & child_risks):
            raise SecurityError("child weakens parent approval requirements")

    def to_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "grant_id": self.grant_id,
            "workspace_root": self.workspace_root,
            "identity": self.identity.to_json(),
            "scope": self.scope.to_json(),
            "tool_rules": [rule.to_json() for rule in self.tool_rules],
            "process": self.process.to_json(),
            "runtime_assurance": self.runtime_assurance.to_json(),
            "provider_routes": [route.to_json() for route in self.provider_routes],
            "credential_refs": list(self.credential_refs),
            "approvals": [approval.to_json() for approval in self.approvals],
            "approval_required_for": [risk.value for risk in self.approval_required_for],
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "parent_grant_hash": self.parent_grant_hash,
        }

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SecurityGrant":
        _exact_keys(
            raw,
            {
                "schema_version", "grant_id", "workspace_root", "identity", "scope", "tool_rules", "process",
                "runtime_assurance", "provider_routes", "credential_refs", "approvals", "approval_required_for",
                "issued_at", "expires_at", "parent_grant_hash",
            },
        )
        if not isinstance(raw["tool_rules"], list) or not isinstance(raw["provider_routes"], list) or not isinstance(raw["approvals"], list):
            raise SecurityError("grant collections must be arrays")
        return cls(
            schema_version=raw["schema_version"],
            grant_id=raw["grant_id"],
            workspace_root=raw["workspace_root"],
            identity=InvocationIdentity.from_dict(raw["identity"]),
            scope=CapabilityScope.from_dict(raw["scope"]),
            tool_rules=tuple(ToolRule.from_dict(item) for item in raw["tool_rules"]),
            process=ProcessPolicy.from_dict(raw["process"]),
            runtime_assurance=RuntimeAssurance.from_dict(raw["runtime_assurance"]),
            provider_routes=tuple(ProviderRoute.from_dict(item) for item in raw["provider_routes"]),
            credential_refs=tuple(raw["credential_refs"]),
            approvals=tuple(ApprovalEvidence.from_dict(item) for item in raw["approvals"]),
            approval_required_for=tuple(raw["approval_required_for"]),
            issued_at=raw["issued_at"],
            expires_at=raw["expires_at"],
            parent_grant_hash=raw["parent_grant_hash"],
        )


@dataclass(frozen=True)
class SignedGrantEnvelope:
    key_id: str
    grant: SecurityGrant
    signature: str
    schema_version: str = SIGNED_ENVELOPE_VERSION
    algorithm: str = "ed25519"

    def __post_init__(self) -> None:
        if self.schema_version != SIGNED_ENVELOPE_VERSION or self.algorithm != "ed25519":
            raise SecurityError("unsupported signed grant envelope")
        _token(self.key_id, "key_id")
        if not isinstance(self.grant, SecurityGrant):
            raise SecurityError("signed envelope requires a typed grant")
        _decode_fixed(self.signature, 64, "signature")

    def unsigned_json(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "algorithm": self.algorithm,
            "key_id": self.key_id,
            "grant": self.grant.to_json(),
        }

    def to_json(self) -> dict[str, Any]:
        return {**self.unsigned_json(), "signature": self.signature}

    @classmethod
    def from_dict(cls, raw: Mapping[str, Any]) -> "SignedGrantEnvelope":
        _exact_keys(raw, {"schema_version", "algorithm", "key_id", "grant", "signature"})
        return cls(
            schema_version=raw["schema_version"],
            algorithm=raw["algorithm"],
            key_id=raw["key_id"],
            grant=SecurityGrant.from_dict(raw["grant"]),
            signature=raw["signature"],
        )


def _decode_fixed(value: Any, size: int, name: str) -> bytes:
    if not isinstance(value, str) or len(value) != 4 * ((size + 2) // 3):
        raise SecurityError(f"invalid {name} encoding")
    try:
        decoded = base64.b64decode(value, validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise SecurityError(f"invalid {name} encoding") from exc
    if len(decoded) != size or base64.b64encode(decoded).decode("ascii") != value:
        raise SecurityError(f"invalid {name} encoding")
    return decoded


def _ed25519():
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
        from cryptography.hazmat.primitives import serialization
        from cryptography.exceptions import InvalidSignature
    except ImportError as exc:
        raise SecurityError("Ed25519 verification unavailable") from exc
    return Ed25519PrivateKey, Ed25519PublicKey, serialization, InvalidSignature


def sign_grant(grant: SecurityGrant, key: Any, *, key_id: str) -> SignedGrantEnvelope:
    """Host-only signer. The private key object must never be serialized to the bundle."""
    _token(key_id, "key_id")
    Ed25519PrivateKey, _, _, _ = _ed25519()
    if not isinstance(key, Ed25519PrivateKey):
        raise SecurityError("Ed25519 private key required")
    unsigned = {
        "schema_version": SIGNED_ENVELOPE_VERSION,
        "algorithm": "ed25519",
        "key_id": key_id,
        "grant": grant.to_json(),
    }
    signature = base64.b64encode(key.sign(canonical_json_bytes(unsigned))).decode("ascii")
    return SignedGrantEnvelope(key_id=key_id, grant=grant, signature=signature)


def verify_signed_grant(
    envelope: SignedGrantEnvelope,
    key: bytes,
    *,
    expected_identity: InvocationIdentity,
    now: datetime | None = None,
) -> SecurityGrant:
    _, Ed25519PublicKey, _, InvalidSignature = _ed25519()
    if not isinstance(key, bytes) or len(key) != 32:
        raise SecurityError("Ed25519 public key must be 32 bytes")
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(
            _decode_fixed(envelope.signature, 64, "signature"),
            canonical_json_bytes(envelope.unsigned_json()),
        )
    except (InvalidSignature, ValueError) as exc:
        raise SecurityError("signed grant authentication failed")
    if envelope.grant.identity != expected_identity:
        raise SecurityError("signed grant identity/fence mismatch")
    if not envelope.grant.is_active(now):
        raise SecurityError("signed grant is not active")
    return envelope.grant


def load_signed_grant(path: str | Path) -> SignedGrantEnvelope:
    policy_path = Path(path)
    if policy_path.is_symlink() or (policy_path.stat().st_mode & 0o222):
        raise SecurityError("signed grant file is mutable")
    raw = policy_path.read_bytes()
    if len(raw) > _MAX_POLICY_BYTES:
        raise SecurityError("signed grant file exceeds size limit")
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecurityError("signed grant file is not valid JSON") from exc
    if not isinstance(parsed, dict):
        raise SecurityError("signed grant envelope must be an object")
    if canonical_json_bytes(parsed) != raw:
        raise SecurityError("signed grant file is not canonical")
    return SignedGrantEnvelope.from_dict(parsed)


@dataclass(frozen=True)
class SealedPolicyBundle:
    path: Path
    sha256: str
    device: int
    inode: int


class PolicyBundleStage:
    """Host-owned pinned inode; retain fd until #82 finishes its mount recheck."""

    def __init__(self, path: Path, fd: int) -> None:
        self.path = path
        self.fd = fd
        info = os.fstat(fd)
        self.device, self.inode = info.st_dev, info.st_ino
        self._attempted = False

    def _same_inode(self) -> None:
        held = os.fstat(self.fd)
        path = os.lstat(self.path)
        if (not stat.S_ISREG(held.st_mode) or not stat.S_ISREG(path.st_mode)
                or (held.st_dev, held.st_ino) != (self.device, self.inode)
                or (path.st_dev, path.st_ino) != (self.device, self.inode)):
            raise SecurityError("policy bundle pinned inode changed")

    def seal(self, grant: SecurityGrant, private_key: Any, *, key_id: str,
             expected_identity: InvocationIdentity,
             expected_attestation_sha256: str) -> SealedPolicyBundle:
        if self._attempted:
            raise SecurityError("policy bundle seal is one-shot")
        self._attempted = True
        self._same_inode()
        if os.fstat(self.fd).st_size != 0:
            raise SecurityError("policy bundle staging inode is not empty")
        if grant.identity != expected_identity or not grant.runtime_assurance.sandbox_verified or grant.runtime_assurance.sandbox_attestation_sha256 != expected_attestation_sha256:
            raise SecurityError("policy bundle identity/attestation mismatch")
        _, _, serialization, _ = _ed25519()
        envelope = sign_grant(grant, private_key, key_id=key_id)
        public = private_key.public_key().public_bytes(
            encoding=serialization.Encoding.Raw, format=serialization.PublicFormat.Raw
        )
        payload = canonical_json_bytes({
            "schema_version": POLICY_BUNDLE_VERSION,
            "envelope": envelope.to_json(),
            "public_key": base64.b64encode(public).decode("ascii"),
        })
        if len(payload) > _MAX_POLICY_BYTES:
            raise SecurityError("policy bundle exceeds size limit")
        offset = 0
        while offset < len(payload):
            written = os.pwrite(self.fd, payload[offset:], offset)
            if written <= 0:
                raise SecurityError("policy bundle write failed")
            offset += written
        os.ftruncate(self.fd, len(payload))
        os.fsync(self.fd)
        self._same_inode()
        reread = os.pread(self.fd, len(payload) + 1, 0)
        if reread != payload:
            raise SecurityError("policy bundle reread mismatch")
        load_policy_bundle(self.path, expected_identity,
                           expected_attestation_sha256=expected_attestation_sha256)
        self._same_inode()
        return SealedPolicyBundle(self.path, hashlib.sha256(payload).hexdigest(),
                                  self.device, self.inode)

    def close(self) -> None:
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def __enter__(self) -> "PolicyBundleStage":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


def stage_policy_bundle(path: Path) -> PolicyBundleStage:
    """Precreate an empty regular file before bwrap binds this exact inode."""
    path = Path(path)
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise SecurityError("policy bundle parent unavailable")
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        stage = PolicyBundleStage(path, fd)
        stage._same_inode()
        parent_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(parent_fd)
        finally:
            os.close(parent_fd)
        return stage
    except BaseException:
        os.close(fd)
        raise


def load_policy_bundle(path: Path, expected_identity: InvocationIdentity, *,
                       expected_attestation_sha256: str | None = None,
                       now: datetime | None = None) -> SecurityGrant:
    """Read a canonical signed file at the caller's fixed, read-only bind path."""
    if expected_attestation_sha256 is not None:
        _sha256(expected_attestation_sha256, "expected_attestation_sha256")
    try:
        fd = os.open(Path(path), os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
    except OSError as exc:
        raise SecurityError("policy bundle file unavailable") from exc
    try:
        before = os.fstat(fd)
        if not stat.S_ISREG(before.st_mode):
            raise SecurityError("policy bundle is not a regular file")
        if before.st_size <= 0 or before.st_size > _MAX_POLICY_BYTES:
            raise SecurityError("policy bundle empty or exceeds size limit")
        chunks = []
        remaining = before.st_size + 1
        while remaining:
            chunk = os.read(fd, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_size) != (after.st_dev, after.st_ino, after.st_size) or len(raw) != before.st_size:
            raise SecurityError("policy bundle changed during read")
    except OSError as exc:
        raise SecurityError("policy bundle read failed") from exc
    finally:
        os.close(fd)
    try:
        parsed = json.loads(raw)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise SecurityError("policy bundle invalid JSON") from exc
    _exact_keys(parsed, {"schema_version", "envelope", "public_key"})
    if parsed["schema_version"] != POLICY_BUNDLE_VERSION:
        raise SecurityError("unsupported policy bundle")
    if canonical_json_bytes(parsed) != raw:
        raise SecurityError("policy bundle is not canonical")
    envelope = SignedGrantEnvelope.from_dict(parsed["envelope"])
    grant = verify_signed_grant(envelope, _decode_fixed(parsed["public_key"], 32, "public_key"),
                                expected_identity=expected_identity, now=now)
    if not grant.runtime_assurance.sandbox_verified or (
        expected_attestation_sha256 is not None
        and grant.runtime_assurance.sandbox_attestation_sha256 != expected_attestation_sha256
    ):
        raise SecurityError("sandbox attestation mismatch")
    return grant


@dataclass(frozen=True)
class ContentProvenance:
    source_kind: str
    source_id: str
    untrusted: bool = True

    def __post_init__(self) -> None:
        _token(self.source_kind, "source_kind")
        _token(self.source_id, "source_id")
        if type(self.untrusted) is not bool:
            raise SecurityError("untrusted must be boolean")


@dataclass(frozen=True)
class TaintRestrictions:
    provenance: tuple[ContentProvenance, ...] = ()
    deny_tools: tuple[str, ...] = ()
    deny_providers: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.provenance, (tuple, list)) or any(
            not isinstance(item, ContentProvenance) for item in self.provenance
        ):
            raise SecurityError("taint provenance must be typed")
        object.__setattr__(self, "provenance", tuple(self.provenance))
        object.__setattr__(self, "deny_tools", _tuple_tokens(self.deny_tools, "deny_tools"))
        object.__setattr__(self, "deny_providers", _tuple_tokens(self.deny_providers, "deny_providers"))

    @classmethod
    def from_untrusted_directives(
        cls,
        provenance: Sequence[ContentProvenance],
        directives: Mapping[str, Any],
    ) -> "TaintRestrictions":
        """Only restrictive directives are accepted from content.

        There is intentionally no allow/permission/grant input here.  If content
        tries to speak authority language, the parser fails closed instead of
        interpreting it.
        """
        _exact_keys(directives, {"deny_tools", "deny_providers"})
        return cls(
            provenance=tuple(provenance),
            deny_tools=directives["deny_tools"],
            deny_providers=directives["deny_providers"],
        )


@dataclass(frozen=True)
class ProviderRequest:
    provider: str
    region: str
    data_class: DataClass
    egress: Egress
    retention: Retention
    training: Training
    credential_ref: str | None = None

    def __post_init__(self) -> None:
        _token(self.provider, "provider")
        _token(self.region, "region")
        object.__setattr__(self, "data_class", _enum(DataClass, self.data_class, "data_class"))
        object.__setattr__(self, "egress", _enum(Egress, self.egress, "egress"))
        object.__setattr__(self, "retention", _enum(Retention, self.retention, "retention"))
        object.__setattr__(self, "training", _enum(Training, self.training, "training"))
        if self.credential_ref is not None:
            _credential_ref(self.credential_ref, "credential_ref")


class ProviderCircuitBreaker:
    """Small per-provider isolation primitive; one open provider does not stop peers."""

    def __init__(self) -> None:
        self._open: dict[str, str] = {}

    def open(self, provider: str, reason: str) -> None:
        self._open[_token(provider, "provider")] = _token(reason, "breaker reason")

    def close(self, provider: str) -> None:
        self._open.pop(_token(provider, "provider"), None)

    def reason(self, provider: str) -> str | None:
        return self._open.get(_token(provider, "provider"))

    def require_closed(self, provider: str) -> None:
        reason = self.reason(provider)
        if reason is not None:
            raise PolicyDenied("provider_isolated", reason)


def _recv_bounded_line(stream: socket.socket, *, limit: int = 256) -> bytes:
    """Read exactly one bounded newline-terminated authority response."""
    data = bytearray()
    while len(data) < limit:
        chunk = stream.recv(min(64, limit - len(data)))
        if not chunk:
            break
        data.extend(chunk)
        if b"\n" in data:
            line, tail = bytes(data).split(b"\n", 1)
            if tail:
                raise OSError("approval authority sent trailing data")
            return line + b"\n"
    raise OSError("approval authority response incomplete or oversized")


@dataclass
class InvocationGuard:
    grant: SecurityGrant
    assurance: RuntimeAssurance | None = None
    aliases: Mapping[str, str] = field(default_factory=dict)
    breaker: ProviderCircuitBreaker = field(default_factory=ProviderCircuitBreaker)
    path_resolver: Callable[[str, str], str | Path] | None = field(
        default=None, repr=False
    )
    approval_socket: Path = APPROVAL_SOCKET
    approval_consumer: Callable[[str, str, str, str], str] | None = field(default=None, repr=False)

    def __post_init__(self) -> None:
        if not isinstance(self.grant, SecurityGrant):
            raise SecurityError("guard requires a typed grant")
        if self.assurance is None:
            self.assurance = self.grant.runtime_assurance
        elif self.assurance != self.grant.runtime_assurance:
            raise SecurityError("runtime assurance must equal signed host evidence")
        if not isinstance(self.assurance, RuntimeAssurance):
            raise SecurityError("guard requires typed runtime assurance")
        if not self.grant.is_active():
            raise SecurityError("grant is not active")
        normalized: dict[str, str] = {}
        for alias, target in self.aliases.items():
            normalized[_token(alias, "tool alias")] = _token(target, "tool alias target")
        self.aliases = normalized

    def canonical_tool(self, tool: str) -> str:
        current = _token(tool, "tool")
        seen: set[str] = set()
        while current in self.aliases:
            if current in seen:
                raise PolicyDenied("tool_alias_cycle")
            seen.add(current)
            current = self.aliases[current]
        return current

    def authorize_tool(
        self,
        tool: str,
        args: Mapping[str, Any] | None,
        *,
        caller_task_id: str | None = None,
        taint: TaintRestrictions | None = None,
        consume_approval: bool = True,
    ) -> str:
        canonical, _checked = self.authorize_tool_call(
            tool,
            args,
            caller_task_id=caller_task_id,
            taint=taint,
            consume_approval=consume_approval,
        )
        return canonical

    def authorize_tool_call(
        self,
        tool: str,
        args: Mapping[str, Any] | None,
        *,
        caller_task_id: str | None = None,
        taint: TaintRestrictions | None = None,
        consume_approval: bool = True,
    ) -> tuple[str, dict[str, Any]]:
        """Authorize and canonicalize the exact arguments Hermes will execute."""
        if not self.grant.is_active():
            raise PolicyDenied("grant_expired")
        canonical = self.canonical_tool(tool)
        if caller_task_id is None:
            caller_task_id = self.grant.identity.task_id
        if caller_task_id != self.grant.identity.task_id:
            raise PolicyDenied("task_identity_mismatch")
        if taint is not None and canonical in taint.deny_tools:
            raise PolicyDenied("tainted_tool_denied")
        if canonical not in self.grant.scope.tools:
            raise PolicyDenied("tool_not_granted", canonical)
        rules = {rule.tool: rule for rule in self.grant.tool_rules}
        rule = rules.get(canonical)
        if rule is None:
            raise PolicyDenied("tool_rule_missing", canonical)
        checked_args = _validate_args(
            args if args is not None else {},
            rule,
            self.grant.credential_refs,
            path_resolver=self.path_resolver,
            task_id=caller_task_id,
        )
        if rule.requires_sandbox and not self.assurance.sandbox_verified:
            raise PolicyDenied("sandbox_attestation_required", canonical)
        if rule.requires_process:
            if not self.grant.process.enabled or canonical not in self.grant.process.tools:
                raise PolicyDenied("process_not_granted", canonical)
            if not self.assurance.sandbox_verified:
                raise PolicyDenied("process_requires_sandbox", canonical)
            if _NETWORK_ORDER[self.assurance.network_access] > _NETWORK_ORDER[self.grant.process.max_network]:
                raise PolicyDenied("network_ceiling_exceeded", canonical)
            if not _roots_subset(self.assurance.writable_roots, self.grant.process.writable_roots):
                raise PolicyDenied("filesystem_write_ceiling_exceeded", canonical)
            if self.grant.process.require_credentials_isolated and not self.assurance.credentials_isolated:
                raise PolicyDenied("credential_boundary_unverified", canonical)
        if rule.risk in self.grant.approval_required_for:
            self._require_approval(canonical, checked_args, consume=consume_approval)
        return canonical, checked_args

    def _require_approval(self, tool: str, args: Mapping[str, Any], *, consume: bool) -> None:
        digest = canonical_digest({"tool": tool, "args": args})
        evidence = next(
            (
                item
                for item in self.grant.approvals
                if item.tool == tool
                and item.args_sha256 == digest
                and item.identity == self.grant.identity
            ),
            None,
        )
        if evidence is None:
            raise PolicyDenied("approval_required", tool)
        if consume:
            if self.approval_consumer is not None:
                answer_text = self.approval_consumer(self.grant.hash, evidence.approval_id, tool, digest)
                if answer_text == "consumed":
                    return
                if answer_text == "replayed":
                    raise PolicyDenied("approval_replayed", evidence.approval_id)
                raise PolicyDenied("approval_authority_unavailable")
            request = canonical_json_bytes({"grant_hash": self.grant.hash,
                                            "approval_id": evidence.approval_id,
                                            "tool": tool, "args_sha256": digest}) + b"\n"
            try:
                with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
                    client.settimeout(2)
                    client.connect(str(self.approval_socket))
                    client.sendall(request)
                    answer = _recv_bounded_line(client, limit=256)
            except (OSError, TimeoutError) as exc:
                raise PolicyDenied("approval_authority_unavailable") from exc
            if answer == b"consumed\n":
                return
            if answer == b"replayed\n":
                raise PolicyDenied("approval_replayed", evidence.approval_id)
            raise PolicyDenied("approval_authority_unavailable")

    def authorize_provider(
        self,
        request: ProviderRequest,
        *,
        taint: TaintRestrictions | None = None,
    ) -> None:
        if not self.grant.is_active():
            raise PolicyDenied("grant_expired")
        if taint is not None and request.provider in taint.deny_providers:
            raise PolicyDenied("tainted_provider_denied", request.provider)
        self.breaker.require_closed(request.provider)
        if request.provider not in self.grant.scope.providers:
            raise PolicyDenied("provider_not_granted", request.provider)
        route = next((item for item in self.grant.provider_routes if item.provider == request.provider), None)
        if route is None:
            raise PolicyDenied("provider_route_missing", request.provider)
        if request.region not in self.grant.scope.regions or request.region not in route.regions:
            raise PolicyDenied("provider_region_denied", request.region)
        if request.data_class not in self.grant.scope.data_classes or request.data_class not in route.data_classes:
            raise PolicyDenied("data_class_denied", request.data_class.value)
        if _EGRESS_ORDER[request.egress] > _EGRESS_ORDER[self.grant.scope.max_egress] or _EGRESS_ORDER[request.egress] > _EGRESS_ORDER[route.max_egress]:
            raise PolicyDenied("egress_denied", request.egress.value)
        if _RETENTION_ORDER[request.retention] > _RETENTION_ORDER[self.grant.scope.max_retention] or _RETENTION_ORDER[request.retention] > _RETENTION_ORDER[route.max_retention]:
            raise PolicyDenied("retention_denied", request.retention.value)
        if _TRAINING_ORDER[request.training] > _TRAINING_ORDER[self.grant.scope.training] or _TRAINING_ORDER[request.training] > _TRAINING_ORDER[route.training]:
            raise PolicyDenied("training_denied", request.training.value)
        if route.credential_refs and request.credential_ref is None:
            raise PolicyDenied("credential_ref_required", request.provider)
        if request.credential_ref is not None:
            if request.credential_ref not in self.grant.credential_refs or request.credential_ref not in route.credential_refs:
                raise PolicyDenied("credential_ref_denied", request.credential_ref)


def _validate_args(
    args: Mapping[str, Any],
    rule: ToolRule,
    credential_refs: Sequence[str],
    *,
    path_resolver: Callable[[str, str], str | Path] | None,
    task_id: str,
) -> dict[str, Any]:
    if not isinstance(args, Mapping):
        raise PolicyDenied("tool_args_invalid")
    keys = set(args)
    if any(not isinstance(key, str) for key in keys):
        raise PolicyDenied("tool_arg_key_invalid")
    if any(isinstance(key, str) and _SECRET_KEY.search(key) and key not in rule.credential_ref_fields for key in keys):
        raise PolicyDenied("raw_credential_material_denied")
    if not keys <= set(rule.allowed_arg_keys):
        raise PolicyDenied("tool_arg_not_granted", ",".join(sorted(keys - set(rule.allowed_arg_keys))))
    # Credential-reference fields are authority-bearing. They may never be
    # omitted or replaced with None/scalars/containers that let a downstream
    # tool fall back to ambient/default credentials.
    for field in rule.credential_ref_fields:
        if field not in args:
            raise PolicyDenied("credential_ref_required", field)
        value = args[field]
        if not isinstance(value, str) or not value:
            raise PolicyDenied("credential_ref_invalid", field)
        if value not in credential_refs:
            raise PolicyDenied("credential_ref_denied", value[:128])
    budget = [0]
    checked = _validate_value(dict(args), rule, credential_refs, depth=0, budget=budget, parent_key="")
    for field in rule.path_fields:
        if field not in checked:
            if rule.tool == "patch" and field == "path" and checked.get("mode") == "patch":
                continue
            raise PolicyDenied("path_arg_required", field)
        value = checked[field]
        if not isinstance(value, str):
            raise PolicyDenied("path_arg_invalid", field)
        resolved = _resolve_authorized_path(value, path_resolver, task_id)
        if not any(_path_within(resolved, Path(root)) for root in rule.allowed_roots):
            raise PolicyDenied("path_outside_grant", field)
        checked[field] = str(resolved)

    if rule.tool == "patch" and checked.get("mode") == "patch":
        patch = checked.get("patch")
        if not isinstance(patch, str):
            raise PolicyDenied("patch_content_required")
        normalized_patch, targets = _normalize_v4a_patch(
            patch, path_resolver=path_resolver, task_id=task_id
        )
        if not targets:
            raise PolicyDenied("patch_target_required")
        if not rule.allowed_roots:
            raise PolicyDenied("path_root_required", "patch")
        for target in targets:
            if not any(_path_within(target, Path(root)) for root in rule.allowed_roots):
                raise PolicyDenied("path_outside_grant", str(target)[:256])
        checked["patch"] = normalized_patch
    return checked


def _resolve_authorized_path(
    value: str,
    resolver: Callable[[str, str], str | Path] | None,
    task_id: str,
) -> Path:
    """Resolve exactly as the runtime will; never guess a relative cwd."""
    try:
        if resolver is not None:
            raw = resolver(value, task_id)
            resolved = Path(str(raw))
        else:
            candidate = Path(value).expanduser()
            if not candidate.is_absolute():
                raise PolicyDenied("path_resolution_context_required")
            resolved = candidate.resolve(strict=False)
    except PolicyDenied:
        raise
    except Exception as exc:
        raise PolicyDenied("path_resolution_failed", type(exc).__name__) from exc
    if not resolved.is_absolute() or ".." in resolved.parts:
        raise PolicyDenied("path_resolution_failed")
    return resolved


def _normalize_v4a_patch(
    patch: str,
    *,
    path_resolver: Callable[[str, str], str | Path] | None,
    task_id: str,
) -> tuple[str, tuple[Path, ...]]:
    """Normalize every V4A path header to the authorized absolute path."""
    targets: list[Path] = []
    lines: list[str] = []
    for raw_line in patch.splitlines():
        move = _V4A_MOVE_HEADER.match(raw_line)
        if move:
            source = _resolve_authorized_path(move.group(1).strip(), path_resolver, task_id)
            destination = _resolve_authorized_path(move.group(2).strip(), path_resolver, task_id)
            targets.extend((source, destination))
            lines.append(f"*** Move File: {source} -> {destination}")
            continue
        single = _V4A_SINGLE_HEADER.match(raw_line)
        if single:
            target = _resolve_authorized_path(single.group(2).strip(), path_resolver, task_id)
            targets.append(target)
            lines.append(f"*** {single.group(1)} File: {target}")
            continue
        if _V4A_ANY_FILE_HEADER.match(raw_line):
            raise PolicyDenied("patch_header_invalid")
        lines.append(raw_line)
    trailing_newline = "\n" if patch.endswith("\n") else ""
    return "\n".join(lines) + trailing_newline, tuple(targets)


def _validate_value(
    value: Any,
    rule: ToolRule,
    credential_refs: Sequence[str],
    *,
    depth: int,
    budget: list[int],
    parent_key: str,
) -> Any:
    if depth > _MAX_ARG_DEPTH:
        raise PolicyDenied("tool_args_too_deep")
    budget[0] += 1
    if budget[0] > _MAX_ARG_ITEMS:
        raise PolicyDenied("tool_args_too_large")
    if parent_key in rule.credential_ref_fields:
        if not isinstance(value, str) or not value:
            raise PolicyDenied("credential_ref_invalid", parent_key)
        if value not in credential_refs:
            raise PolicyDenied("credential_ref_denied", value[:128])
        return value
    if value is None or type(value) in (bool, int, float):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise PolicyDenied("tool_arg_nonfinite")
        return value
    if isinstance(value, str):
        if len(value) > _MAX_ARG_STRING:
            raise PolicyDenied("tool_arg_string_too_large")
        if _SECRET_KEY.search(parent_key) or any(pattern.search(value) for pattern in _SECRET_VALUE):
            raise PolicyDenied("raw_credential_material_denied", parent_key[:128])
        return value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str) or len(key) > 256:
                raise PolicyDenied("tool_arg_key_invalid")
            if _SECRET_KEY.search(key) and key not in rule.credential_ref_fields:
                raise PolicyDenied("raw_credential_material_denied", key[:128])
            result[key] = _validate_value(
                item,
                rule,
                credential_refs,
                depth=depth + 1,
                budget=budget,
                parent_key=key,
            )
        return result
    if isinstance(value, (list, tuple)):
        return [
            _validate_value(
                item,
                rule,
                credential_refs,
                depth=depth + 1,
                budget=budget,
                parent_key=parent_key,
            )
            for item in value
        ]
    raise PolicyDenied("tool_arg_type_denied", type(value).__name__)


def _roots_subset(child_roots: Sequence[str], parent_roots: Sequence[str]) -> bool:
    return all(
        any(_path_within(Path(child), Path(parent)) for parent in parent_roots)
        for child in child_roots
    )


def _path_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _route_subset(child: ProviderRoute, parent: ProviderRoute) -> bool:
    return (
        child.base_url == parent.base_url
        and child.api_mode == parent.api_mode
        and
        set(child.regions) <= set(parent.regions)
        and set(child.data_classes) <= set(parent.data_classes)
        and _EGRESS_ORDER[child.max_egress] <= _EGRESS_ORDER[parent.max_egress]
        and _RETENTION_ORDER[child.max_retention] <= _RETENTION_ORDER[parent.max_retention]
        and _TRAINING_ORDER[child.training] <= _TRAINING_ORDER[parent.training]
        and set(child.credential_refs) <= set(parent.credential_refs)
    )


def _exact_keys(raw: Any, expected: set[str]) -> None:
    if not isinstance(raw, Mapping):
        raise SecurityError("contract object required")
    if set(raw) != expected:
        raise SecurityError(f"contract fields differ: {sorted(set(raw) ^ expected)}")


__all__ = [
    "ApprovalEvidence",
    "ContentProvenance",
    "InvocationGuard",
    "InvocationIdentity",
    "NetworkAccess",
    "PolicyDenied",
    "ProcessPolicy",
    "ProviderCircuitBreaker",
    "ProviderRequest",
    "ProviderRoute",
    "RiskClass",
    "RuntimeAssurance",
    "SECURITY_GRANT_VERSION",
    "SIGNED_ENVELOPE_VERSION",
    "POLICY_BUNDLE_VERSION",
    "SecurityError",
    "SecurityGrant",
    "SignedGrantEnvelope",
    "TaintRestrictions",
    "ToolRule",
    "canonical_digest",
    "canonical_json_bytes",
    "load_signed_grant",
    "load_policy_bundle",
    "stage_policy_bundle",
    "PolicyBundleStage",
    "SealedPolicyBundle",
    "sign_grant",
    "verify_signed_grant",
]
