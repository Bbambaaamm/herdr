"""Pinned, provider-neutral Agent Skills. Text is context data, never a grant.

Host-owned approvals and node scopes are inputs. Package code is never imported
or executed. Physical tool invocation remains the security boundary's job.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import re
import stat
from dataclasses import dataclass, fields
from enum import StrEnum
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

from .capability import (
    CapabilityError, CapabilityScope, DataClass, Egress, Feature, Modality,
    RegistrySnapshot, Retention, Training,
)

VERSION = "1.0.0"
MAX_PACKAGE = 2_000_000
MAX_FILE = 262_144
MAX_BODY = 65_536
MAX_MANIFEST = 32_768
MAX_INDEX = 16_384
MAX_BUNDLE = 262_144
_NAME = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")
_SEMVER = re.compile(r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)(?:-[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?")
_SHA = re.compile(r"[0-9a-f]{64}")
_REV = re.compile(r"[0-9a-f]{40}")
_TOKEN = re.compile(r"[A-Za-z0-9._:/@+-]{1,256}")


class SkillError(ValueError):
    """Malformed, unapproved, stale or out-of-scope context; no authority change."""


def need(condition, code):
    if not condition:
        raise SkillError(code)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError, UnicodeError) as exc:
        raise SkillError("invalid_json") from exc


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def decode(raw):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            need(key not in result, "duplicate_json_key")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=unique,
                          parse_constant=lambda _: (_ for _ in ()).throw(SkillError("nonfinite_json")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise SkillError("invalid_json") from exc


def strict(cls, raw):
    need(isinstance(raw, dict) and set(raw) == {f.name for f in fields(cls)},
         "manifest_fields")
    return dict(raw)


def token(value):
    need(isinstance(value, str) and _TOKEN.fullmatch(value), "invalid_identity")
    return value


def text(value, maximum):
    need(isinstance(value, str) and 0 < len(value) <= maximum
         and "\x00" not in value, "invalid_text")
    return value


def safe_path(value):
    need(isinstance(value, str) and 0 < len(value) <= 256
         and "\\" not in value and "\x00" not in value, "invalid_resource_path")
    parts = value.split("/")
    need(all(re.fullmatch(r"[A-Za-z0-9_.-]{1,128}", x) and x not in {".", ".."} for x in parts)
         and PurePosixPath(value).as_posix() == value, "invalid_resource_path")
    return value


def values(value, check=token, maximum=64):
    need(isinstance(value, (tuple, list)) and len(value) <= maximum, "invalid_list")
    parsed = tuple(check(x) for x in value)
    need(len(parsed) == len(set(parsed)), "duplicate_list_value")
    return tuple(sorted(parsed))


def name(value):
    need(isinstance(value, str) and 1 <= len(value) <= 64 and _NAME.fullmatch(value),
         "invalid_skill_name")
    return value


def sha(value):
    need(isinstance(value, str) and _SHA.fullmatch(value), "invalid_digest")
    return value


def revision(value):
    need(isinstance(value, str) and _REV.fullmatch(value), "invalid_source_revision")
    return value


def semver(value):
    need(isinstance(value, str) and len(value) <= 128 and _SEMVER.fullmatch(value), "invalid_semver")
    core = value.split("+", 1)[0]
    if "-" in core:
        prerelease = core.split("-", 1)[1]
        need(all(not x.isdigit() or x == "0" or not x.startswith("0")
                 for x in prerelease.split(".")), "invalid_semver")
    return value


def source_uri(value):
    need(isinstance(value, str) and len(value) <= 512, "invalid_source_uri")
    try:
        parsed = urlsplit(value)
        need(parsed.scheme == "https" and parsed.hostname and not parsed.username
             and not parsed.password and not parsed.query and not parsed.fragment,
             "invalid_source_uri")
        _ = parsed.port
    except ValueError as exc:
        raise SkillError("invalid_source_uri") from exc
    return value


class TrustTier(StrEnum):
    UNTRUSTED = "untrusted"
    REVIEWED = "reviewed"
    FIRST_PARTY = "first_party"


@dataclass(frozen=True)
class SkillFile:
    path: str
    size: int
    sha256: str
    media_type: str
    data_class: DataClass

    def __post_init__(self):
        safe_path(self.path)
        need(type(self.size) is int and 0 < self.size <= MAX_FILE, "file_size")
        sha(self.sha256)
        need(self.media_type in {"text/plain", "text/markdown", "application/json",
                                "image/png", "image/jpeg", "application/octet-stream"}, "file_media")
        try:
            object.__setattr__(self, "data_class", DataClass(self.data_class))
        except (ValueError, TypeError) as exc:
            raise SkillError("file_data_class") from exc
        if self.path == "SKILL.md":
            need(self.size <= MAX_BODY and self.media_type == "text/markdown", "skill_body_contract")
        else:
            need(self.path.split("/")[0] in {"scripts", "references", "assets"}, "file_layout")

    def to_json(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}

    @classmethod
    def from_dict(cls, raw):
        return cls(**strict(cls, raw))


@dataclass(frozen=True)
class SkillManifest:
    name: str
    version: str
    description: str
    publisher: str
    source_uri: str
    authoring_base_revision: str
    tools: tuple[str, ...]
    permissions: tuple[str, ...]
    capabilities: tuple[str, ...]
    features: tuple[Feature, ...]
    platforms: tuple[str, ...]
    files: tuple[SkillFile, ...]
    schema_version: str = VERSION

    def __post_init__(self):
        name(self.name)
        semver(self.version)
        text(self.description, 1024)
        token(self.publisher)
        source_uri(self.source_uri)
        revision(self.authoring_base_revision)
        need(self.schema_version == VERSION, "manifest_version")
        for key in ("tools", "permissions", "capabilities"):
            object.__setattr__(self, key, values(getattr(self, key)))
        try:
            features = values(self.features, lambda x: Feature.TOOL_USE if Feature(x) == Feature.TOOLS else Feature(x))
        except SkillError:
            raise
        except (ValueError, TypeError) as exc:
            raise SkillError("unknown_feature") from exc
        object.__setattr__(self, "features", features)
        platforms = values(self.platforms)
        need(platforms and set(platforms) <= {"linux", "windows", "darwin"}, "platform")
        object.__setattr__(self, "platforms", platforms)
        need(isinstance(self.files, (tuple, list)) and 1 <= len(self.files) <= 64
             and all(isinstance(x, SkillFile) for x in self.files), "manifest_files")
        paths = [x.path for x in self.files]
        need(len(paths) == len(set(paths)) and "SKILL.md" in paths, "manifest_files")
        need(sum(x.size for x in self.files) <= MAX_PACKAGE, "package_size")
        object.__setattr__(self, "files", tuple(sorted(self.files, key=lambda x: x.path)))

    def to_json(self):
        return {f.name: ([x.to_json() for x in self.files] if f.name == "files"
                         else list(getattr(self, f.name)) if isinstance(getattr(self, f.name), tuple)
                         else getattr(self, f.name)) for f in fields(self)}

    @property
    def hash(self):
        return digest(self.to_json())

    @classmethod
    def from_dict(cls, raw):
        data = strict(cls, raw)
        need(isinstance(data["files"], list), "manifest_files")
        data["files"] = tuple(SkillFile.from_dict(x) for x in data["files"])
        return cls(**data)


@dataclass(frozen=True)
class SkillApproval:
    """External host trust root; never inferred from self-claimed package metadata."""
    name: str
    version: str
    package_hash: str
    publisher: str
    source_uri: str
    approved_revision: str
    trust_tier: TrustTier

    def __post_init__(self):
        name(self.name)
        semver(self.version)
        sha(self.package_hash)
        token(self.publisher)
        source_uri(self.source_uri)
        revision(self.approved_revision)
        try:
            object.__setattr__(self, "trust_tier", TrustTier(self.trust_tier))
        except (ValueError, TypeError) as exc:
            raise SkillError("trust_tier") from exc

    def to_json(self):
        return {f.name: getattr(self, f.name) for f in fields(self)}


def _read_at(root_fd, path, maximum):
    """Open every component relative to the held directory; never follow links."""
    parts = safe_path(path).split("/")
    current = os.dup(root_fd)
    try:
        for part in parts[:-1]:
            next_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=current)
            os.close(current)
            current = next_fd
        fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=current)
        try:
            info = os.fstat(fd)
            need(stat.S_ISREG(info.st_mode) and 0 < info.st_size <= maximum, "regular_bounded_file")
            chunks, remaining = [], maximum + 1
            while remaining:
                chunk = os.read(fd, min(65_536, remaining))
                if not chunk:
                    break
                chunks.append(chunk)
                remaining -= len(chunk)
            data = b"".join(chunks)
            need(len(data) == info.st_size and len(data) <= maximum, "changed_or_oversized_file")
            return data
        finally:
            os.close(fd)
    except OSError as exc:
        raise SkillError("resource_unavailable_or_symlink") from exc
    finally:
        os.close(current)


def parse_skill_body(raw, manifest):
    """Portable authoring subset: YAML frontmatter with JSON-quoted scalar values.

    Unsupported YAML tags/aliases, nested values and implicit coercion fail closed.
    This is deliberately a subset of Agent Skills' YAML, not a general YAML parser.
    """
    try:
        body = raw.decode("utf-8")
    except UnicodeError as exc:
        raise SkillError("skill_body_encoding") from exc
    need(body.startswith("---\n") and "\x00" not in body, "skill_frontmatter")
    header, separator, instructions = body[4:].partition("\n---\n")
    need(separator and instructions.strip(), "skill_instructions")
    meta = {}
    for line in header.splitlines():
        key, colon, value = line.partition(":")
        need(colon and key in {"name", "description", "license", "compatibility", "allowed-tools"}
             and key not in meta, "skill_frontmatter_fields")
        parsed = decode(value.strip().encode())
        text(parsed, 1024 if key == "description" else 500)
        meta[key] = parsed
    need(meta.get("name") == manifest.name and meta.get("description") == manifest.description,
         "frontmatter_manifest_mismatch")
    # allowed-tools is informative, never an authorization source.
    return instructions


class SkillPackage:
    def __init__(self, root: Path, approval: SkillApproval):
        need(isinstance(approval, SkillApproval), "host_approval_required")
        need(approval.trust_tier != TrustTier.UNTRUSTED, "untrusted_skill")
        self.fd = -1
        try:
            self.fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            manifest = SkillManifest.from_dict(decode(_read_at(self.fd, "manifest.json", MAX_MANIFEST)))
            need(Path(root).name == manifest.name, "directory_name_mismatch")
            need((manifest.name, manifest.version, manifest.hash, manifest.publisher, manifest.source_uri)
                 == (approval.name, approval.version, approval.package_hash, approval.publisher, approval.source_uri),
                 "approval_mismatch")
            self._manifest = manifest
            self._approval = approval
        except BaseException:
            self.close()
            raise

    @property
    def manifest(self):
        return self._manifest

    @property
    def approval(self):
        return self._approval

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1

    def load(self, path):
        need(self.fd >= 0, "closed_package")
        safe_path(path)
        entry = next((x for x in self.manifest.files if x.path == path), None)
        need(entry is not None, "undeclared_resource")
        raw = _read_at(self.fd, path, entry.size)
        need(len(raw) == entry.size and hashlib.sha256(raw).hexdigest() == entry.sha256,
             "resource_digest_mismatch")
        if path == "SKILL.md":
            parse_skill_body(raw, self.manifest)
        return raw


@dataclass(frozen=True)
class ConsumerSkillPolicy:
    consumer: str
    allowed_hashes: tuple[str, ...]
    mandatory_hashes: tuple[str, ...] = ()
    disabled_names: tuple[str, ...] = ()
    trust_tiers: tuple[TrustTier, ...] = (TrustTier.REVIEWED, TrustTier.FIRST_PARTY)
    version: str = VERSION

    def __post_init__(self):
        token(self.consumer)
        semver(self.version)
        for key in ("allowed_hashes", "mandatory_hashes"):
            object.__setattr__(self, key, values(getattr(self, key), sha))
        need(set(self.mandatory_hashes) <= set(self.allowed_hashes), "mandatory_not_approved")
        object.__setattr__(self, "disabled_names", values(self.disabled_names, name))
        try:
            tiers = values(self.trust_tiers, TrustTier, maximum=3)
        except (TypeError, ValueError) as exc:
            raise SkillError("trust_tier") from exc
        need(tiers and TrustTier.UNTRUSTED not in tiers, "unsafe_consumer_trust")
        object.__setattr__(self, "trust_tiers", tiers)

    @property
    def hash(self):
        return digest({f.name: list(getattr(self, f.name)) if isinstance(getattr(self, f.name), tuple)
                       else getattr(self, f.name) for f in fields(self)})


@dataclass(frozen=True)
class SkillNodeContext:
    consumer: str
    task_id: str
    run_token: str
    attempt: int
    fencing_token: int
    spec_policy_hash: str
    platform: str
    scope: CapabilityScope
    parent_scope: CapabilityScope
    consumer_scope: CapabilityScope
    registry: RegistrySnapshot

    def __post_init__(self):
        for key in ("consumer", "task_id", "run_token"):
            token(getattr(self, key))
        need(all(type(x) is int and 0 < x <= (1 << 63) - 1
                 for x in (self.attempt, self.fencing_token)), "attempt_fence")
        sha(self.spec_policy_hash)
        need(self.platform in {"linux", "windows", "darwin"}, "platform")
        need(all(isinstance(x, CapabilityScope) for x in (
            self.scope, self.parent_scope, self.consumer_scope))
            and isinstance(self.registry, RegistrySnapshot), "typed_host_context")
        try:
            self.scope.require_subset_of(self.parent_scope)
            self.scope.require_subset_of(self.consumer_scope)
        except CapabilityError as exc:
            raise SkillError("scope_escalation") from exc

    def binding(self):
        return {"consumer": self.consumer, "task_id": self.task_id, "run_token": self.run_token,
                "attempt": self.attempt, "fencing_token": self.fencing_token,
                "spec_policy_hash": self.spec_policy_hash, "platform": self.platform, "scope_hash": self.scope.hash,
                "parent_scope_hash": self.parent_scope.hash, "consumer_scope_hash": self.consumer_scope.hash,
                "registry_hash": self.registry.hash}


@dataclass(frozen=True)
class SkillRequest:
    name: str
    reason: str
    resources: tuple[str, ...] = ()

    def __post_init__(self):
        name(self.name)
        text(self.reason, 256)
        object.__setattr__(self, "resources", values(self.resources, safe_path, maximum=16))
        need("SKILL.md" not in self.resources, "body_is_automatic")


@dataclass(frozen=True)
class PolicyLayers:
    herdr: str
    consumer: str
    node: str

    def __post_init__(self):
        for key in ("herdr", "consumer", "node"):
            text(getattr(self, key), 16_384)

    def to_json(self):
        return [{"authority": key, "text": getattr(self, key)} for key in ("herdr", "consumer", "node")]


@dataclass(frozen=True)
class SkillBundle:
    # Immutable serialized context. No provider SDK or mutable caller objects.
    payload: bytes
    trace: bytes

    @property
    def hash(self):
        return hashlib.sha256(self.payload).hexdigest()

    def render(self):
        """One provider-independent control/data envelope for the #73 compiler."""
        return decode(self.payload)

    def telemetry(self):
        """Version/hash/reason codes only, excluding loaded text and resource bytes."""
        return decode(self.trace)


def compatibility(manifest, context, executor_id):
    scope = context.scope
    if context.platform not in manifest.platforms:
        return "platform_incompatible"
    if not set(manifest.tools) <= set(scope.tools) or not set(manifest.permissions) <= set(scope.permissions):
        return "grant_insufficient"
    if not set(manifest.capabilities) <= set(scope.capabilities):
        return "capability_scope"
    executor = next((x for x in context.registry.executors if x.id == executor_id), None)
    if executor is None or executor.id not in scope.executors or executor.provider_id not in scope.providers:
        return "executor_scope"
    cap = next(x for x in context.registry.capabilities if x.id == executor.capability_id)
    provider = next(x for x in context.registry.providers if x.id == executor.provider_id)
    if (cap.id not in scope.capabilities or not set(manifest.capabilities) <= {cap.id}
            or not set(manifest.features) <= set(cap.features)
            or not set(manifest.tools) <= set(executor.tools)):
        return "executor_incompatible"
    if Modality.TEXT not in set(scope.input_modalities) & set(cap.input_modalities):
        return "text_context_unavailable"
    if not set(scope.regions) & set(cap.data_policy.regions) & set(provider.data_policy.regions):
        return "data_policy_incompatible"
    for policy in (cap.data_policy, provider.data_policy):
        if (not set(policy.regions) & set(scope.regions)
                or list(Egress).index(policy.egress) > list(Egress).index(scope.max_egress)
                or list(Retention).index(policy.retention) > list(Retention).index(scope.max_retention)
                or list(Training).index(policy.training) > list(Training).index(scope.training)):
            return "data_policy_incompatible"
        if any(x.data_class not in set(scope.data_classes) & set(policy.data_classes)
               for x in manifest.files):
            return "data_class_incompatible"
    return None


class SkillRegistry:
    def __init__(self, packages: tuple[tuple[Path, SkillApproval], ...]):
        need(isinstance(packages, (list, tuple)) and len(packages) <= 64, "registry_size")
        loaded = []
        try:
            for root, approval in packages:
                package = SkillPackage(root, approval)
                loaded.append(package)
            names = [x.manifest.name for x in loaded]
            need(len(names) == len(set(names)), "duplicate_skill_name")
            self.packages = tuple(sorted(loaded, key=lambda x: x.manifest.name))
        except BaseException:
            for package in loaded:
                package.close()
            raise

    def close(self):
        for package in self.packages:
            package.close()

    def _reason(self, package, context, policy, executor_id):
        if (package.manifest.hash not in policy.allowed_hashes
                or package.approval.trust_tier not in policy.trust_tiers):
            return "consumer_unapproved"
        if package.manifest.name in policy.disabled_names:
            return "consumer_disabled"
        return compatibility(package.manifest, context, executor_id)

    def discovery(self, context: SkillNodeContext, policy: ConsumerSkillPolicy, *, executor_id: str):
        self._check(context, policy)
        index, rejected = [], []
        need(set(policy.mandatory_hashes) <= {x.manifest.hash for x in self.packages},
             "mandatory_skill_missing")
        for package in self.packages:
            manifest = package.manifest
            reason = self._reason(package, context, policy, executor_id)
            if reason is not None:
                need(manifest.hash not in policy.mandatory_hashes, "mandatory_skill_unavailable")
                rejected.append({"name": manifest.name, "code": reason})
                continue
            index.append({"name": manifest.name, "description": manifest.description[:256],
                          "description_truncated": len(manifest.description) > 256,
                          "version": manifest.version, "package_hash": manifest.hash})
        value = {"schema_version": VERSION, "index": index, "rejected": rejected}
        need(len(canonical(value)) <= MAX_INDEX, "discovery_budget")
        return value

    @staticmethod
    def _check(context, policy):
        need(isinstance(context, SkillNodeContext) and isinstance(policy, ConsumerSkillPolicy)
             and context.consumer == policy.consumer, "consumer_context_mismatch")

    def resolve(self, requests: tuple[SkillRequest, ...], context: SkillNodeContext,
                policy: ConsumerSkillPolicy, layers: PolicyLayers, *, executor_id: str,
                max_bytes=MAX_BUNDLE):
        self._check(context, policy)
        need(isinstance(layers, PolicyLayers), "typed_policy_layers")
        need(type(max_bytes) is int and 0 < max_bytes <= MAX_BUNDLE, "context_budget")
        need(isinstance(requests, (tuple, list)) and len(requests) <= 64
             and all(isinstance(x, SkillRequest) for x in requests), "skill_requests")
        requested = {x.name: x for x in requests}
        need(len(requested) == len(requests), "duplicate_skill_request")
        by_hash = {x.manifest.hash: x for x in self.packages}
        mandatory = set()
        for package_hash in policy.mandatory_hashes:
            package = by_hash.get(package_hash)
            need(package is not None, "mandatory_skill_missing")
            mandatory.add(package.manifest.name)
            if package.manifest.name not in requested:
                requested[package.manifest.name] = SkillRequest(package.manifest.name, "mandatory_project_security")
        by_name = {x.manifest.name: x for x in self.packages}
        selected, rejected, content = [], [], []
        binding = {**context.binding(), "executor_id": executor_id}
        envelope = {"schema_version": VERSION, "binding": binding,
                    "consumer_skill_policy_hash": policy.hash,
                    "policy_layers": layers.to_json(), "skills": content}
        used_bytes = len(canonical(envelope))
        need(used_bytes <= max_bytes, "context_budget_exceeded")
        # Trace all omissions without opening any unused body/resource.
        for package in self.packages:
            if package.manifest.name not in requested:
                reason = self._reason(package, context, policy, executor_id) or "not_needed"
                rejected.append({"name": package.manifest.name, "code": reason})
        for skill_name, request in sorted(requested.items()):
            package = by_name.get(skill_name)
            reason = "unknown_skill" if package is None else self._reason(package, context, policy, executor_id)
            if reason is None:
                declared = {x.path for x in package.manifest.files}
                if not set(request.resources) <= declared:
                    reason = "undeclared_resource"
                else:
                    executor = next(x for x in context.registry.executors if x.id == executor_id)
                    capability = next(x for x in context.registry.capabilities if x.id == executor.capability_id)
                    requested_entries = [x for x in package.manifest.files if x.path in request.resources]
                    if (any(x.media_type in {"image/png", "image/jpeg"} for x in requested_entries)
                            and Modality.IMAGE not in set(context.scope.input_modalities) & set(capability.input_modalities)):
                        reason = "resource_modality_incompatible"
            if reason is not None:
                need(skill_name not in mandatory, "mandatory_skill_unavailable")
                rejected.append({"name": skill_name, "code": reason})
                continue
            manifest = package.manifest
            body = parse_skill_body(package.load("SKILL.md"), manifest)
            provenance = {"name": manifest.name, "version": manifest.version, "package_hash": manifest.hash,
                          "publisher": manifest.publisher, "source_uri": manifest.source_uri,
                          "approved_revision": package.approval.approved_revision,
                          "trust_tier": package.approval.trust_tier}
            item = {**provenance, "authority": "context_data", "instructions": body, "resources": []}
            used_bytes += len(canonical(item)) + int(bool(content))
            need(used_bytes <= max_bytes, "context_budget_exceeded")
            resource_trace = []
            for path in request.resources:
                entry = next(x for x in manifest.files if x.path == path)
                textual = entry.media_type.startswith("text/") or entry.media_type == "application/json"
                lower_bound = entry.size if textual else 4 * ((entry.size + 2) // 3)
                # Reject oversized declared bytes before reading or expanding them.
                need(lower_bound <= max_bytes - used_bytes, "context_budget_exceeded")
                raw = package.load(path)
                if textual:
                    try:
                        value = {"encoding": "utf-8", "data": raw.decode("utf-8")}
                    except UnicodeError as exc:
                        raise SkillError("resource_encoding") from exc
                else:
                    value = {"encoding": "base64", "data": base64.b64encode(raw).decode("ascii")}
                resource = {"path": path, "sha256": entry.sha256,
                            "media_type": entry.media_type, **value}
                used_bytes += len(canonical(resource)) + int(bool(item["resources"]))
                need(used_bytes <= max_bytes, "context_budget_exceeded")
                item["resources"].append(resource)
                resource_trace.append({"path": path, "sha256": entry.sha256, "size": entry.size,
                                       "media_type": entry.media_type, "data_class": entry.data_class})
            content.append(item)
            selected.append({**provenance, "reason": request.reason, "mandatory": skill_name in mandatory,
                             "resources": resource_trace})
        payload = canonical(envelope)
        need(len(payload) == used_bytes and len(payload) <= max_bytes, "context_budget_exceeded")
        trace = canonical({"schema_version": VERSION, "binding": binding,
                           "consumer_skill_policy_hash": policy.hash,
                           "selected": selected, "rejected": rejected})
        return SkillBundle(payload, trace)


def lint_package(root: Path):
    """Authoring validation, without granting trust or executing declared scripts."""
    fd = -1
    try:
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        manifest = SkillManifest.from_dict(decode(_read_at(fd, "manifest.json", MAX_MANIFEST)))
        need(Path(root).name == manifest.name, "directory_name_mismatch")
        for entry in manifest.files:
            raw = _read_at(fd, entry.path, entry.size)
            need(len(raw) == entry.size and hashlib.sha256(raw).hexdigest() == entry.sha256,
                 "resource_digest_mismatch")
            if entry.media_type.startswith("text/") or entry.media_type == "application/json":
                try:
                    raw.decode("utf-8")
                except UnicodeError as exc:
                    raise SkillError("resource_encoding") from exc
            if entry.path == "SKILL.md":
                parse_skill_body(raw, manifest)
        return {"name": manifest.name, "version": manifest.version, "package_hash": manifest.hash,
                "publisher": manifest.publisher, "files": len(manifest.files),
                "authoring_base_revision": manifest.authoring_base_revision}
    except OSError as exc:
        raise SkillError("package_unavailable_or_symlink") from exc
    finally:
        if fd >= 0:
            os.close(fd)
