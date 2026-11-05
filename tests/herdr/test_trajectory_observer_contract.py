import itertools
import json

import pytest

from herdr.trajectory_observer import (
    MAX_CONTROL_CASES, MAX_CONTROL_EVENTS, MAX_EVENTS,
    SyntheticTrajectoryCase, TrajectoryInputError, TrajectorySignal,
    inspect_trajectory, replay_synthetic_controls,
)


def guarded_repeat(value, limit):
    seen = []
    def stream():
        for n in itertools.count():
            seen.append(n)
            assert n <= limit, "observer read beyond limit plus one"
            yield value
    return stream(), seen


@pytest.mark.parametrize("field", ["repeat_threshold", "max_steps"])
@pytest.mark.parametrize("bad", [True, False, 1.5, "4", None, -1, 0, MAX_EVENTS + 1])
def test_thresholds_are_strict_finite_integers(field, bad):
    with pytest.raises(TrajectoryInputError, match="^invalid_observer_thresholds$"):
        inspect_trajectory([], **{field: bad})


def test_limit_is_exact_and_overflow_reads_only_one_extra_item():
    assert inspect_trajectory(["read"] * MAX_EVENTS)[0].count == MAX_EVENTS
    seen = []
    def guarded():
        for n in range(MAX_EVENTS + 2):
            seen.append(n)
            assert n <= MAX_EVENTS
            yield "read"
    with pytest.raises(TrajectoryInputError, match="^trajectory_event_limit$"):
        inspect_trajectory(guarded())
    assert len(seen) == MAX_EVENTS + 1
    stream, seen = guarded_repeat("read", MAX_EVENTS)
    with pytest.raises(TrajectoryInputError):
        inspect_trajectory(stream)
    assert len(seen) == MAX_EVENTS + 1


@pytest.mark.parametrize("bad", ["", "../secret", "/home/key", "read\n", "read\x1b",
                               "a" * 129, "čti", "Bearer secret", 1, None,
                               "sk-" + "a" * 40, "ghp_" + "a" * 40])
def test_unsafe_ids_fail_without_echoing_input(bad):
    with pytest.raises(TrajectoryInputError) as error:
        inspect_trajectory([bad])
    assert str(error.value) in {"invalid_trajectory_identifier", "secret_trajectory_identifier"}
    assert len(str(error.value)) < 64


@pytest.mark.parametrize("bad", ["read", b"read", {}, {"read"}, frozenset({"read"}), None, 3])
def test_scalar_or_mapping_event_input_is_not_an_event_stream(bad):
    with pytest.raises(TrajectoryInputError):
        inspect_trajectory(bad)


def test_iterator_error_is_bounded_and_does_not_leak_payload():
    def bad():
        yield "read"
        raise RuntimeError("private prompt payload")
    with pytest.raises(TrajectoryInputError, match="^trajectory_event_limit$") as error:
        inspect_trajectory(bad())
    assert error.value.__cause__ is None


@pytest.mark.parametrize("args", [("stop", 1), ("consecutive_tool_repeat", True),
                                 ("step_budget_observed", MAX_EVENTS + 1),
                                 ("step_budget_observed", 0)])
def test_direct_signal_cannot_forge_an_action_or_unbounded_count(args):
    with pytest.raises(TrajectoryInputError):
        TrajectorySignal(*args)
    with pytest.raises(TrajectoryInputError):
        TrajectorySignal("step_budget_observed", 1, "terminate")


def test_export_revalidates_signal_and_contains_only_aggregate_fields():
    signal = TrajectorySignal("consecutive_tool_repeat", 4)
    assert signal.to_json() == {"kind": "consecutive_tool_repeat", "count": 4, "severity": "observe"}
    object.__setattr__(signal, "severity", "stop")
    with pytest.raises(TrajectoryInputError):
        signal.to_json()


def controls():
    return (SyntheticTrajectoryCase("normal", ("read", "search"), ()),
            SyntheticTrajectoryCase("repeat", ("read",) * 4, ("consecutive_tool_repeat",)),
            SyntheticTrajectoryCase("steps", ("read", "search", "write"), ("step_budget_observed",)))


def test_replay_is_deterministic_binds_inputs_and_never_reports_production_scores():
    cases = controls()
    a = replay_synthetic_controls(cases, max_steps=2)
    b = replay_synthetic_controls(iter(cases), max_steps=2)
    assert json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)
    # The repeat case also exceeds the configured step threshold: labels must
    # match actual controls instead of automatically counting every case PASS.
    assert a["synthetic_controls"]["matched_cases"] == 2
    assert a["scope"] == "synthetic_controls_only"
    assert a["historical_metrics"]["sample_count"] == 0
    for metric in a["historical_metrics"]["metrics"].values():
        assert metric["status"] == "UNKNOWN" and metric["value"] is None
        assert metric["denominator"] == 0 and metric["reason"]
    assert "tool_names" not in json.dumps(a)
    assert a["input_sha256"] != replay_synthetic_controls(cases, max_steps=3)["input_sha256"]
    a["historical_metrics"]["metrics"]["precision"]["value"] = 1
    assert replay_synthetic_controls(cases, max_steps=2) == b


def test_empty_replay_does_not_fabricate_zero_quality_or_overhead():
    report = replay_synthetic_controls([])
    assert report["synthetic_controls"]["case_count"] == 0
    assert all(m["value"] is None for m in report["historical_metrics"]["metrics"].values())


def test_valid_controls_all_match_without_promoting_historical_metrics():
    cases = (SyntheticTrajectoryCase("normal", ("read", "search"), ()),
             SyntheticTrajectoryCase("repeat", ("read",) * 4, ("consecutive_tool_repeat",)),
             SyntheticTrajectoryCase("steps", ("read", "write", "search", "read", "write"),
                                     ("step_budget_observed",)))
    report = replay_synthetic_controls(cases, max_steps=4)
    assert report["synthetic_controls"]["matched_cases"] == 3
    assert all(m["status"] == "UNKNOWN" and m["value"] is None
               for m in report["historical_metrics"]["metrics"].values())


def test_repeat_count_is_longest_consecutive_run_not_total_occurrences():
    signals = inspect_trajectory(["read", "read", "write", "read", "read", "read", "search"],
                                 repeat_threshold=3, max_steps=6)
    assert [(s.kind, s.count) for s in signals] == [
        ("step_budget_observed", 7), ("consecutive_tool_repeat", 3)]


def test_replay_bounds_labels_identity_and_total_events():
    with pytest.raises(TrajectoryInputError):
        SyntheticTrajectoryCase("safe", (), ("stop",))
    with pytest.raises(TrajectoryInputError):
        SyntheticTrajectoryCase("safe", (), ("consecutive_tool_repeat",) * 2)
    one = SyntheticTrajectoryCase("one", (), ())
    with pytest.raises(TrajectoryInputError, match="^duplicate_trajectory_control$"):
        replay_synthetic_controls([one, one])
    stream, seen = guarded_repeat(one, MAX_CONTROL_CASES)
    with pytest.raises(TrajectoryInputError, match="^trajectory_control_limit$"):
        replay_synthetic_controls(stream)
    assert len(seen) == MAX_CONTROL_CASES + 1
    with pytest.raises(TrajectoryInputError):
        replay_synthetic_controls([{}])
    many = [SyntheticTrajectoryCase("case" + str(n), ("read",) * MAX_EVENTS, ())
            for n in range(MAX_CONTROL_EVENTS // MAX_EVENTS)]
    assert replay_synthetic_controls(many)["synthetic_controls"]["case_count"] == 4
    many.append(SyntheticTrajectoryCase("extra", ("read",), ()))
    with pytest.raises(TrajectoryInputError, match="^trajectory_control_event_limit$"):
        replay_synthetic_controls(many)
    assert len(replay_synthetic_controls(
        SyntheticTrajectoryCase("case" + str(n), (), ()) for n in range(MAX_CONTROL_CASES)
    )["synthetic_controls"]["cases"]) == MAX_CONTROL_CASES


def test_replay_revalidates_direct_case_mutation():
    case = SyntheticTrajectoryCase("case", (), ())
    object.__setattr__(case, "tool_names", ("/private/path",))
    with pytest.raises(TrajectoryInputError):
        replay_synthetic_controls([case])
