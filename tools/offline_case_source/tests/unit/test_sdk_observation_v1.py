"""Inert compatibility checks for the current authenticated v3 self observation."""
import unittest
from pathlib import Path
from herdr import bootstrap_self_observation as observation
from herdr import credential_isolation

ROOT = Path(__file__).resolve().parents[2]


class SDKObservationV1(unittest.TestCase):
    def status(self, **changed):
        rows = {"Uid": "1001 1001 1001 1001", "Gid": "1001 1001 1001 1001",
                "NSpid": "1", "NoNewPrivs": "1", "Seccomp": "2", "Seccomp_filters": "1"}
        rows.update({name: "0000000000000000" for name in
                     ("CapInh", "CapPrm", "CapEff", "CapBnd", "CapAmb")})
        rows.update(changed)
        return ("\n".join(key + ":\t" + value for key, value in rows.items()) + "\n").encode()

    def test_status_requires_uid_cap_nnp_and_seccomp(self):
        self.assertEqual(observation.status_values(self.status())["Uid"], (1001,) * 4)
        for changed in ({"CapAmb": "0000000000000001"}, {"NoNewPrivs": "0"},
                        {"Seccomp": "0"}, {"Uid": "0 0 0 0"},
                        {"Seccomp_filters": "0"}):
            with self.subTest(changed=changed), self.assertRaises(Exception):
                observation.status_values(self.status(**changed))
        with self.assertRaises(Exception):
            observation.status_values(self.status() + b"Uid:\t1001 1001 1001 1001\n")

    def test_stage_two_requires_authenticated_v3_response_before_local_reference(self):
        source = (ROOT.parents[1] / "agent-stack/bin/agent-hermes-policy-run").read_text()
        self.assertIn("_AuthenticatedKernelReply", source)
        self.assertIn("observe_self_from_bootstrap", source)
        self.assertIn("_verified_bootstrap_reference(authenticated_reference", source)
        self.assertIn("reference_module.HostCredentialReference(**authenticated_reference)", source)
        self.assertLess(source.index("_verified_bootstrap_reference(authenticated_reference"),
                        source.index("reference_module.HostCredentialReference(**authenticated_reference)"))

    def test_legacy_direct_sdk_observation_is_not_a_v3_substitute(self):
        source = (ROOT.parents[1] / "agent-stack/bin/agent-hermes-policy-run").read_text()
        v3 = source[source.index("def _verified_bootstrap_reference("):
                    source.index("def bootstrap(")]
        self.assertIn('proof.get("schema_version") == "herdr-policy-bootstrap-3"', v3)
        self.assertIn("inherited authenticated v3 bootstrap response required", v3)
        self.assertIn("stage-two local and root observation denied", v3)
        self.assertIs(credential_isolation.WORKER_PROFILE_SOURCE_SHA256.__class__, str)


if __name__ == "__main__": unittest.main()
