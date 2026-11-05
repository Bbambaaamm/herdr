"""Data-only compact closure regressions against the immutable reference."""
import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

import reference_support
from offline_case.case import Denied, parse, pinned_bytes, sha, validate_build
from offline_case import runtime_inputs
from verify_runtime_history import validate_only


class RuntimeHistory(unittest.TestCase):
    def setUp(self):
        self.root = reference_support.package_root()
        self.origin = reference_support.accepted_root()
        self.build = parse((self.root / 'integration-manifest.json').read_bytes(), 262144)
        self.rows = json.loads((self.root / 'runtime-input-index.json').read_bytes())['files']

    def test_compact_package_excludes_archive_and_receipt_history(self):
        self.assertFalse(any('.tar.gz.part' in name or 'raw-receipts' in name
                             for name in self.rows))
        actual = {p.relative_to(self.root / 'accepted-source').as_posix()
                  for p in (self.root / 'accepted-source').rglob('*') if p.is_file()}
        self.assertEqual(actual, set(self.rows))
        self.assertEqual(validate_only(self.root)['status'], 'DATA_ONLY_UNISSUED')
        native = self.root / 'native/herdr'
        from offline_case.native_source import NATIVE_BYTES, NATIVE_SHA256
        self.assertEqual(native.stat().st_size, NATIVE_BYTES)
        self.assertEqual(sha(native.read_bytes()), NATIVE_SHA256)

    def test_entire_sdk_tree_set_and_hashes_are_preserved(self):
        prefix = 'proposed/sdk-source/'
        actual = {name: row['sha256'] for name, row in self.rows.items()
                  if name.startswith(prefix)}
        origin = json.loads((self.root / 'accepted-source-index.json').read_bytes())['files']
        expected = {name: digest for name, digest in origin.items() if name.startswith(prefix)}
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 1249)
        for name, digest in actual.items():
            self.assertEqual(sha((self.root / 'accepted-source' / name).read_bytes()), digest)
            self.assertEqual((self.root / 'accepted-source' / name).read_bytes(),
                             (self.origin / name).read_bytes())

    def test_runtime_validation_never_reads_original_reference(self):
        original = runtime_inputs.pinned_bytes
        root = self.root
        def only_package(path, *args, **kwargs):
            self.assertTrue(Path(path).is_relative_to(root), path)
            return original(path, *args, **kwargs)
        from offline_case import case, native_source
        import verify_runtime_history
        with patch.object(case, 'pinned_bytes', side_effect=only_package), \
             patch.object(runtime_inputs, 'pinned_bytes', side_effect=only_package), \
             patch.object(native_source, 'pinned_bytes', side_effect=only_package), \
             patch.object(verify_runtime_history, 'pinned_bytes', side_effect=only_package):
            validate_build(self.build, root, baseline=root / 'accepted-source')
            self.assertEqual(validate_only(root)['status'], 'DATA_ONLY_UNISSUED')

    def test_missing_changed_and_aliased_native_input_deny(self):
        native = self.root / 'native/herdr'
        original = native.read_bytes()
        native.chmod(0o644)
        try:
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            native.chmod(0o444)
        native.chmod(0o644)
        try:
            with native.open('r+b') as stream:
                stream.write(b'changed')
            native.chmod(0o444)
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            native.chmod(0o644)
            native.write_bytes(original)
            native.chmod(0o444)
        held = native.with_name('herdr.held')
        native.rename(held)
        try:
            with self.assertRaises((Denied, FileNotFoundError)): validate_only(self.root)
            native.symlink_to(held)
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            if native.is_symlink(): native.unlink()
            held.rename(native)

    def test_changed_late_sdk_file_denies(self):
        name = sorted(n for n in self.rows if n.startswith('proposed/sdk-source/'))[-1]
        path = self.root / 'accepted-source' / name
        original = path.read_bytes()
        try:
            path.write_bytes(b'changed late SDK byte')
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            path.write_bytes(original)

    def test_missing_late_input_denies(self):
        name = sorted(n for n in self.rows if n.startswith('proposed/sdk-source/'))[-2]
        path = self.root / 'accepted-source' / name
        absent = path.with_name(path.name + '.held')
        path.rename(absent)
        try:
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            absent.rename(path)

    def test_extra_and_alias_input_deny(self):
        extra = self.root / 'accepted-source' / 'unexpected-history.txt'
        alias = self.root / 'accepted-source' / 'unsafe-link'
        try:
            extra.write_bytes(b'unindexed')
            with self.assertRaises(Denied): validate_only(self.root)
            extra.unlink()
            alias.symlink_to(self.root / 'accepted-source/proposed/offline.apparmor')
            with self.assertRaises(Denied): validate_only(self.root)
        finally:
            if extra.exists(): extra.unlink()
            if alias.is_symlink(): alias.unlink()

    def test_origin_and_runtime_index_binding_denies(self):
        original = runtime_inputs.pinned_bytes
        for filename in ('accepted-source-index.json', 'runtime-input-index.json'):
            path = self.root / filename
            def changed(candidate, *args, **kwargs):
                raw = original(candidate, *args, **kwargs)
                return raw + b' ' if candidate == path else raw
            with patch.object(runtime_inputs, 'pinned_bytes', side_effect=changed):
                with self.assertRaises(Denied): validate_only(self.root)

    def test_publisher_plan_never_reads_historical_baseline(self):
        # Isolate the publisher's data-only enumeration after its independent
        # host-policy/native prerequisites. No root effect or SDK is invoked.
        from offline_case import case, publisher, publication, native_source
        from offline_case import admission
        from verify_runtime_history import publication_plan
        original = case.pinned_bytes
        root = self.root
        policy = b'{"fixture":"existing policy verified by separate gate"}'
        unit = (root / 'units' / admission.HOST_UNIT).read_bytes()
        def only_compact(path, maximum=16_777_216, *, root_owned=False):
            if path == admission.HOST_POLICY:
                return policy
            self.assertTrue(Path(path).is_relative_to(root), path)
            return original(path, maximum, root_owned=False)
        with patch.object(case, 'pinned_bytes', side_effect=only_compact), \
             patch.object(runtime_inputs, 'pinned_bytes', side_effect=only_compact), \
             patch.object(publication, 'verify_existing_runtime'), \
             patch.object(publication, 'render_host_unit', return_value=unit), \
             patch.object(native_source, 'pinned_bytes', side_effect=only_compact):
            entries = publisher.publication_entries(self.build, root)
        compact = {str(source) for source, _, _, _ in entries
                   if Path(source).is_relative_to(root / 'accepted-source')}
        expected = {str(root / 'accepted-source' / name) for name in self.rows}
        self.assertEqual(compact, expected)
        self.assertIn((root / 'native/herdr', native_source.NATIVE_TARGET,
                       native_source.NATIVE_SHA256, 0o555), entries)
        self.assertFalse(any('.tar.gz.part' in str(source) or 'raw-receipts' in str(source)
                             for source, _, _, _ in entries))
        pure = publication_plan(root, self.build, {'files': self.rows})
        self.assertEqual({str(target) for _, target, _, _ in entries},
                         {row['target'] for row in pure})

    def test_external_baseline_fallback_denies(self):
        with self.assertRaises(Denied):
            validate_build(self.build, self.root, baseline=self.origin)
        with self.assertRaises(Denied):
            validate_build(self.build, self.root, baseline=self.root / 'accepted-source',
                           baseline_index=self.origin.parent / 'accepted-source-index.json')


if __name__ == '__main__': unittest.main()
