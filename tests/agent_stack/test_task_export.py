import importlib.machinery
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[2] / "agent-stack" / "bin" / "agent-task-export"


def load_module():
    loader = importlib.machinery.SourceFileLoader("herdr_task_export_test", str(SCRIPT))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class TaskExportTests(unittest.TestCase):
    def setUp(self):
        self.exporter = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "tasks"
        for name in ("pending", "running", "blocked", "failed", "done", "results"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.exporter.ROOT = self.root
        self.exporter.INTAKE = self.root / "github-intake-state.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_intake_state_reads_legacy_and_repo_scoped_keys(self):
        self.exporter.INTAKE.write_text(
            json.dumps(
                {
                    "45": {
                        "open": True,
                        "title": "Legacy Quant",
                        "scheduler_state": "active",
                    },
                    "Bbambaaamm/dotacni-majak#45": {
                        "open": True,
                        "repo": "Bbambaaamm/dotacni-majak",
                        "issue": 45,
                        "title": "Majak 45",
                        "scheduler_state": "queued",
                    },
                }
            ),
            encoding="utf-8",
        )
        state = self.exporter.intake_state()
        self.assertEqual(
            state[("Bbambaaamm/Autonomous-Quant-Lab", 45)]["title"],
            "Legacy Quant",
        )
        self.assertEqual(
            state[("Bbambaaamm/dotacni-majak", 45)]["scheduler_state"],
            "queued",
        )

    def test_rows_keep_same_issue_number_isolated_by_repository(self):
        self.exporter.INTAKE.write_text(
            json.dumps(
                {
                    "Bbambaaamm/Autonomous-Quant-Lab#45": {
                        "open": True,
                        "repo": "Bbambaaamm/Autonomous-Quant-Lab",
                        "issue": 45,
                        "title": "Quant 45",
                        "scheduler_state": "active",
                    },
                    "Bbambaaamm/dotacni-majak#45": {
                        "open": True,
                        "repo": "Bbambaaamm/dotacni-majak",
                        "issue": 45,
                        "title": "Majak 45",
                        "scheduler_state": "queued",
                    },
                }
            ),
            encoding="utf-8",
        )
        tasks = [
            {
                "id": "quant-45",
                "repo": "Bbambaaamm/Autonomous-Quant-Lab",
                "issue": 45,
                "agent": "quantlab-hermes",
                "kind": "github_issue_slice",
                "attempts": 0,
                "max_attempts": 4,
            },
            {
                "id": "majak-45",
                "repo": "Bbambaaamm/dotacni-majak",
                "issue": 45,
                "agent": "dotacni-majak-hermes",
                "kind": "github_root_orchestration",
                "attempts": 0,
                "max_attempts": 4,
            },
        ]
        for task in tasks:
            (self.root / "pending" / f"{task['id']}.json").write_text(
                json.dumps(task), encoding="utf-8"
            )

        rows = {row["task_id"]: row for row in self.exporter.rows()}
        self.assertEqual(rows["quant-45"]["issue_title"], "Quant 45")
        self.assertEqual(rows["quant-45"]["scheduler_state"], "active")
        self.assertEqual(rows["majak-45"]["issue_title"], "Majak 45")
        self.assertEqual(rows["majak-45"]["scheduler_state"], "queued")
        self.assertEqual(rows["majak-45"]["repo"], "Bbambaaamm/dotacni-majak")
        self.assertEqual(rows["majak-45"]["agent"], "dotacni-majak-hermes")

    def test_majak_missing_or_malformed_coordinator_fails_closed_but_legacy_quantlab_defaults(self):
        self.exporter.INTAKE.write_text("{}", encoding="utf-8")
        tasks = [
            {
                "id": "legacy-quant-no-agent",
                "issue": 9,
            },
            {
                "id": "majak-no-agent",
                "repo": "Bbambaaamm/dotacni-majak",
                "issue": 662,
            },
            {
                "id": "majak-malformed-agent",
                "repo": "Bbambaaamm/dotacni-majak",
                "issue": 662,
                "agent": "bad agent with spaces",
            },
        ]
        for task in tasks:
            (self.root / "pending" / f"{task['id']}.json").write_text(
                json.dumps(task), encoding="utf-8"
            )
        rows = {row["task_id"]: row for row in self.exporter.rows()}
        self.assertIn("legacy-quant-no-agent", rows)
        self.assertEqual(rows["legacy-quant-no-agent"]["agent"], "quantlab-hermes")
        self.assertNotIn("majak-no-agent", rows)
        self.assertNotIn("majak-malformed-agent", rows)

    def test_unknown_repo_or_wrong_coordinator_is_fail_closed(self):
        self.exporter.INTAKE.write_text("{}", encoding="utf-8")
        bad = [
            {
                "id": "unknown",
                "repo": "example/unknown",
                "issue": 1,
                "agent": "unknown-hermes",
            },
            {
                "id": "wrong-parent",
                "repo": "Bbambaaamm/dotacni-majak",
                "issue": 662,
                "agent": "quantlab-hermes",
            },
        ]
        for task in bad:
            (self.root / "pending" / f"{task['id']}.json").write_text(
                json.dumps(task), encoding="utf-8"
            )
        self.assertEqual(self.exporter.rows(), [])


if __name__ == "__main__":
    unittest.main()
