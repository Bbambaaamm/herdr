"""Import real consumers from a private archive selected by the release payload."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

import pytest

from herdr import release


SOURCE_ROOT = Path(release.__file__).resolve().parents[1]

# This fixed fixture program is the sole subprocess. It loads no site packages,
# credentials or checkout modules and cannot start a collector or another process.
IMPORT_PROBE = r'''
import importlib
import json
import pathlib
import sys

payload = pathlib.Path(sys.argv[1]).resolve()
mode = sys.argv[2]
assert sys.flags.isolated and sys.flags.no_site and sys.dont_write_bytecode
assert mode in {'contract', 'consumers'}
sys.path.insert(0, str(payload))

def audit(event, args):
    if event.startswith('socket.') or event in {
        'subprocess.Popen', 'os.system', 'os.exec', 'os.fork', 'os.posix_spawn',
        'os.remove', 'os.rename', 'os.rmdir', 'os.mkdir', 'os.chmod', 'os.symlink', 'os.link',
    }:
        raise AssertionError('packaged import attempted an external effect: ' + event)
    if event == 'open':
        flags = args[2] if len(args) > 2 else 0
        # os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
        import os
        if flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            raise AssertionError('packaged import attempted a file write')

sys.addaudithook(audit)
contract = importlib.import_module('agent_platform_dashboard.production_contract')
snapshot = contract.unavailable(1000)
assert contract.MAX_BYTES == 131072
assert len(contract.encode(snapshot)) <= contract.MAX_BYTES
if mode == 'consumers':
    for name in (
        'agent_platform_dashboard.production_export',
        'agent_platform_dashboard.production_herdr',
        'agent_platform_dashboard.production_web',
        'herdr.mcp', 'herdr.memory',
    ):
        importlib.import_module(name)
    assert hasattr(sys.modules['herdr.mcp'], 'ToolSelection')
    assert hasattr(sys.modules['herdr.memory'], 'MemoryProposal')
origins = {}
for name, module in tuple(sys.modules.items()):
    if name.split('.')[0] not in {'agent_platform_dashboard', 'herdr'}:
        continue
    origin = pathlib.Path(module.__file__).resolve()
    assert origin.is_relative_to(payload), (name, str(origin))
    origins[name] = origin.relative_to(payload).as_posix()
assert origins['agent_platform_dashboard.observability'] == 'agent_platform_dashboard/observability.py'
print(json.dumps({'mode': mode, 'origins': origins, 'isolated': True, 'site': False,
                  'snapshot_bytes': len(contract.encode(snapshot))}, sort_keys=True))
'''


def selected_runtime_files():
    """Use the actual path allowlist; do not smuggle missing dependencies in."""
    selected = {}
    for package in ('agent_platform_dashboard', 'herdr'):
        for path in sorted((SOURCE_ROOT / package).rglob('*')):
            if (not path.is_file() or path.is_symlink()
                    or '__pycache__' in path.parts or path.suffix not in {'.py', '.json'}):
                continue
            relative = path.relative_to(SOURCE_ROOT).as_posix()
            if any(relative == prefix or relative.startswith(prefix + '/')
                   for prefix in release.PAYLOAD_PATHS):
                selected[relative] = path.read_bytes().replace(b'\r\n', b'\n')
    return selected


@pytest.fixture
def staged_runtime_payload(tmp_path):
    selected = selected_runtime_files()
    # Materialize the selected bytes through a real tar and the release extractor.
    archive_path = tmp_path / 'runtime-payload.tar'
    with tarfile.open(archive_path, 'w', format=tarfile.PAX_FORMAT) as archive:
        for relative, data in sorted(selected.items()):
            member = tarfile.TarInfo(relative)
            member.size = len(data)
            member.mode = 0o644
            archive.addfile(member, io.BytesIO(data))
    stage = tmp_path / 'payload'
    with tarfile.open(archive_path, 'r:') as archive:
        release.safe_extract(archive, stage)
    # The isolated program and its home/cwd are outside the staged package.
    home, cwd = tmp_path / 'empty-home', tmp_path / 'empty-cwd'
    home.mkdir(); cwd.mkdir()
    probe = cwd / 'release_payload_import_probe.py'
    probe.write_bytes(IMPORT_PROBE.encode('utf-8'))
    return stage, home, cwd, probe, selected


@pytest.mark.parametrize('mode', [
    'contract',
    pytest.param('consumers', marks=pytest.mark.skipif(os.name != 'posix',
        reason='Production consumers use the real Linux fcntl boundary')),
])
def test_packaged_consumers_import_only_shipped_modules(staged_runtime_payload, mode):
    stage, home, cwd, probe, selected = staged_runtime_payload
    environment = {'PATH': os.defpath, 'LANG': 'C.UTF-8', 'HOME': str(home),
                   'USERPROFILE': str(home)}
    if os.name == 'nt' and os.environ.get('SYSTEMROOT'):
        environment['SYSTEMROOT'] = os.environ['SYSTEMROOT']
    result = subprocess.run([sys.executable, '-I', '-S', '-B', str(probe), str(stage), mode],
        cwd=cwd, env=environment, capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, (result.stdout, result.stderr)
    value = json.loads(result.stdout)
    assert value['mode'] == mode and value['isolated'] and value['site'] is False
    assert value['snapshot_bytes'] <= 131072
    assert (stage / 'agent_platform_dashboard/observability.py').read_bytes() == selected[
        'agent_platform_dashboard/observability.py']
    assert list(home.iterdir()) == []
    assert sorted(path.name for path in cwd.iterdir()) == ['release_payload_import_probe.py']
    assert not any(stage.rglob('__pycache__'))
