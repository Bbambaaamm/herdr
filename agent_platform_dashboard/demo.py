"""Deterministic synthetic data only. Importing never starts a server or reads files."""
from .contracts import AgentRow, Grant, RepoRow, ReportRow, RouterRow, Scope, Snapshot, TaskRow


def fixture_snapshot():
    scope = Scope('1' * 64, '2' * 64, '3' * 64, '4' * 64, 'agent-platform')
    return Snapshot(1, 100, '5' * 64, (
        AgentRow(scope, '6' * 64, 'working'),
        TaskRow(scope, '7' * 64, '8' * 64, 'running'),
        RouterRow(scope, '9' * 64, 'nous', 'fixture-free', 1200, 240, None, 'baseline'),
        RepoRow(scope, 'a' * 64, 'b' * 40, False),
        ReportRow(scope, 'c' * 64, 'passed', 35, 0, 'd' * 64),
    ))


def fixture_grant():
    return Grant('e' * 64, (fixture_snapshot().rows[0].scope,), 200)
