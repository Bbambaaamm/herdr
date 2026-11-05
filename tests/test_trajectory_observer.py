from herdr.trajectory_observer import inspect_trajectory
import pytest


def test_normal_trajectory_has_no_signals():
    assert inspect_trajectory(["read", "search", "write"]) == ()


def test_repeat_is_advisory_only():
    signals = inspect_trajectory(["read"] * 4)
    assert signals[0].kind == "consecutive_tool_repeat"
    assert signals[0].severity == "observe"


def test_step_threshold():
    assert inspect_trajectory(["read", "write", "read"], max_steps=2)[0].kind == "step_budget_observed"


def test_invalid_input_rejected():
    with pytest.raises(ValueError):
        inspect_trajectory(["read", ""])
    with pytest.raises(ValueError):
        inspect_trajectory([], repeat_threshold=1)
