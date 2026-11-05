"""Inert tests of the real worker handoff decision seam."""
import unittest

from offline_case.case import Denied
from offline_case.payload import main, verify_worker


class View:
    def __init__(self):
        self.uid = (1001, 1001)
        self.descriptors = [0, 1, 2]
        self.label = "herdr189-reference-lifetime (enforce)"
        self.seccomp = "2"
        self.filters = "1"
        self.namespaces = {key: key + ":[42]" for key in ("pid", "mnt", "net", "user")}
    def identity(self): return self.uid
    def fds(self): return self.descriptors
    def home(self): return "/home/agentops"
    def namespace(self, kind): return self.namespaces[kind]
    def text(self, path):
        if path == "/proc/self/attr/current": return self.label
        if path == "/proc/self/status":
            return "".join(key + ":\t0000000000000000\n" for key in
                           ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")) + \
                   "NoNewPrivs:\t1\nSeccomp:\t" + self.seccomp + \
                   "\nSeccomp_filters:\t" + self.filters + "\n"
        raise AssertionError(path)


ENV = {name: "test" for name in (
    "HERDR_POLICY_CONSUMER", "HERDR_POLICY_AGENT_ID",
    "HERDR_POLICY_PARENT_AGENT_ID", "HERDR_POLICY_PARENT_TASK_ID",
    "HERDR_POLICY_TASK_ID", "HERDR_POLICY_RUN_TOKEN",
    "HERDR_POLICY_FENCING_TOKEN")}
ENV.update(HERDR_POLICY_STAGE1_PROOF_SHA256="a" * 64)


class Payload(unittest.TestCase):
    def test_entry_uses_accepted_stage_one_shim(self):
        calls = []
        with self.assertRaisesRegex(RuntimeError, "returned unexpectedly"):
            main(view=View(), environ=ENV,
                 execve=lambda *args: calls.append(args))
        self.assertEqual(calls, [(
            "/run/herdr-bootstrap/hermes",
            ["/run/herdr-bootstrap/hermes", "-p", "quantlab", "chat"], ENV)])

    def test_raw_key_and_fake_descriptor_authority_denied(self):
        for addition in ({"OPENAI_API_KEY": "raw"},
                         {"HERDR_VERIFIED_STAGE2_FD": "4"},
                         {"HERDR_OFFLINE_HOST_NS_PID": "pid:[1]"}):
            calls = []
            with self.assertRaises(Denied):
                main(view=View(), environ=ENV | addition,
                     execve=lambda *args: calls.append(args))
            self.assertEqual(calls, [])

    def test_kernel_state_checks_precede_exec(self):
        for attribute, value in (("uid", (0, 0)), ("descriptors", [0, 1, 2, 9]),
                                 ("label", "unconfined"), ("seccomp", "0"),
                                 ("filters", "0")):
            view = View(); setattr(view, attribute, value)
            calls = []
            with self.assertRaises(Denied):
                main(view=view, environ=ENV, execve=lambda *args: calls.append(args))
            self.assertEqual(calls, [])
        view = View(); view.namespaces["mnt"] = "bad"
        with self.assertRaises(Denied): verify_worker(view)


if __name__ == "__main__": unittest.main()
