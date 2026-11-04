"""Inert durable retirement checks; no SDK, issuer or host process is started."""
import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from core_bridge import DurableLaunchJournal, NativeHerdrHost, Denied


EMPTY = {"complete": True, "fenced": True, "case_cgroup_empty": True,
         "descendants": [], "fds": [], "maps": [], "profile_holders": []}


class LaunchRecovery(unittest.TestCase):
    def test_consumed_intent_survives_new_journal_instance_and_retirement_order(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            os.chmod(directory, 0o700)
            identity = SimpleNamespace(task_id="root", agent_id="root", fencing_token=7,
                                       to_json=lambda: {"task_id": "root", "fencing_token": 7})
            journal = DurableLaunchJournal(directory)
            journal.publish_once("prepare-intent-root", {"identity": identity.to_json()})
            with self.assertRaises(FileExistsError):
                journal.publish_once("prepare-intent-root", {"identity": identity.to_json()})
            events = []
            bridge = SimpleNamespace(api=SimpleNamespace(InvocationIdentity=SimpleNamespace),
                journal=DurableLaunchJournal(directory),
                factory=SimpleNamespace(cleanup_orphan=lambda bound:
                    events.append(("cleanup_orphan", bound.task_id)) or True),
                registry=SimpleNamespace(release=lambda *args, **kwargs:
                    events.append(("registry_release", args, kwargs))))
            self.assertTrue(NativeHerdrHost.recover_cleanup_after_empty(bridge, identity, EMPTY))
            self.assertEqual([row[0] for row in events], ["cleanup_orphan", "registry_release"])
            self.assertEqual(bridge.journal.read_once("retired-root"), EMPTY)
            self.assertTrue(NativeHerdrHost.recover_cleanup_after_empty(bridge, identity, EMPTY))
            self.assertEqual([row[0] for row in events], ["cleanup_orphan", "registry_release"])

    def test_unknown_holders_and_torn_receipt_cannot_retire(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            os.chmod(directory, 0o700)
            identity = SimpleNamespace(task_id="root", agent_id="root", fencing_token=7,
                                       to_json=lambda: {"task_id": "root"})
            journal = DurableLaunchJournal(directory)
            journal.publish_once("prepare-intent-root", {"identity": identity.to_json()})
            events = []
            bridge = SimpleNamespace(api=SimpleNamespace(InvocationIdentity=SimpleNamespace),
                journal=journal,
                factory=SimpleNamespace(cleanup_orphan=lambda _: events.append("cleanup") or True),
                registry=SimpleNamespace(release=lambda *a, **k: events.append("release")))
            with self.assertRaises(Denied):
                NativeHerdrHost.recover_cleanup_after_empty(bridge, identity,
                    {**EMPTY, "profile_holders": [(123, 4)]})
            self.assertEqual(events, [])
            name = journal._name("prepare-intent-root")
            (directory / name).write_bytes(b"{")
            with self.assertRaises((ValueError, Denied)):
                NativeHerdrHost.recover_cleanup_after_empty(bridge, identity, EMPTY)
            self.assertEqual(events, [])


if __name__ == "__main__":
    unittest.main()
