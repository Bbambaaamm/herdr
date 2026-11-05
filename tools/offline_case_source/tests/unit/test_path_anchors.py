"""Synthetic policy closure check at the real protected open call sites."""
import os
import stat
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import prep_entry
import trusted_prepare
from offline_case.case import pinned_bytes

ROOT = Path(__file__).resolve().parents[2]


class PathAnchors(unittest.TestCase):
    def test_observer_literals_cover_protected_final_reads(self):
        policy = (ROOT / "overlays/observer-profile.apparmor").read_text()
        for rule in ("/proc/sys/kernel/random/boot_id r,",
                     "/sys/fs/cgroup/system.slice/*/{cgroup.procs,cgroup.threads} r,",
                     "/etc/herdr/{worker-confinement.json,worker-profile.apparmor} r,",
                     "/etc/herdr/offline-03414499dd0d1986/** r,"):
            self.assertIn(rule, policy)

    def test_protected_reads_traverse_without_directory_read(self):
        with tempfile.TemporaryDirectory() as name:
            directory = Path(name) / "nested"
            directory.mkdir()
            target = directory / "policy.json"
            target.write_bytes(b'{"synthetic":true}')
            real_open, real_fstat, real_stat = os.open, os.fstat, os.stat
            opened = []

            def checked_open(path, flags, *args, **kwargs):
                if flags & os.O_DIRECTORY:
                    self.assertTrue(flags & os.O_PATH,
                                    "ancestor directory required unapproved read")
                opened.append((str(path), flags))
                return real_open(path, flags, *args, **kwargs)

            def root_stat(info):
                fields = ("st_mode", "st_dev", "st_ino", "st_nlink", "st_size",
                          "st_mtime_ns", "st_ctime_ns")
                values = {field: getattr(info, field) for field in fields}
                values["st_mode"] &= ~0o022
                return SimpleNamespace(**values, st_uid=0)

            with patch.object(os, "open", side_effect=checked_open):
                self.assertEqual(pinned_bytes(target), b'{"synthetic":true}')
                with patch.object(os, "fstat", side_effect=lambda fd: root_stat(real_fstat(fd))), \
                     patch.object(os, "stat", side_effect=lambda path, **kw: root_stat(real_stat(path, **kw))):
                    self.assertEqual(prep_entry.protected_bytes(target), b'{"synthetic":true}')
            self.assertTrue(any(path == target.name and not flags & os.O_PATH
                                for path, flags in opened))

    def test_private_target_creation_uses_path_anchors(self):
        with tempfile.TemporaryDirectory() as name:
            target = Path(name) / "private" / "target"
            real_open = os.open
            def checked_open(path, flags, *args, **kwargs):
                if flags & os.O_DIRECTORY:
                    self.assertTrue(flags & os.O_PATH,
                                    "private target ancestry required read")
                return real_open(path, flags, *args, **kwargs)
            with patch.object(os, "open", side_effect=checked_open):
                trusted_prepare.LinuxOps.target(object.__new__(trusted_prepare.LinuxOps),
                                                str(target), directory=True)
            self.assertTrue(target.is_dir())
            self.assertEqual(stat.S_IMODE(target.stat().st_mode), 0o755)


if __name__ == "__main__": unittest.main()
