import importlib.machinery
import importlib.util
import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent-github-intake"


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
            "priority_default": 10,
            "priority_architecture": 10,
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

    def test_registry_enables_quantlab_and_majak_but_not_disabled_heating(self):
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
        self.write_config([self.quantlab_consumer(), self.majak_consumer(), heating])
        consumers = self.intake.load_consumers()
        self.assertEqual([row["consumer"] for row in consumers], ["quantlab", "majak"])

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
        self.assertEqual(task["priority"], 10)
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


if __name__ == "__main__":
    unittest.main()
