import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent-github-intake"
if str(SCRIPT.parent) not in sys.path:
    sys.path.insert(0, str(SCRIPT.parent))


def load_module():
    loader = importlib.machinery.SourceFileLoader("herdr_github_intake_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class GitHubIntakeTests(unittest.TestCase):
    def setUp(self):
        self.intake = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name) / "tasks"
        for name in ("pending", "running", "blocked", "done", "failed", "results", "logs"):
            (root / name).mkdir(parents=True, exist_ok=True)
        self.intake.ROOT = root
        self.intake.PENDING = root / "pending"
        self.intake.RESULTS = root / "results"
        self.intake.STATE = root / "github-intake-state.json"
        self.intake.STAMP = root / "github-intake.stamp"
        self.intake.LOG = root / "github-intake.log"

    def tearDown(self):
        self.tmp.cleanup()

    def write_config(self, consumers):
        path = Path(self.tmp.name) / "consumers.json"
        path.write_text(
            json.dumps({"schema_version": 1, "consumers": consumers}),
            encoding="utf-8",
        )
        self.intake.CONFIG = path
        return path

    @staticmethod
    def quantlab_consumer():
        return {
            "consumer": "quantlab",
            "enabled": True,
            "repository": "Bbambaaamm/Autonomous-Quant-Lab",
            "mode": "all_open",
            "coordinator_agent": "quantlab-hermes",
            "workspace": "/home/agentops/workspaces/quantlab",
            "safety_profile": "quantlab",
            "hermes_profile": "quantlab",
            "priority_default": 60,
            "priority_architecture": 50,
        }

    @staticmethod
    def majak_consumer():
        return {
            "consumer": "majak",
            "enabled": True,
            "repository": "Bbambaaamm/dotacni-majak",
            "mode": "root_only",
            "root_issue": 662,
            "coordinator_agent": "dotacni-majak-hermes",
            "workspace": "/home/agentops/workspaces/dotacni-majak",
            "safety_profile": "dotacni-majak",
            "hermes_profile": "majak",
            "priority_default": 60,
            "priority_architecture": 60,
        }

    @staticmethod
    def herdr_consumer():
        return {
            "consumer": "herdr",
            "enabled": True,
            "repository": "Bbambaaamm/herdr",
            "mode": "root_only",
            "root_issue": 53,
            "coordinator_agent": "herdr-hermes",
            "workspace": "/home/agentops/workspaces/herdr",
            "safety_profile": "herdr-core",
            "hermes_profile": "quantlab",
            "priority_default": 60,
            "priority_architecture": 60,
        }

    def test_load_state_migrates_legacy_quantlab_keys(self):
        self.intake.STATE.write_text(
            json.dumps({"45": {"open": True, "scheduler_state": "active"}}),
            encoding="utf-8",
        )
        state = self.intake.load_state()
        key = "Bbambaaamm/Autonomous-Quant-Lab#45"
        self.assertIn(key, state)
        self.assertEqual(state[key]["repo"], "Bbambaaamm/Autonomous-Quant-Lab")
        self.assertEqual(state[key]["issue"], 45)

    def test_task_index_scopes_same_issue_number_by_repository(self):
        now = time.time()
        tasks = [
            ("quant.json", "Bbambaaamm/Autonomous-Quant-Lab", "quantlab-hermes"),
            ("majak.json", "Bbambaaamm/dotacni-majak", "dotacni-majak-hermes"),
        ]
        for name, repo, agent in tasks:
            path = self.intake.PENDING / name
            path.write_text(
                json.dumps({"id": name, "issue": 45, "repo": repo, "agent": agent}),
                encoding="utf-8",
            )
            path.touch()
        indexed = self.intake.task_index()
        self.assertIn("Bbambaaamm/Autonomous-Quant-Lab#45", indexed)
        self.assertIn("Bbambaaamm/dotacni-majak#45", indexed)
        self.assertEqual(len(indexed["Bbambaaamm/Autonomous-Quant-Lab#45"]), 1)
        self.assertEqual(len(indexed["Bbambaaamm/dotacni-majak#45"]), 1)

    def test_registry_enables_quantlab_majak_and_herdr_but_not_disabled_heating(self):
        heating = {
            "consumer": "heating",
            "enabled": False,
            "repository": "Bbambaaamm/heating",
            "mode": "all_open",
            "coordinator_agent": "heating-hermes",
            "workspace": "/home/agentops/workspaces/heating",
            "safety_profile": "heating-safe-engineering",
            "hermes_profile": "heating",
        }
        self.write_config(
            [self.quantlab_consumer(), self.majak_consumer(), self.herdr_consumer(), heating]
        )
        consumers = self.intake.load_consumers()
        self.assertEqual(
            [row["consumer"] for row in consumers], ["quantlab", "majak", "herdr"]
        )

    def test_root_consumers_do_not_outrank_quantlab_default_work(self):
        quant = self.quantlab_consumer()
        for root in (self.majak_consumer(), self.herdr_consumer()):
            self.assertGreaterEqual(
                root["priority_default"],
                quant["priority_default"],
            )
            self.assertGreaterEqual(
                root["priority_architecture"],
                quant["priority_default"],
            )

    def test_registry_fails_closed_on_duplicate_repository(self):
        duplicate = self.majak_consumer()
        duplicate["repository"] = "Bbambaaamm/Autonomous-Quant-Lab"
        self.write_config([self.quantlab_consumer(), duplicate])
        with self.assertRaisesRegex(RuntimeError, "duplicate repository"):
            self.intake.load_consumers()

    def test_majak_root_fetch_targets_only_662(self):
        seen = []
        def fake_fetch(url):
            seen.append(url)
            return {
                "number": 662,
                "state": "open",
                "title": "HERDR CONTROL",
                "html_url": "https://github.com/Bbambaaamm/dotacni-majak/issues/662",
                "body": "root",
            }
        self.intake.fetch_json = fake_fetch
        issues = self.intake.fetch_issues(self.majak_consumer())
        self.assertEqual([row["number"] for row in issues], [662])
        self.assertEqual(
            seen,
            ["https://api.github.com/repos/Bbambaaamm/dotacni-majak/issues/662"],
        )

    def test_closed_majak_root_is_not_returned(self):
        self.intake.fetch_json = lambda _url: {"number": 662, "state": "closed"}
        self.assertEqual(self.intake.fetch_issues(self.majak_consumer()), [])

    def test_majak_root_rejects_malformed_mismatched_or_pr_responses(self):
        bad = [
            {},
            {"number": 663, "state": "open"},
            {"number": 662, "state": "mystery"},
            {"number": 662, "state": "open", "pull_request": {}},
        ]
        for payload in bad:
            with self.subTest(payload=payload):
                self.intake.fetch_json = lambda _url, value=payload: value
                with self.assertRaises(RuntimeError):
                    self.intake.fetch_issues(self.majak_consumer())

    def test_herdr_root_fetch_targets_only_53(self):
        seen = []

        def fake_fetch(url):
            seen.append(url)
            return {
                "number": 53,
                "state": "open",
                "title": "HERDR CONTROL: autonomous backlog drain",
                "html_url": "https://github.com/Bbambaaamm/herdr/issues/53",
                "body": "root",
            }

        self.intake.fetch_json = fake_fetch
        issues = self.intake.fetch_issues(self.herdr_consumer())
        self.assertEqual([row["number"] for row in issues], [53])
        self.assertEqual(
            seen,
            ["https://api.github.com/repos/Bbambaaamm/herdr/issues/53"],
        )

    def test_queue_herdr_root_carries_backlog_drain_contract(self):
        issue = {
            "number": 53,
            "title": "HERDR CONTROL: autonomous backlog drain",
            "body": "Drain Herdr safely",
            "html_url": "https://github.com/Bbambaaamm/herdr/issues/53",
        }
        task_id = self.intake.queue_issue(self.herdr_consumer(), issue, [])
        task = json.loads((self.intake.PENDING / f"{task_id}.json").read_text())
        self.assertTrue(task_id.startswith("github-herdr-issue-53-"))
        self.assertEqual(task["kind"], "github_root_orchestration")
        self.assertEqual(task["repo"], "Bbambaaamm/herdr")
        self.assertEqual(task["workspace"], "/home/agentops/workspaces/herdr")
        self.assertEqual(task["safety_profile"], "herdr-core")
        self.assertEqual(task["hermes_profile"], "quantlab")
        self.assertEqual(task["agent"], "herdr-hermes")
        self.assertEqual(task["coordinator_agent"], "herdr-hermes")
        self.assertEqual(task["priority"], 60)
        self.assertIn("autonomous backlog-drain", task["prompt"])
        self.assertIn("ACCEPTANCE_GATE", task["prompt"])
        self.assertIn("Do not flatten", task["prompt"])
        self.assertNotIn("/home/agentops/worktrees/herdr/", task["prompt"])
        self.assertIn("/home/agentops/workspaces/herdr/worktrees/", task["prompt"])

    def test_queue_majak_root_carries_explicit_consumer_identity(self):
        issue = {
            "number": 662,
            "title": "HERDR CONTROL",
            "body": "Finish Majak",
            "html_url": "https://github.com/Bbambaaamm/dotacni-majak/issues/662",
        }
        task_id = self.intake.queue_issue(self.majak_consumer(), issue, [])
        task = json.loads((self.intake.PENDING / f"{task_id}.json").read_text())
        self.assertTrue(task_id.startswith("github-majak-issue-662-"))
        self.assertEqual(task["kind"], "github_root_orchestration")
        self.assertEqual(task["repo"], "Bbambaaamm/dotacni-majak")
        self.assertEqual(task["workspace"], "/home/agentops/workspaces/dotacni-majak")
        self.assertEqual(task["safety_profile"], "dotacni-majak")
        self.assertEqual(task["hermes_profile"], "majak")
        self.assertEqual(task["agent"], "dotacni-majak-hermes")
        self.assertEqual(task["coordinator_agent"], "dotacni-majak-hermes")
        self.assertEqual(task["priority"], 60)
        self.assertIn("control-plane root", task["prompt"])
        self.assertIn("Do not flatten", task["prompt"])

    def test_repo_scoped_prior_evidence_does_not_cross_consumers(self):
        qtask = {
            "id": "q45",
            "issue": 45,
            "repo": "Bbambaaamm/Autonomous-Quant-Lab",
        }
        mtask = {
            "id": "m45",
            "issue": 45,
            "repo": "Bbambaaamm/dotacni-majak",
        }
        qpath = self.intake.DONE = self.intake.ROOT / "done"
        (self.intake.RESULTS / "q45.json").write_text(
            json.dumps({"summary": "quant evidence"}), encoding="utf-8"
        )
        (self.intake.RESULTS / "m45.json").write_text(
            json.dumps({"summary": "majak evidence"}), encoding="utf-8"
        )
        for task in (qtask, mtask):
            path = self.intake.ROOT / "done" / f"{task['id']}.json"
            path.write_text(json.dumps(task), encoding="utf-8")
        indexed = self.intake.task_index()
        qprior = self.intake.prior_evidence(
            indexed["Bbambaaamm/Autonomous-Quant-Lab#45"]
        )
        mprior = self.intake.prior_evidence(
            indexed["Bbambaaamm/dotacni-majak#45"]
        )
        self.assertIn("quant evidence", qprior)
        self.assertNotIn("majak evidence", qprior)
        self.assertIn("majak evidence", mprior)
        self.assertNotIn("quant evidence", mprior)


    def test_prior_evidence_preserves_latest_failed_task_error_without_result(self):
        failed_path = self.intake.ROOT / "failed" / "root-failed-evidence.json"
        failed_path.write_text(
            json.dumps({
                "id": "root-failed-evidence",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
                "last_error": "provider startup failed",
            }),
            encoding="utf-8",
        )
        records = self.intake.task_index()["Bbambaaamm/dotacni-majak#662"]
        prior = json.loads(self.intake.prior_evidence(records))
        self.assertEqual(prior["previous_task"], "root-failed-evidence")
        self.assertEqual(prior["previous_state"], "failed")
        self.assertEqual(prior["last_error"], "provider startup failed")

    def test_root_orchestrator_replans_after_noninteractive_failed_task(self):
        failed_path = self.intake.ROOT / "failed" / "root-failed.json"
        failed_path.write_text(
            json.dumps({
                "id": "root-failed",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
                "last_error": "executor crashed",
            }),
            encoding="utf-8",
        )
        records = self.intake.task_index()["Bbambaaamm/dotacni-majak#662"]
        self.assertIsNone(
            self.intake.intervention_blocker(records, allow_failed_replan=True)
        )
        task_id, blocker = self.intake.intervention_blocker(
            records, allow_failed_replan=False
        )
        self.assertEqual(task_id, "root-failed")
        self.assertEqual(blocker, "executor crashed")

    def test_root_orchestrator_still_stops_on_human_blocker(self):
        blocked_path = self.intake.ROOT / "blocked" / "root-human.json"
        blocked_path.write_text(
            json.dumps({
                "id": "root-human",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
            }),
            encoding="utf-8",
        )
        (self.intake.RESULTS / "root-human.json").write_text(
            json.dumps({"blocker": "user_action_required"}),
            encoding="utf-8",
        )
        records = self.intake.task_index()["Bbambaaamm/dotacni-majak#662"]
        self.assertEqual(
            self.intake.intervention_blocker(records, allow_failed_replan=True),
            ("root-human", "user_action_required"),
        )


    def _root_issue(self):
        return {
            "number": 662,
            "state": "open",
            "title": "HERDR CONTROL",
            "html_url": "https://github.com/Bbambaaamm/dotacni-majak/issues/662",
            "body": "root",
            "updated_at": "2026-09-29T06:00:00Z",
        }

    def _run_main_with_majak(self):
        self.write_config([self.majak_consumer()])
        self.intake.fetch_issues = lambda _consumer: [self._root_issue()]
        original_argv = list(self.intake.sys.argv)
        try:
            self.intake.sys.argv = ["agent-github-intake", "--force"]
            return self.intake.main()
        finally:
            self.intake.sys.argv = original_argv

    def test_main_does_not_duplicate_active_majak_root(self):
        running = self.intake.ROOT / "running" / "root-active.json"
        running.write_text(
            json.dumps({
                "id": "root-active",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
                "agent": "dotacni-majak-hermes",
            }),
            encoding="utf-8",
        )
        self.assertEqual(self._run_main_with_majak(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        state = json.loads(self.intake.STATE.read_text(encoding="utf-8"))
        row = state["Bbambaaamm/dotacni-majak#662"]
        self.assertEqual(row["scheduler_state"], "active")
        self.assertEqual(row["task_ids"], ["root-active"])

    def test_main_respects_cooldown_for_completed_majak_root(self):
        done = self.intake.ROOT / "done" / "root-done.json"
        done.write_text(
            json.dumps({
                "id": "root-done",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
                "agent": "dotacni-majak-hermes",
            }),
            encoding="utf-8",
        )
        self.assertEqual(self._run_main_with_majak(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        state = json.loads(self.intake.STATE.read_text(encoding="utf-8"))
        self.assertEqual(
            state["Bbambaaamm/dotacni-majak#662"]["scheduler_state"],
            "cooldown",
        )

    def test_main_requeues_old_technical_failure_for_majak_root(self):
        failed = self.intake.ROOT / "failed" / "root-old-failed.json"
        failed.write_text(
            json.dumps({
                "id": "root-old-failed",
                "issue": 662,
                "repo": "Bbambaaamm/dotacni-majak",
                "agent": "dotacni-majak-hermes",
                "last_error": "executor crashed",
            }),
            encoding="utf-8",
        )
        old = time.time() - self.intake.COOLDOWN_SECONDS - 10
        import os
        os.utime(failed, (old, old))
        self.assertEqual(self._run_main_with_majak(), 0)
        pending = list(self.intake.PENDING.glob("github-majak-issue-662-*.json"))
        self.assertEqual(len(pending), 1)
        task = json.loads(pending[0].read_text(encoding="utf-8"))
        self.assertEqual(task["agent"], "dotacni-majak-hermes")
        state = json.loads(self.intake.STATE.read_text(encoding="utf-8"))
        self.assertEqual(
            state["Bbambaaamm/dotacni-majak#662"]["scheduler_state"],
            "queued",
        )


    def test_main_never_replans_pending_verification_as_another_work_episode(self):
        path = self.intake.ROOT / "blocked" / "verification-pending.json"
        path.write_text(json.dumps({
            "id": "verification-pending", "issue": 662, "repo": "Bbambaaamm/dotacni-majak",
            "attempt_state": "verification_pending", "verification_status": "evidence_unavailable",
            "run_token": "stable-run", "attempts": 1,
        }))
        self.assertEqual(self._run_main_with_majak(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        state = json.loads(self.intake.STATE.read_text())
        self.assertEqual(state["Bbambaaamm/dotacni-majak#662"]["scheduler_state"], "blocked")
        self.assertEqual(state["Bbambaaamm/dotacni-majak#662"]["blocker"],
                         "durable_task_requires_reconciliation")
        records = self.intake.task_index()["Bbambaaamm/dotacni-majak#662"]
        self.assertEqual(self.intake.intervention_blocker(records, allow_failed_replan=True),
                         ("verification-pending", "evidence_unavailable"))



    def _run_main_with_herdr(self):
        self.write_config([self.herdr_consumer()])
        self.intake.fetch_issues = lambda _consumer: [{
            "number": 53, "state": "open",
            "title": "HERDR CONTROL: autonomous backlog drain",
            "html_url": "https://github.com/Bbambaaamm/herdr/issues/53",
            "body": "Drain only with admission and existing cost grant",
        }]
        original_argv = list(self.intake.sys.argv)
        try:
            self.intake.sys.argv = ["agent-github-intake", "--force"]
            return self.intake.main()
        finally:
            self.intake.sys.argv = original_argv

    def test_blocked_herdr_root_stays_blocked_and_does_not_duplicate(self):
        blocked = self.intake.ROOT / "blocked" / "root-53-original.json"
        original = {
            "id": "root-53-original", "issue": 53,
            "repo": "Bbambaaamm/herdr", "consumer": "herdr",
            "attempt_state": "blocked",
            "watchdog_blocker": "delivery_uncertain_requires_recovery",
            "run_token": "original-run", "attempts": 3, "max_attempts": 3,
        }
        blocked.write_text(json.dumps(original))
        before = blocked.read_bytes()
        self.intake.disk_headroom_blocker = lambda *_: None
        for _ in range(2):
            self.assertEqual(self._run_main_with_herdr(), 0)
            self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
            self.assertEqual(before, blocked.read_bytes())
            state = json.loads(self.intake.STATE.read_text())
            root = state["Bbambaaamm/herdr#53"]
            self.assertEqual(root["scheduler_state"], "blocked")
            self.assertEqual(root["blocker"], "delivery_uncertain_requires_recovery")
            self.assertEqual(root["task_ids"], ["root-53-original"])
            self.assertEqual(root["task_id"], "root-53-original")

    def test_herdr_capacity_gate_auto_recovers_for_new_eligible_episode(self):
        self.intake.disk_headroom_blocker = (
            lambda *_: "autonomy_disk_headroom_insufficient"
        )
        self.assertEqual(self._run_main_with_herdr(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        state = json.loads(self.intake.STATE.read_text())
        self.assertEqual(state["Bbambaaamm/herdr#53"]["scheduler_state"], "blocked")
        self.assertEqual(state["Bbambaaamm/herdr#53"]["blocker"],
                         "autonomy_disk_headroom_insufficient")

        # A later scheduler tick can create one new root only after the capacity
        # gate has cleared; no prior blocked/running task exists in this fixture.
        self.intake.disk_headroom_blocker = lambda *_: None
        self.assertEqual(self._run_main_with_herdr(), 0)
        pending = list(self.intake.PENDING.glob("github-herdr-issue-53-*.json"))
        self.assertEqual(len(pending), 1)
        task = json.loads(pending[0].read_text())
        self.assertEqual(task["kind"], "github_root_orchestration")
        self.assertEqual(task["issue"], 53)
        self.assertEqual(task["agent"], "herdr-hermes")
        self.assertEqual(self._run_main_with_herdr(), 0)
        self.assertEqual(len(list(self.intake.PENDING.glob("*.json"))), 1)


if __name__ == "__main__":
    unittest.main()
