"""One isolated ordinary dispatch; no model/client/worker replacement."""
from pathlib import Path
import fcntl
import hashlib
import json
import os
import signal
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
CODE=Path(_composition['runtime']['code'])
SESSION = 'taskgraph77-approved38'
QUEUE = HOME / '.local/state/agent-stack/tasks'
CONTROL = HOME / '.local/state/agent-stack/pilot-control-runtime-approved38'
TASK = 'issue77-validation-repair-20261026'
NATIVE = HOME / '.local/bin/herdr'
sys.path[:0] = [str(CODE), str(CODE / 'agent-stack/bin'), '/opt/herdr/releases/p0-5035d92-test/hermes/venv/lib/python3.11/site-packages']
from agent_durable_sandbox import pane_input_ready, verify_pane_prompt
from herdr.launch_environment import process_environment
from agent_completion_evidence import store_for
from herdr.evidence import binding, digest
ENV = {'PATH': str(HOME / '.local/bin') + ':/usr/local/bin:/usr/bin:/bin', 'HOME': str(HOME), 'LANG': 'C.UTF-8', 'SHELL': '/bin/bash', 'XDG_RUNTIME_DIR': '/run/user/1001'}

def save(path, value):
    temporary = path.with_suffix('.tmp')
    with temporary.open('w') as stream:
        json.dump(value, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    temporary.chmod(384)
    os.replace(temporary, path)

def call(args, *, timeout_seconds=20):
    result = subprocess.run([str(NATIVE), '--session', SESSION, *args], env=ENV, capture_output=True, text=True, timeout=timeout_seconds)
    if result.returncode:
        raise RuntimeError('native operation denied: ' + json.dumps({'operation': args[:3], 'exit': result.returncode, 'error_sha256': hashlib.sha256(result.stderr.encode()).hexdigest()}))
    if args[:2] == ['pane', 'run']:
        if result.stdout.strip() or result.stderr.strip():
            raise RuntimeError('unexpected owned pane acknowledgement output')
        return None
    return json.loads(result.stdout)

def ready(pane, marker):
    deadline = time.monotonic() + 15
    while time.monotonic() < deadline:
        reply = call(['pane', 'process-info', '--pane', pane], timeout_seconds=3)
        info = reply.get('result', {}).get('process_info', {})
        if pane_input_ready(info, marker):
            verify_pane_prompt(call, pane, marker, timeout_seconds=10)
            return info
        time.sleep(0.05)
    raise RuntimeError('owned shell readiness denied')

def host_action(operation, context, **data):
    sequence = len(list((CONTROL / 'requests').glob('*.json')))
    identity = f'{sequence:04d}-{operation}'
    request = {'operation': operation, 'request_id': identity, 'native_context': context, **data}
    save(CONTROL / 'requests' / (identity + '.json'), request)
    response = CONTROL / 'responses' / (identity + '.json')
    deadline = time.monotonic() + 240
    while not response.exists():
        if time.monotonic() > deadline:
            raise RuntimeError('host action unresolved; original request retained')
        time.sleep(0.2)
    result = json.loads(response.read_text())
    if not result.get('ok'):
        raise RuntimeError('host action stopped; inspect original private evidence')
    return result

def canonical_task():
    matches = [QUEUE / state / (TASK + '.json') for state in ('running', 'blocked', 'failed', 'done', 'pending') if (QUEUE / state / (TASK + '.json')).exists()]
    if len(matches) != 1:
        raise RuntimeError('canonical task count differs from one')
    path = matches[0]
    return (path, json.loads(path.read_text()))

def worker_quiet():
    path = QUEUE / 'worker.loop.lock'
    if not path.exists():
        return False
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        return True
    finally:
        os.close(fd)

def budget_observation():
    reserved, started, settled = ({}, set(), set())
    for path in (HOME / '.local/state/herdr-policy-approved38/work-budget').glob('*/events.jsonl'):
        for line in path.read_text().splitlines():
            row = json.loads(line)
            if isinstance(row.get('record'), dict):
                row = row['record']
            event, operation = (row.get('event'), row.get('operation_id'))
            if event == 'work_budget_reserve' and row.get('operation_kind') == 'model':
                reserved[operation] = row
            elif event == 'work_budget_start':
                started.add(operation)
            elif event in ('work_budget_settle', 'work_budget_reconcile'):
                settled.add(operation)
    return {'model_reservations': len(reserved), 'model_started': len(set(reserved) & started), 'model_unsettled': len((set(reserved) & started) - settled)}

def progress(phase, **extra):
    record = {'phase': phase, 'at_epoch': time.time(), 'task': TASK, 'prior_unknown_model_reservations_held': 1, 'prior_unknown_held': True, 'cost_limit_microusd': 0, **budget_observation(), **extra}
    save(CONTROL / 'progress.json', record)

def main():
    CONTROL.mkdir(mode=448, parents=True, exist_ok=True)
    for name in ('requests', 'responses'):
        (CONTROL / name).mkdir(mode=448, exist_ok=True)
    assert not list((CONTROL / 'requests').glob('*.json'))
    log = (CONTROL / 'native-server.log').open('ab')
    workspace = HOME / 'worktrees/pilot/workspace'
    server = subprocess.Popen([str(NATIVE), '--session', SESSION, 'server'], cwd=workspace, env=ENV, stdout=log, stderr=log, start_new_session=True)
    published = None
    try:
        deadline = time.monotonic() + 25
        while True:
            if server.poll() is not None:
                raise RuntimeError('owned native server exited during startup')
            try:
                call(['workspace', 'list'], timeout_seconds=3)
                break
            except (RuntimeError, subprocess.TimeoutExpired):
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
        marker = 'pilot-coordinator-fsqlbiyr'
        layout = call(['workspace', 'create', '--cwd', str(workspace), '--label', 'Issue77 real bounded TaskGraph', '--env', 'HERDR_DURABLE_TASK_PANE=' + marker, '--no-focus'])['result']
        coordinator = layout['root_pane']['pane_id']
        ready(coordinator, marker)
        call(['agent', 'start', 'quantlab-hermes', '--kind', 'hermes', '--pane', coordinator, '--timeout', '60000', '--', '-p', 'quantlab', 'chat', '--model', 'meituan/longcat-2.0:free', '--continue', 'pilot-control-approved38', '--create-if-missing', '--in', str(workspace)], timeout_seconds=75)
        progress('coordinator_ready_no_prompt', coordinator_ui_started=True)
        marker = 'pilot-host-control-fsqlbiyr'
        tab = call(['tab', 'create', '--workspace', layout['workspace']['workspace_id'], '--cwd', str(workspace), '--label', 'Host control', '--env', 'HERDR_DURABLE_TASK_PANE=' + marker, '--no-focus'])['result']
        control_pane = tab['root_pane']['pane_id']
        info = ready(control_pane, marker)
        native_context = {key: value for key, value in process_environment(int(info['shell_pid'])).items() if key.startswith('HERDR_')}
        assert native_context.get('HERDR_ENV') == '1'
        progress('dispatching_one_original_task', task_submitted=False)
        host_action('dispatch', native_context)
        progress('ordinary_worker_running', task_submitted=True)
        deadline = time.monotonic() + 3600
        next_reconcile = 0
        while time.monotonic() < deadline:
            path, task = canonical_task()
            session = task.get('execution_session') or {}
            if session.get('pane_id') and (not session.get('economic_delivery_attempted')):
                observation = subprocess.run([str(NATIVE), '--session', SESSION, 'pane', 'read', session['pane_id'], '--lines', '80', '--format', 'text'], env=ENV, capture_output=True, timeout=5)
                save(CONTROL / 'owned-sdk-startup-observation.json', {'schema_version': 'herdr-owned-pre-delivery-pane-observation-1', 'task_prompt_not_delivered': True, 'exit_code': observation.returncode, 'stdout': observation.stdout[-65536:].decode(errors='replace'), 'stderr': observation.stderr[-4096:].decode(errors='replace')})
            if session.get('pane_id') and session.get('economic_delivery_attempted'):
                observation = subprocess.run([str(NATIVE), '--session', SESSION, 'pane', 'read', session['pane_id'], '--lines', '80', '--format', 'text'], env=ENV, capture_output=True, timeout=5)
                save(CONTROL / 'owned-sdk-post-delivery-observation.json', {'schema_version': 'herdr-owned-post-delivery-pane-observation-1', 'task_prompt_not_delivered': False, 'exit_code': observation.returncode, 'stdout': observation.stdout[-65536:].decode(errors='replace'), 'stderr': observation.stderr[-4096:].decode(errors='replace')})
            progress(task.get('attempt_state', path.parent.name), task_submitted=True, canonical_state=path.parent.name, verification_status=task.get('verification_status'), sdk_session_closed=bool(session.get('closed_at')), pull_request=published)
            if path.parent.name == 'done':
                assert task.get('verification_status') == 'accepted'
                save(CONTROL / 'completion.json', {'ordinary_worker_accepted': True, 'same_task_identity': True, 'pull_request': published, **budget_observation(), 'result_sha256': hashlib.sha256((QUEUE / 'results' / (TASK + '.json')).read_bytes()).hexdigest(), 'whole_issue77_complete': False})
                progress('accepted', pull_request=published)
                return
            if task.get('attempt_state') == 'verification_pending' and session.get('closed_at') and worker_quiet():
                if published is None:
                    plan = store_for(QUEUE, task).read('plan', digest(binding(task)))
                    result = host_action('publish', native_context, completion_identity=plan['identity'], completion_plan_hash=plan['plan_hash'], completion_spec_hash=plan['spec_hash'])
                    published = result['pull_request']
                    next_reconcile = time.monotonic()
                if time.monotonic() >= next_reconcile:
                    host_action('reconcile', native_context)
                    next_reconcile = time.monotonic() + 30
            elif path.parent.name in ('failed', 'blocked'):
                raise RuntimeError('original ordinary attempt stopped; no redispatch')
            elif path.parent.name == 'pending':
                raise RuntimeError('original worker retained pending state; no redispatch')
            time.sleep(2)
        raise RuntimeError('bounded original task deadline; no redispatch')
    except Exception as error:
        save(CONTROL / 'failure.json', {'error_type': type(error).__name__, 'error_sha256': hashlib.sha256(str(error).encode()).hexdigest(), 'automatic_retry_allowed': False, 'pull_request': published, **budget_observation()})
        progress('stopped_original_retained', pull_request=published)
        raise
    finally:
        if server.poll() is None:
            try:
                call(['server', 'stop'], timeout_seconds=10)
            except Exception:
                pass
            try:
                server.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(server.pid, signal.SIGTERM)
                try:
                    server.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    os.killpg(server.pid, signal.SIGKILL)
                    server.wait()
        log.close()
if __name__ == '__main__':
    main()
