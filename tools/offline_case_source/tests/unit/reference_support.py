"""Explicit test-only reference injection; never consulted by runtime code."""
import atexit
import json
import tempfile
from pathlib import Path

_context = None
_package = None
_package_owner = None
_reference_json = None


def _cleanup_package():
    global _package, _package_owner
    owner = _package_owner
    _package = None
    _package_owner = None
    if owner is not None:
        owner.cleanup()


atexit.register(_cleanup_package)


def configure(reference_json_path):
    global _context, _reference_json
    reference = Path(reference_json_path).resolve(strict=True)
    context = json.loads(reference.read_bytes())
    if reference != _reference_json or context != _context:
        _cleanup_package()
    _reference_json = reference
    _context = context
    return _context


def accepted_root():
    if _context is None:
        raise RuntimeError('full reference integration requires reference_support.configure')
    return Path(_context['accepted_source_root'])


def source_root():
    return Path(__file__).resolve().parents[2]


def repo_root():
    return source_root().parents[1]


def runtime_policy():
    # Portable, data-only test fixture derived from the pinned candidate's
    # public binding. It is never a host policy or runtime approval.
    binding = json.loads((source_root() / 'runtime-binding.json').read_bytes())
    executable = Path(binding['executable'])
    return {'schema_version': 2, 'host_uid': 1001, 'runtime': [
        {'source': str(executable.parent.parent),
         'target': '/home/agentops/.local/share/uv/python/cpython-3.11.16-linux-x86_64-gnu',
         'files': {'bin/python3.11': binding['executable_sha256']},
         'executable_files': ['bin/python3.11'], 'max_bytes': 1,
         'max_file_bytes': 1},
        {'source': '/opt/herdr/releases/p0-5035d92-test/hermes', 'target': '/opt/herdr/releases/p0-5035d92-test/hermes',
         'files': {}, 'executable_files': [], 'max_bytes': 1, 'max_file_bytes': 1}]}


def package_root():
    global _package, _package_owner
    if _package is None:
        if _context is None:
            raise RuntimeError('full reference integration requires reference_support.configure')
        import sys
        source_path = str(source_root())
        if source_path not in sys.path:
            sys.path.insert(0, source_path)
        from verify_runtime_history import build_only
        owner = tempfile.TemporaryDirectory(prefix='compact-runtime-test-')
        output = Path(owner.name) / 'runtime'
        try:
            build_only(repo_root(), _reference_json, output)
        except BaseException:
            owner.cleanup()
            raise
        _package_owner = owner
        _package = output
    return _package
