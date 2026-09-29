import json
import sqlite3
import sys
import tempfile
import time
import unittest
from pathlib import Path

import pytest

DASHBOARD = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(DASHBOARD))

from agent_platform_dashboard import production_contract as c  # noqa: E402
from agent_platform_dashboard import production_sources as sources  # noqa: E402
from agent_platform_dashboard.production_export import collect  # noqa: E402


def queue_row(**overrides):
    row = {
        "task_id": "github-issue-234-20260926T141907Z",
        "issue": 234,
        "issue_title": "Unified swarm telemetry",
        "issue_open": True,
        "scheduler_state": "active",
        "status": "running",
        "attempts": 1,
        "max_attempts": 4,
        "not_before": None,
        "updated_at": 100,
        "agent": "quantlab-hermes",
        "kind": "github_issue_slice",
        "blocker": None,
        "pr_number": None,
    }
    row.update(overrides)
    return row
def codex_payload(observed_at=100):
    return {
        "version": 1,
        "observed_at": observed_at,
        "rate_limit": {
            "used_percent": 82,
            "window_minutes": 10080,
            "resets_at": 200,
            "ordinary_usage_allowed": True,
            "has_credits": False,
            "credits_unlimited": False,
            "credits_balance": "0",
            "reset_credits_available": 0,
        },
        "usage": {
            "lifetime_tokens": 123456789,
            "peak_daily_tokens": 9000000,
            "longest_running_turn_sec": 1234,
            "current_streak_days": 7,
            "longest_streak_days": 9,
            "daily": [
                {"day": "2026-09-24", "tokens": 1000},
                {"day": "2026-09-25", "tokens": 2000},
            ],
        },
        "limit_history": [
            {"at": 90, "used_percent": 79},
            {"at": 100, "used_percent": 82},
        ],
    }


def routing_payload(observed_at):
    return {
        "version": 1,
        "observed_at": observed_at,
        "policy": {
            "version": "cost-aware-v1.0",
            "soft_limit_pct": 70,
            "hard_limit_pct": 90,
        },
        "totals": {
            "decisions": 7,
            "free": 5,
            "sol": 2,
            "astra": 0,
            "astra_escalations": 0,
            "premium_denied": 0,
        },
        "recent": [{
            "at": observed_at,
            "task_id": "github-issue-230-test",
            "issue": 230,
            "attempt": 2,
            "tier": "sol",
            "model": "gpt-6-sol",
            "selected_agent": "quantlab-sol",
            "reason": "cheap_attempts_exhausted",
            "complexity_score": 0.61,
            "codex_used_percent": 8,
        }],
    }


class ObservabilityContractTests(unittest.TestCase):
    def test_source_matrix_is_closed_and_asymmetric(self):
        self.assertEqual(len(c.SOURCE_PAIRS), 18)
        self.assertIn(("quantlab", "queue"), c.SOURCE_PAIRS)
        self.assertIn(("majak", "queue"), c.SOURCE_PAIRS)
        self.assertIn(("majak", "codex"), c.SOURCE_PAIRS)
        self.assertNotIn(("quantlab", "codex"), c.SOURCE_PAIRS)
        self.assertIn(("quantlab", "admission"), c.SOURCE_PAIRS)
        self.assertNotIn(("majak", "admission"), c.SOURCE_PAIRS)
        self.assertIn(("quantlab", "swarm"), c.SOURCE_PAIRS)
        self.assertNotIn(("majak", "swarm"), c.SOURCE_PAIRS)
        self.assertIn(("quantlab", "release"), c.SOURCE_PAIRS)
        self.assertNotIn(("majak", "release"), c.SOURCE_PAIRS)
    def test_queue_v2_legacy_and_v3_multi_consumer_projection(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "queue.json"
            legacy = {
                "version": 2,
                "profile": "quantlab",
                "observed_at": 100,
                "tasks": [queue_row()],
            }
            path.write_text(json.dumps(legacy), encoding="utf-8")
            original = sources.QUEUE_PATH
            sources.QUEUE_PATH = str(path)
            try:
                rows, stamp = sources.queue(str(path), "quantlab")
                self.assertEqual(stamp, 100)
                self.assertEqual(rows, legacy["tasks"])
                with self.assertRaises(ValueError):
                    sources.queue(str(path), "majak")

                quant = queue_row(repo="Bbambaaamm/Autonomous-Quant-Lab")
                majak = queue_row(
                    task_id="github-majak-issue-662-test",
                    repo="Bbambaaamm/dotacni-majak",
                    issue=662,
                    issue_title="HERDR CONTROL",
                    agent="dotacni-majak-hermes",
                    kind="github_root_orchestration",
                )
                current = {
                    "version": 3,
                    "observed_at": 101,
                    "tasks": [quant, majak],
                }
                path.write_text(json.dumps(current), encoding="utf-8")
                quant_rows, stamp = sources.queue(str(path), "quantlab")
                majak_rows, _ = sources.queue(str(path), "majak")
                self.assertEqual(stamp, 101)
                self.assertEqual(quant_rows, [quant])
                self.assertEqual(majak_rows, [majak])
                self.assertNotIn("prompt", json.dumps(quant_rows + majak_rows))

                current["tasks"][1]["prompt"] = "PRIVATE"
                path.write_text(json.dumps(current), encoding="utf-8")
                with self.assertRaises(ValueError):
                    sources.queue(str(path), "majak")
            finally:
                sources.QUEUE_PATH = original

    def test_codex_usage_projection_exposes_allowance_without_identity(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "codex.json"
            path.write_text(json.dumps(codex_payload()), encoding="utf-8")
            original = sources.CODEX_USAGE_PATH
            sources.CODEX_USAGE_PATH = str(path)
            try:
                rows, stamp = sources.codex(str(path), "majak")
                self.assertEqual(stamp, 100)
                self.assertEqual(rows[0]["used_percent"], 82)
                self.assertEqual(rows[0]["lifetime_tokens"], 123456789)
                rendered = json.dumps(rows).lower()
                self.assertNotIn("account_id", rendered)
                self.assertNotIn("access_token", rendered)
                self.assertNotIn("prompt", rendered)
                with self.assertRaises(ValueError):
                    sources.codex(str(path), "quantlab")
            finally:
                sources.CODEX_USAGE_PATH = original
    def test_codex_projection_includes_cost_aware_routing_summary(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            now = int(time.time())
            codex = root / "codex.json"
            routing = root / "routing.json"
            codex.write_text(json.dumps(codex_payload(observed_at=now)), encoding="utf-8")
            routing.write_text(json.dumps(routing_payload(now - 3600)), encoding="utf-8")
            old_usage, old_routing = sources.CODEX_USAGE_PATH, sources.MODEL_ROUTING_PATH
            sources.CODEX_USAGE_PATH, sources.MODEL_ROUTING_PATH = str(codex), str(routing)
            try:
                rows, stamp = sources.codex(str(codex), "majak")
                row = rows[0]
                self.assertEqual(stamp, now)
                self.assertEqual(row["routing_status"], "available")
                self.assertEqual((row["routing_free"], row["routing_sol"], row["routing_astra"]), (5, 2, 0))
                self.assertEqual(row["routing_astra_escalations"], 0)
                self.assertEqual(row["routing_soft_limit_pct"], 70)
                self.assertEqual(row["routing_hard_limit_pct"], 90)
                self.assertEqual(row["routing_observed_at"], now - 3600)
                self.assertEqual(row["last_route_model"], "gpt-6-sol")
                self.assertEqual(row["last_route_reason"], "cheap_attempts_exhausted")

                v11 = routing_payload(now)
                v11["policy"]["version"] = "cost-aware-v1.1-hermes-parent"
                v11["recent"][0].update({
                    "delivery_reconcile_count": 0,
                    "coordinator_agent": "quantlab-hermes",
                    "executor_agent": "quantlab-sol",
                    "routing_scope": "child_node",
                })
                routing.write_text(json.dumps(v11), encoding="utf-8")
                upgraded, _ = sources.codex(str(codex), "majak")
                self.assertEqual(upgraded[0]["routing_status"], "available")

                routing_data = routing_payload(now)
                routing_data["recent"][0]["prompt"] = "PRIVATE"
                routing.write_text(json.dumps(routing_data), encoding="utf-8")
                degraded, _ = sources.codex(str(codex), "majak")
                self.assertEqual(degraded[0]["routing_status"], "unavailable")
                self.assertNotIn("PRIVATE", json.dumps(degraded))
            finally:
                sources.CODEX_USAGE_PATH, sources.MODEL_ROUTING_PATH = old_usage, old_routing

    def test_search_projection_is_bounded_operational_only(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "search.db"
            db = sqlite3.connect(path)
            db.execute(
                "CREATE TABLE searches("
                "id INTEGER PRIMARY KEY,started_at INTEGER,ended_at INTEGER,"
                "route_mode TEXT,actual_provider TEXT,fallback_provider TEXT,"
                "fallback_used INTEGER,duration_ms INTEGER,result_count INTEGER,"
                "extract_count INTEGER,success INTEGER,cost_usd REAL,"
                "query_hash TEXT,query_chars INTEGER)"
            )
            db.execute(
                "INSERT INTO searches VALUES("
                "1,10,11,'fast','exa-keyless','exa-keyless',1,125,5,0,1,0.0,"
                "'PRIVATEHASH',99)"
            )
            db.commit()
            db.close()
            rows, stamp = sources.search(str(path), "majak")
            self.assertEqual(stamp, 11)
            self.assertEqual(rows[0]["searches"], 1)
            self.assertEqual(rows[0]["fallback_count"], 1)
            self.assertEqual(rows[0]["cost_microusd"], 0)
            self.assertNotIn("PRIVATEHASH", json.dumps(rows))

    def test_collect_materializes_queue_and_codex_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            queue = root / "queue.json"
            codex = root / "codex.json"
            queue.write_text(json.dumps({
                "version": 2,
                "profile": "quantlab",
                "observed_at": 100,
                "tasks": [queue_row()],
            }), encoding="utf-8")
            codex.write_text(json.dumps(codex_payload()), encoding="utf-8")
            old_queue, old_codex = sources.QUEUE_PATH, sources.CODEX_USAGE_PATH
            sources.QUEUE_PATH, sources.CODEX_USAGE_PATH = str(queue), str(codex)
            try:
                config = {
                    "version": 1,
                    "output": str(root / "snapshot.json"),
                    "herdr": None,
                    "profiles": {
                        profile: {
                            "router": None,
                            "search": None,
                            "kanban": None,
                            "git": None,
                            "tests": None,
                        }
                        for profile in c.PROFILES
                    },
                }
                snapshot = collect(config, 100)
                self.assertEqual(len(snapshot["sources"]), 18)
                q = next(s for s in snapshot["sources"] if s["kind"] == "queue")
                x = next(s for s in snapshot["sources"] if s["kind"] == "codex")
                self.assertEqual(q["status"], "available")
                self.assertEqual(x["status"], "available")
                self.assertEqual(x["rows"][0]["used_percent"], 82)

                stale = collect(config, 1001)
                x = next(s for s in stale["sources"] if s["kind"] == "codex")
                self.assertEqual((x["status"], x["reason"], x["rows"]),
                                 ("unavailable", "stale", []))
            finally:
                sources.QUEUE_PATH, sources.CODEX_USAGE_PATH = old_queue, old_codex


if __name__ == "__main__":
    unittest.main()


def _admission_event(event, ts, **overrides):
    base = {
        "ts": ts,
        "event": event,
        "admit:role": "reader",
        "admit:repo": "Bbambaaamm/herdr",
        "admit:issue": "3",
        "admit:node_count": 3,
        "admit:max_depth": 2,
        "admit:max_fanout": 2,
        "admit:child_tools_count": 0,
    }
    if event == "allow":
        base.update({"agents_after": 2, "utilization": {"agents": 0.25}})
    else:
        base.update({"reason": "global_agent_limit", "detail": "PRIVATE TOOL ARGUMENT"})
    base.update(overrides)
    return base


def test_admission_projection_is_bounded_and_sanitized():
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "admission.jsonl"
        events = [
            _admission_event("allow", "2026-09-27T01:00:00+00:00"),
            _admission_event(
                "deny",
                "2026-09-27T01:01:00+00:00",
                **{"admit:denied_tool": "SECRET_TOOL_PAYLOAD"},
            ),
        ]
        path.write_text(
            "".join(json.dumps(event) + "\n" for event in events),
            encoding="utf-8",
        )
        original = sources.ADMISSION_PATH
        sources.ADMISSION_PATH = str(path)
        try:
            rows, stamp = sources.admission(str(path), "quantlab")
            assert stamp > 0
            assert [row["event"] for row in rows] == ["allow", "deny"]
            assert rows[-1]["reason"] == "global_agent_limit"
            rendered = json.dumps(rows)
            assert "PRIVATE TOOL ARGUMENT" not in rendered
            assert "SECRET_TOOL_PAYLOAD" not in rendered
            with pytest.raises(ValueError):
                sources.admission(str(path), "majak")
        finally:
            sources.ADMISSION_PATH = original
