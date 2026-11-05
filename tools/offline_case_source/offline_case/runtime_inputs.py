"""Frozen origin metadata and the checked, closed operational input tree.

The origin index attests provenance. Runtime checks only the retained bytes;
missing historical bytes are never reported as verified at runtime.
"""
from __future__ import annotations

import stat
from pathlib import Path

from .case import BASELINE, BASELINE_INDEX, RUNTIME_INDEX, Denied, hex64, parse, pinned_bytes, require, sha


def safe_name(name):
    return (type(name) is str and name and not name.startswith('/') and
            all(part not in ('', '.', '..') for part in name.split('/')))


def retained(origin):
    return {name: digest for name, digest in origin.items()
            if name.startswith(('proposed/sdk-source/', 'proposed/core/')) or
            name in ('proposed/offline.apparmor', 'proposed/runtime-composition.json')}


def checked_indices(root: Path, *, root_owned=False):
    origin_raw = pinned_bytes(root / 'accepted-source-index.json', maximum=262144,
                              root_owned=root_owned)
    require(sha(origin_raw) == BASELINE_INDEX, 'origin index changed')
    origin = parse(origin_raw, 262144)
    require(set(origin) == {'sha256', 'files'} and origin['sha256'] == BASELINE and
            type(origin['files']) is dict and len(origin['files']) == 1471 and
            all(safe_name(k) and hex64(v) for k, v in origin['files'].items()),
            'origin index invalid')
    runtime_raw = pinned_bytes(root / 'runtime-input-index.json', maximum=524288,
                               root_owned=root_owned)
    require(sha(runtime_raw) == RUNTIME_INDEX, 'runtime index changed')
    runtime = parse(runtime_raw, 524288)
    require(set(runtime) == {'schema', 'kind', 'origin_index_sha256', 'sdk_source_identity', 'files', 'native_input'} and
            type(runtime['schema']) is int and runtime['schema'] == 1 and
            runtime['kind'] == 'CLOSED_RUNTIME_INPUTS' and
            runtime['origin_index_sha256'] == BASELINE_INDEX and
            runtime['sdk_source_identity'] == 'b54a131be69f0918690847fb345a491c1c4373176b02beb64ed803b17ad103d6' and
            type(runtime['files']) is dict, 'runtime index schema')
    from .native_source import NATIVE_RELATIVE, NATIVE_SHA256, NATIVE_BYTES
    require(runtime['native_input'] == {
        'path': NATIVE_RELATIVE, 'sha256': NATIVE_SHA256, 'bytes': NATIVE_BYTES,
        'class': 'native-cli', 'provenance': 'reference-context.json#native_cli_input'},
        'native input index changed')
    expected = retained(origin['files'])
    require(set(runtime['files']) == set(expected), 'retained input set changed')
    for name, digest in expected.items():
        row = runtime['files'][name]
        cls = ('sdk-source' if name.startswith('proposed/sdk-source/') else
               'canonical-baseline' if name.startswith('proposed/core/') else
               'profile-or-composition')
        require(type(row) is dict and row == {
            'sha256': digest, 'class': cls,
            'provenance': 'accepted-source-index.json#files/' + name},
            'retained input provenance changed: ' + name)
    return origin, runtime


def validate_retained(root: Path, baseline: Path, *, root_owned=False):
    origin, runtime = checked_indices(root, root_owned=root_owned)
    expected = set(runtime['files'])
    require(baseline.is_absolute() and baseline.resolve(strict=True) == baseline,
            'aliased retained root')
    actual = set()
    expected_dirs = {str(Path(name).parent) for name in expected}
    expected_dirs |= {str(parent) for name in expected for parent in Path(name).parents if str(parent) != '.'}
    for path in baseline.rglob('*'):
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                'retained input has unsafe type')
        relative = path.relative_to(baseline).as_posix()
        if stat.S_ISDIR(info.st_mode):
            require(relative in expected_dirs, 'extra retained directory')
        else:
            actual.add(relative)
    require(actual == expected, 'retained input inventory differs')
    for name, row in runtime['files'].items():
        require(sha(pinned_bytes(baseline / name, root_owned=root_owned)) == row['sha256'],
                'retained input changed: ' + name)
    return runtime


def verify_full_origin(root: Path, baseline: Path):
    """SOURCE construction only: verify every byte of the original frozen input."""
    origin, _ = checked_indices(root)
    require(baseline.is_absolute() and baseline.resolve(strict=True) == baseline,
            'aliased origin root')
    actual = set()
    for path in baseline.rglob('*'):
        info = path.lstat()
        require(stat.S_ISDIR(info.st_mode) or stat.S_ISREG(info.st_mode),
                'origin input has unsafe type')
        if stat.S_ISREG(info.st_mode):
            actual.add(path.relative_to(baseline).as_posix())
    require(actual == set(origin['files']), 'full origin inventory differs')
    for name, digest in origin['files'].items():
        require(sha(pinned_bytes(baseline / name)) == digest,
                'full origin changed: ' + name)
    return origin


def validate_package_inventory(root: Path, build: dict, runtime: dict, *, installed=False):
    expected = (set(build['files']) |
                {'composed-core/' + name for name in build['core_files']} |
                {'integration-manifest.json', 'accepted-source-index.json',
                 'runtime-input-index.json', 'canonical-core-index.json',
                 runtime['native_input']['path']} |
                {'accepted-source/' + name for name in runtime['files']})
    from .native_source import native_source_bytes
    native_source_bytes(root, root_owned=installed, installed=installed)
    actual = set()
    expected_dirs = {str(parent) for name in expected for parent in Path(name).parents if str(parent) != '.'}
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'package alias or unsafe type')
        relative = path.relative_to(root).as_posix()
        if stat.S_ISDIR(mode):
            require(relative in expected_dirs, 'extra package directory')
        else:
            actual.add(relative)
    require(actual == expected, 'package inventory differs')
