"""Fixed host commands in a private credential namespace; no SDK execution."""
from pathlib import Path
import ctypes
import secrets
import signal
import socket
import hashlib
import json
import os
import stat
import subprocess
import sys
import time

import runpy
import sys
COMPOSITION_PATH,COMPOSITION_SHA=sys.argv[1:3]
_helpers=runpy.run_path(str(Path(__file__).resolve().parents[1]/'approved_pilot.py'),run_name='native_pilot_helpers')
_composition=_helpers['_readiness']().load_composition(COMPOSITION_PATH,COMPOSITION_SHA)
sys.argv=[sys.argv[0],*sys.argv[3:]]
ROOT=Path(_composition['runtime']['root'])
HOME = Path('/home/agentops')
QUEUE = HOME / '.local/state/agent-stack/tasks'
TASK = 'issue77-validation-repair-20261026'
CONTROL = HOME / '.local/state/agent-stack/pilot-control-runtime-approved38'
PYTHON = '/opt/herdr/releases/p0-5035d92-test/python/bin/python3.11'
CODE=Path(_composition['runtime']['code'])
sys.path.insert(0, str(CODE))
from herdr.evidence import binding


def environment(context):
    return {'PATH': '/home/agentops/.local/bin:/usr/local/bin:/usr/bin:/bin',
            'HOME': str(HOME), 'LANG': 'C.UTF-8', 'SHELL': '/bin/bash',
            'XDG_RUNTIME_DIR': '/run/user/1001', **context}


def publisher_child(target, root_pid):
    assert os.geteuid() == 0 and os.getppid() == root_pid
    libc = ctypes.CDLL(None, use_errno=True)
    assert libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0 and os.getppid() == root_pid
    subprocess.run(['/usr/bin/mount', '--make-rprivate', '/'], check=True)
    # This is a new mount namespace. Mask host credentials before ANY
    # unprivileged exec, including its initial dumpable interpreter window.
    from herdr.policy_launch import _verify_root_owned_ancestry
    for path in (ROOT/'host-only-github-approved38', Path('/etc/herdr/heating-github-guard')):
        _verify_root_owned_ancestry(path)
        held = os.open(path, os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            before, named = os.fstat(held), path.stat()
            assert (before.st_dev,before.st_ino)==(named.st_dev,named.st_ino)
            subprocess.run(['/usr/bin/mount', '--no-canonicalize', '-t', 'tmpfs', '-o',
                'mode=700,size=4096', 'tmpfs', '/proc/self/fd/'+str(held)],
                check=True, pass_fds=(held,))
            masked=path.stat()
            assert (masked.st_dev,masked.st_ino)!=(before.st_dev,before.st_ino)
            assert masked.st_uid==0 and stat.S_IMODE(masked.st_mode)==0o700
        finally:
            os.close(held)
    os.setgroups([]); os.setgid(1001); os.setuid(1001)
    assert libc.prctl(1, signal.SIGKILL, 0, 0, 0) == 0 and os.getppid() == root_pid
    command = [PYTHON, '-I', '-B', str(CODE/'agent-stack/bin/agent-herdr-host-entrypoint'),
               'scripts/publish-herdr-parent-result.py', '--permit', str(target)]
    os.execve(command[0], command, dict(os.environ))


def publish(value, context):
    from herdr.parent_publication import ParentPublicationPermit
    from herdr.parent_github_transport import GitHubParentTransport
    from herdr.parent_github_peer import serve_parent_transport
    permit = ParentPublicationPermit(**value['permit'])
    # dispatch/reconcile never mount credentials. Only this root executor does.
    subprocess.run(['/usr/bin/mount', '--make-rprivate', '/'], check=True)
    # The original gh directory is already pinned beneath root-only ancestry.
    # Never bind it beneath mutable HOME/.config, even in a privileged child.
    descriptor = os.open(ROOT/'host-only-github-approved38/guard', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        target = Path('/etc/herdr/heating-github-guard')
        subprocess.run(['/usr/bin/mount', '--no-canonicalize', '--bind', '/proc/self/fd/'+str(descriptor),
                        str(target)], check=True, pass_fds=(descriptor,))
        subprocess.run(['/usr/bin/mount', '--no-canonicalize', '-o', 'remount,bind,ro', str(target)], check=True)
        held, observed = os.fstat(descriptor), target.stat()
        assert (held.st_dev,held.st_ino)==(observed.st_dev,observed.st_ino)
    finally:
        os.close(descriptor)

    client = GitHubParentTransport(repo=permit.repo, scratch=ROOT/'root-parent-transport-approved38',
        gh=Path('/usr/local/libexec/herdr-heating-guard/gh'), home=HOME,
        config_dir=ROOT/'host-only-github-approved38/gh')
    target = ROOT/'parent-publication-permit-approved38.json'
    _helpers['_readiness']().write_owned_json(target, value)
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as listener:
        listener.bind('\0'+value['transport']['address'])
        listener.listen(4)
        child = subprocess.Popen(['/usr/bin/unshare', '--mount', '--', PYTHON, '-I', '-B',
            str(Path(__file__).resolve()), COMPOSITION_PATH, COMPOSITION_SHA,
            '--publisher-child', str(target), str(os.getpid())],
            env=environment(context), close_fds=True, start_new_session=True)
        try:
            return serve_parent_transport(listener, child, permit=permit, transport=client)
        finally:
            try:
                os.killpg(child.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            child.wait(timeout=3)


def main():
    assert os.geteuid() == 0 and len(sys.argv) == 4
    request_path = Path(sys.argv[1])
    assert request_path.parent == CONTROL / 'requests'
    fd = os.open(request_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        assert stat.S_ISREG(st.st_mode) and st.st_uid == 1001 and st.st_nlink == 1
        assert stat.S_IMODE(st.st_mode) == 0o600 and 0 < st.st_size <= 65536
        raw = os.read(fd, 65537)
        assert len(raw) == st.st_size and os.fstat(fd).st_mtime_ns == st.st_mtime_ns
    finally:
        os.close(fd)
    request = json.loads(raw)
    operation = request['operation']
    assert operation in ('dispatch', 'publish', 'reconcile')
    assert request_path.name == request['request_id'] + '.json'
    assert set(request) == ({'operation', 'request_id', 'native_context'} |
        ({'completion_identity', 'completion_plan_hash', 'completion_spec_hash'}
         if operation == 'publish' else set()))
    context = request['native_context']
    assert isinstance(context, dict) and context.get('HERDR_ENV') == '1'
    assert len(context) <= 40 and all(isinstance(k, str) and k.startswith('HERDR_')
        and isinstance(v, str) and len(v) <= 4096 and '\0' not in v
        for k, v in context.items())
    os.close(int(sys.argv[2])); os.close(int(sys.argv[3]))
    prefix = [PYTHON, '-I', '-B', str(CODE / 'agent-stack/bin/agent-herdr-host-entrypoint')]
    if operation == 'dispatch':
        assert not any((QUEUE / state / (TASK + '.json')).exists()
            for state in ('running', 'done', 'blocked', 'failed'))
        task = json.loads((ROOT / 'resume-task-reviewed-approved38.json').read_text())
        assert task['id'] == TASK and task['max_attempts'] == 1
        target = QUEUE / 'pending' / (TASK + '.json')
        assert target.exists() and json.loads(target.read_text()) == task
        assert binding(task) == json.loads((ROOT/'same-identity-approved38.json').read_text())['identity']
        assert task.get('completion_plan_pending') is True
        command = prefix + ['agent-stack/bin/agent-task-dispatcher']
    else:
        matches = [QUEUE / state / (TASK + '.json') for state in ('running', 'done')
                   if (QUEUE / state / (TASK + '.json')).exists()]
        assert len(matches) == 1
        task = json.loads(matches[0].read_text())
        assert task['attempt_state'] == 'verification_pending' and binding(task) == json.loads((ROOT/'same-identity-approved38.json').read_text())['identity']
        assert task.get('execution_session', {}).get('closed_at')
        if operation == 'reconcile':
            command = prefix + ['agent-stack/bin/agent-task-worker', str(matches[0])]
        else:
            sys.path.insert(0, str(CODE))
            assert binding(task) == request['completion_identity']
            assert request['completion_spec_hash'] == '80802792c7b2790aac5a0ddc3557274e4030d822fb2f2ffa46551a6948a51e61'
            assert len(request['completion_plan_hash']) == 64
            permit = {'version': 1, 'permit': {
                'identity': binding(task), 'repo': 'Bbambaaamm/herdr',
                'spec_hash': request['completion_spec_hash'],
                'plan_hash': request['completion_plan_hash'],
                'base_sha': '687c0c5041d9871c5a2eb0d4a116673b09c85438',
                'base_branch': 'review/issue77-retained-business-20261026-v5',
                'head_branch': 'herdr/issue77-validation-20261026-fsqlbiyr',
                'expires_at_epoch': int(time.time()) + 1800,
                'public_summary': (ROOT / 'parent-public-summary.txt').read_text()},
                'transport': {'mode': 'root-peer', 'address': 'herdr-parent-'+secrets.token_hex(24),
                              'root_pid': os.getpid()}}
            return publish(permit, context)
    env = {'PATH': '/home/agentops/.local/bin:/usr/local/bin:/usr/bin:/bin',
           'HOME': str(HOME), 'LANG': 'C.UTF-8', 'SHELL': '/bin/bash',
           'XDG_RUNTIME_DIR': '/run/user/1001', **context}
    os.setgroups([]); os.setgid(1001); os.setuid(1001)
    os.execve(command[0], command, env)


if __name__ == '__main__':
    if len(sys.argv) == 4 and sys.argv[1] == '--publisher-child':
        publisher_child(Path(sys.argv[2]), int(sys.argv[3]))
    else:
        raise SystemExit(main())
