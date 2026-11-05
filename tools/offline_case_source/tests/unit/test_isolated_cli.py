"""The repository verifier must resolve its own package under isolated Python."""
import subprocess
import sys
import unittest
from pathlib import Path


SOURCE = Path(__file__).resolve().parents[2]


class IsolatedCli(unittest.TestCase):
    def test_help_uses_reviewed_local_package(self):
        result = subprocess.run(
            [sys.executable, '-I', '-B', str(SOURCE / 'verify_runtime_history.py'), '--help'],
            cwd='/', stdin=subprocess.DEVNULL, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr.decode())
        self.assertIn(b'--validate-only', result.stdout)


if __name__ == '__main__':
    unittest.main()
