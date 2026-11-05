"""One bounded, private staging unit; broker only fixed parent host commands."""
from pathlib import Path
import hashlib
import json
import os
import signal
import stat
import subprocess
import time

import runpy
import sys
COMPOSITION_PATH,COMPOSITION_SHA=sys.argv[1:3]
_helpers=runpy.run_path(str(Path(__file__).resolve().parents[1]/'approved_pilot.py'),run_name='native_pilot_helpers')
_readiness_module=_helpers['_readiness']()
_composition=_helpers['_readiness']().load_composition(COMPOSITION_PATH,COMPOSITION_SHA)
sys.argv=[sys.argv[0],*sys.argv[3:]]
ROOT=Path(_composition['runtime']['root'])
PYTHON=_composition['runtime']['python']
CODE=Path(_composition['runtime']['code'])
HOME = Path('/home/agentops')
CONTROL = HOME / '.local/state/agent-stack/pilot-control-runtime-approved38'


def mount(args, fds=()):
    subprocess.run(['/usr/bin/mount', *args], check=True, pass_fds=fds,
                   stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)


def save(path, value, owner=0):
    _readiness_module.write_owned_json(path, value, owner=owner,
        mode=0o444 if owner == 0 else 0o600)


def drop():
    os.setgroups([]);os.setgid(1001);os.setuid(1001)


def main():
    assert os.geteuid() == 0
    replies = ROOT/'host-responses-approved38'
    replies.mkdir(mode=0o755)
    os.chown(replies, 0, 0)
    gh_fd = os.open('/home/agentops/.config/gh', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    guard_fd = os.open('/etc/herdr/heating-github-guard', os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW)
    mount(['--make-rprivate', '/'])
    pins = ROOT/'host-only-github-approved38'
    pins.mkdir(mode=0o700);os.chown(pins,0,0)
    for fd,name in ((gh_fd,'gh'),(guard_fd,'guard')):
        destination=pins/name;destination.mkdir(mode=0o700)
        mount(['--no-canonicalize','--bind','/proc/self/fd/'+str(fd),str(destination)],(fd,))
        mount(['--no-canonicalize','-o','remount,bind,ro',str(destination)])
        original=os.fstat(fd);actual=destination.stat()
        assert (original.st_dev,original.st_ino)==(actual.st_dev,actual.st_ino)
    mount(['--bind', str(ROOT / 'home-diagnostic15'), str(HOME.parent)])
    mount(['--bind', str(ROOT / 'etc-approved38'), '/etc/herdr'])
    for path, mode in (('/tmp', '1777'), ('/run/user', '755'), ('/run/herdr-launch-authority', '755')):
        Path(path).mkdir(parents=True, exist_ok=True)
        mount(['-t', 'tmpfs', '-o', 'mode=' + mode + ',size=268435456', 'tmpfs', path])
    Path('/run/user/1001').mkdir(mode=0o700);os.chown('/run/user/1001', 1001, 1001)
    mount(['--bind', str(ROOT / 'private-routing-diagnostic15'), '/var/lib/agent-platform-herdr'])
    policy = json.loads((ROOT / 'etc-approved38/host-policy.json').read_text())
    env = {'PATH': '/home/agentops/.local/bin:/usr/local/bin:/usr/bin:/bin',
           'HOME': str(HOME), 'LANG': 'C.UTF-8', 'SHELL': '/bin/bash',
           'XDG_RUNTIME_DIR': '/run/user/1001'}
    issuer_log = (ROOT / 'issuer-live-approved38.log').open('xb')
    issuer = subprocess.Popen([PYTHON, '-I', '-B',
        str(CODE/'scripts/serve-herdr-launch-plan-issuer.py')],
        env=env, stdout=issuer_log, stderr=subprocess.STDOUT)
    worker = None
    children = {}
    handled = set()
    try:
        deadline = time.monotonic() + 25
        while not Path('/run/herdr-launch-authority/issuer.sock').exists():
            assert issuer.poll() is None, 'private issuer exited'
            assert time.monotonic() < deadline, 'private issuer startup deadline'
            time.sleep(.1)
        log = (ROOT / 'ordinary-parent-live-approved38.log').open('xb')
        worker = subprocess.Popen([PYTHON, '-I', '-B', str(Path(__file__).with_name('parent.py')),COMPOSITION_PATH,COMPOSITION_SHA],
            cwd=HOME, env=env, preexec_fn=drop, stdout=log, stderr=subprocess.STDOUT)
        deadline = time.monotonic() + 4500
        while worker.poll() is None:
            assert issuer.poll() is None, 'private issuer exited'
            assert time.monotonic() < deadline, 'bounded private unit deadline'
            # The actual ordinary factory allocation owns the economic clock.
            for ledger in (ROOT/'home-diagnostic15/agentops/.local/state/herdr-policy-approved38/work-budget').glob('*/events.jsonl'):
                for line in ledger.read_bytes().split(b'\n')[:-1]:
                    row=json.loads(line);row=row.get('record',row)
                    if row.get('event')=='work_budget_allocation':
                        end=row['at_ms']/1000+row['allocation']['limits']['max_elapsed_ms']/1000
                        assert time.time()<end, 'canonical original task window exhausted; never readmit'
            fs = os.statvfs('/')
            assert fs.f_bavail * fs.f_frsize >= 9697230848, 'documented disk stop floor'
            for request in sorted((CONTROL / 'requests').glob('*.json')):
                if request.name in handled:
                    continue
                assert len(handled) < 100, 'finite host observations'
                handled.add(request.name)
                # Durable intent precedes each fixed external parent action.
                intent = ROOT / ('host-action-approved38-' + request.stem + '-intent.json')
                save(intent, {'request_sha256': hashlib.sha256(request.read_bytes()).hexdigest(),
                              'started_at_epoch': time.time(), 'automatic_retry_allowed': False})
                output = (ROOT / ('host-action-approved38-' + request.stem + '.log')).open('xb')
                command=_helpers['_readiness']().host_action_command(PYTHON,Path(__file__).with_name('host_action.py'),
                    COMPOSITION_PATH,COMPOSITION_SHA,request,gh_fd,guard_fd)
                process = subprocess.Popen(command, pass_fds=(gh_fd, guard_fd),
                    env=env, stdout=output, stderr=subprocess.STDOUT)
                children[request.name] = (process, output, time.monotonic(), request)
            for key, (process, output, started, request) in list(children.items()):
                assert time.monotonic() - started < 220, 'host action unresolved; do not repeat'
                if process.poll() is None:
                    continue
                output.close()
                response = {'ok': process.returncode == 0, 'exit_code': process.returncode}
                if request.stem.endswith('-publish') and response['ok']:
                    lines = (ROOT / ('host-action-approved38-' + request.stem + '.log')).read_text().splitlines()
                    receipt = json.loads(lines[-1]);response['pull_request'] = receipt['pull_request']
                save(replies / request.name, response)
                del children[key]
            time.sleep(.2)
        assert worker.returncode == 0, 'ordinary parent stopped; retain original'
        assert (CONTROL / 'completion.json').exists(), 'original completion unavailable'
        save(ROOT / 'ordinary-run-approved38-completed.json', json.loads((CONTROL / 'completion.json').read_text()))
    finally:
        os.close(gh_fd);os.close(guard_fd)
        if worker is not None and worker.poll() is None:
            worker.terminate()
        for process, output, _, _ in children.values():
            if process.poll() is None:process.terminate()
            output.close()
        if issuer.poll() is None:
            issuer.terminate()
            try:issuer.wait(timeout=5)
            except subprocess.TimeoutExpired:issuer.kill();issuer.wait()
        issuer_log.close()


if __name__ == '__main__':
    main()
