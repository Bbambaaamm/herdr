import importlib.machinery
import importlib.util
import copy
import io
import json
import subprocess
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
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
        self.clock = datetime(2026, 10, 20, 12, 0, tzinfo=timezone.utc)
        self.intake.now = lambda: self.clock
        self.api_calls = []
        self.real_fetch_json = self.intake.fetch_json
        self.repository_rows = {}
        self.issue_rows = {}
        self.comment_rows = {}
        self.permission_role = ("maintain", "write")
        self.authenticated = {"id": 900, "login": "intake-reader", "type": "User"}
        for repo, number, title, body in [
            ("Bbambaaamm/herdr", 53, "HERDR CONTROL: autonomous backlog drain", "Drain Herdr safely"),
            ("Bbambaaamm/dotacni-majak", 662, "HERDR CONTROL", "Finish Majak"),
            ("Bbambaaamm/Autonomous-Quant-Lab", 45, "Synthetic authorized issue", "Bounded work"),
        ]:
            api = f"https://api.github.com/repos/{repo}"
            repository = {"id": number + 1000, "full_name": repo}
            issue = {"id": number + 10000, "number": number, "state": "open", "title": title,
                     "body": body, "repository_url": api, "url": f"{api}/issues/{number}",
                     "html_url": f"https://github.com/{repo}/issues/{number}", "comments": 1,
                     "created_at": (self.clock - timedelta(days=1)).isoformat(),
                     "updated_at": (self.clock - timedelta(minutes=1)).isoformat()}
            approval = {"action": "approve", "repository": repo, "issue_number": number,
                        "issue_id": issue["id"], "content_sha256": self.intake.issue_revision(repo, repository, issue),
                        "expires_at": (self.clock + timedelta(minutes=30)).isoformat()}
            comment = {"id": 42, "body": self.intake.APPROVAL_MARKER + json.dumps(approval),
                       "issue_url": issue["url"], "user": {"id": 500, "login": "maintainer", "type": "User"},
                       "created_at": (self.clock - timedelta(seconds=30)).isoformat(),
                       "updated_at": (self.clock - timedelta(seconds=30)).isoformat()}
            self.repository_rows[repo] = repository
            self.issue_rows[repo] = issue
            self.comment_rows[repo] = [comment]
        self.intake.fetch_json = self.fake_api

    def fake_api(self, url):
        self.api_calls.append(url)
        if url == "https://api.github.com/user":
            return copy.deepcopy(self.authenticated)
        for repo, issue in self.issue_rows.items():
            api = f"https://api.github.com/repos/{repo}"
            number = {"Bbambaaamm/herdr": 53, "Bbambaaamm/dotacni-majak": 662,
                      "Bbambaaamm/Autonomous-Quant-Lab": 45}[repo]
            issue_url = f"{api}/issues/{number}"
            if url == api:
                return copy.deepcopy(self.repository_rows[repo])
            if url == issue_url:
                return copy.deepcopy(issue)
            if url.startswith(issue_url + "/comments?per_page=100&page="):
                page = int(url.rsplit("=", 1)[1])
                return copy.deepcopy(self.comment_rows[repo][(page - 1) * 100:page * 100])
            if url == api + "/collaborators/maintainer/permission":
                role, permission = self.permission_role
                return {"role_name": role, "permission": permission,
                        "user": {"id": 500, "login": "maintainer", "type": "User"}}
        raise AssertionError("unregistered synthetic API path: " + url)


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
            "admission": {"signal": "maintainer-comment-v1", "max_age_seconds": 86400},
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
            "admission": {"signal": "maintainer-comment-v1", "max_age_seconds": 86400},
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
            "admission": {"signal": "maintainer-comment-v1", "max_age_seconds": 86400},
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
        self.assertEqual(state["Bbambaaamm/dotacni-majak#662"]["scheduler_state"], "active")
        records = self.intake.task_index()["Bbambaaamm/dotacni-majak#662"]
        self.assertEqual(self.intake.intervention_blocker(records, allow_failed_replan=True),
                         ("verification-pending", "evidence_unavailable"))



    def assert_no_authorized_queue(self, consumer=None):
        consumer = consumer or self.herdr_consumer()
        issue = self.issue_rows[consumer["repository"]]
        with self.assertRaises(self.intake.AdmissionDenied):
            self.intake.queue_issue(consumer, issue, [])
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])

    def test_explicit_maintainer_approval_binds_the_complete_current_revision(self):
        consumer = self.herdr_consumer()
        task_id = self.intake.queue_issue(consumer, {"number": 53}, [])
        task = json.loads((self.intake.PENDING / (task_id + ".json")).read_bytes())
        self.assertEqual(task_id, "github-herdr-issue-53-approval-42")
        self.assertEqual(task["github_admission"]["approver_user_id"], 500)
        self.assertEqual(task["github_admission"]["content_sha256"], self.intake.issue_revision(
            consumer["repository"], self.repository_rows[consumer["repository"]], self.issue_rows[consumer["repository"]]))
        self.assertEqual(self.api_calls[0], "https://api.github.com/user")
        self.assertEqual(sum(path == self.issue_rows[consumer["repository"]]["url"] for path in self.api_calls), 2)

    def test_author_identity_and_forged_label_alone_are_never_admission(self):
        issue = self.issue_rows["Bbambaaamm/herdr"]
        issue["user"] = {"id": 500, "login": "maintainer", "type": "User"}
        issue["labels"] = [{"name": "approved"}, {"name": "herdr-approved"}]
        issue["comments"] = 0
        self.comment_rows["Bbambaaamm/herdr"] = []
        self.assert_no_authorized_queue()

    def test_forged_author_association_and_write_permission_are_not_maintainer_control(self):
        self.comment_rows["Bbambaaamm/herdr"][0]["author_association"] = "OWNER"
        for role in [("write", "write"), ("triage", "read"), ("admin", "read"), ("unknown", "admin")]:
            with self.subTest(role=role):
                self.permission_role = role
                self.assert_no_authorized_queue()

    def test_issue_content_edit_after_approval_is_denied(self):
        self.issue_rows["Bbambaaamm/herdr"]["body"] += "\nChanged after approval"
        self.assert_no_authorized_queue()

    def test_changed_revision_time_even_for_unchanged_content_is_denied(self):
        self.issue_rows["Bbambaaamm/herdr"]["updated_at"] = self.clock.isoformat()
        self.assert_no_authorized_queue()

    def test_changed_during_permission_check_is_denied_before_queue(self):
        original = self.intake.fetch_json
        reads = 0
        def changed(url):
            nonlocal reads
            value = original(url)
            if url == self.issue_rows["Bbambaaamm/herdr"]["url"]:
                reads += 1
                if reads == 2:
                    value["title"] += " changed"
            return value
        self.intake.fetch_json = changed
        self.assert_no_authorized_queue()

    def test_edited_or_expired_or_unbounded_approval_is_denied(self):
        original = copy.deepcopy(self.comment_rows["Bbambaaamm/herdr"][0])
        for variation in ("edited", "expired", "unbounded"):
            with self.subTest(variation=variation):
                comment = copy.deepcopy(original)
                if variation == "edited":
                    comment["updated_at"] = self.clock.isoformat()
                else:
                    body = json.loads(comment["body"][len(self.intake.APPROVAL_MARKER):])
                    body["expires_at"] = (self.clock + timedelta(days=2) if variation == "unbounded"
                                          else self.clock - timedelta(seconds=1)).isoformat()
                    comment["body"] = self.intake.APPROVAL_MARKER + json.dumps(body)
                self.comment_rows["Bbambaaamm/herdr"] = [comment]
                self.assert_no_authorized_queue()

    def test_latest_trusted_rejection_does_not_fall_back_to_old_approval(self):
        revoke = copy.deepcopy(self.comment_rows["Bbambaaamm/herdr"][0]);revoke["id"] = 43
        payload = json.loads(revoke["body"][len(self.intake.APPROVAL_MARKER):]);payload["action"] = "revoke"
        revoke["body"] = self.intake.APPROVAL_MARKER + json.dumps(payload)
        self.comment_rows["Bbambaaamm/herdr"].append(revoke)
        self.issue_rows["Bbambaaamm/herdr"]["comments"] = 2
        self.assert_no_authorized_queue()

    def test_approval_wrong_repo_issue_id_number_or_digest_is_denied(self):
        original = copy.deepcopy(self.comment_rows["Bbambaaamm/herdr"][0])
        for field, value in [("repository", "attacker/other"), ("issue_number", 54), ("issue_id", 999),
                             ("content_sha256", "0" * 64), ("action", "anything")]:
            with self.subTest(field=field):
                comment = copy.deepcopy(original);payload = json.loads(comment["body"][len(self.intake.APPROVAL_MARKER):])
                payload[field] = value;comment["body"] = self.intake.APPROVAL_MARKER + json.dumps(payload)
                self.comment_rows["Bbambaaamm/herdr"] = [comment]
                self.assert_no_authorized_queue()

    def test_replayed_admission_after_terminal_state_does_not_schedule_again(self):
        self.assertEqual(self._run_main_with_majak(), 0)
        pending = next(self.intake.PENDING.glob("*.json"))
        done = self.intake.ROOT / "done" / pending.name;pending.rename(done)
        old = time.time() - self.intake.COOLDOWN_SECONDS - 10
        import os
        os.utime(done, (old, old))
        before = done.read_bytes()
        self.assertEqual(self._run_main_with_majak(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        self.assertEqual(done.read_bytes(), before)
        self.assertEqual(json.loads(self.intake.STATE.read_bytes())["Bbambaaamm/dotacni-majak#662"]["scheduler_state"], "admission_replayed")

    def test_existing_state_keeps_consumed_approval_even_when_task_materialization_is_absent(self):
        self.assertEqual(self._run_main_with_majak(), 0)
        for path in self.intake.PENDING.glob("*.json"):
            path.unlink()  # Only this disposable test's private queue.
        self.assertEqual(self._run_main_with_majak(), 0)
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])

    def test_same_approval_direct_replay_is_exclusive_and_unchanged(self):
        consumer = self.herdr_consumer();issue = self.issue_rows[consumer["repository"]]
        first = self.intake.queue_issue(consumer, issue, []);path = self.intake.PENDING / (first + ".json")
        before = path.read_bytes();self.assertEqual(self.intake.queue_issue(consumer, issue, []), first)
        self.assertEqual(path.read_bytes(), before);self.assertEqual(len(list(self.intake.PENDING.glob("*.json"))), 1)

    def test_incomplete_issue_and_unknown_closed_state_are_denied(self):
        original = copy.deepcopy(self.issue_rows["Bbambaaamm/herdr"])
        for field in ("id", "number", "title", "body", "comments", "created_at", "updated_at", "url", "repository_url", "html_url"):
            with self.subTest(field=field):
                value = copy.deepcopy(original);value.pop(field);self.issue_rows["Bbambaaamm/herdr"] = value
                self.assert_no_authorized_queue()
        for state in ("closed", "unknown", None):
            value = copy.deepcopy(original);value["state"] = state;self.issue_rows["Bbambaaamm/herdr"] = value
            self.assert_no_authorized_queue()

    def test_missing_authentication_or_incomplete_authenticated_user_fails_closed(self):
        for value in ({}, {"id": 1}, {"id": True, "login": "user", "type": "User"}):
            with self.subTest(value=value):
                self.authenticated = value;self.assert_no_authorized_queue()

    def test_incomplete_or_malformed_pagination_never_uses_partial_approval(self):
        self.issue_rows["Bbambaaamm/herdr"]["comments"] = 101
        self.assert_no_authorized_queue()
        self.issue_rows["Bbambaaamm/herdr"]["comments"] = 1
        self.comment_rows["Bbambaaamm/herdr"][0].pop("issue_url")
        self.assert_no_authorized_queue()

    def test_complete_pagination_can_find_trusted_approval_on_second_page(self):
        approval = copy.deepcopy(self.comment_rows["Bbambaaamm/herdr"][0]);approval["id"] = 101
        rows = []
        for number in range(1, 101):
            comment = copy.deepcopy(approval);comment["id"] = number;comment["body"] = "Ordinary untrusted discussion"
            rows.append(comment)
        self.comment_rows["Bbambaaamm/herdr"] = rows + [approval]
        self.issue_rows["Bbambaaamm/herdr"]["comments"] = 101
        self.intake.queue_issue(self.herdr_consumer(), {"number": 53}, [])
        self.assertTrue(any(url.endswith("page=2") for url in self.api_calls))

    def test_gh_guard_transport_has_no_anonymous_or_direct_http_fallback(self):
        with patch.object(self.intake.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"", b"authentication unavailable")) as run:
            self.intake.fetch_json = self.real_fetch_json
            self.assert_no_authorized_queue()
            self.assertEqual(run.call_args.args[0], ["gh", "api", "--hostname", "github.com", "--method", "GET", "user"])
            self.assertIs(run.call_args.kwargs["stdin"], subprocess.DEVNULL)
        with patch.object(self.intake.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, b'{"id":1,"id":2}', b"")):
            with self.assertRaises(self.intake.AdmissionDenied):self.real_fetch_json("https://api.github.com/user")

    def test_malformed_http_json_and_empty_eof_fail_closed(self):
        for body in (b"", b"{", b"null", b"[]"):
            with self.subTest(body=body),patch.object(self.intake.subprocess, "run", return_value=subprocess.CompletedProcess([], 0, body, b"")):
                self.intake.fetch_json = self.real_fetch_json
                self.assert_no_authorized_queue()

    def test_registry_missing_admission_policy_is_denied(self):
        consumer = self.herdr_consumer();consumer.pop("admission")
        self.write_config([consumer]);payload = json.loads(self.intake.CONFIG.read_bytes())
        payload["consumers"][0].pop("admission", None);self.intake.CONFIG.write_text(json.dumps(payload))
        with self.assertRaisesRegex(RuntimeError, "trusted admission policy"):
            self.intake.load_consumers()

    def test_corrupt_consumed_state_does_not_reset_admission_history(self):
        self.intake.STATE.write_text("{broken")
        self.assert_no_authorized_queue()



    def test_readonly_digest_helper_never_creates_state_stamp_or_task(self):
        self.write_config([self.herdr_consumer()])
        original = list(self.intake.sys.argv)
        output = io.StringIO()
        try:
            self.intake.sys.argv = ["agent-github-intake", "--approval-digest", "Bbambaaamm/herdr", "53"]
            with redirect_stdout(output):
                self.assertEqual(self.intake.main(), 0)
        finally:
            self.intake.sys.argv = original
        report = json.loads(output.getvalue())
        self.assertTrue(report["read_only"]);self.assertFalse(report["task_created"])
        self.assertNotIn("Drain Herdr safely", output.getvalue())
        payload = json.loads(report["approval_body"][len(self.intake.APPROVAL_MARKER):])
        self.assertEqual(payload["content_sha256"], self.intake.issue_revision("Bbambaaamm/herdr", self.repository_rows["Bbambaaamm/herdr"], self.issue_rows["Bbambaaamm/herdr"]))
        self.assertEqual(list(self.intake.PENDING.glob("*.json")), [])
        self.assertFalse(self.intake.STATE.exists());self.assertFalse(self.intake.STAMP.exists())

    def test_permission_identity_mismatch_cannot_use_maintainer_role(self):
        original = self.intake.fetch_json
        def mismatch(url):
            value = original(url)
            if url.endswith("/permission"):
                value["user"]["id"] = 501
            return value
        self.intake.fetch_json = mismatch
        self.assert_no_authorized_queue()

    def test_duplicate_approval_fields_are_rejected(self):
        comment = self.comment_rows["Bbambaaamm/herdr"][0]
        payload = comment["body"][len(self.intake.APPROVAL_MARKER):]
        comment["body"] = self.intake.APPROVAL_MARKER + payload[:-1] + ', "action": "approve"}'
        self.assert_no_authorized_queue()

if __name__ == "__main__":
    unittest.main()
