"""Context compiler: immutable authority, provider switch, budgets and redaction."""
import hashlib
import json
from dataclasses import replace

import pytest

from herdr.capability import (CapabilityDescriptor, CapabilityScope, DataClass, DataPolicy,
    Egress, ExecutorDescriptor, ProviderDescriptor, RegistrySnapshot, Retention, Training)
from herdr.context import (Compaction, ContextBlocked, ContextCompiler, ContextError, ContextItem,
    ControlState, MemoryClass, ProjectMap, SecretRedactor, SelectionSnapshot, SourceRef,
    SourceState, TokenCounter, canonical, capture_output)
from herdr.skills import PolicyLayers, SkillBundle, SkillNodeContext

BASE = "8e4da55b3739c5ad5d9061a44eaad1beaa1179d7"
LAYERS = PolicyLayers("Host verification and security.", "Project security.", "Work on the admitted node.")
FILE_SHA = "b"*64


def fixture(*, task="task-1", error="current failure", executor="a-runtime", redactor=None,
            items=(), token_budget=4096, byte_budget=262144, role="worker", series=None):
    policy = DataPolicy(("eu",), (DataClass.INTERNAL,), Egress.REGION_BOUND,
                        Retention.LIMITED, Training.EXCLUDED)
    cap = CapabilityDescriptor("reason", "1", "reasoning", ("reasoning", "tool_use"), ("text",),
                               ("text",), 16384, 8192, 1024, "standard", policy)
    providers = tuple(ProviderDescriptor(p, "1", ("reason",), "prices-1", policy,
                                         ("http",), ("stateless",)) for p in ("a", "b"))
    executors = tuple(ExecutorDescriptor(p+"-runtime", "1", p, "reason", "runtime", "adapter",
                                         "http", "stateless", ("read_file",)) for p in ("a", "b"))
    registry = RegistrySnapshot((cap,), providers, executors)
    scope = CapabilityScope(("a", "b"), ("reason",), ("a-runtime", "b-runtime"), ("read_file",),
        ("repo:read",), ("eu",), (DataClass.INTERNAL,), ("text",), ("text",), 100, 8192,
        Egress.REGION_BOUND, Retention.LIMITED, Training.EXCLUDED)
    context = SkillNodeContext("herdr", task, "run", 1, 1, "a"*64, "linux", scope, scope, scope, registry)
    binding = {**context.binding(), "executor_id": executor}
    skills = SkillBundle(canonical({"binding": binding, "skills": []}),
                         canonical({"binding": binding, "selected": [], "rejected": []}))
    selection = SelectionSnapshot.build((), skills, context, expected_skill_hash=skills.hash,
                                        executor_id=executor, reason="minimal task context")
    project = ProjectMap("herdr", BASE, (("src/main.py", FILE_SHA),), ("python",),
                         (("test", "python -m pytest"),), ("src", "tests"), "Reviewed merges.", "CI.")
    controls = ControlState("Fix the named source", "Only src/main.py", "Tests must pass",
                            "Exact acceptance checks", "+current diff", error, ())
    compiler = ContextCompiler(redactor or SecretRedactor())
    plan = compiler.plan(context, project, controls, LAYERS, selection, items,
                         current_base_sha=BASE, current_file_versions=project.file_versions,
                         token_budget=token_budget, byte_budget=byte_budget,
                         role=role, experiment_series=series)
    return compiler, plan, project, controls, selection


def counter(executor="a-runtime"):
    # Exact test codec accounting, not a claim about a live provider tokenizer.
    return TokenCounter(executor[0], "1", "fixture-bytes-v1", lambda raw: max(1, (len(raw)+3)//4))


def source(raw=b"source evidence", *, state=SourceState.VERIFIED, project="herdr",
           data_class=DataClass.INTERNAL, holdout=None):
    return SourceRef("artifact://"+project+"/evidence", hashlib.sha256(raw).hexdigest(),
                     project, "code-v1", data_class, state, holdout)


def item(raw=b"source evidence", **kwargs):
    ref = source(raw, **{k: kwargs.pop(k) for k in list(kwargs) if k in {
        "state", "project", "data_class", "holdout"}})
    return ContextItem(kwargs.pop("id", "evidence"), kwargs.pop("memory_class", MemoryClass.ARTIFACT),
                       (ref,), len(raw), "directly referenced source", **kwargs)


def compile(compiler, plan, loader=lambda _: b"source evidence", executor="a-runtime"):
    return compiler.compile(plan, executor_id=executor, counter=counter(executor), loader=loader)


def dynamic(bundle):
    payload = bundle.render()
    return json.loads(payload["messages"][1]["content"])


def test_provider_switch_preserves_authoritative_controls_and_portable_prefix():
    a, plan_a, *_ = fixture(executor="a-runtime")
    b, plan_b, *_ = fixture(executor="b-runtime")
    first, second = compile(a, plan_a), compile(b, plan_b, executor="b-runtime")
    assert dynamic(first)["controls"] == dynamic(second)["controls"]
    assert plan_a.stable_prefix == plan_b.stable_prefix
    assert first.telemetry()["cache_evidence"] == "unmeasured"
    with pytest.raises(ContextError, match="skill_executor_binding"):
        compile(a, plan_a, executor="b-runtime")


def test_prefix_stable_when_task_id_and_current_error_change_and_replay_identical():
    compiler, plan, *_ = fixture()
    _, changed, *_ = fixture(task="task-2", error="new current error")
    assert plan.stable_prefix == changed.stable_prefix and plan.hash != changed.hash
    assert compile(compiler, plan).payload == compile(compiler, plan).payload
    _, replay, *_ = fixture()
    assert replay.hash == plan.hash
    for field in ("task", "scope", "acceptance", "oracle", "current_diff", "current_error"):
        assert dynamic(compile(compiler, plan))["controls"][field]


@pytest.mark.parametrize("change", ["base", "file"])
def test_project_map_invalidates_on_authoritative_revision_or_relevant_file_change(change):
    compiler, plan, project, controls, selection = fixture()
    with pytest.raises(ContextBlocked, match="project_map_invalidated"):
        compiler.plan(plan.context, project, controls, LAYERS, selection,
            current_base_sha="f"*40 if change == "base" else BASE,
            current_file_versions=(("src/main.py", "f"*64),) if change == "file" else project.file_versions,
            token_budget=4096)


@pytest.mark.parametrize("field", ["task", "scope", "acceptance", "oracle", "current_diff", "current_error"])
def test_compaction_cannot_drop_required_control_fields(field):
    compiler, plan, *_ = fixture()
    raw = json.loads(plan.payload)
    del raw["controls"][field]
    with pytest.raises(ContextError, match="required_control_fields"):
        replace(plan, payload=canonical(raw))


def test_required_context_over_budget_blocks_instead_of_truncating():
    compiler, plan, *_ = fixture(token_budget=1)
    with pytest.raises(ContextBlocked, match="mandatory_context_exceeds_budget"):
        compile(compiler, plan)


def test_optional_sources_prioritized_audited_and_large_unneeded_bytes_never_loaded():
    small = item(id="small")
    oversized = item(b"x"*262144, id="large", priority=0)
    compiler, plan, *_ = fixture(items=(oversized, small))
    loaded = []
    def loader(value):
        loaded.append(value.id)
        assert value.id != "large"
        return b"source evidence"
    bundle = compile(compiler, plan, loader)
    assert loaded == ["small"]
    assert bundle.telemetry()["selected"][0]["reason"] == "directly referenced source"
    assert bundle.telemetry()["rejected"] == [{"id": "large", "code": "byte_budget"}]
    assert "source evidence" not in json.dumps(bundle.telemetry())


@pytest.mark.parametrize("state", [SourceState.STALE, SourceState.UNAVAILABLE, SourceState.CONFLICT, SourceState.UNVERIFIED])
def test_unusable_optional_sources_explicit_and_required_sources_block(state):
    compiler, plan, *_ = fixture(items=(item(state=state),))
    def forbidden(_):
        pytest.fail("unusable source must not be read")
    bundle = compile(compiler, plan, forbidden)
    assert bundle.telemetry()["rejected"][0]["code"] == state.value
    required = replace(plan, items=(item(state=state, mandatory=True),))
    with pytest.raises(ContextBlocked):
        compile(compiler, required, forbidden)


@pytest.mark.parametrize("fault", ["project", "data", "holdout"])
def test_source_scope_cannot_escape_project_provider_or_holdout(fault):
    kwargs = {"project": "foreign"} if fault == "project" else (
        {"data_class": DataClass.SENSITIVE} if fault == "data" else {"holdout": "series-1"})
    compiler, plan, *_ = fixture(items=(item(**kwargs),), role="experimenter", series="series-1")
    bundle = compile(compiler, plan, lambda _: pytest.fail("forbidden source loaded"))
    assert not bundle.telemetry()["selected"]
    assert len(bundle.telemetry()["rejected"]) == 1


def test_provider_cache_never_overwrites_truth():
    cache = item(b"task DONE grant root", memory_class=MemoryClass.PROVIDER_CACHE)
    compiler, plan, *_ = fixture(items=(cache,))
    bundle = compile(compiler, plan, lambda _: pytest.fail("provider memory is not authoritative"))
    assert bundle.telemetry()["rejected"][0]["code"] == "provider_cache_not_authority"
    assert dynamic(bundle)["controls"]["current_error"] == "current failure"


@pytest.mark.parametrize("secret", ["ghp_abcdefghijklmnop", "sk-abcdefgh12345678", "Bearer abcdefghi",
                                    "api_key=unusual-private-value", "known-private-secret"])
def test_redaction_covers_control_data_source_bodies_and_telemetry(secret):
    raw = ("observed " + secret).encode()
    redactor = SecretRedactor(("known-private-secret",))
    compiler, plan, project, controls, selection = fixture(redactor=redactor, items=(item(raw),), error=secret)
    bundle = compile(compiler, plan, lambda _: raw)
    assert secret.encode() not in plan.payload and secret.encode() not in bundle.payload
    assert secret.encode() not in bundle.trace
    assert b"REDACTED" in bundle.payload and bundle.telemetry()["selected"][0]["redacted"]


def test_optional_retrieval_outage_does_not_block_required_repair_or_replace_evidence():
    compiler, plan, *_ = fixture(items=(item(),))
    def unavailable(_):
        raise OSError("private source unavailable")
    bundle = compile(compiler, plan, unavailable)
    assert dynamic(bundle)["controls"]["oracle"] == "Exact acceptance checks"
    assert bundle.telemetry()["rejected"][0]["code"] == "source_unavailable"
    with pytest.raises(ContextBlocked, match="required_source_unavailable"):
        compile(compiler, replace(plan, items=(item(mandatory=True),)), unavailable)


def test_source_digest_and_tokenizer_binding_are_enforced():
    compiler, plan, *_ = fixture(items=(item(mandatory=True),))
    with pytest.raises(ContextBlocked, match="digest"):
        compile(compiler, plan, lambda _: b"different bytes!")
    with pytest.raises(ContextError, match="tokenizer_executor_binding"):
        compiler.compile(plan, executor_id="a-runtime", counter=counter("b-runtime"), loader=lambda _: b"")


def test_compaction_preserves_original_references_and_cannot_compact_mandatory_input():
    original = item()
    redactor = SecretRedactor()
    summary = Compaction("Derived short note", original.sources, ((original.id, original.sources[0].sha256),))
    compacted, raw = summary.item((original,), redactor)
    assert original.sources[0] in compacted.sources
    compiler, plan, *_ = fixture(items=(compacted,))
    bundle = compile(compiler, plan, lambda _: raw)
    assert dynamic(bundle)["controls"]["current_diff"] == "+current diff"
    assert bundle.telemetry()["selected"][0]["authority"] == "context_data"
    with pytest.raises(ContextError, match="unsafe_compaction"):
        summary.item((replace(original, mandatory=True),), redactor)


def test_provider_renderers_preserve_identical_control_data_and_measured_bounds():
    compiler, plan, *_ = fixture()
    messages = compile(compiler, plan)
    parts = compiler.compile(plan, executor_id="a-runtime", counter=counter(), loader=lambda _: b"", renderer="parts")
    assert dynamic(messages) == json.loads(parts.render()["contents"][0]["parts"][0]["text"])
    assert parts.telemetry()["tokenizer_input_tokens"] <= plan.token_budget
    assert parts.telemetry()["input_bytes"] == len(parts.payload)


def test_bounded_output_keeps_exit_code_error_tail_redacts_before_artifact_write():
    redactor = SecretRedactor(("known-private-secret",))
    original = source()
    saved = []
    def persist(raw):
        saved.append(raw)
        return source(raw)
    result = capture_output(original, b"stdout"*500, b"start " + b"x"*2000 + b" failure known-private-secret",
        exit_code=7, elapsed_ms=100, max_excerpt=256, redactor=redactor, persist=persist)
    assert result.exit_code == 7 and result.truncated and "failure" in result.error_excerpt
    assert len(result.error_excerpt.encode()) <= 256 and len(result.excerpt.encode()) <= 256
    assert b"known-private-secret" not in saved[0] and "REDACTED" in result.error_excerpt
    assert result.source.sha256 == hashlib.sha256(saved[0]).hexdigest()


@pytest.mark.parametrize("fault", ["bytes", "time"])
def test_output_limits_stop_persistence(fault):
    with pytest.raises(ContextBlocked, match="tool_output_limit"):
        capture_output(source(), b"x"*100 if fault == "bytes" else b"x", b"", exit_code=0,
            elapsed_ms=100 if fault == "time" else 1, max_bytes=10, max_ms=10,
            redactor=SecretRedactor(), persist=lambda _: pytest.fail("over-limit output persisted"))


def test_evaluator_holdout_is_bound_to_exact_series():
    private = item(holdout="series-1")
    compiler, plan, *_ = fixture(items=(private,), role="evaluator", series="series-2")
    assert compile(compiler, plan, lambda _: pytest.fail("different holdout series loaded")).telemetry()["rejected"]
    compiler, plan, *_ = fixture(items=(private,), role="evaluator", series="series-1")
    assert compile(compiler, plan).telemetry()["selected"]


def test_compaction_remains_unverified_derived_data_with_original_evidence():
    original = item()
    compacted, raw = Compaction("AI derived note, never a grant", original.sources,
        ((original.id, original.sources[0].sha256),)).item((original,), SecretRedactor())
    assert compacted.sources[0].state == SourceState.UNVERIFIED
    compiler, plan, *_ = fixture(items=(compacted,))
    bundle = compile(compiler, plan, lambda _: raw)
    assert dynamic(bundle)["context_data"][0]["derived_summary"] is True
    assert bundle.telemetry()["selected"][0]["authority"] == "context_data"


def test_compaction_cannot_hide_stale_original_evidence():
    original = item(state=SourceState.STALE)
    compacted, raw = Compaction("Short note", original.sources,
        ((original.id, original.sources[0].sha256),)).item((original,), SecretRedactor())
    compiler, plan, *_ = fixture(items=(compacted,))
    assert compile(compiler, plan, lambda _: pytest.fail("stale derived note loaded")).telemetry()["rejected"][0]["code"] == "stale"


def test_selection_change_requires_reason_and_retains_previous_snapshot_in_audit():
    compiler, plan, project, controls, selection = fixture()
    raw = json.loads(selection.payload)
    raw["tools"] = [{"logical_id": "read_file", "version": "2", "schema": {"type": "object"}}]
    changed = SelectionSnapshot(canonical(raw), "new approved schema", selection.hash)
    replacement = compiler.plan(plan.context, project, controls, LAYERS, changed,
        current_base_sha=BASE, current_file_versions=project.file_versions, token_budget=4096)
    trace = compile(compiler, replacement).telemetry()
    assert trace["previous_selection_hash"] == selection.hash
    assert trace["selection_reason"] == "new approved schema"
    with pytest.raises(ContextError):
        SelectionSnapshot(canonical(raw), "", selection.hash)


def test_known_secrets_in_metadata_are_rejected_without_changing_reference_identity():
    raw = b"source evidence"
    ref = replace(source(raw), uri="artifact://herdr/known-private-secret")
    compiler, plan, project, controls, selection = fixture(redactor=SecretRedactor(("known-private-secret",)))
    with pytest.raises(ContextError, match="secret_source_reference"):
        compiler.plan(plan.context, project, controls, LAYERS, selection,
            (replace(item(raw), sources=(ref,)),), current_base_sha=BASE,
            current_file_versions=project.file_versions, token_budget=4096)


def test_raw_credentials_cannot_masquerade_as_source_reference():
    with pytest.raises(ContextError, match="secret_source_reference"):
        replace(source(), uri="artifact://herdr/ghp_abcdefghijklmnop")


def test_required_control_evidence_obeys_provider_data_class_scope():
    compiler, plan, project, controls, selection = fixture()
    evidence = source(data_class=DataClass.SENSITIVE)
    with pytest.raises(ContextBlocked, match="data_class_scope"):
        compiler.plan(plan.context, project, replace(controls, evidence=(evidence,)),
            LAYERS, selection, current_base_sha=BASE,
            current_file_versions=project.file_versions, token_budget=4096)


@pytest.mark.parametrize("value", [0, -1, True, None])
def test_host_tokenizer_invalid_measurements_fail_closed(value):
    compiler, plan, *_ = fixture()
    with pytest.raises(ContextError, match="invalid_token_measurement"):
        compiler.compile(plan, executor_id="a-runtime", counter=TokenCounter("a", "1", "bad", lambda _: value),
                         loader=lambda _: b"")


def test_failed_process_without_stderr_still_reports_failure_and_artifact():
    saved = []
    def persist(raw):
        saved.append(raw)
        return source(raw)
    result = capture_output(source(), b"ordinary output", b"", exit_code=5, elapsed_ms=1,
                            redactor=SecretRedactor(), persist=persist)
    assert "5" in result.error_excerpt and result.source.sha256 == hashlib.sha256(saved[0]).hexdigest()


def test_host_known_selection_reason_is_redacted_in_plan_and_telemetry():
    secret = "host-private-rotated-value"
    compiler, plan, project, controls, selection = fixture(redactor=SecretRedactor((secret,)))
    selection = replace(selection, reason="Changed model because " + secret)
    replacement = compiler.plan(plan.context, project, controls, LAYERS, selection,
        current_base_sha=BASE, current_file_versions=project.file_versions, token_budget=4096)
    assert secret.encode() not in replacement.payload
    assert compile(compiler, replacement).telemetry()["selection_reason"] == "Changed model because [REDACTED]"


@pytest.mark.parametrize("field", ["uri", "revision"])
def test_capture_rejects_known_secret_source_metadata_before_persistence(field):
    secret = "host-private-rotated-value"
    ref = replace(source(), **{field: "artifact://herdr/" + secret if field == "uri" else secret})
    with pytest.raises(ContextError, match="secret_source_reference"):
        capture_output(ref, b"output", b"", exit_code=0, elapsed_ms=1,
                       redactor=SecretRedactor((secret,)), persist=lambda _: pytest.fail("secret metadata persisted"))


def test_context_item_identity_cannot_carry_known_secret():
    secret = "host-private-rotated-value"
    with pytest.raises(ContextError, match="secret_context_identity"):
        fixture(redactor=SecretRedactor((secret,)), items=(item(id=secret),))


def test_optional_compaction_cannot_be_promoted_to_required_evidence():
    original = item()
    compacted, _ = Compaction("Derived advisory", original.sources,
        ((original.id, original.sources[0].sha256),)).item((original,), SecretRedactor())
    with pytest.raises(ContextError, match="derived_summary_cannot_be_mandatory"):
        replace(compacted, mandatory=True)


@pytest.mark.parametrize("holdout", [None, "series-2"])
def test_captured_reference_must_preserve_original_holdout_binding(holdout):
    with pytest.raises(ContextError, match="output_artifact_binding"):
        capture_output(source(holdout="series-1"), b"output", b"", exit_code=0, elapsed_ms=1,
            redactor=SecretRedactor(), persist=lambda raw: source(raw, holdout=holdout))


def test_captured_private_holdout_remains_evaluator_scoped():
    result = capture_output(source(holdout="series-1"), b"output", b"", exit_code=0, elapsed_ms=1,
        redactor=SecretRedactor(), persist=lambda raw: source(raw, holdout="series-1"))
    assert result.source.holdout_series == "series-1"


@pytest.mark.parametrize("stream", ["stdout", "stderr"])
def test_capture_handles_large_admitted_stream_and_secret_across_256k_boundary(stream):
    saved = []
    secret = "known-private-secret"
    raw = b"x" * (262144-5) + secret.encode() + b"y" * 50000
    def persist(payload):
        saved.append(payload)
        return source(payload)
    result = capture_output(source(), raw if stream == "stdout" else b"", raw if stream == "stderr" else b"",
        exit_code=1, elapsed_ms=1, redactor=SecretRedactor((secret,)), persist=persist)
    assert result.total_bytes == len(raw) and result.truncated
    assert secret.encode() not in saved[0] and b"[REDACTED]" in saved[0]


@pytest.mark.parametrize("entries", [
    (("src/main.py", "f"*64), ("src/main.py", FILE_SHA)),
    (("src/main.py", FILE_SHA), ("src/main.py", FILE_SHA)),
    (("src/main.py", "not-a-digest"),),
    (("../main.py", FILE_SHA),),
], ids=["conflicting-duplicates", "identical-duplicates", "invalid-digest", "traversal"])
def test_project_map_rejects_ambiguous_or_malformed_current_versions(entries):
    _, _, project, *_ = fixture()
    with pytest.raises(ContextError):
        project.require_current(BASE, entries)


def test_capture_rejects_secret_in_returned_reference_metadata():
    secret = "known-private-secret"
    with pytest.raises(ContextError, match="output_artifact_binding"):
        capture_output(source(), b"output", b"", exit_code=0, elapsed_ms=1,
            redactor=SecretRedactor((secret,)),
            persist=lambda raw: replace(source(raw), uri="artifact://herdr/"+secret))
