import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

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
        self.exporter.INTAKE = self.root / "github-intake-state.json"
        self.exporter.OUTPUT = self.output

    def private_records(self, payload):
        return [{"task_id": task["task_id"], "repo": payload["repo"],
                 "raw": {"execution_session": {"agent_name": task["agent_id"], "pane_id": "%1"}}}
                for task in payload["tasks"]]

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

    def test_default_materializer_output_never_aliases_runtime_scheduler_snapshot(self):
        fresh = load_module()
        self.assertEqual(fresh.OUTPUT, Path(sources.SWARM_FALLBACK_PATH))
        self.assertNotEqual(fresh.OUTPUT, Path(sources.SWARM_PATH))

    def test_terminal_only_is_fresh_and_has_zero_active_agents(self):
        self.write_task("done", self.herdr_task(result_sha="a" * 64))
        records = self.exporter.load_records()
        payload = self.exporter.materialize(records, observed_at=100)
        self.assertEqual(payload["observed_at"], 100)
        self.assertEqual(payload["agents"], [])
        self.assertEqual(payload["tasks"][0]["state"], "done")
        self.assertEqual(payload["issue_state"], "unknown")
        self.exporter.publish(payload)
        previous = sources.SWARM_PATH
        try:
            sources.SWARM_PATH = str(self.output)
            rows, stamp = sources.swarm(str(self.output), "quantlab")
        finally:
            sources.SWARM_PATH = previous
        self.assertEqual(stamp, 100)
        self.assertEqual(rows[0]["issue_state"], "unknown")
        self.assertEqual(rows[0]["tasks"][0]["state"], "done")
        self.assertEqual(rows[0]["edges"], [])

    def test_runtime_projection_keeps_live_state_separate_from_durable_delivery_uncertain(self):
        self.write_task(
            "pending",
            self.herdr_task(
                "root",
                attempt_state="delivery_uncertain",
                delivery_reconcile_count=5,
                execution_session={"agent_name": "task-hermes", "pane_id": "%1"},
            ),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(payload["tasks"][0]["state"], "pending")
        self.assertEqual(payload["tasks"][0]["attempt_state"], "delivery_uncertain")
        self.assertEqual(payload["tasks"][0]["delivery_reconcile_count"], 5)
        runtime = {
            "id": "cli:agent:list",
            "result": {
                "type": "agent_list",
                "agents": [
                    {"name": "herdr-hermes", "agent_status": "idle"},
                    {"name": "herdr-codex", "agent_status": "working"},
                    {"name": "task-hermes", "agent_status": "working", "pane_id": "%1"},
                    {"name": "quantlab-codex", "agent_status": "working"},
                ],
            },
        }
        fake = SimpleNamespace(returncode=0, stdout=json.dumps(runtime), stderr="")
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            status, agents = self.exporter.runtime_agent_projection(payload, records=self.private_records(payload))
        self.assertEqual(status, "available")
        self.assertEqual(
            agents,
            [
                {"agent_id": "herdr-codex", "status": "working", "task_id": None},
                {"agent_id": "herdr-hermes", "status": "idle", "task_id": None},
                {"agent_id": "task-hermes", "status": "working", "task_id": "root"},
            ],
        )
        payload["runtime_status"] = status
        payload["runtime_agents"] = agents
        self.exporter.publish(payload)
        previous = sources.SWARM_PATH
        try:
            sources.SWARM_PATH = str(self.output)
            rows, _ = sources.swarm(str(self.output), "quantlab")
        finally:
            sources.SWARM_PATH = previous
        self.assertEqual(rows[0]["tasks"][0]["state"], "pending")
        self.assertEqual(rows[0]["tasks"][0]["attempt_state"], "delivery_uncertain")
        self.assertEqual([row["agent_id"] for row in rows[0]["runtime_agents"]],
                         ["herdr-codex", "herdr-hermes", "task-hermes"])

    def test_runtime_projection_includes_blocked_tasks_in_unique_binding(self):
        payload = {"repo": "Bbambaaamm/herdr", "tasks": [
            {"task_id": "blocked", "state": "blocked", "agent_id": "task-hermes"},
        ]}
        raw = {"id": "cli:agent:list", "result": {"type": "agent_list", "agents": [
            {"name": "task-hermes", "agent_status": "blocked", "pane_id": "%1"},
        ]}}
        fake = SimpleNamespace(returncode=0, stdout=json.dumps(raw), stderr="")
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            status, agents = self.exporter.runtime_agent_projection(payload, records=self.private_records(payload))
        self.assertEqual(status, "available")
        self.assertEqual(agents[0]["task_id"], "blocked")
        payload["tasks"].append(
            {"task_id": "pending", "state": "pending", "agent_id": "task-hermes"})
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            _, agents = self.exporter.runtime_agent_projection(payload, records=self.private_records(payload))
        self.assertIsNone(agents[0]["task_id"])

    def test_runtime_projection_binds_only_unique_nonterminal_task(self):
        payload = {
            "repo": "Bbambaaamm/herdr",
            "tasks": [
                {"task_id": "old", "state": "failed", "agent_id": "task-hermes"},
                {"task_id": "current", "state": "pending", "agent_id": "task-hermes"},
            ],
        }
        runtime = {
            "id": "cli:agent:list",
            "result": {"type": "agent_list", "agents": [
                {"name": "task-hermes", "agent_status": "working", "pane_id": "%1"},
            ]},
        }
        fake = SimpleNamespace(returncode=0, stdout=json.dumps(runtime), stderr="")
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            status, agents = self.exporter.runtime_agent_projection(payload, records=self.private_records(payload))
        self.assertEqual(status, "available")
        self.assertEqual(agents, [{
            "agent_id": "task-hermes", "status": "working", "task_id": "current",
        }])

        payload["tasks"].append(
            {"task_id": "also-current", "state": "running", "agent_id": "task-hermes"}
        )
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            status, agents = self.exporter.runtime_agent_projection(payload, records=self.private_records(payload))
        self.assertEqual(status, "available")
        self.assertEqual(agents, [{
            "agent_id": "task-hermes", "status": "working", "task_id": None,
        }])

    def test_runtime_projection_enforces_downstream_sixteen_row_limit(self):
        tasks = [
            {"task_id": f"task-{index}", "state": "pending", "agent_id": f"agent-{index}"}
            for index in range(17)
        ]
        runtime = {
            "id": "cli:agent:list",
            "result": {"type": "agent_list", "agents": [
                {"name": f"agent-{index}", "agent_status": "working"}
                for index in range(17)
            ]},
        }
        fake = SimpleNamespace(returncode=0, stdout=json.dumps(runtime), stderr="")
        with patch.object(self.exporter, "runtime_command", return_value=fake.stdout.encode()):
            status, agents = self.exporter.runtime_agent_projection({
                "repo": "Bbambaaamm/herdr", "tasks": tasks,
            })
        self.assertEqual((status, agents), ("unavailable", []))

    def test_runtime_projection_keeps_canonical_dynamic_children_without_fallback_task(self):
        payload = {"repo": "Bbambaaamm/herdr", "tasks": []}
        raw = {"id": "cli:agent:list", "result": {"type": "agent_list", "agents": [
            {"name": "agent-1", "agent_status": "working", "pane_id": "%7"}]}}
        with patch.object(self.exporter, "canonical_agent_ids", return_value={"agent-1"}), patch.object(
                self.exporter, "runtime_command", return_value=json.dumps(raw).encode()):
            status, agents = self.exporter.runtime_agent_projection(payload, records=[])
        self.assertEqual(status, "available")
        self.assertEqual(agents, [{"agent_id": "agent-1", "status": "working", "task_id": None}])

    def test_runtime_projection_rejects_stale_or_missing_private_pane_binding(self):
        payload = {"repo": "Bbambaaamm/herdr", "tasks": [
            {"task_id": "task", "state": "pending", "agent_id": "task-hermes"}]}
        raw = {"id": "cli:agent:list", "result": {"type": "agent_list", "agents": [
            {"name": "task-hermes", "agent_status": "working", "pane_id": "%2"}]}}
        with patch.object(self.exporter, "runtime_command", return_value=json.dumps(raw).encode()):
            for records in ([], self.private_records(payload)):
                status, agents = self.exporter.runtime_agent_projection(payload, records=records)
                self.assertEqual(status, "available")
                self.assertIsNone(agents[0]["task_id"])
        self.assertNotIn("pane_id", agents[0])

    def test_actual_runtime_command_bounds_stdout_and_discards_unbounded_stderr(self):
        import sys
        from agent_platform_dashboard.production_sources import command
        with self.assertRaises(ValueError):
            command([sys.executable, "-c", "import sys; sys.stdout.write('x'*1000000)"],
                    limit=1024, timeout=2)
        self.assertEqual(command([sys.executable, "-c",
                         "import sys; sys.stderr.write('x'*1000000); print('ok')"],
                         limit=1024, timeout=2), b"ok\n")

    def test_verification_wait_remains_same_blocked_attempt_in_valid_public_snapshot(self):
        self.write_task("blocked", self.herdr_task(
            attempt_state="verification_pending", verification_status="evidence_unavailable",
            attempts=1, run_token="same-run"))
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        row = payload["tasks"][0]
        self.assertEqual(row["state"], "blocked")
        self.assertEqual(row["attempt_state"], "verification_pending")
        self.assertEqual(row["blocker"], "evidence_unavailable")
        self.assertEqual(row["attempts"], 1)
        self.exporter.publish(payload)
        previous = sources.SWARM_PATH
        try:
            sources.SWARM_PATH = str(self.output)
            normalized, _ = sources.swarm(str(self.output), "quantlab")
        finally:
            sources.SWARM_PATH = previous
        self.assertEqual(normalized[0]["tasks"][0]["attempt_state"], "verification_pending")

    def test_permanent_verification_replan_exports_reason(self):
        self.write_task("blocked", self.herdr_task(
            attempt_state="blocked", verification_status="evidence_invalid",
            verification_resolution="needs_replan", attempts=1, run_token="same-run"))
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        row = payload["tasks"][0]
        self.assertEqual(row["state"], "blocked")
        self.assertEqual(row["blocker"], "evidence_invalid")
        self.assertEqual(row["attempts"], 1)

    def test_closed_issue_is_explicit_and_cannot_mask_open_work(self):
        self.exporter.INTAKE.write_text(
            json.dumps({
                "Bbambaaamm/herdr#48": {
                    "open": False,
                    "repo": "Bbambaaamm/herdr",
                    "issue": 48,
                },
                "Bbambaaamm/herdr#53": {
                    "open": True,
                    "repo": "Bbambaaamm/herdr",
                    "issue": 53,
                },
            }),
            encoding="utf-8",
        )
        self.write_task("blocked", self.herdr_task("closed-blocked", issue=48))
        self.write_task("done", self.herdr_task("open-done", issue=53))

        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)

        self.assertEqual(payload["issue"], "53")
        self.assertEqual(payload["issue_state"], "open")
        self.assertEqual([task["task_id"] for task in payload["tasks"]], ["open-done"])

    def test_closed_terminal_group_remains_available_as_history(self):
        self.exporter.INTAKE.write_text(
            json.dumps({
                "Bbambaaamm/herdr#48": {
                    "open": False,
                    "repo": "Bbambaaamm/herdr",
                    "issue": 48,
                }
            }),
            encoding="utf-8",
        )
        self.write_task("blocked", self.herdr_task("closed-blocked"))

        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)

        self.assertEqual(payload["issue_state"], "closed")
        self.assertEqual(payload["tasks"][0]["state"], "blocked")

    def test_closed_issue_with_live_task_still_outranks_open_terminal_history(self):
        self.exporter.INTAKE.write_text(
            json.dumps({
                "Bbambaaamm/herdr#48": {
                    "open": False,
                    "repo": "Bbambaaamm/herdr",
                    "issue": 48,
                },
                "Bbambaaamm/herdr#53": {
                    "open": True,
                    "repo": "Bbambaaamm/herdr",
                    "issue": 53,
                },
            }),
            encoding="utf-8",
        )
        self.write_task("running", self.herdr_task("closed-running", issue=48))
        self.write_task("done", self.herdr_task("open-done", issue=53))

        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)

        self.assertEqual(payload["issue"], "48")
        self.assertEqual(payload["issue_state"], "closed")
        self.assertEqual(payload["tasks"][0]["state"], "running")

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

    def test_paper_only_requires_exact_boolean_type(self):
        for malformed in (0, 1, 0.0, 1.0):
            with self.subTest(paper_only=malformed):
                path = self.write_task(
                    "pending",
                    self.herdr_task(
                        f"bad-paper-{str(malformed).replace('.', '-')}",
                        paper_only=malformed,
                    ),
                )
                with self.assertRaisesRegex(ValueError, "invalid_paper_only"):
                    self.exporter.load_records()
                path.unlink()

    def test_generic_herdr_explicit_non_paper_is_valid(self):
        self.write_task(
            "pending",
            self.herdr_task(
                "generic-non-paper",
                policy_profile="default",
                paper_only=False,
            ),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertFalse(payload["paper_only"])
        self.assertFalse(payload["tasks"][0]["paper_only"])
        self.assertEqual(payload["tasks"][0]["policy_profile"], "default")

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

    def test_herdr_core_safety_profile_is_materialized_as_non_paper(self):
        self.write_task(
            "pending",
            self.herdr_task(
                "herdr-root",
                safety_profile="herdr-core",
                paper_only=False,
            ),
        )
        payload = self.exporter.materialize(
            self.exporter.load_records(),
            observed_at=100,
        )
        self.assertFalse(payload["paper_only"])
        self.assertEqual(payload["policy_profiles"], ["herdr-core"])
        self.assertEqual(payload["tasks"][0]["policy_profile"], "herdr-core")
        self.assertFalse(payload["tasks"][0]["paper_only"])

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

    def test_stale_result_run_token_is_ignored_for_current_attempt(self):
        task = self.herdr_task(
            "current",
            run_token="a" * 32,
            blocker="current_blocker",
        )
        self.write_task("blocked", task)
        (self.root / "results" / "current.json").write_text(
            json.dumps({
                "task_id": "current",
                "run_token": "b" * 32,
                "blocker": "stale_blocker",
                "result_sha": "f" * 64,
            }),
            encoding="utf-8",
        )
        payload = self.exporter.materialize(
            self.exporter.load_records(),
            observed_at=100,
        )
        self.assertEqual(payload["tasks"][0]["blocker"], "current_blocker")
        self.assertNotIn("result_sha", payload["tasks"][0])

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

    def test_parent_and_dependency_graphs_are_validated_independently(self):
        self.write_task(
            "pending",
            self.herdr_task("parent", dependencies=["child"]),
        )
        self.write_task(
            "pending",
            self.herdr_task("child", parent_task_id="parent"),
        )
        payload = self.exporter.materialize(self.exporter.load_records(), observed_at=100)
        self.assertEqual(
            payload["edges"],
            [
                {"from": "child", "to": "parent", "kind": "dependency"},
                {"from": "parent", "to": "child", "kind": "parent"},
            ],
        )

    def test_same_path_rewrite_after_read_forces_snapshot_retry(self):
        path = self.write_task("running", self.herdr_task("rewritten", attempts=0))
        original = self.exporter.file_identity
        calls = {"count": 0}

        def rewrite_before_final_recheck(candidate):
            if candidate == path:
                calls["count"] += 1
                if calls["count"] == 3:
                    changed = self.herdr_task("rewritten", attempts=1)
                    path.write_text(json.dumps(changed), encoding="utf-8")
            return original(candidate)

        self.exporter.file_identity = rewrite_before_final_recheck
        try:
            with self.assertRaisesRegex(self.exporter.SnapshotRace, "task_replaced_after_read"):
                self.exporter._load_records_once()
        finally:
            self.exporter.file_identity = original

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
