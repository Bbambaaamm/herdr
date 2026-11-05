"""Inert current preparation ticket boundary tests."""
from dataclasses import fields
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from herdr.native_ticket_v2 import NativePreparationTicket
from herdr.case_roster import Roster
from herdr.security import PolicyDenied


class DefaultTicket(unittest.TestCase):
    def test_cannot_construct_ticket_from_local_claim(self):
        names = {field.name for field in fields(NativePreparationTicket)}
        self.assertTrue({"roster", "role", "identity", "plan", "record", "_construction"} <= names)
        with self.assertRaises((PolicyDenied, ValueError, TypeError)):
            NativePreparationTicket(None, "root", None, None, (), (), {}, object())

    def test_admit_rejects_untyped_launch_before_roster_or_issuer(self):
        with patch("herdr.case_roster.load_roster", side_effect=AssertionError("roster reached")):
            with self.assertRaises((PolicyDenied, ValueError, TypeError)):
                NativePreparationTicket.admit(SimpleNamespace(sealed=None), case_binding={})

    def test_revalidate_cannot_accept_changed_original_roster(self):
        # A retained typed ticket must re-read the exact root-owned roster.
        ticket = object.__new__(NativePreparationTicket)
        object.__setattr__(ticket, "roster", SimpleNamespace(sha256="a" * 64))
        object.__setattr__(ticket, "role", "root")
        object.__setattr__(ticket, "plan", SimpleNamespace(authorize=lambda *_: (_ for _ in ()).throw(AssertionError("plan reached"))))
        with patch("herdr.case_roster.load_roster", return_value=SimpleNamespace(sha256="b" * 64)):
            with self.assertRaises((PolicyDenied, ValueError, TypeError)):
                ticket.revalidate()


if __name__ == "__main__": unittest.main()
