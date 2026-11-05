"""Regression oracles use only the original PR130 public API."""
import pytest

from herdr.trajectory_observer import TrajectorySignal, inspect_trajectory


@pytest.mark.parametrize("kwargs", [{"max_steps": True}, {"max_steps": 1.5},
                                    {"repeat_threshold": 2.5},
                                    {"repeat_threshold": 4097}, {"max_steps": 4097}])
def test_legacy_threshold_loopholes_reject(kwargs):
    with pytest.raises(ValueError):
        inspect_trajectory([], **kwargs)


@pytest.mark.parametrize("name", ["../private", "read\n", "x" * 129,
                                  "sk-" + "a" * 40, "ghp_" + "a" * 40])
def test_legacy_unsafe_identifiers_reject(name):
    with pytest.raises(ValueError):
        inspect_trajectory([name])


def test_legacy_stream_cannot_consume_more_than_limit_plus_one():
    seen = []
    def guarded():
        for n in range(4098):
            seen.append(n)
            assert n <= 4096, "observer consumed beyond the fixed contract"
            yield "read"
    with pytest.raises(ValueError):
        inspect_trajectory(guarded())
    assert len(seen) == 4097


@pytest.mark.parametrize("args", [("stop", 1), ("consecutive_tool_repeat", True),
                                 ("step_budget_observed", 4097)])
def test_legacy_direct_signal_cannot_forge_values(args):
    with pytest.raises(ValueError):
        TrajectorySignal(*args)
