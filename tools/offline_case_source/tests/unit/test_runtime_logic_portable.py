"""Portable closed-index tests; no private host reference is needed."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from offline_case.case import Denied, sha
from offline_case import runtime_inputs as inputs


class PortableRuntimeInputs(unittest.TestCase):
    def test_safe_relative_names(self):
        self.assertTrue(inputs.safe_name('proposed/sdk-source/hermes_cli/main.py'))
        for name in ('', '/absolute', 'a//b', 'a/../b', 'a/./b'):
            self.assertFalse(inputs.safe_name(name), name)

    def test_retained_selection_is_explicit(self):
        all_files = {'proposed/sdk-source/main.py': 'a' * 64,
                     'proposed/core/herdr/main.py': 'b' * 64,
                     'proposed/offline.apparmor': 'c' * 64,
                     'proposed/runtime-composition.json': 'd' * 64,
                     'proposed/raw-receipts/failure.zip': 'e' * 64,
                     'proposed/archive.tar.gz.part001': 'f' * 64}
        self.assertEqual(set(inputs.retained(all_files)), set(all_files) -
                         {'proposed/raw-receipts/failure.zip',
                          'proposed/archive.tar.gz.part001'})

    def test_closed_package_inventory_rejects_extra_and_link(self):
        from offline_case import native_source
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / 'integration-manifest.json').write_bytes(b'{}')
            (root / 'accepted-source-index.json').write_bytes(b'{}')
            (root / 'runtime-input-index.json').write_bytes(b'{}')
            (root / 'canonical-core-index.json').write_bytes(b'{}')
            native = root / 'native/herdr'
            native.parent.mkdir()
            native.write_bytes(b'fixture')
            native.chmod(0o444)
            runtime = {'files': {}, 'native_input': {'path': 'native/herdr'}}
            with patch.object(native_source, 'NATIVE_BYTES', 7), \
                 patch.object(native_source, 'NATIVE_SHA256', sha(b'fixture')):
                inputs.validate_package_inventory(root, {'files': {}, 'core_files': {}},
                                                  runtime)
                (root / 'extra').write_bytes(b'x')
                with self.assertRaises(Denied):
                    inputs.validate_package_inventory(root, {'files': {}, 'core_files': {}}, runtime)
                (root / 'extra').unlink()
                (root / 'alias').symlink_to(root / 'integration-manifest.json')
                with self.assertRaises(Denied):
                    inputs.validate_package_inventory(root, {'files': {}, 'core_files': {}}, runtime)

    def test_installed_native_input_is_exact_and_required(self):
        import stat
        from types import SimpleNamespace
        from offline_case import native_source
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            for name in ('integration-manifest.json', 'accepted-source-index.json',
                         'runtime-input-index.json', 'canonical-core-index.json'):
                (root / name).write_bytes(b'{}')
            native = root / 'native/herdr'
            native.parent.mkdir()
            native.write_bytes(b'inert executable fixture')
            native.chmod(0o555)
            original_lstat = Path.lstat
            def root_native(path, *args, **kwargs):
                if path == native:
                    return SimpleNamespace(st_mode=stat.S_IFREG | 0o555,
                                           st_uid=0, st_nlink=1, st_size=native.stat().st_size)
                return original_lstat(path, *args, **kwargs)
            with patch.object(native_source, 'NATIVE_BYTES', native.stat().st_size), \
                 patch.object(native_source, 'NATIVE_SHA256', sha(native.read_bytes())), \
                 patch.object(Path, 'lstat', root_native), \
                 patch.object(native_source, 'pinned_bytes', side_effect=lambda path, **kw: Path(path).read_bytes()):
                inputs.validate_package_inventory(root, {'files': {}, 'core_files': {}},
                                                  {'files': {}, 'native_input': {'path':'native/herdr'}}, installed=True)
                native.chmod(0o755)
                native.write_bytes(b'changed')
                native.chmod(0o555)
                with self.assertRaises(Denied):
                    inputs.validate_package_inventory(root, {'files': {}, 'core_files': {}},
                                                      {'files': {}, 'native_input': {'path':'native/herdr'}}, installed=True)


if __name__ == '__main__': unittest.main()
