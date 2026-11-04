"""Inert fixed response data and exact ROOT/CHILD binding checks."""
import json
import ast
import inspect
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT.parents[1] / ""))
from herdr import host_model_transport as transport
from herdr.security import InvocationIdentity
from offline_case.case import NONCE


TASK_ID = "offline188-" + NONCE
WORKSPACE = "/home/agentops/worktrees/" + TASK_ID + "/workspace"
CHILD_WORKSPACE = WORKSPACE + "/.managed-child/workspace"


def definition():
    child = {"key": "arithmetic-child", "objective": "Repair frozen arithmetic in managed child",
             "role": "writer", "ownership": {"write_scope": []},
             "tools": ["read_file", "write_file"], "permissions": [],
             "worktree_identity": CHILD_WORKSPACE + "|1:2"}
    return {"spec_version": "offline-arithmetic-1", "policy_version": "offline-clean-1",
            "criteria": ["arithmetic"],
            "discovery_files": ["arithmetic.py", "check_arithmetic.py"],
            "files": [{"path": "arithmetic.py", "subtree": False, "symbols": []}],
            "managed_children": {"version": 1, "children": [child]}}


def payload(role, messages=()):
    names = ["read_file", "write_file", "herdr_verify_work", "herdr_submit_result"]
    if role == "root":
        names.append("herdr_delegate_child")
    return {"model": transport._FIXTURE_MODEL,
            "tools": [{"type": "function", "function": {"name": name}} for name in names],
            "messages": list(messages)}


class OfflineFixture(unittest.TestCase):
    def test_transport_keeps_credential_http_outside_case_branch(self):
        tree = ast.parse(inspect.getsource(transport.execute_host_model))
        offline_checks = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
                          and isinstance(node.func, ast.Name) and
                          node.func.id in {"_case_host", "_case_unit", "_fixture_binding",
                                           "_credential", "_perform_fixture", "_perform_http"}]
        positions = {node.func.id: node.lineno for node in offline_checks}
        self.assertLess(positions["_fixture_binding"], positions["_credential"])
        self.assertLess(positions["_credential"], positions["_perform_fixture"])
        credential_guards = [node for node in ast.walk(tree) if isinstance(node, ast.If)
                             and isinstance(node.test, ast.UnaryOp) and
                             isinstance(node.test.op, ast.Not) and
                             isinstance(node.test.operand, ast.Name) and
                             node.test.operand.id == "offline"]
        self.assertTrue(any(any(isinstance(n, ast.Call) and
                                isinstance(n.func, ast.Name) and n.func.id == "_credential"
                                for n in ast.walk(guard)) for guard in credential_guards))
        self.assertTrue(any(isinstance(node, ast.IfExp) and
                            any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and
                                n.func.id == "_perform_fixture" for n in ast.walk(node.body)) and
                            any(isinstance(n, ast.Name) and n.id == "_perform_http"
                                for n in ast.walk(node.orelse))
                            for node in ast.walk(tree)))

    def test_original_case_identity_selects_two_distinct_roles(self):
        root = InvocationIdentity("github:Bbambaaamm/herdr", "root-agent",
                                  "coordinator", "coordinator:coordinator",
                                  TASK_ID, NONCE, 1)
        child = InvocationIdentity("github:Bbambaaamm/herdr", "child-agent",
                                   "root-agent", TASK_ID, TASK_ID + "-child",
                                   "1" * 32, 2)
        selector = {"nonce": NONCE, "host_label": "herdr-offline-controller-03414499dd0d1986",
                    "task_id": TASK_ID, "run_token": NONCE, "fencing_token": 1}
        with patch("herdr.host_configuration._read_configuration", return_value=selector):
            for role, identity in (("root", root), ("child", child)):
                task = {"id": identity.task_id, "run_token": identity.run_token,
                        "fencing_token": identity.fencing_token,
                        "parent_agent_id": identity.parent_agent_id,
                        "derived_parent_admission_sha256": "a" * 64}
                factory = SimpleNamespace(host_task=task,
                                          host_admission={"definition": definition()})
                grant = SimpleNamespace(identity=identity)
                self.assertEqual(transport._fixture_binding(factory, identity, grant,
                                                              payload(role))[0], role)
                with self.assertRaises(Exception):
                    transport._fixture_binding(factory, identity, grant,
                                               {**payload(role), "model": "paid-model"})

    def test_fixed_sequence_requires_actual_nested_host_verification(self):
        work = definition()
        root = payload("root")
        child = payload("child")
        delegated = transport._fixture_response(root, "root", work, 1, WORKSPACE)
        self.assertEqual(delegated["body"]["choices"][0]["message"]["tool_calls"][0]
                         ["function"]["name"], "herdr_delegate_child")
        for ordinal, expected in ((1, "read_file"), (2, "write_file"),
                                  (3, "herdr_verify_work")):
            answer = transport._fixture_response(child, "child", work, ordinal,
                                                 CHILD_WORKSPACE)
            self.assertEqual(answer["body"]["choices"][0]["message"]["tool_calls"][0]
                             ["function"]["name"], expected)
        with self.assertRaises(Exception):
            transport._fixture_response(child, "child", work, 4, CHILD_WORKSPACE)
        receipt = {"result": {"verification": {"status": "pass",
                    "submission": {"artifact_sha256": "a" * 64}}}}
        child["messages"] = [{"role": "tool", "content": json.dumps(receipt)}]
        answer = transport._fixture_response(child, "child", work, 4,
                                             CHILD_WORKSPACE)
        self.assertEqual(answer["body"]["choices"][0]["message"]["tool_calls"][0]
                         ["function"]["name"], "herdr_submit_result")
        self.assertEqual(transport._fixture_response(child, "child", work, 5,
                         CHILD_WORKSPACE)["body"]["choices"][0]["finish_reason"], "stop")
        with self.assertRaises(Exception):
            transport._fixture_response(child, "child", work, 6, CHILD_WORKSPACE)


if __name__ == "__main__":
    unittest.main()
