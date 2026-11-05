"""Inert checks of the installed default dispatcher and recovery boundary."""
from contextlib import nullcontext
import unittest
from unittest.mock import patch
from herdr import offline_case_host, canonical_case_runtime as runtime
from offline_case.case import NONCE, Denied


class FakeRuntime:
    def __init__(self): self.calls = []
    def operation(self, packet):
        self.calls.append(("enter", packet["operation"]))
        return nullcontext()
    def fenced(self):
        self.calls.append(("fenced",))
        return True
    def admit(self, authority):
        self.calls.append(("admit", authority))
        raise Denied("original admission denied")


class DefaultDispatch(unittest.TestCase):
    def setUp(self):
        self.previous = runtime._LIVE
        runtime._LIVE = None
        self.addCleanup(setattr, runtime, "_LIVE", self.previous)

    def packet(self, operation, arguments=None):
        return {"case": NONCE, "operation": operation, "arguments": arguments or {}}

    def test_default_entry_is_canonical_dispatch_and_denies_unknown_operation(self):
        self.assertIs(offline_case_host.dispatch, runtime.dispatch)
        fake = FakeRuntime()
        runtime._LIVE = fake
        with self.assertRaises(Denied):
            offline_case_host.dispatch(self.packet("plan"))
        self.assertEqual(fake.calls, [])
        with self.assertRaises(Denied):
            offline_case_host.dispatch(self.packet("fence", {"authority": {}}))
        self.assertEqual(fake.calls, [])

    def test_failed_admit_is_consumed_before_original_admission(self):
        fake = FakeRuntime()
        with patch.object(runtime.CanonicalCaseRuntime, "from_configuration", return_value=fake) as factory:
            with self.assertRaises(Denied):
                offline_case_host.dispatch(self.packet("admit", {"authority": {"exact": "fixture"}}))
            factory.assert_called_once()
            self.assertIs(runtime._LIVE, fake)
            with self.assertRaises(Denied):
                offline_case_host.dispatch(self.packet("admit", {"authority": {"exact": "fixture"}}))
            factory.assert_called_once()
        self.assertEqual(fake.calls, [("enter", "admit"), ("admit", {"exact": "fixture"})])

    def test_cold_recovery_rejects_birth_and_routes_only_allowed_read(self):
        fake = FakeRuntime()
        with patch.object(runtime.CanonicalCaseRuntime, "from_configuration", return_value=fake) as factory:
            with self.assertRaises(Denied):
                offline_case_host.dispatch(self.packet("run", {"budget": {}, "phase": "root"}))
            factory.assert_not_called()
            self.assertTrue(offline_case_host.dispatch(self.packet("fenced")))
            factory.assert_called_once_with(self.packet("fenced"), recovery=True)
        self.assertEqual(fake.calls, [("enter", "fenced"), ("fenced",)])


if __name__ == "__main__": unittest.main()
