"""Inert atomic receipt tests against the real subordinate journal code."""
import os
import tempfile
import threading
import unittest
from pathlib import Path

from offline_case.custody import ATTEMPT, RootCustody
from offline_case.case import NONCE, Denied, canonical


class Journal(unittest.TestCase):
    def test_exclusive_receipt_survives_racing_publishers(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            one = RootCustody(Path(directory)); two = RootCustody(Path(directory))
            one.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            two.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            one.locked = two.locked = True  # synthetic held-lock seam
            barrier = threading.Barrier(2)
            outcomes = []
            def attempt(custody):
                barrier.wait()
                try:
                    custody.consume("a" * 64, {"nonce": NONCE,
                        "challenge": "a" * 64, "id": id(custody)})
                    outcomes.append("won")
                except (FileExistsError, Denied):
                    outcomes.append("lost")
            try:
                a = threading.Thread(target=attempt, args=(one,))
                b = threading.Thread(target=attempt, args=(two,))
                a.start(); b.start(); a.join(); b.join()
                self.assertCountEqual(outcomes, ["won", "lost"])
                self.assertTrue(one.consumed("b" * 64))
            finally:
                os.close(one.fd); os.close(two.fd)

    def test_occupied_symlink_is_never_reusable(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            link = Path(directory) / ATTEMPT
            link.symlink_to("absent")
            custody = RootCustody(Path(directory))
            custody.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            custody.locked = True
            try:
                self.assertTrue(custody.consumed("b" * 64))
            finally:
                os.close(custody.fd)

    def test_crash_after_consume_survives_challenge_reissue(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            custody = RootCustody(Path(directory))
            custody.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            custody.locked = True
            # The fixture account is not root; retain the real read and
            # publication path while bypassing only the owner check here.
            custody._regular = lambda fd, minsize=1: os.fstat(fd)
            first = {"nonce": NONCE, "challenge": "a" * 64,
                     "boot_id": "boot", "authority_sha256": "b" * 64,
                     "build_sha256": "c" * 64}
            try:
                custody.consume("a" * 64, first)
                # No state publication; replacing the authority challenge
                # cannot move the fixed case marker.
                (Path(directory) / "authority.json").write_bytes(canonical(
                    {"challenge": "d" * 64}))
                self.assertEqual(custody.state(), {"phase": "CONSUMED", "binding": first})
                self.assertTrue(custody.consumed("d" * 64))
                with self.assertRaises(Denied):
                    custody.save({"phase": "ARMED", "binding": dict(first, challenge="d" * 64)})
                with self.assertRaises(Denied):
                    custody.consume("d" * 64, dict(first, challenge="d" * 64))
            finally:
                os.close(custody.fd)

    def test_torn_pending_marker_blocks_replay(self):
        with tempfile.TemporaryDirectory(dir="/tmp") as directory:
            (Path(directory) / (".pending-" + "e" * 32)).write_bytes(b"torn")
            custody = RootCustody(Path(directory))
            custody.fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
            custody.locked = True
            try:
                self.assertTrue(custody.consumed("a" * 64))
                with self.assertRaises(Denied):
                    custody.consume("a" * 64, {"nonce": NONCE, "challenge": "a" * 64})
            finally:
                os.close(custody.fd)


if __name__ == "__main__": unittest.main()
