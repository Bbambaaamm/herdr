"""Small test-only package fixtures must not retain failed or stale builds."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import reference_support
import verify_runtime_history


class ReferenceSupportLifecycle(unittest.TestCase):
    def test_failed_construction_cleans_partial_package_immediately(self):
        outputs = []

        def fail_after_partial_write(_repo, _reference, output):
            output.mkdir()
            (output / 'partial').write_bytes(b'inert')
            outputs.append(output)
            raise ValueError('stale pin')

        source_path = str(reference_support.source_root())
        with patch.object(sys, 'path', [p for p in sys.path if p != source_path]), \
             patch.object(reference_support, '_context', {'fixture': True}), \
             patch.object(reference_support, '_reference_json', Path('/tmp/inert-reference.json')), \
             patch.object(reference_support, '_package', None), \
             patch.object(reference_support, '_package_owner', None), \
             patch.object(verify_runtime_history, 'build_only', side_effect=fail_after_partial_write):
            for _ in range(2):
                with self.assertRaisesRegex(ValueError, 'stale pin'):
                    reference_support.package_root()
                self.assertFalse(outputs[-1].parent.exists())
                self.assertIsNone(reference_support._package)
                self.assertIsNone(reference_support._package_owner)
            self.assertNotEqual(outputs[0].parent, outputs[1].parent)
            self.assertEqual(sys.path.count(source_path), 1)

    def test_shared_package_cleans_on_context_change_and_suite_exit(self):
        outputs = []

        def build_small(_repo, _reference, output):
            output.mkdir()
            (output / 'inert').write_bytes(b'fixture')
            outputs.append(output)

        with tempfile.TemporaryDirectory() as temp, \
             patch.object(reference_support, '_context', None), \
             patch.object(reference_support, '_reference_json', None), \
             patch.object(reference_support, '_package', None), \
             patch.object(reference_support, '_package_owner', None), \
             patch.object(verify_runtime_history, 'build_only', side_effect=build_small):
            first_reference = Path(temp) / 'first.json'
            second_reference = Path(temp) / 'second.json'
            first_reference.write_text(json.dumps({'fixture': 1}))
            second_reference.write_text(json.dumps({'fixture': 2}))
            try:
                reference_support.configure(first_reference)
                first = reference_support.package_root()
                self.assertEqual(reference_support.package_root(), first)
                reference_support.configure(first_reference)
                self.assertEqual(reference_support.package_root(), first)
                self.assertEqual(outputs, [first])

                first_reference.write_text(json.dumps({'fixture': 3}))
                reference_support.configure(first_reference)
                self.assertFalse(first.parent.exists())
                second = reference_support.package_root()
                self.assertNotEqual(second, first)

                reference_support.configure(second_reference)
                self.assertFalse(second.parent.exists())
                third = reference_support.package_root()
                self.assertEqual(len(outputs), 3)
                self.assertTrue(third.exists())
            finally:
                # This is the same callback registered for interpreter exit.
                reference_support._cleanup_package()
            self.assertFalse(third.parent.exists())
            self.assertIsNone(reference_support._package)
            self.assertIsNone(reference_support._package_owner)


if __name__ == '__main__':
    unittest.main()
