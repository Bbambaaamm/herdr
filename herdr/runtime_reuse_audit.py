"""Non-authorizing root-publication inventory audit; no file publication.

Old records are never upgraded into trusted records. Their manifests are only
review inputs, bound to independent root-owned approval requests.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from .host_configuration import _read_configuration
from .runtime_publication import validate_publication_record, _manifest_sha256
from .security import SecurityError, canonical_json_bytes

VERSION = 'herdr-runtime-reuse-audit-1'
ROLES = frozenset(('code', 'hermes', 'python'))


def inspect_pair(request: dict, record: dict, *, tree_presence: dict[str, bool]):
    """Pure inspection; cannot grant approval even if every check is true."""
    candidate = (isinstance(request, dict) and isinstance(record, dict)
                 and request.get('schema_version') == 'herdr-runtime-publication-1'
                 and set(request.get('trees', {})) == ROLES
                 and set(record.get('trees', {})) == ROLES)
    match = False
    old_format = False
    if candidate:
        try:
            approved = hashlib.sha256(canonical_json_bytes(request)).hexdigest()
            match = (record.get('approval_sha256') == approved
                     and record.get('version') == request.get('version')
                     and all(record['trees'][role]['manifest_sha256'] ==
                             _manifest_sha256(request['trees'][role]['files'])
                             for role in ROLES))
            try:
                validate_publication_record(record)
            except (SecurityError, KeyError, TypeError, ValueError):
                old_format = True
            else:
                old_format = False
        except (KeyError, TypeError, ValueError):
            match = False
    trees = {role: bool(tree_presence.get(role, False)) for role in sorted(ROLES)}
    return {'request_record_digest_match': match, 'tree_present': trees,
            'current_record_contract_pass': candidate and not old_format and match,
            'historical_record_only': old_format,
            'source_only_reuse_candidate': match and all(trees.values()),
            'authorized_for_schema2': False,
            'can_publish_without_operator': False}


def inspect_root_owned_pair(request_path: Path, record_path: Path):
    """Protected root reader; reject mutable paths; do not copy/rehash SDK trees."""
    request = _read_configuration(request_path)
    record = _read_configuration(record_path)
    if not isinstance(request, dict) or not isinstance(record, dict):
        raise SecurityError('root publication records must be objects')
    trees = {}
    for role in ROLES:
        expected = record_path.parent / role
        source = record.get('trees', {}).get(role, {}).get('source')
        # Do not trust a manifest's own arbitrary source or follow symlinks.
        try:
            info = expected.lstat()
            import stat
            trees[role] = (source == str(expected) and stat.S_ISDIR(info.st_mode)
                           and info.st_uid == 0 and not info.st_mode & 0o022)
        except OSError:
            trees[role] = False
    return inspect_pair(request, record, tree_presence=trees)


def audit_historical_publications(*, release_dir=Path('/opt/herdr/releases')):
    """Fixed known historical candidates only; no mutable path parameter via CLI."""
    rows = {}
    for prefix in ('p0-5035d92', 'p0-8e34c6f'):
        request = release_dir / f'{prefix}-publication-request.json'
        record = release_dir / f'{prefix}-test' / 'publication.json'
        try:
            rows[prefix] = inspect_root_owned_pair(request, record)
        except (SecurityError, OSError, ValueError, KeyError, TypeError) as exc:
            rows[prefix] = {'status': 'BLOCKED', 'error': type(exc).__name__,
                            'authorized_for_schema2': False}
    return {'schema_version': VERSION, 'status': 'OPERATOR_REVIEW_REQUIRED',
            'historical': rows, 'native_e2e_accepted': False,
            'root_publication_authorized': False}
