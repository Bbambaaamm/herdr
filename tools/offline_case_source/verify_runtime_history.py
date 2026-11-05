#!/usr/bin/env python3
"""Data-only SOURCE materialization and offline compact-package verification."""
from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path

# Isolated Python omits the script directory. Load only this verifier's reviewed
# sibling package; never consult PYTHONPATH, a reference tree, or an installed copy.
SOURCE_ROOT = Path(__file__).resolve(strict=True).parent
if not (SOURCE_ROOT / 'offline_case' / '__init__.py').is_file():
    raise RuntimeError('local offline_case source missing')
sys.path.insert(0, str(SOURCE_ROOT))

from offline_case.case import Denied, canonical, parse, pinned_bytes, plan, require, sha, validate_build
from offline_case.runtime_inputs import checked_indices, safe_name, verify_full_origin

PACKAGE_FILES = ('integration-manifest.json', 'accepted-source-index.json',
                 'runtime-input-index.json', 'canonical-core-index.json')


def inventory(build, runtime):
    return (set(build['files']) |
            {'composed-core/' + name for name in build['core_files']} |
            set(PACKAGE_FILES) | {runtime['native_input']['path']} |
            {'accepted-source/' + name for name in runtime['files']})


def publication_plan(root, build, runtime):
    """Exact destination/byte/mode plan from package-local inputs."""
    from offline_case.case import COMPOSED_CORE, INSTALL_ROOT
    from offline_case.native_source import NATIVE_RELATIVE, NATIVE_TARGET, NATIVE_SHA256, native_source_bytes
    entries = {}
    executable = set(build['installed_modes']['executable_targets'])
    def add(source, target, digest, *, native=False):
        mode = 0o555 if native or target in executable else 0o444
        row = {'source': source, 'target': target, 'sha256': digest, 'mode': mode}
        old = entries.get(target)
        require(old is None or (old['sha256'], old['mode']) == (digest, mode),
                'publication destination conflict')
        entries[target] = row
    for name, digest in build['core_files'].items():
        add('composed-core/' + name, COMPOSED_CORE + '/' + name, digest)
    for name, digest in build['files'].items():
        target = build['install_targets'][name]
        add(name, target, digest)
        alias = INSTALL_ROOT + '/' + name
        if target != alias:
            add(name, alias, digest)
    for name, row in runtime['files'].items():
        add('accepted-source/' + name, INSTALL_ROOT + '/accepted-source/' + name,
            row['sha256'])
    for name, target in build['metadata_install_targets'].items():
        add(name, target, sha(pinned_bytes(root / name, maximum=524288)))
    native_source_bytes(root)
    add(NATIVE_RELATIVE, str(NATIVE_TARGET), NATIVE_SHA256, native=True)
    require(executable <= set(entries), 'executable target missing')
    return list(sorted(entries.values(), key=lambda row: row['target']))


def closed_package(root, build, runtime):
    expected = inventory(build, runtime)
    actual = set()
    for path in root.rglob('*'):
        mode = path.lstat().st_mode
        require(stat.S_ISDIR(mode) or stat.S_ISREG(mode), 'package alias or unsafe type')
        if stat.S_ISREG(mode):
            actual.add(path.relative_to(root).as_posix())
    require(actual == expected, 'package inventory differs')
    validate_build(build, root, baseline=root / 'accepted-source')
    require(pinned_bytes(root / 'integration-manifest.json', maximum=262144) == canonical(build),
            'package manifest noncanonical')
    publication = publication_plan(root, build, runtime)
    return {'status': 'DATA_ONLY_UNISSUED',
            'retained_origin_inputs': len(runtime['files']),
            'retained_inputs': len(runtime['files']) + 1,
            'files': len(expected), 'publication_targets': len(publication),
            'publication_plan_sha256': sha(canonical(publication)),
            'native_input_bytes': runtime['native_input']['bytes'],
            'case_plan': plan(build)}


def validate_only(package_root):
    package_root = Path(package_root).absolute()
    require(package_root.resolve(strict=True) == package_root, 'package root alias')
    build = parse(pinned_bytes(package_root / 'integration-manifest.json', maximum=262144),
                  262144)
    _, runtime = checked_indices(package_root)
    return closed_package(package_root, build, runtime)


def build_only(repo_root, reference_json, output):
    repo_root = Path(repo_root).absolute()
    output = Path(output).absolute()
    context = parse(pinned_bytes(Path(reference_json).resolve(strict=True), maximum=65536))
    source = repo_root / 'tools/offline_case_source'
    require(context['repository_root'] == str(repo_root) and
            context['package_source_root'] == str(source) and
            context['accepted_source_snapshot'] ==
            '524cc4a35746ea7fa2aa7bac7a7a5b42dabc05e97b3c572ee88774eda21db544' and
            context['accepted_source_index_sha256'] ==
            sha(pinned_bytes(source / 'accepted-source-index.json', maximum=262144)),
            'reference context mismatch')
    from offline_case.native_source import NATIVE_RELATIVE, NATIVE_BYTES, NATIVE_SHA256
    native = context.get('native_cli_input')
    require(type(native) is dict and set(native) == {'path', 'bytes', 'sha256',
            'original_verified_source', 'source_only_nonexecutable_copy'} and
            native['bytes'] == NATIVE_BYTES and native['sha256'] == NATIVE_SHA256 and
            native['original_verified_source'] == '/home/agentops/.local/bin/herdr' and
            native['source_only_nonexecutable_copy'] is True and
            Path(native['path']) == Path('/home/agentops/tmp/hermes-runtime-history-split-20261104-r1/reference/native-cli-input'),
            'native reference binding changed')
    native_path = Path(native['path'])
    native_info = native_path.lstat()
    require(stat.S_ISREG(native_info.st_mode) and native_info.st_nlink == 1 and
            stat.S_IMODE(native_info.st_mode) == 0o444 and native_info.st_size == NATIVE_BYTES,
            'native reference metadata changed')
    native_raw = pinned_bytes(native_path, maximum=NATIVE_BYTES)
    require(sha(native_raw) == NATIVE_SHA256, 'native reference bytes changed')
    origin_root = Path(context['accepted_source_root'])
    require(origin_root.is_absolute() and origin_root.resolve(strict=True) == origin_root,
            'origin root alias')
    require(sha(pinned_bytes(Path(context['accepted_source_index']), maximum=262144)) ==
            context['accepted_source_index_sha256'], 'external origin index changed')
    origin = verify_full_origin(source, origin_root)
    _, runtime = checked_indices(source)
    build = parse(pinned_bytes(source / 'integration-manifest.json', maximum=262144), 262144)
    require(not output.exists() and not output.is_symlink(), 'output already exists')
    require(repo_root not in output.parents and origin_root not in output.parents,
            'output inside input tree')
    output.mkdir(parents=True)
    try:
        for name in sorted(inventory(build, runtime)):
            require(safe_name(name), 'unsafe materialized name')
            if name == NATIVE_RELATIVE:
                raw = native_raw
            elif name.startswith('accepted-source/'):
                origin_name = name.removeprefix('accepted-source/')
                raw = pinned_bytes(origin_root / origin_name)
                require(sha(raw) == origin['files'][origin_name], 'origin changed during materialization')
            else:
                if name.startswith('composed-core/'):
                    # The frozen canonical source manifest describes the
                    # repository tree before these explicitly pinned overlays.
                    # Compose from the overlay byte when one replaces a core
                    # path; the base index remains the immutable base oracle.
                    overlay = build['overlay_targets'].get(name)
                    input_path = source / overlay if overlay else repo_root / name.removeprefix('composed-core/')
                else:
                    input_path = source / name
                raw = pinned_bytes(input_path)
                if name.startswith('composed-core/'):
                    digest = build['core_files'][name.removeprefix('composed-core/')]
                    require(sha(raw) == digest, 'core source changed')
                elif name in build['files']:
                    require(sha(raw) == build['files'][name], 'candidate source changed')
            dest = output / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('xb') as stream:
                stream.write(raw)
            if name == NATIVE_RELATIVE:
                dest.chmod(0o444)
        result = validate_only(output)
        result['package_bytes'] = sum(p.stat().st_size for p in output.rglob('*') if p.is_file())
        result['original_expanded_bytes'] = 84185101
        result['native_input_bytes'] = NATIVE_BYTES
        return result
    except BaseException:
        # Leave an interrupted output for explicit inspection; never touch originals.
        raise


def main(argv=None):
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--build-only', action='store_true')
    mode.add_argument('--validate-only', action='store_true')
    parser.add_argument('--repo-root', type=Path)
    parser.add_argument('--reference-json', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--package-root', type=Path)
    args = parser.parse_args(argv)
    if args.build_only:
        require(all((args.repo_root, args.reference_json, args.output)) and
                args.package_root is None, 'build arguments')
        result = build_only(args.repo_root, args.reference_json, args.output)
    else:
        require(args.package_root is not None and
                all(x is None for x in (args.repo_root, args.reference_json, args.output)),
                'validate arguments')
        result = validate_only(args.package_root)
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
