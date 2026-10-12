"""Read-only OnTrack-inspired trajectory signals; no scheduler authority.

Inputs are sanitized event summaries, never prompts, credentials or tool payloads.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TrajectorySignal:
    kind: str
    count: int
    severity: str = "observe"


def inspect_trajectory(tool_names: Iterable[str], *, repeat_threshold: int = 4,
                       max_steps: int = 100) -> tuple[TrajectorySignal, ...]:
    """Return deterministic advisory signals without stopping execution."""
    if repeat_threshold < 2 or max_steps < 1:
        raise ValueError("invalid observer thresholds")
    names = tuple(tool_names)
    if not all(isinstance(name, str) and name for name in names):
        raise ValueError("tool names must be nonempty strings")
    signals = []
    if len(names) > max_steps:
        signals.append(TrajectorySignal("step_budget_observed", len(names)))
    if names:
        run = 1
        longest = 1
        for prev, current in zip(names, names[1:]):
            run = run + 1 if prev == current else 1
            longest = max(longest, run)
        if longest >= repeat_threshold:
            signals.append(TrajectorySignal("consecutive_tool_repeat", longest))
    return tuple(signals)
