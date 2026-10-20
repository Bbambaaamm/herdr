"""Pinned SDK initialization inside the real read-only private HOME/FD launcher."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

import pytest

from herdr.private_profile_namespace import PrivateProfileSnapshot
from tests.herdr.test_private_profile_fd_bridge import bridge_module, command_for

SDK = Path('/opt/herdr/releases/p0-5035d92-test/hermes')
PYTHON = Path('/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11')


def test_sdk_skeleton_adds_no_writable_profile_mounts(tmp_path):
    source = tmp_path/'approved'
    source.mkdir()
    values = {'config.yaml':b'fixture: true\n','.env':b'# no credentials\n'}
    for name, value in values.items(): (source/name).write_bytes(value)
    with PrivateProfileSnapshot.from_approved(source,name='quantlab',approved_sha256={
            name:hashlib.sha256(value).hexdigest() for name,value in values.items()}) as snapshot:
        args = snapshot.mount_arguments()
        for name in ('cron','memories','pairing','hooks','image_cache','audio_cache','skills'):
            index = args.index(str(snapshot.destination/name))
            assert args[index-1] == '--dir'
        writable = {args[index+1] for index,option in enumerate(args) if option=='--tmpfs'}
        assert writable == {str(snapshot.home), *(str(snapshot.destination/name) for name in ('sessions','cache','logs','pastes'))}
        assert args[-2:] == ['--remount-ro',str(snapshot.home)]


def test_pinned_sdk_initializes_without_writing_approved_profile(tmp_path):
    if not SDK.is_dir() or not PYTHON.is_file() or not Path('/home/agentops').is_dir() or not shutil.which('bwrap'):
        pytest.skip('fixed pinned Hermes SDK and Linux staging home required')
    source = tmp_path / 'approved'
    source.mkdir()
    values = {'config.yaml': b'model:\n  provider: none\n  default: fixture\n',
              '.env': b'# isolated compatibility fixture\n', 'SOUL.md': b'You are the isolated profile compatibility fixture.\n'}
    for name, value in values.items(): (source / name).write_bytes(value)
    before = {name: hashlib.sha256(value).hexdigest() for name, value in values.items()}
    profile = '/home/agentops/.hermes/profiles/quantlab'
    script = '''
import errno,json,os,sys
from pathlib import Path
sdk,profile=Path(sys.argv[1]),Path(sys.argv[2])
os.environ['HERMES_HOME']=str(profile)
os.environ['HERMES_SAFE_MODE']='1'
os.environ['HERMES_ENABLE_PROJECT_PLUGINS']='0'
sys.path[:0]=[str(sdk),str(sdk/'venv/lib/python3.11/site-packages')]
from hermes_cli.config import ensure_hermes_home,_HERMES_HOME_SUBDIRS
ensure_hermes_home()
assert all((profile/name).is_dir() for name in _HERMES_HOME_SUBDIRS)
for name in ('cron','memories','pairing','hooks','image_cache','audio_cache','skills'):
 try: (profile/name/'forbidden').write_text('must stay read-only')
 except OSError as error: assert error.errno==errno.EROFS
 else: raise AssertionError('approved profile skeleton became writable')
try: (profile/'config.yaml').write_text('must stay immutable')
except OSError as error: assert error.errno==errno.EROFS
else: raise AssertionError('profile configuration became writable')
(profile/'logs'/'allowed').write_text('private runtime only')
print(json.dumps({'pinned_sdk_initialization':True,'profile_readonly':True,'private_logs_writable':True}))
'''
    with PrivateProfileSnapshot.from_approved(source, name='quantlab', approved_sha256=before) as snapshot:
        command = command_for(bridge_module(), snapshot)
        command.insert(command.index('--unshare-pid'), '--unshare-net')
        index = command.index('--')
        command[index:] = ['--', str(PYTHON), '-I', '-B', '-c', script, str(SDK), profile]
        result = subprocess.run(command, capture_output=True, text=True, timeout=45)
        if 'Operation not permitted' in result.stderr or 'Creating new namespace failed' in result.stderr:
            pytest.skip('unprivileged namespaces disabled by runner')
        assert result.returncode == 0, result.stdout + result.stderr
        assert json.loads(result.stdout) == {'pinned_sdk_initialization':True,'profile_readonly':True,'private_logs_writable':True}
    assert {name: hashlib.sha256((source/name).read_bytes()).hexdigest() for name in values} == before
