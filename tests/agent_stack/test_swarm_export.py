import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from agent_platform_dashboard import production_sources as sources

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent-swarm-export"


def load_module():
    loader = importlib.machinery.SourceFileLoader("herdr_swarm_export_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class SwarmExportTests(unittest.TestCase):
    def setUp(self):
        self.exporter = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.root = base / "tasks"
        for name in ("pending", "running", "blocked", "failed", "done", "results"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.output = base / "swarm.json"
        self.exporter.ROOT = self.root
        self.exporter.RESULTS = self.root / "results"
        self.exporter.OUTPUT = self.output

    def tearDown(self):
        self.tmp.cleanup()

    def write_task(self, state, task):
        path = self.root / state / f"{task['id']}.json"
        path.write_text(json.dumps(task), encoding="utf-8")
        return path

    def herdr_task(self, task_id="root", **overrides):
        task = {
            "id": task_id,
            "repo": "Bbambaaamm/herdr",
            "issue": 48,
            "kind": "github_issue_slice",
            "attempts": 0,
            "max_attempts": 4,
            "dependencies": [],
            "created_at": "2026-09-29T10:00:00+00:00",
        }
        task.update(overrides)
        return task

    def test_terminal_only_is_fresh_and_has_zero_active_agents(self):
        self.write_task("done", self.herdr_task(result_sha="a" * 64))
        records = self.exporter.load_records()
        payload = self.exporter.materialize(records, observed_at=100)
        self.assertEqual(payload["observed_at"], 100)
        self.assertEqual(payload["agents"], [])
        self.assertEqual(payload["tasks"][0]["state"], "done")
        self.exporter.publish(payload)
        previous = sources.SWARM_PATH
        try:
            sources.SWARM_PATH = str(self.output)
            rows, stamp = sources.swarm(str(self.output), "quantlab")
        finally:
            sources.SWARM_PATH = previous
        self.assertEqual(stamp, 100)
        self.assertEqual(rows[0]["tasks"][0]["state"], "done")
        self.assertEqual(rows[0]["edges"], [])

    def test_parent_children_and_fencing_are_exact(self):
        self.write_task(
            "running",
            self.herdr_task(
                "parent",
                agent_id="parent-agent",
                fencing_token=10,
                role="planner",
            ),
        )
        self.write_task(
            "running",
            self.herdr_task(
                "child-a",
                parent_task_id="parent",
                parent_agent_id="parent-agent",
                agent_id="child-a-agent",
                fencing_token=11,
                role="reader",
            ),
        )
        self.write_task(
            "running",
            self.herdr_task(
                "child-b",
                parent_task_id="parent",
                parent_agent_id="parent-agent",
                agent_id="child-b-agent",
                fencing_token=12,
                role="tester",
            ),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(
            payload["edges"],
            [
                {"from": "parent", "to": "child-a", "kind": "parent"},
                {"from": "parent", "to": "child-b", "kind": "parent"},
            ],
        )
        tokens = {task["fencing_token"] for task in payload["tasks"]}
        self.assertEqual(tokens, {10, 11, 12})
        self.assertEqual(len(payload["agents"]), 3)

    def test_dependencies_are_exact_and_blocked_failed_remain_distinct(self):
        self.write_task("blocked", self.herdr_task("build", watchdog_blocker="human_gate"))
        self.write_task(
            "failed",
            self.herdr_task("verify", dependencies=["build"], blocker="test_failed"),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        states = {task["task_id"]: task["state"] for task in payload["tasks"]}
        self.assertEqual(states, {"build": "blocked", "verify": "failed"})
        self.assertEqual(
            payload["edges"],
            [{"from": "build", "to": "verify", "kind": "dependency"}],
        )

    def test_running_to_blocked_is_reflected_without_restart(self):
        running = self.write_task(
            "running",
            self.herdr_task("transition", execution_session={"agent_name": "task-agent"}),
        )
        first = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(first["tasks"][0]["state"], "running")
        self.assertEqual(first["agents"][0]["agent_id"], "task-agent")
        blocked = self.root / "blocked" / running.name
        running.replace(blocked)
        second = self.exporter.materialize(self.exporter.load_records(), observed_at=101)
        self.assertEqual(second["tasks"][0]["state"], "blocked")
        self.assertEqual(second["agents"], [])

    def test_duplicate_and_dangling_graph_fail_closed_and_preserve_previous_file(self):
        sentinel = b'{"previous":"valid"}\n'
        self.output.write_bytes(sentinel)
        task = self.herdr_task("duplicate")
        self.write_task("running", task)
        self.write_task("blocked", task)
        with self.assertRaisesRegex(ValueError, "unstable_snapshot"):
            self.exporter.main()
        self.assertEqual(self.output.read_bytes(), sentinel)

        for path in (self.root / "running").glob("*.json"):
            path.unlink()
        for path in (self.root / "blocked").glob("*.json"):
            path.unlink()
        self.write_task(
            "pending",
            self.herdr_task("dangling", dependencies=["missing"]),
        )
        with self.assertRaisesRegex(ValueError, "dangling_dependency"):
            self.exporter.main()
        self.assertEqual(self.output.read_bytes(), sentinel)

    def test_done_task_drops_obsolete_watchdog_blocker(self):
        self.write_task(
            "done",
            self.herdr_task(
                "reconciled-done",
                watchdog_blocker="orphaned_running_unknown_delivery",
            ),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(payload["tasks"][0]["state"], "done")
        self.assertNotIn("blocker", payload["tasks"][0])

    def test_snapshot_scan_retries_task_move_between_state_directories(self):
        running = self.write_task("running", self.herdr_task("moving"))
        blocked = self.root / "blocked" / running.name
        original = self.exporter.read_json
        moved = {"value": False}

        def move_after_read(path):
            raw = original(path)
            if path == running and not moved["value"]:
                running.replace(blocked)
                moved["value"] = True
            return raw

        self.exporter.read_json = move_after_read
        try:
            records = self.exporter.load_records()
        finally:
            self.exporter.read_json = original
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["state"], "blocked")
        self.assertEqual(records[0]["task_id"], "moving")

    def test_snapshot_scan_retries_disappearing_source_path(self):
        running = self.write_task("running", self.herdr_task("vanishing"))
        blocked = self.root / "blocked" / running.name
        original = self.exporter.read_json
        moved = {"value": False}

        def move_before_read(path):
            if path == running and not moved["value"]:
                running.replace(blocked)
                moved["value"] = True
                raise FileNotFoundError(path)
            return original(path)

        self.exporter.read_json = move_before_read
        try:
            records = self.exporter.load_records()
        finally:
            self.exporter.read_json = original
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["state"], "blocked")
        self.assertEqual(records[0]["task_id"], "vanishing")

    def test_non_paper_quantlab_is_rejected(self):
        self.write_task(
            "pending",
            {
                **self.herdr_task("quantlab"),
                "repo": "Bbambaaamm/Autonomous-Quant-Lab",
                "issue": 230,
                "paper_only": False,
            },
        )
        with self.assertRaisesRegex(ValueError, "quantlab_non_paper"):
            self.exporter.load_records()

    def test_pr46_quantlab_safety_profile_maps_to_paper_policy(self):
        self.write_task(
            "pending",
            {
                **self.herdr_task("quantlab-pr46"),
                "repo": "Bbambaaamm/Autonomous-Quant-Lab",
                "issue": 230,
                "safety_profile": "quantlab",
            },
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertTrue(payload["paper_only"])
        self.assertEqual(payload["tasks"][0]["policy_profile"], "quantlab-paper")
        self.assertTrue(payload["tasks"][0]["paper_only"])

    def test_non_quantlab_safety_profile_is_excluded_from_quantlab_swarm(self):
        for safety_profile in ("dotacni-majak", "heating"):
            with self.subTest(safety_profile=safety_profile):
                path = self.write_task(
                    "pending",
                    self.herdr_task(
                        f"foreign-{safety_profile}",
                        safety_profile=safety_profile,
                    ),
                )
                with self.assertRaisesRegex(ValueError, "non_quantlab_safety_profile"):
                    self.exporter.load_records()
                path.unlink()

    def test_sensitive_fields_never_leave_durable_store(self):
        task = self.herdr_task(
            "private",
            agent_id="safe-agent",
            prompt="PRIVATE_PROMPT",
            agent_output_tail="PRIVATE_OUTPUT",
            last_error="PRIVATE_ERROR_TEXT",
            workspace="/PRIVATE/WORKSPACE",
            execution_session={
                "agent_name": "safe-agent",
                "pane_id": "PRIVATE_PANE",
                "session_name": "PRIVATE_SESSION",
            },
        )
        self.write_task("running", task)
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        encoded = json.dumps(payload)
        for secret in (
            "PRIVATE_PROMPT",
            "PRIVATE_OUTPUT",
            "PRIVATE_ERROR_TEXT",
            "PRIVATE/WORKSPACE",
            "PRIVATE_PANE",
            "PRIVATE_SESSION",
        ):
            self.assertNotIn(secret, encoded)
        self.assertIn("safe-agent", encoded)

    def test_same_fixture_is_deterministic_except_observed_at(self):
        self.write_task(
            "done",
            self.herdr_task(
                "deterministic",
                policy_profile="default",
                routing={"model": "model-a", "fallback_model": "model-b"},
            ),
        )
        records = self.exporter.load_records()
        one = self.exporter.materialize(records, observed_at=100)
        two = self.exporter.materialize(records, observed_at=101)
        one.pop("observed_at")
        two.pop("observed_at")
        self.assertEqual(one, two)

    def test_no_matching_consumer_does_not_refresh_stale_output(self):
        sentinel = b'{"previous":"stale"}\n'
        self.output.write_bytes(sentinel)
        self.write_task(
            "running",
            {
                **self.herdr_task("majak"),
                "repo": "Bbambaaamm/dotacni-majak",
                "issue": 662,
            },
        )
        self.assertEqual(self.exporter.main(), 0)
        self.assertEqual(self.output.read_bytes(), sentinel)

    def test_result_identity_must_match_current_run_token(self):
        task = self.herdr_task("current", run_token="a" * 32)
        self.write_task("running", task)
        (self.root / "results" / "current.json").write_text(
            json.dumps({"task_id": "current", "run_token": "b" * 32, "blocker": "stale"}),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(ValueError, "result_run_token_mismatch"):
            self.exporter.materialize(self.exporter.load_records(), observed_at=100)

    def test_result_lookup_cannot_escape_results_directory(self):
        with self.assertRaisesRegex(ValueError, "invalid_task_id"):
            self.exporter.result_for("../../private", {"run_token": "a" * 32})

    def test_uppercase_result_sha_is_rejected_before_publish(self):
        self.write_task("done", self.herdr_task("upper", result_sha="A" * 64))
        with self.assertRaisesRegex(ValueError, "invalid_result_sha"):
            self.exporter.materialize(self.exporter.load_records(), observed_at=100)

    def test_duplicate_task_ids_are_scoped_to_repo_and_issue(self):
        self.write_task("running", self.herdr_task("root", issue=48))
        self.write_task("blocked", self.herdr_task("root", issue=49))
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(payload["issue"], "48")
        self.assertEqual([task["task_id"] for task in payload["tasks"]], ["root"])

    def test_duplicate_running_agent_identity_fails_before_publish(self):
        sentinel = b'{"previous":"valid"}\n'
        self.output.write_bytes(sentinel)
        self.write_task("running", self.herdr_task("one", agent_id="shared-agent"))
        self.write_task("running", self.herdr_task("two", agent_id="shared-agent"))
        with self.assertRaisesRegex(ValueError, "duplicate_agent_id"):
            self.exporter.main()
        self.assertEqual(self.output.read_bytes(), sentinel)

    def test_long_lived_issue_retains_newest_closed_graph_components(self):
        for index in range(self.exporter.MAX_TASKS + 1):
            self.write_task(
                "done",
                self.herdr_task(
                    f"slice-{index:03d}",
                    created_at=f"2026-09-29T10:{index // 60:02d}:{index % 60:02d}+00:00",
                ),
            )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        task_ids = {task["task_id"] for task in payload["tasks"]}
        self.assertEqual(len(task_ids), self.exporter.MAX_TASKS)
        self.assertNotIn("slice-000", task_ids)
        self.assertIn(f"slice-{self.exporter.MAX_TASKS:03d}", task_ids)

    def test_bounded_history_never_cuts_a_connected_graph(self):
        for index in range(self.exporter.MAX_TASKS):
            self.write_task(
                "done",
                self.herdr_task(
                    f"old-{index:03d}",
                    created_at=f"2026-09-28T10:{index // 60:02d}:{index % 60:02d}+00:00",
                ),
            )
        self.write_task(
            "running",
            self.herdr_task(
                "current-parent",
                agent_id="current-agent",
                created_at="2026-09-29T10:00:00+00:00",
            ),
        )
        self.write_task(
            "pending",
            self.herdr_task(
                "current-child",
                parent_task_id="current-parent",
                created_at="2026-09-29T10:00:01+00:00",
            ),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        task_ids = {task["task_id"] for task in payload["tasks"]}
        self.assertIn("current-parent", task_ids)
        self.assertIn("current-child", task_ids)
        self.assertLessEqual(len(task_ids), self.exporter.MAX_TASKS)
        self.assertEqual(
            payload["edges"],
            [{"from": "current-parent", "to": "current-child", "kind": "parent"}],
        )

    def test_parent_and_dependency_cycles_fail_closed(self):
        self.write_task("pending", self.herdr_task("a", parent_task_id="b"))
        self.write_task("pending", self.herdr_task("b", parent_task_id="a"))
        with self.assertRaisesRegex(ValueError, "cyclic_graph"):
            self.exporter.materialize(self.exporter.load_records(), observed_at=100)

    def test_explicit_false_cannot_be_overridden_by_policy_label(self):
        self.write_task(
            "pending",
            self.herdr_task("contradictory", policy_profile="quantlab-paper", paper_only=False),
        )
        with self.assertRaisesRegex(ValueError, "explicit_non_paper"):
            self.exporter.load_records()

    def test_oversized_snapshot_preserves_previous_file(self):
        sentinel = b'{"previous":"valid"}\n'
        self.output.write_bytes(sentinel)
        with self.assertRaisesRegex(ValueError, "snapshot_too_large"):
            self.exporter.publish({"padding": "x" * self.exporter.MAX_BYTES})
        self.assertEqual(self.output.read_bytes(), sentinel)


if __name__ == "__main__":
    unittest.main()
