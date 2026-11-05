"""Host-owned, bounded context compilation. Provider sessions are never authority."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from typing import Callable
from urllib.parse import urlsplit

from .capability import DataClass, Egress, Modality, Retention, Training
from .skills import PolicyLayers, SkillBundle, SkillNodeContext

VERSION = "1.0.0"
MAX_BYTES = 262_144
MAX_ITEMS = 64
MAX_TEXT = 65_536


class ContextError(ValueError):
    """Safe reason code, excluding source bytes and private exceptions."""


class ContextBlocked(ContextError):
    """Required context cannot be safely compiled; split or block the task."""


def require(value, code):
    if not value:
        raise ContextError(code)


def canonical(value):
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, UnicodeError) as exc:
        raise ContextError("invalid_context_encoding") from exc


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def hash_value(value):
    require(isinstance(value, str) and re.fullmatch(r"[a-f0-9]{64}", value), "invalid_digest")
    return value


def token(value):
    require(isinstance(value, str) and re.fullmatch(r"[A-Za-z0-9_.:/-]{1,256}", value), "invalid_identity")
    if "SecretRedactor" in globals():
        require(not any(x.search(value) for x in SecretRedactor._patterns), "secret_identity")
    return value


def bounded_text(value, maximum=MAX_TEXT, *, empty=False):
    require(isinstance(value, str) and (empty or value) and len(value.encode("utf-8")) <= maximum,
            "text_limit")
    return value


class MemoryClass(StrEnum):
    DURABLE = "durable_task_event"
    EPISODIC = "episodic_summary"
    KNOWLEDGE = "knowledge_reference"
    SKILL = "skill"
    ARTIFACT = "artifact"
    PROVIDER_CACHE = "provider_session_cache"


class SourceState(StrEnum):
    VERIFIED = "verified"
    UNVERIFIED = "unverified_note"
    STALE = "stale"
    UNAVAILABLE = "unavailable"
    CONFLICT = "conflicting_evidence"


@dataclass(frozen=True)
class SourceRef:
    uri: str
    sha256: str
    project: str
    revision: str
    data_class: DataClass
    state: SourceState = SourceState.VERIFIED
    holdout_series: str | None = None

    def __post_init__(self):
        bounded_text(self.uri, 2048)
        require(not any(x.search(self.uri) for x in SecretRedactor._patterns), "secret_source_reference")
        parsed = urlsplit(self.uri)
        require(parsed.scheme in {"https", "artifact", "herdr"} and parsed.netloc
                and not parsed.username and not parsed.password and not parsed.query
                and not parsed.fragment, "unsafe_source_reference")
        hash_value(self.sha256)
        token(self.project)
        token(self.revision)
        object.__setattr__(self, "data_class", DataClass(self.data_class))
        object.__setattr__(self, "state", SourceState(self.state))
        if self.holdout_series is not None:
            token(self.holdout_series)


@dataclass(frozen=True)
class ContextItem:
    id: str
    memory_class: MemoryClass
    sources: tuple[SourceRef, ...]
    size: int
    reason: str
    priority: int = 50
    mandatory: bool = False
    derived_summary: bool = False

    def __post_init__(self):
        token(self.id)
        object.__setattr__(self, "memory_class", MemoryClass(self.memory_class))
        require(isinstance(self.sources, (tuple, list)) and 0 < len(self.sources) <= 16
                and all(isinstance(x, SourceRef) for x in self.sources), "source_provenance_required")
        object.__setattr__(self, "sources", tuple(self.sources))
        require(type(self.size) is int and 0 < self.size <= MAX_BYTES, "item_size")
        bounded_text(self.reason, 512)
        require(type(self.priority) is int and 0 <= self.priority <= 1000
                and type(self.mandatory) is bool, "item_priority")
        require(type(self.derived_summary) is bool and (not self.derived_summary
                or self.memory_class == MemoryClass.EPISODIC and len(self.sources) > 1
                and self.sources[0].state == SourceState.UNVERIFIED
                and self.sources[0].uri.startswith("herdr://derived/")), "derived_summary_binding")
        require(not (self.mandatory and self.derived_summary), "derived_summary_cannot_be_mandatory")
        require(not self.mandatory or self.memory_class != MemoryClass.PROVIDER_CACHE,
                "cache_cannot_be_mandatory")


@dataclass(frozen=True)
class ProjectMap:
    project: str
    base_sha: str
    file_versions: tuple[tuple[str, str], ...]
    languages: tuple[str, ...]
    commands: tuple[tuple[str, str], ...]
    directories: tuple[str, ...]
    git_rules: str
    automation: str

    def __post_init__(self):
        token(self.project)
        require(isinstance(self.base_sha, str) and re.fullmatch(r"[a-f0-9]{40}|[a-f0-9]{64}", self.base_sha),
                "base_revision")
        for key in ("file_versions", "languages", "commands", "directories"):
            value = getattr(self, key)
            require(isinstance(value, (tuple, list)) and len(value) <= 64, "project_map_limit")
            object.__setattr__(self, key, tuple(tuple(x) if isinstance(x, list) else x for x in value))
        paths = []
        for path, version in self.file_versions:
            require(isinstance(path, str) and len(path) <= 512 and not path.startswith("/")
                    and "\\" not in path and all(x not in {"", ".", ".."} for x in path.split("/")),
                    "project_map_path")
            hash_value(version)
            paths.append(path)
        require(len(paths) == len(set(paths)), "duplicate_map_file")
        for language in self.languages:
            token(language)
        for purpose, command in self.commands:
            token(purpose)
            bounded_text(command, 1024)
        for directory in self.directories:
            bounded_text(directory, 512)
        bounded_text(self.git_rules, 4096, empty=True)
        bounded_text(self.automation, 4096, empty=True)
        require(len(canonical(asdict(self))) <= 16_384, "project_map_limit")

    @property
    def hash(self):
        return digest(asdict(self))

    def require_current(self, base_sha, file_versions):
        require(isinstance(file_versions, (tuple, list)) and len(file_versions) <= 64,
                "current_file_versions")
        current = {}
        for entry in file_versions:
            require(isinstance(entry, (tuple, list)) and len(entry) == 2, "current_file_versions")
            path, version = entry
            require(isinstance(path, str) and len(path) <= 512 and not path.startswith("/")
                    and "\\" not in path and all(x not in {"", ".", ".."} for x in path.split("/")),
                    "current_file_versions")
            hash_value(version)
            require(path not in current, "duplicate_current_file")
            current[path] = version
        if base_sha != self.base_sha or dict(self.file_versions) != current:
            raise ContextBlocked("project_map_invalidated")


@dataclass(frozen=True)
class ControlState:
    task: str
    scope: str
    acceptance: str
    oracle: str
    current_diff: str
    current_error: str
    evidence: tuple[SourceRef, ...]
    data_class: DataClass = DataClass.INTERNAL

    def __post_init__(self):
        object.__setattr__(self, "data_class", DataClass(self.data_class))
        for key in ("task", "scope", "acceptance", "oracle", "current_diff", "current_error"):
            bounded_text(getattr(self, key), empty=key in {"current_diff", "current_error"})
        require(isinstance(self.evidence, (tuple, list)) and len(self.evidence) <= 32
                and all(isinstance(x, SourceRef) for x in self.evidence), "control_evidence")
        object.__setattr__(self, "evidence", tuple(self.evidence))


class SecretRedactor:
    """Host-provided known secrets plus bounded common credential forms."""
    _patterns = (
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.S),
        re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9_]{8,}|github_pat_[A-Za-z0-9_]{8,}|sk-[A-Za-z0-9_-]{8,}|AKIA[A-Z0-9]{16})\b"),
        re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]+"),
        re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|password|secret|credential)\s*[:=]\s*[\"']?[^\s,;\"']+"),
        re.compile(r"https?://[^\s/]+:[^\s/@]+@[^\s]+"),
    )

    def __init__(self, secrets=()):
        require(isinstance(secrets, (tuple, list)) and len(secrets) <= 128
                and all(isinstance(x, str) and 4 <= len(x.encode("utf-8")) <= 8192 for x in secrets),
                "redaction_configuration")
        self._secrets = tuple(sorted(set(secrets), key=lambda x: (-len(x), x)))
        self.policy_hash = digest({"version": VERSION, "known_secret_hashes":
                                   sorted(hashlib.sha256(x.encode()).hexdigest() for x in self._secrets)})

    def redact(self, value, *, maximum=MAX_BYTES):
        # Capture may decode up to 1 MiB of bytes; replacement UTF-8 characters
        # can expand malformed input to three times that size. Keep one bounded
        # string so credentials spanning any chunk boundary remain redacted.
        require(type(maximum) is int and 0 < maximum <= 3_145_728, "redaction_limit")
        bounded_text(value, maximum, empty=True)
        for secret in self._secrets:
            value = value.replace(secret, "[REDACTED]")
        for pattern in self._patterns:
            value = pattern.sub("[REDACTED]", value)
        return value

    def tree(self, value):
        if isinstance(value, str):
            return self.redact(value)
        if isinstance(value, dict):
            return {self.redact(k): self.tree(v) for k, v in value.items()}
        if isinstance(value, (list, tuple)):
            return [self.tree(x) for x in value]
        return value


@dataclass(frozen=True)
class SelectionSnapshot:
    """Frozen host-approved schemas and skill data, without grant authority."""
    payload: bytes
    reason: str
    previous_hash: str | None = None

    def __post_init__(self):
        require(isinstance(self.payload, bytes) and len(self.payload) <= 131_072, "selection_limit")
        raw = json.loads(self.payload)
        require(isinstance(raw, dict) and set(raw) == {"tools", "skills", "skill_trace"}, "selection_shape")
        require(isinstance(raw["tools"], list) and len(raw["tools"]) <= 64
                and isinstance(raw["skills"], list) and isinstance(raw["skill_trace"], dict), "selection_shape")
        require(canonical(raw) == self.payload, "noncanonical_selection")
        bounded_text(self.reason, 512)
        if self.previous_hash is not None:
            hash_value(self.previous_hash)
            require(self.previous_hash != self.hash, "selection_change_required")

    @property
    def hash(self):
        return hashlib.sha256(self.payload).hexdigest()

    @classmethod
    def build(cls, tools, skills: SkillBundle, context: SkillNodeContext, *,
              expected_skill_hash, executor_id, reason, previous_hash=None):
        require(isinstance(skills, SkillBundle) and skills.hash == hash_value(expected_skill_hash),
                "skill_snapshot_hash")
        raw, trace = skills.render(), skills.telemetry()
        binding = {**context.binding(), "executor_id": executor_id}
        require(raw.get("binding") == binding and trace.get("binding") == binding,
                "skill_context_binding")
        require(all(isinstance(x, dict) and x.get("authority") == "context_data" for x in raw["skills"]),
                "skill_data_authority")
        require(isinstance(tools, (list, tuple)) and len(tools) <= 64, "tool_snapshot")
        names = []
        for tool in tools:
            require(isinstance(tool, dict) and set(tool) == {"logical_id", "version", "schema"}
                    and tool["logical_id"] in context.scope.tools and isinstance(tool["schema"], dict),
                    "tool_snapshot_scope")
            token(tool["version"])
            names.append(tool["logical_id"])
        require(len(names) == len(set(names)), "duplicate_tool_snapshot")
        return cls(canonical({"tools": sorted(tools, key=lambda x: x["logical_id"]),
                              "skills": raw["skills"], "skill_trace": trace}), reason, previous_hash)


@dataclass(frozen=True)
class ContextPlan:
    """Immutable provider-independent reconstruction input. No source bodies."""
    context: SkillNodeContext
    project: str
    payload: bytes
    items: tuple[ContextItem, ...]
    token_budget: int
    byte_budget: int
    redaction_hash: str
    experiment_series: str | None = None
    role: str = "worker"

    def __post_init__(self):
        require(isinstance(self.context, SkillNodeContext), "typed_plan_context")
        token(self.project)
        require(isinstance(self.payload, bytes) and len(self.payload) <= MAX_BYTES, "plan_bytes")
        raw = json.loads(self.payload)
        require(canonical(raw) == self.payload and isinstance(raw, dict)
                and raw.get("binding") == self.context.binding(), "plan_binding")
        expected = {"binding", "stable_prefix", "controls", "node_instructions", "selection_hash",
                    "selection_reason", "previous_selection_hash", "skill_trace", "control_source_digest"}
        require(set(raw) == expected, "plan_schema")
        controls = raw["controls"]
        require(isinstance(controls, dict) and set(controls) == {
            "task", "scope", "acceptance", "oracle", "current_diff", "current_error", "evidence", "data_class"},
            "required_control_fields")
        ControlState(**{**controls, "evidence": tuple(SourceRef(**x) for x in controls["evidence"])})
        require(type(self.token_budget) is int and 0 < self.token_budget <= 1_000_000
                and type(self.byte_budget) is int and 0 < self.byte_budget <= MAX_BYTES, "context_budget")
        require(isinstance(self.items, (tuple, list)) and len(self.items) <= MAX_ITEMS
                and all(isinstance(x, ContextItem) for x in self.items), "context_items")
        object.__setattr__(self, "items", tuple(self.items))
        require(len({x.id for x in self.items}) == len(self.items), "duplicate_context_item")
        hash_value(self.redaction_hash)
        require(self.role in {"worker", "experimenter", "evaluator"}, "context_role")
        if self.experiment_series is not None:
            token(self.experiment_series)

    @property
    def hash(self):
        return digest({"payload_sha256": hashlib.sha256(self.payload).hexdigest(),
                       "items": [asdict(x) for x in self.items], "token_budget": self.token_budget,
                       "byte_budget": self.byte_budget, "redaction_hash": self.redaction_hash,
                       "series": self.experiment_series, "role": self.role})

    @property
    def stable_prefix(self):
        return json.loads(self.payload)["stable_prefix"]


@dataclass(frozen=True)
class TokenCounter:
    """Trusted host adapter for a pinned provider/executor tokenizer.

    This is an injected host boundary, not a model-supplied token estimate.
    Live provider token/cache usage remains a separately measured observation.
    """
    provider_id: str
    executor_version: str
    tokenizer_version: str
    count: Callable[[bytes], int]

    def measure(self, raw):
        try:
            value = self.count(raw)
        except Exception as exc:
            raise ContextBlocked("tokenizer_unavailable") from exc
        require(type(value) is int and 0 <= value <= 2**31 and (not raw or value > 0),
                "invalid_token_measurement")
        return value


@dataclass(frozen=True)
class ContextBundle:
    plan_hash: str
    executor_id: str
    payload: bytes
    trace: bytes

    @property
    def hash(self):
        return hashlib.sha256(self.payload).hexdigest()

    def render(self):
        return json.loads(self.payload)

    def telemetry(self):
        return json.loads(self.trace)


def _source_policy(source, project, context, *, series=None, role="worker"):
    if source.project != project:
        return "project_scope"
    if source.holdout_series is not None and (role != "evaluator" or source.holdout_series != series):
        return "holdout_private"
    if source.data_class not in context.scope.data_classes:
        return "data_class_scope"
    if source.state != SourceState.VERIFIED:
        return source.state.value
    return None


class ContextCompiler:
    def __init__(self, redactor: SecretRedactor):
        require(isinstance(redactor, SecretRedactor), "host_redactor")
        self.redactor = redactor

    def plan(self, context: SkillNodeContext, project_map: ProjectMap, controls: ControlState,
             layers: PolicyLayers, selection: SelectionSnapshot, items=(), *,
             current_base_sha, current_file_versions, token_budget, byte_budget=MAX_BYTES,
             experiment_series=None, role="worker"):
        require(isinstance(context, SkillNodeContext) and isinstance(project_map, ProjectMap)
                and isinstance(controls, ControlState) and isinstance(layers, PolicyLayers)
                and isinstance(selection, SelectionSnapshot), "typed_context_inputs")
        binding = context.binding()
        require(canonical(self.redactor.tree(binding)) == canonical(binding), "secret_context_binding")
        require(self.redactor.redact(project_map.project) == project_map.project, "secret_context_binding")
        project_map.require_current(current_base_sha, current_file_versions)
        require(type(token_budget) is int and 0 < token_budget <= 1_000_000
                and type(byte_budget) is int and 0 < byte_budget <= MAX_BYTES, "context_budget")
        require(isinstance(items, (tuple, list)) and len(items) <= MAX_ITEMS
                and all(isinstance(x, ContextItem) for x in items), "context_items")
        require(len({x.id for x in items}) == len(items), "duplicate_context_item")
        require(role in {"worker", "experimenter", "evaluator"}, "context_role")
        if experiment_series is not None:
            token(experiment_series)
        require(controls.data_class in context.scope.data_classes, "control_data_class_scope")
        for source in controls.evidence:
            require(self.redactor.tree(asdict(source)) == asdict(source), "secret_source_reference")
            reason = _source_policy(source, project_map.project, context, series=experiment_series, role=role)
            if reason:
                raise ContextBlocked("required_evidence_" + reason)
        safe_items = []
        for item in items:
            require(self.redactor.redact(item.id) == item.id, "secret_context_identity")
            require(all(canonical(self.redactor.tree(asdict(x))) == canonical(asdict(x)) for x in item.sources),
                    "secret_source_reference")
            safe_items.append(replace(item, reason=self.redactor.redact(item.reason)))
        snapshot = json.loads(selection.payload)
        controls_raw = self.redactor.tree(asdict(controls))
        # Original immutable references/digests survive redaction or compaction.
        stable = self.redactor.tree({
            "schema_version": VERSION, "host_policy": layers.herdr, "consumer_policy": layers.consumer,
            "project_map": asdict(project_map), "selection": {"tools": snapshot["tools"], "skills": snapshot["skills"]}})
        payload = canonical({"binding": context.binding(), "stable_prefix": stable,
                             "controls": controls_raw, "node_instructions": self.redactor.redact(layers.node),
                             "selection_hash": selection.hash, "selection_reason": self.redactor.redact(selection.reason),
                             "previous_selection_hash": selection.previous_hash,
                             "skill_trace": self.redactor.tree(snapshot["skill_trace"]),
                             "control_source_digest": digest(asdict(controls))})
        if len(payload) > byte_budget:
            raise ContextBlocked("mandatory_context_bytes_exceeded")
        return ContextPlan(context, project_map.project, payload, tuple(sorted(safe_items, key=lambda x:
                           (not x.mandatory, -x.priority, x.id))), token_budget, byte_budget,
                           self.redactor.policy_hash, experiment_series, role)

    @staticmethod
    def _executor(plan, executor_id):
        context = plan.context
        executor = next((x for x in context.registry.executors if x.id == executor_id), None)
        require(executor is not None and executor_id in context.scope.executors
                and executor.provider_id in context.scope.providers
                and executor.capability_id in context.scope.capabilities, "executor_scope")
        cap = next(x for x in context.registry.capabilities if x.id == executor.capability_id)
        provider = next(x for x in context.registry.providers if x.id == executor.provider_id)
        require(Modality.TEXT in set(cap.input_modalities) & set(context.scope.input_modalities), "text_context_unavailable")
        require(set(cap.data_policy.regions) & set(provider.data_policy.regions) & set(context.scope.regions),
                "provider_data_policy")
        for policy in (cap.data_policy, provider.data_policy):
            require(list(Egress).index(policy.egress) <= list(Egress).index(context.scope.max_egress)
                    and list(Retention).index(policy.retention) <= list(Retention).index(context.scope.max_retention)
                    and list(Training).index(policy.training) <= list(Training).index(context.scope.training),
                    "provider_data_policy")
        return executor, cap, provider

    def preflight(self, plan: ContextPlan, *, executor_id, counter: TokenCounter,
                  renderer="messages",allowed_data_classes=None):
        """Validate source-independent host metadata before any source loader."""
        require(isinstance(plan, ContextPlan) and plan.redaction_hash == self.redactor.policy_hash,
                "plan_redaction_policy")
        require(isinstance(counter, TokenCounter) and callable(counter.count), "host_tokenizer_required")
        executor, cap, provider = self._executor(plan, executor_id)
        require(counter.provider_id == executor.provider_id and counter.executor_version == executor.version,
                "tokenizer_executor_binding")
        token(counter.tokenizer_version)
        limits = [x for x in (plan.token_budget, plan.context.scope.max_context_tokens,
                               cap.context_tokens, cap.max_input_tokens) if x is not None]
        budget = min(limits)
        require(renderer in {"messages", "parts"}, "renderer")
        raw = json.loads(plan.payload)
        require(plan.project==raw["stable_prefix"]["project_map"]["project"],"context_project_binding")
        provider_classes=set(cap.data_policy.data_classes)&set(provider.data_policy.data_classes)
        if allowed_data_classes is not None:
            require(isinstance(allowed_data_classes,tuple) and all(isinstance(x,DataClass) for x in allowed_data_classes)
                    and len(set(allowed_data_classes))==len(allowed_data_classes),"host_provider_data_classes")
            provider_classes &= set(allowed_data_classes)
        controls_class = DataClass(raw["controls"]["data_class"])
        require(controls_class in provider_classes,
                "required_provider_data_class")
        for source_raw in raw["controls"]["evidence"]:
            source = SourceRef(**source_raw)
            require(self.redactor.tree(asdict(source)) == asdict(source), "secret_source_reference")
            require(_source_policy(source, plan.project, plan.context, series=plan.experiment_series,
                                   role=plan.role) is None and source.data_class in
                    provider_classes,"required_provider_evidence_scope")
        for item in plan.items:
            if item.mandatory:
                require(self.redactor.redact(item.id) == item.id, "secret_context_identity")
                if item.memory_class == MemoryClass.PROVIDER_CACHE:
                    raise ContextBlocked("required_source_provider_cache_not_authority")
                for source in item.sources:
                    require(self.redactor.tree(asdict(source)) == asdict(source), "secret_source_reference")
                    reason = _source_policy(source, plan.project, plan.context,
                                            series=plan.experiment_series, role=plan.role)
                    if reason:
                        raise ContextBlocked("required_source_" + reason)
                    if source.data_class not in provider_classes:
                        raise ContextBlocked("required_provider_source_data_class")
        # The skill resolver checked this executor; a switch re-resolves skills first.
        require(raw["skill_trace"].get("binding") == {**plan.context.binding(), "executor_id": executor_id},
                "skill_executor_binding")
        return executor, cap, provider, raw, budget

    def compile(self, plan: ContextPlan, *, executor_id, counter: TokenCounter, loader: Callable,
                renderer="messages", envelope=None, input_token_limit=None,allowed_data_classes=None):
        executor, cap, provider, raw, budget = self.preflight(
            plan, executor_id=executor_id, counter=counter, renderer=renderer,
            allowed_data_classes=allowed_data_classes)
        provider_classes=set(cap.data_policy.data_classes)&set(provider.data_policy.data_classes)
        if allowed_data_classes is not None:provider_classes &= set(allowed_data_classes)
        require(envelope is None or callable(envelope), "host_context_envelope")
        if input_token_limit is not None:
            require(type(input_token_limit) is int and 0 < input_token_limit <= 2**31,
                    "host_context_input_limit")
            budget = min(budget, input_token_limit)
        content, selected, rejected = [], [], []
        def render():
            # Both adapters preserve the same host-control / untrusted-data envelope.
            data = {"binding": raw["binding"], "controls": raw["controls"],
                    "node_instructions": raw["node_instructions"], "context_data": content}
            if renderer == "messages":
                value = {"messages": [{"role": "system", "content": canonical(raw["stable_prefix"]).decode()},
                                      {"role": "user", "content": canonical(data).decode()}]}
            else:
                value = {"system": canonical(raw["stable_prefix"]).decode(),
                         "contents": [{"role": "user", "parts": [{"text": canonical(data).decode()}]}]}
            return canonical(value)
        def measured(wire):
            transport = envelope(wire) if envelope is not None else wire
            require(isinstance(transport,bytes),"host_context_envelope_bytes")
            return transport
        def fits(wire):
            transport = measured(wire)
            return len(transport) <= plan.byte_budget and counter.measure(transport) <= budget
        wire = render()
        if not fits(wire):
            raise ContextBlocked("mandatory_context_exceeds_budget")
        for item in plan.items:
            reason = "provider_cache_not_authority" if item.memory_class == MemoryClass.PROVIDER_CACHE else None
            for source_index, source in enumerate(item.sources):
                if self.redactor.tree(asdict(source)) != asdict(source):
                    reason = reason or "secret_source_reference"
                source_reason = _source_policy(source, plan.project, plan.context,
                                                series=plan.experiment_series, role=plan.role)
                if (item.derived_summary and not item.mandatory and source_index == 0
                        and source_reason == SourceState.UNVERIFIED.value):
                    source_reason = None
                reason = reason or source_reason
                if source.data_class not in provider_classes:
                    reason = reason or "provider_data_class"
            if reason:
                if item.mandatory:
                    raise ContextBlocked("required_source_" + reason)
                rejected.append({"id": self.redactor.redact(item.id), "code": reason})
                continue
            # Source size is integrity metadata. The bounded source may shrink
            # under redaction; only the rendered candidate determines fit.
            try:
                source_bytes = loader(item)
            except Exception as exc:
                if item.mandatory:
                    raise ContextBlocked("required_source_unavailable") from exc
                rejected.append({"id": self.redactor.redact(item.id), "code": "source_unavailable"})
                continue
            if (not isinstance(source_bytes, bytes) or len(source_bytes) != item.size
                    or hashlib.sha256(source_bytes).hexdigest() != item.sources[0].sha256):
                if item.mandatory:
                    raise ContextBlocked("required_source_digest_mismatch")
                rejected.append({"id": self.redactor.redact(item.id), "code": "source_digest_mismatch"})
                continue
            try:
                text = self.redactor.redact(source_bytes.decode("utf-8"))
            except (UnicodeError, ContextError) as exc:
                if item.mandatory:
                    raise ContextBlocked("required_source_encoding") from exc
                rejected.append({"id": self.redactor.redact(item.id), "code": "source_encoding"})
                continue
            content.append({"id": self.redactor.redact(item.id), "authority": "context_data", "text": text,
                            "memory_class": item.memory_class, "derived_summary": item.derived_summary, "sources": [asdict(x) for x in item.sources]})
            candidate = render()
            if not fits(candidate):
                content.pop()
                if item.mandatory:
                    raise ContextBlocked("mandatory_context_exceeds_budget")
                rejected.append({"id": self.redactor.redact(item.id), "code": "context_budget"})
                continue
            wire = candidate
            selected.append({"id": self.redactor.redact(item.id), "reason": self.redactor.redact(item.reason), "sources": [asdict(x) for x in item.sources],
                              "redacted": text.encode() != source_bytes, "derived_summary": item.derived_summary,
                             "authority": "context_data"})
        trace = canonical({"plan_hash": plan.hash, "binding": raw["binding"], "executor_id": executor.id,
                           "provider_id": provider.id, "tokenizer_version": counter.tokenizer_version,
                           "tokenizer_input_tokens": counter.measure(measured(wire)),
                            **({"measurement":"host_envelope","measurement_bytes":len(measured(wire))} if envelope is not None else {}), "provider_usage": "unmeasured", "input_bytes": len(wire),
                           "stable_prefix_hash": digest(raw["stable_prefix"]),
                           "cache_evidence": "unmeasured", "selection_hash": raw["selection_hash"],
                           "selection_reason": raw["selection_reason"], "previous_selection_hash": raw["previous_selection_hash"],
                           "selected": selected, "rejected": rejected, "control_source_digest": raw["control_source_digest"]})
        return ContextBundle(plan.hash, executor.id, wire, trace)


@dataclass(frozen=True)
class Compaction:
    summary: str
    sources: tuple[SourceRef, ...]
    original_item_hashes: tuple[tuple[str, str], ...]

    def __post_init__(self):
        bounded_text(self.summary, 16_384)
        require(isinstance(self.sources, (tuple, list)) and 0 < len(self.sources) <= 16
                and all(isinstance(x, SourceRef) for x in self.sources), "compaction_provenance")
        object.__setattr__(self, "sources", tuple(self.sources))
        require(isinstance(self.original_item_hashes, (tuple, list))
                and 0 < len(self.original_item_hashes) <= 16, "compaction_provenance")
        object.__setattr__(self, "original_item_hashes", tuple(self.original_item_hashes))
        for item_id, sha in self.original_item_hashes:
            token(item_id)
            hash_value(sha)

    def item(self, originals, redactor):
        originals = {x.id: x for x in originals}
        source_set = {digest(asdict(x)) for x in self.sources}
        for item_id, sha in self.original_item_hashes:
            original = originals.get(item_id)
            require(original is not None and not original.mandatory and original.sources[0].sha256 == sha
                    and all(digest(asdict(x)) in source_set for x in original.sources), "unsafe_compaction")
        raw = redactor.redact(self.summary).encode()
        origin = self.sources[0]
        # Summary bytes are derived data; original evidence refs remain attached.
        summary_ref = replace(origin, uri="herdr://derived/" + hashlib.sha256(raw).hexdigest(),
                              sha256=hashlib.sha256(raw).hexdigest(), state=SourceState.UNVERIFIED)
        item = ContextItem("compaction-" + hashlib.sha256(raw).hexdigest(), MemoryClass.EPISODIC,
                           (summary_ref, *self.sources), len(raw), "explicit_evidence_preserving_compaction",
                           derived_summary=True)
        return item, raw


@dataclass(frozen=True)
class BoundedOutput:
    source: SourceRef
    exit_code: int
    elapsed_ms: int
    excerpt: str
    error_excerpt: str
    total_bytes: int
    truncated: bool


def capture_output(source: SourceRef, stdout: bytes, stderr: bytes, *, exit_code, elapsed_ms,
                   max_bytes=1_048_576, max_ms=30_000, max_excerpt=8192, redactor: SecretRedactor,
                   persist: Callable[[bytes], SourceRef]):
    """Bound and redact before persistence; errors retain a dedicated excerpt."""
    require(isinstance(source, SourceRef) and isinstance(stdout, bytes) and isinstance(stderr, bytes),
            "output_source")
    require(type(exit_code) is int and -(2**31) <= exit_code < 2**31
            and type(elapsed_ms) is int and elapsed_ms >= 0, "output_status")
    require(type(max_bytes) is int and 0 < max_bytes <= 1_048_576
            and type(max_ms) is int and 0 < max_ms <= 300_000
            and type(max_excerpt) is int and 256 <= max_excerpt <= 32_768, "output_limits")
    require(isinstance(redactor, SecretRedactor), "host_redactor")
    require(canonical(redactor.tree(asdict(source))) == canonical(asdict(source)), "secret_source_reference")
    if elapsed_ms > max_ms or len(stdout) + len(stderr) > max_bytes:
        raise ContextBlocked("tool_output_limit")
    out = redactor.redact(stdout.decode("utf-8", errors="replace"), maximum=3 * max_bytes)
    err = redactor.redact(stderr.decode("utf-8", errors="replace"), maximum=3 * max_bytes)
    # Redaction expansion can increase bytes; artifact limit still applies.
    artifact = canonical({"source": asdict(source), "exit_code": exit_code,
                          "elapsed_ms": elapsed_ms, "stdout": out, "stderr": err})
    if len(artifact) > max_bytes:
        raise ContextBlocked("tool_output_limit")
    ref = persist(artifact)
    require(isinstance(ref, SourceRef) and ref.sha256 == hashlib.sha256(artifact).hexdigest()
            and ref.project == source.project and ref.data_class == source.data_class
            and ref.holdout_series == source.holdout_series
            and canonical(redactor.tree(asdict(ref))) == canonical(asdict(ref))
            and ref.state == SourceState.VERIFIED, "output_artifact_binding")
    def excerpt(value):
        raw = value.encode()
        return raw[:max_excerpt].decode("utf-8", errors="ignore"), len(raw) > max_excerpt
    out_excerpt, out_cut = excerpt(out)
    # Include the error tail as well as its beginning; never silently omit errors.
    if len(err.encode()) > max_excerpt:
        marker = "\n[bounded error excerpt]\n"
        half = (max_excerpt - len(marker.encode())) // 2
        head = err.encode()[:half].decode("utf-8", errors="ignore")
        tail = err.encode()[-half:].decode("utf-8", errors="ignore")
        err_excerpt, err_cut = head + marker + tail, True
    else:
        err_excerpt, err_cut = err, False
    if exit_code != 0 and not err_excerpt:
        err_excerpt = f"Process exited with code {exit_code}; inspect the preserved artifact."
    return BoundedOutput(ref, exit_code, elapsed_ms, out_excerpt, err_excerpt,
                         len(stdout) + len(stderr), out_cut or err_cut)
