"""Bounded advisory trajectory summaries, disconnected from execution authority.

Only host-sanitized tool identifiers belong here, never prompts or tool payloads.
Synthetic control replay is deliberately separate from historical measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
from itertools import islice
import json
import re
from typing import Iterable

from .context import SecretRedactor


VERSION = 1
MAX_EVENTS = 4096
MAX_TOOL_ID = 128
MAX_CONTROL_CASES = 64
MAX_CONTROL_EVENTS = 16384
MAX_REPLAY_BYTES = 4 * 1024 * 1024
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_.:-]{0,127}")
_KINDS = ("step_budget_observed", "consecutive_tool_repeat")


class TrajectoryInputError(ValueError):
    """Fixed bounded code; rejected input is never copied to the error."""


def _need(condition: bool, code: str) -> None:
    if not condition:
        raise TrajectoryInputError(code)


def _identifier(value: object) -> str:
    _need(type(value) is str and len(value) <= MAX_TOOL_ID
          and _ID.fullmatch(value) is not None and ".." not in value,
          "invalid_trajectory_identifier")
    _need(SecretRedactor().redact(value) == value, "secret_trajectory_identifier")
    return value


def _bounded(values: Iterable, limit: int, code: str) -> tuple:
    _need(not isinstance(values, (str, bytes, dict, set, frozenset)), code)
    try:
        result = tuple(islice(iter(values), limit + 1))
    except Exception:
        raise TrajectoryInputError(code) from None
    _need(len(result) <= limit, code)
    return result


def _thresholds(repeat_threshold: int, max_steps: int) -> None:
    _need(type(repeat_threshold) is int and 2 <= repeat_threshold <= MAX_EVENTS
          and type(max_steps) is int and 1 <= max_steps <= MAX_EVENTS,
          "invalid_observer_thresholds")


def _names(values: Iterable[str]) -> tuple[str, ...]:
    result = _bounded(values, MAX_EVENTS, "trajectory_event_limit")
    for value in result:
        _identifier(value)
    return result


@dataclass(frozen=True)
class TrajectorySignal:
    kind: str
    count: int
    severity: str = "observe"

    def __post_init__(self) -> None:
        _need(type(self.kind) is str and self.kind in _KINDS
              and type(self.count) is int and 1 <= self.count <= MAX_EVENTS
              and type(self.severity) is str and self.severity == "observe",
              "invalid_trajectory_signal")

    def to_json(self) -> dict[str, object]:
        self.__post_init__()
        return {"kind": self.kind, "count": self.count, "severity": self.severity}


def inspect_trajectory(tool_names: Iterable[str], *, repeat_threshold: int = 4,
                       max_steps: int = 100) -> tuple[TrajectorySignal, ...]:
    """Return aggregate advisory signals, with at most MAX_EVENTS+1 reads.

    Hosts must supply terminating iterator steps; this pure contract cannot
    preempt arbitrary caller code inside next(). Overflow rejects, not truncates.
    """
    _thresholds(repeat_threshold, max_steps)
    names = _names(tool_names)
    signals = []
    if len(names) > max_steps:
        signals.append(TrajectorySignal("step_budget_observed", len(names)))
    if names:
        run = longest = 1
        for previous, current in zip(names, names[1:]):
            run = run + 1 if previous == current else 1
            longest = max(longest, run)
        if longest >= repeat_threshold:
            signals.append(TrajectorySignal("consecutive_tool_repeat", longest))
    return tuple(signals)


@dataclass(frozen=True)
class SyntheticTrajectoryCase:
    """Explicit synthetic labels, never historical/production ground truth."""
    case_id: str
    tool_names: tuple[str, ...]
    expected_kinds: tuple[str, ...]

    def __post_init__(self) -> None:
        _identifier(self.case_id)
        object.__setattr__(self, "tool_names", _names(self.tool_names))
        expected = _bounded(self.expected_kinds, len(_KINDS), "invalid_control_labels")
        _need(all(type(kind) is str and kind in _KINDS for kind in expected)
              and len(set(expected)) == len(expected), "invalid_control_labels")
        object.__setattr__(self, "expected_kinds", expected)


def _canonical(value: object) -> bytes:
    result = bytearray()
    encoder = json.JSONEncoder(sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True, allow_nan=False)
    for chunk in encoder.iterencode(value):
        raw = chunk.encode("ascii")
        _need(len(result) + len(raw) <= MAX_REPLAY_BYTES, "trajectory_replay_bytes")
        result.extend(raw)
    return bytes(result)


def replay_synthetic_controls(cases: Iterable[SyntheticTrajectoryCase], *,
                              repeat_threshold: int = 4,
                              max_steps: int = 100) -> dict[str, object]:
    """Deterministic controls only. Missing historical measurements stay UNKNOWN.

    No trace loader, timer, telemetry stream, model or execution callback exists.
    The caller receives a fresh plain value, not an acceptance/permission receipt.
    """
    _thresholds(repeat_threshold, max_steps)
    rows = _bounded(cases, MAX_CONTROL_CASES, "trajectory_control_limit")
    seen, total, inputs, outputs = set(), 0, [], []
    for case in rows:
        _need(type(case) is SyntheticTrajectoryCase, "invalid_trajectory_control")
        case = SyntheticTrajectoryCase(case.case_id, case.tool_names, case.expected_kinds)
        _need(case.case_id not in seen, "duplicate_trajectory_control")
        seen.add(case.case_id)
        total += len(case.tool_names)
        _need(total <= MAX_CONTROL_EVENTS, "trajectory_control_event_limit")
        signals = inspect_trajectory(case.tool_names, repeat_threshold=repeat_threshold,
                                     max_steps=max_steps)
        inputs.append({"case_id": case.case_id, "tool_names": case.tool_names,
                       "expected_kinds": case.expected_kinds})
        outputs.append({"case_id": case.case_id,
                        "signals": [signal.to_json() for signal in signals],
                        "matches_control": tuple(signal.kind for signal in signals)
                                           == case.expected_kinds})
    bound = {"version": VERSION, "repeat_threshold": repeat_threshold,
             "max_steps": max_steps, "cases": inputs}
    reasons = {"precision": "historical_labels_not_supplied",
               "detection_rate": "historical_labels_not_supplied",
               "false_positive_rate": "historical_labels_not_supplied",
               "p95_overhead_ms": "historical_timing_not_supplied",
               "token_cost_correlation": "historical_usage_not_supplied"}
    return {"version": VERSION, "scope": "synthetic_controls_only",
            "input_sha256": hashlib.sha256(_canonical(bound)).hexdigest(),
            "synthetic_controls": {"case_count": len(rows),
                                   "matched_cases": sum(row["matches_control"] for row in outputs),
                                   "cases": outputs},
            "historical_metrics": {
                "sample_count": 0,
                "metrics": {name: {"status": "UNKNOWN", "value": None,
                                   "denominator": 0, "reason": reason}
                            for name, reason in reasons.items()}}}
