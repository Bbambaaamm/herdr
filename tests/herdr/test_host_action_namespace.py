import os
from pathlib import Path
import subprocess
import sys
import pytest
from herdr.operation_readiness import host_action_command


def test_credential_mount_action_cannot_start_in_the_coordinator_namespace(tmp_path):
    command=host_action_command(sys.executable,tmp_path/'action.py',tmp_path/'composition.json','frozen',tmp_path/'request.json',7,8)
    assert command[:3]==['/usr/bin/unshare','--mount','--fork']
    assert command[-2:]==['7','8']


@pytest.mark.skipif(sys.platform!='linux' or os.geteuid()!=0, reason='physical mount namespace requires administrator')
def test_private_host_action_mount_never_changes_parent_view(tmp_path):
    view=tmp_path/'view';view.write_text('coordinator-view')
    source=tmp_path/'source';source.write_text('private-host-credential-view')
    before=(view.stat().st_dev,view.stat().st_ino)
    script=tmp_path/'action.py'
    script.write_text("from pathlib import Path\nimport subprocess,sys\nsubprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)\nsubprocess.run(['/usr/bin/mount','--bind',sys.argv[3],sys.argv[1]],check=True)\nassert Path(sys.argv[1]).read_text()=='private-host-credential-view'\n")
    command=host_action_command(sys.executable,script,view,'unused',source,7,8)
    result=subprocess.run(command,capture_output=True,text=True,timeout=15)
    assert result.returncode==0,result.stderr
    assert view.read_text()=='coordinator-view' and (view.stat().st_dev,view.stat().st_ino)==before
