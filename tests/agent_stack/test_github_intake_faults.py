"""Fault/deadline regressions use only the existing disposable intake fixture."""
import ast
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import time
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('_intake_base_tests', Path(__file__).with_name('test_github_intake.py'))
_base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(_base)


class IntakeFollowupTests(_base.GitHubIntakeTests):
    def tearDown(self):
        self.intake._SCAN_DEADLINE = None
        self.intake._SCAN_USER = None
        super().tearDown()

    def test_actual_queue_write_failure_never_exposes_partial_final_task(self):
        original = self.intake.os.fdopen
        class PartialWriter:
            def __init__(self, fd, *args, **kwargs): self.handle = original(fd, *args, **kwargs)
            def __enter__(self): return self
            def __exit__(self, *args): return self.handle.__exit__(*args)
            def write(self, value):
                self.handle.write(value[:5]);self.handle.flush()
                raise OSError('injected queue write failure')
        with patch.object(self.intake.os, 'fdopen', PartialWriter), self.assertRaises(OSError):
            self.intake.queue_issue(self.herdr_consumer(), {'number': 53}, [])
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_retained_scalar_rows_and_invalid_keys_fail_closed_without_queue(self):
        key = 'Bbambaaamm/herdr#53'
        for value in ({key: None}, {key: False}, {key: []}, {'garbage': {}},
                      {'Bbambaaamm/herdr#0': {}}, {'Bbambaaamm/herdr#053': {}},
                      {'Bbambaaamm/herdr#53': {'repo': 'attacker/other'}},
                      {'Bbambaaamm/herdr#53': {'issue': 54}}):
            with self.subTest(value=value):
                self.intake.STATE.write_text(json.dumps(value))
                before = self.intake.STATE.read_bytes()
                with self.assertRaises(self.intake.AdmissionDenied):
                    self.intake.load_state()
                self.assertEqual(self.intake.STATE.read_bytes(), before)
                self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_unselected_closed_row_cannot_drop_malformed_consumed_history(self):
        self.intake.STATE.write_text(json.dumps({'old/repository#99': {'open': False, 'used_approvals': []}}))
        with self.assertRaises(self.intake.AdmissionDenied):
            self.intake.load_state()

    def test_duplicate_and_migrated_colliding_state_keys_deny(self):
        for text in ('{"Bbambaaamm/herdr#53":{},"Bbambaaamm/herdr#53":{}}',
                     '{"45":{},"Bbambaaamm/Autonomous-Quant-Lab#45":{}}'):
            self.intake.STATE.write_text(text)
            with self.assertRaises(self.intake.AdmissionDenied):
                self.intake.load_state()

    def task_and_path(self):
        task = {'id': 'github-herdr-issue-53-approval-42', 'github_admission': {'approval_id': 42}, 'prompt': 'synthetic'}
        return task, self.intake.PENDING / (task['id'] + '.json')

    def test_write_or_file_fsync_failure_never_publishes_final_json(self):
        task, path = self.task_and_path()
        for seam in ('write', 'fsync'):
            with self.subTest(seam=seam):
                if seam == 'write':
                    original = self.intake.os.fdopen
                    class PartialWriter:
                        def __init__(self, fd, *args, **kwargs): self.handle = original(fd, *args, **kwargs)
                        def __enter__(self): return self
                        def __exit__(self, *args): return self.handle.__exit__(*args)
                        def write(self, value):
                            self.handle.write(value[:5]);self.handle.flush()
                            raise OSError('injected write failure')
                    context = patch.object(self.intake.os, 'fdopen', PartialWriter)
                else:
                    context = patch.object(self.intake.os, 'fsync', side_effect=OSError('injected fsync failure'))
                with context, self.assertRaises(OSError):
                    self.intake.publish_task(path, task, task['github_admission'])
                self.assertFalse(path.exists())
                self.assertEqual(list(self.intake.PENDING.iterdir()), [])

    def test_rename_failure_cleans_only_temporary_and_preserves_existing_target(self):
        task, path = self.task_and_path()
        path.write_bytes(b'existing foreign bytes')
        with patch.object(self.intake, '_rename_exclusive', side_effect=OSError('injected rename failure')):
            with self.assertRaises(OSError):self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(path.read_bytes(), b'existing foreign bytes')
        self.assertEqual(list(self.intake.PENDING.iterdir()), [path])

    def test_linux_exclusive_atomic_publish_has_one_link_and_retains_collision(self):
        task, path = self.task_and_path()
        self.intake.publish_task(path, task, task['github_admission'])
        before = path.read_bytes();inode = path.stat().st_ino
        self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(path.stat().st_nlink, 1)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(json.loads(before), task)
        bad = dict(task);bad['github_admission'] = {'approval_id': 43}
        with self.assertRaises(self.intake.AdmissionDenied):self.intake.publish_task(path, bad, bad['github_admission'])
        self.assertEqual(path.read_bytes(), before)

    def test_retained_collision_replay_syncs_directory_and_preserves_final_on_failure(self):
        task, path = self.task_and_path()
        self.intake.publish_task(path, task, task['github_admission'])
        before = path.read_bytes();inode = path.stat().st_ino
        fsync = self.intake.os.fsync
        directory_calls = []
        def observe(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):directory_calls.append(fd)
            return fsync(fd)
        with patch.object(self.intake.os, 'fsync', side_effect=observe):
            self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(len(directory_calls), 1)
        def deny(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode):raise OSError('injected replay directory sync failure')
            return fsync(fd)
        with patch.object(self.intake.os, 'fsync', side_effect=deny), self.assertRaises(OSError):
            self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(list(self.intake.PENDING.iterdir()), [path])

    @unittest.skipUnless(hasattr(os, 'fork'), 'Linux process-death regression')
    def test_process_death_before_publication_leaves_no_dispatchable_partial(self):
        task, path = self.task_and_path()
        pid = os.fork()
        if pid == 0:
            self.intake._rename_exclusive = lambda *args: os._exit(77)
            self.intake.publish_task(path, task, task['github_admission'])
            os._exit(1)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 77)
        self.assertFalse(path.exists())
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])
        self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(json.loads(path.read_bytes()), task)

    @unittest.skipUnless(hasattr(os, 'fork'), 'Linux process-death regression')
    def test_death_at_directory_sync_leaves_complete_replayable_final(self):
        task, path = self.task_and_path()
        pid = os.fork()
        if pid == 0:
            fsync = self.intake.os.fsync
            def crash(fd):
                if stat.S_ISDIR(os.fstat(fd).st_mode):os._exit(78)
                return fsync(fd)
            self.intake.os.fsync = crash
            self.intake.publish_task(path, task, task['github_admission'])
            os._exit(1)
        _, status = os.waitpid(pid, 0)
        self.assertEqual(os.waitstatus_to_exitcode(status), 78)
        before = path.read_bytes();self.assertEqual(json.loads(before), task)
        self.intake.publish_task(path, task, task['github_admission'])
        self.assertEqual(path.read_bytes(), before)

    @unittest.skipUnless(hasattr(os, 'fork'), 'Linux exclusive concurrent publication')
    def test_concurrent_same_approval_publishes_exactly_one_complete_task(self):
        task, path = self.task_and_path()
        children = []
        for _ in range(2):
            pid = os.fork()
            if pid == 0:
                try:self.intake.publish_task(path, task, task['github_admission'])
                except Exception:os._exit(1)
                os._exit(0)
            children.append(pid)
        for pid in children:self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]), 0)
        self.assertEqual(json.loads(path.read_bytes()), task)
        self.assertEqual(path.stat().st_nlink, 1)
        self.assertEqual(len(list(self.intake.PENDING.glob('*.json'))), 1)

    def test_deadline_caps_each_gh_call_and_stops_before_next_call(self):
        self.intake._SCAN_DEADLINE = 124.0
        clock = [100.0]
        def run(*args, **kwargs):
            self.assertLessEqual(kwargs['timeout'], 5)
            clock[0] += kwargs['timeout']
            return subprocess.CompletedProcess([], 0, b'{}', b'')
        with patch.object(self.intake.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(self.intake.subprocess, 'run', side_effect=run) as process:
            for _ in range(4):self.real_fetch_json('https://api.github.com/user')
            with self.assertRaises(self.intake.ScanExpired):self.real_fetch_json('https://api.github.com/user')
            self.assertEqual(process.call_count, 5)
            self.assertEqual(clock[0], 124)

    def test_expired_scan_after_approval_never_publishes_a_task(self):
        self.intake._SCAN_DEADLINE = 124.0
        clock = [100.0]
        authorize = self.intake.approved_revision
        def late(*args):
            result = authorize(*args)
            clock[0] = 124.0
            return result
        with patch.object(self.intake.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(self.intake, 'approved_revision', side_effect=late):
            with self.assertRaises(self.intake.ScanExpired):
                self.intake.queue_issue(self.herdr_consumer(), {'number': 53}, [])
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_actual_child_timeout_uses_private_dummy_gh_and_no_network(self):
        dummy = self.intake.ROOT / 'dummy-bin';dummy.mkdir()
        gh = dummy / 'gh';gh.write_text('#!/bin/sh\nexec /bin/sleep 2\n');gh.chmod(0o700)
        self.intake._SCAN_DEADLINE = time.monotonic() + 0.05
        start = time.monotonic()
        with patch.dict(os.environ, {'PATH': str(dummy)}):
            with self.assertRaises(self.intake.ScanExpired):self.real_fetch_json('https://api.github.com/user')
        self.assertLess(time.monotonic() - start, 1)

    def test_partial_deadline_preserves_unvisited_history_and_rotates_issue(self):
        consumer = self.herdr_consumer();consumer['mode'] = 'all_open'
        key = 'Bbambaaamm/herdr#99';retained = {'used_approvals': {'42': 'github-herdr-issue-99-approval-42'}, 'open': True}
        self.intake.STATE.write_text(json.dumps({key: retained}))
        issues = [{'number': 53}, {'number': 54}];seen = [];clock = [1.0]
        def attempt(c, issue, *args):
            seen.append(issue['number']);clock[0] += 30
            raise self.intake.ScanExpired('intake-scan-deadline')
        with patch.object(self.intake.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(self.intake, 'fetch_issues', return_value=issues), patch.object(self.intake, '_scan_issue', side_effect=attempt):
            self.intake.scan_intake([consumer]);self.intake.scan_intake([consumer])
        self.assertEqual(seen, [53, 54])
        state = json.loads(self.intake.STATE.read_bytes())
        self.assertEqual(state[key]['used_approvals'], retained['used_approvals'])
        self.assertTrue(state[key]['open'])
        self.assertFalse(self.intake.STAMP.exists())
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_deadline_during_consumer_fetch_rotates_to_other_consumer(self):
        consumers = [self.herdr_consumer(), self.majak_consumer()];seen = [];clock = [1.0]
        def fetch(c):
            seen.append(c['repository']);clock[0] += 30
            raise self.intake.ScanExpired('intake-scan-deadline')
        with patch.object(self.intake.time, 'monotonic', side_effect=lambda: clock[0]), patch.object(self.intake, 'fetch_issues', side_effect=fetch):
            self.intake.scan_intake(consumers);self.intake.scan_intake(consumers)
        self.assertEqual(seen, [c['repository'] for c in consumers])

    def test_only_authenticated_identity_is_scan_cached_not_maintainer_permission(self):
        self.intake._SCAN_DEADLINE = time.monotonic() + 10
        self.intake.authenticated_user();self.intake.authenticated_user()
        self.assertEqual(self.api_calls.count('https://api.github.com/user'), 1)
        self.intake.approved_revision(self.herdr_consumer(), {'number': 53})
        self.permission_role = ('write', 'write')
        with self.assertRaises(self.intake.AdmissionDenied):self.intake.approved_revision(self.herdr_consumer(), {'number': 53})

    def test_runbook_is_in_both_release_and_canonical_selectors(self):
        root = Path(__file__).resolve().parents[2]
        name = 'docs/architecture/GITHUB_INTAKE_ADMISSION.md'
        for path, variable in [('herdr/release.py', 'PAYLOAD_PATHS'), ('scripts/refresh_source_manifest.py', 'FILES')]:
            tree = ast.parse((root / path).read_bytes())
            assignment = next(n.value for n in tree.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == variable for t in n.targets))
            value = [n.value for n in ast.walk(assignment) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
            self.assertIn(name, value)
        self.assertTrue((root / name).is_file())


    def test_removed_consumer_closes_row_without_losing_approval_history(self):
        retired = 'retired/repository#99'
        history = {'42': 'github-retired-issue-99-approval-42'}
        self.intake.STATE.write_text(json.dumps({retired: {'repo': 'retired/repository', 'issue': 99,
            'open': True, 'used_approvals': history, 'task_id': 'old-retained-task'}}))
        self._run_main_with_majak()
        row = json.loads(self.intake.STATE.read_bytes())[retired]
        self.assertFalse(row['open'])
        self.assertEqual(row['scheduler_state'], 'closed')
        self.assertEqual(row['used_approvals'], history)
        self.assertEqual(row['previous_task_id'], 'old-retained-task')

    def test_all_disabled_registry_is_close_only_without_authentication(self):
        key = 'Bbambaaamm/herdr#53'
        self.intake.STATE.write_text(json.dumps({key: {'open': True, 'used_approvals': {'42': 'github-herdr-issue-53-approval-42'}}}))
        self.write_config([])
        self.assertEqual(self.intake.load_consumers(), [])
        with patch.object(self.intake, 'authenticated_user', side_effect=AssertionError('no authentication for close-only')):
            self.assertEqual(self.intake.scan_intake([]), 0)
        row = json.loads(self.intake.STATE.read_bytes())[key]
        self.assertFalse(row['open'])
        self.assertTrue(row['retired_consumer'])
        self.assertEqual(row['used_approvals']['42'], 'github-herdr-issue-53-approval-42')

    def test_postrename_sync_failure_dispatcher_move_and_cooldown_cannot_reissue(self):
        consumer = self.herdr_consumer()
        fsync = self.intake.os.fsync
        def fail_pending_directory(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) and os.fstat(fd).st_ino == self.intake.PENDING.stat().st_ino:
                raise OSError('pending publication directory sync failed')
            return fsync(fd)
        with patch.object(self.intake.os, 'fsync', side_effect=fail_pending_directory), self.assertRaises(OSError):
            self.intake.queue_issue(consumer, {'number': 53}, [])
        pending = next(self.intake.PENDING.glob('*.json'))
        done = self.intake.ROOT / 'done' / pending.name
        pending.rename(done)  # Disposable dispatcher can claim immediately after rename.
        old = time.time() - self.intake.COOLDOWN_SECONDS - 10
        os.utime(done, (old, old))
        done.unlink()  # Completed disposable materialization pruned; durable admission must suffice.
        try:
            self.intake.queue_issue(consumer, {'number': 53}, [])
        except self.intake.AdmissionDenied:
            pass
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])
        row = self.intake.load_state()['Bbambaaamm/herdr#53']
        self.assertEqual(row['used_approvals']['42'], 'github-herdr-issue-53-approval-42')
        self.assertEqual(row['admission_intent']['state'], 'publication_pending')

    def test_intent_is_durable_before_publish_and_prepublish_failure_requires_reconciliation(self):
        consumer = self.herdr_consumer()
        def stop_before_exposure(path, task, admission):
            row = self.intake.load_state()['Bbambaaamm/herdr#53']
            self.assertEqual(row['used_approvals']['42'], task['id'])
            self.assertEqual(row['admission_intent']['state'], 'publication_pending')
            raise OSError('publication not attempted')
        with patch.object(self.intake, 'publish_task', side_effect=stop_before_exposure), self.assertRaises(OSError):
            self.intake.queue_issue(consumer, {'number': 53}, [])
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])
        for approval in (42, 43):
            self.comment_rows[consumer['repository']][0]['id'] = approval
            with self.assertRaisesRegex(self.intake.AdmissionDenied, 'reconciliation-required'):
                self.intake.queue_issue(consumer, {'number': 53}, [])
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_state_directory_sync_failure_prevents_pending_exposure(self):
        fsync = self.intake.os.fsync
        parent_inode = self.intake.STATE.parent.stat().st_ino
        def deny(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) and os.fstat(fd).st_ino == parent_inode:
                raise OSError('intent directory sync failure')
            return fsync(fd)
        with patch.object(self.intake.os, 'fsync', side_effect=deny), patch.object(self.intake, 'publish_task') as publish:
            with self.assertRaises(OSError):self.intake.queue_issue(self.herdr_consumer(), {'number': 53}, [])
        publish.assert_not_called()
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    def test_final_scan_snapshot_preserves_newly_persisted_published_intent(self):
        self.assertEqual(self._run_main_with_majak(), 0)
        row = self.intake.load_state()['Bbambaaamm/dotacni-majak#662']
        self.assertEqual(row['admission_intent']['state'], 'published')
        self.assertEqual(row['used_approvals']['42'], row['admission_intent']['task_id'])

    def test_pending_intent_survives_retirement_and_blocks_new_approval_when_reenabled(self):
        consumer = self.herdr_consumer()
        with patch.object(self.intake, 'publish_task', side_effect=OSError('before exposure')):
            with self.assertRaises(OSError):self.intake.queue_issue(consumer, {'number': 53}, [])
        self.intake.scan_intake([])
        row = self.intake.load_state()['Bbambaaamm/herdr#53']
        self.assertFalse(row['open'])
        self.assertEqual(row['admission_intent']['state'], 'publication_pending')
        self.comment_rows[consumer['repository']][0]['id'] = 43
        with self.assertRaisesRegex(self.intake.AdmissionDenied, 'reconciliation-required'):
            self.intake.queue_issue(consumer, {'number': 53}, [])

    def test_all_intent_rows_are_validated_including_retired_consumers(self):
        task_id = 'github-retired-issue-99-approval-42'
        valid = {'version': 1, 'approval_id': 42, 'task_id': task_id, 'content_sha256': 'a'*64, 'state': 'publication_pending'}
        for field, value in [('version', True), ('approval_id', 43), ('task_id', 'wrong'),
                             ('content_sha256', 'wrong'), ('state', 'unknown')]:
            with self.subTest(field=field):
                intent = dict(valid);intent[field] = value
                self.intake.STATE.write_text(json.dumps({'retired/repository#99': {'open': False,
                    'used_approvals': {'42': task_id}, 'admission_intent': intent}}))
                with self.assertRaises(self.intake.AdmissionDenied):self.intake.load_state()

    @unittest.skipUnless(hasattr(os, 'fork'), 'actual cross-process intake flock')
    def test_inherited_process_cannot_reuse_parent_lock_ownership(self):
        consumer = self.herdr_consumer()
        with self.intake.intake_lock():
            pid = os.fork()
            if pid == 0:
                try:self.intake.queue_issue(consumer, {'number': 53}, [])
                except self.intake.AdmissionDenied as exc:os._exit(0 if str(exc) == 'intake-already-running' else 2)
                except Exception:os._exit(3)
                os._exit(1)
            self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]), 0)
        self.assertEqual(list(self.intake.PENDING.glob('*.json')), [])

    @unittest.skipUnless(hasattr(os, 'fork'), 'actual concurrent admission producers')
    def test_concurrent_producers_cannot_overwrite_consumed_admission(self):
        children = []
        for _ in range(2):
            pid = os.fork()
            if pid == 0:
                try:self.intake.queue_issue(self.herdr_consumer(), {'number': 53}, [])
                except self.intake.AdmissionDenied as exc:os._exit(0 if str(exc) == 'intake-already-running' else 2)
                except Exception:os._exit(3)
                os._exit(0)
            children.append(pid)
        for pid in children:self.assertEqual(os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]), 0)
        self.assertEqual(len(list(self.intake.PENDING.glob('*.json'))), 1)
        row = self.intake.load_state()['Bbambaaamm/herdr#53']
        self.assertEqual(row['admission_intent']['state'], 'published')
        self.assertEqual(len(row['used_approvals']), 1)


def load_tests(loader, tests, pattern):
    return unittest.TestSuite(IntakeFollowupTests(name) for name in vars(IntakeFollowupTests) if name.startswith('test_'))


if __name__ == '__main__':
    unittest.main()

