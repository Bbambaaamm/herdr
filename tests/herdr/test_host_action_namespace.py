import os
from pathlib import Path
import subprocess
import sys
import pytest
from herdr.operation_readiness import host_action_command, ReadinessError
from herdr import operation_readiness as readiness


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


@pytest.fixture
def host_action_fixture(tmp_path):
    """Real source main/selector, synthetic UID-1001 queue, no external effects."""
    import ast
    import json
    import secrets
    from types import SimpleNamespace
    from herdr.evidence import binding

    if sys.platform != "linux" or os.geteuid() != 1001:
        pytest.skip("synthetic host request ownership requires Linux UID 1001")
    repo = Path(__file__).resolve().parents[2]
    host_path = repo / "deploy/herdr/native_pilot/host_action.py"
    parent_path = repo / "deploy/herdr/native_pilot/parent.py"
    root = tmp_path / "approved"
    queue = tmp_path / "queue"
    control = tmp_path / "control"
    for directory in (root, control / "requests", *(
            queue / s for s in ("pending", "running", "blocked", "failed", "done"))):
        directory.mkdir(parents=True, exist_ok=True)
    task = {
        "id": "issue77-validation-repair-20261026",
        "run_token": "retained-unit-run", "idempotency_key": "retained-unit-key",
        "attempt_id": 0, "attempts": 0, "fencing_token": 8, "max_attempts": 1,
        "attempt_state": "verification_pending",
        "completion_plan_pending": True,
        "execution_session": {"closed_at": "2026-10-29T00:00:00+00:00"},
    }
    expected = binding(task)
    (root / "same-identity-approved38.json").write_text(
        json.dumps({"identity": expected}))
    (root / "resume-task-reviewed-approved38.json").write_text(json.dumps(task))
    (root / "parent-public-summary.txt").write_text("synthetic reviewed artifact")
    observed = []

    class ObservedExec(Exception):
        pass

    def observe_exec(path, argv, env):
        observed.append(("exec", path, argv, env))
        raise ObservedExec()

    # Privileged execution and publication transports are intercepted. File
    # reads, metadata, identity/state/session guards and lookup run unchanged.
    class HostOS:
        def __getattr__(self, name):
            return getattr(os, name)
        def geteuid(self):
            return 0
        def setgroups(self, groups):
            observed.append(("setgroups", groups))
        def setgid(self, gid):
            observed.append(("setgid", gid))
        def setuid(self, uid):
            observed.append(("setuid", uid))
        execve = staticmethod(observe_exec)

    def publish(value, context):
        observed.append(("publish", value, context))
        return {"pull_request": 999, "fixture_only": True}

    namespace = {
        "Path": Path, "json": json, "stat": __import__("stat"),
        "os": HostOS(), "sys": SimpleNamespace(argv=[], path=[]), "time": __import__("time"),
        "secrets": secrets, "binding": binding, "publish": publish,
        "ROOT": root, "HOME": tmp_path, "QUEUE": queue, "TASK": task["id"],
        "CONTROL": control, "PYTHON": "/pinned/python", "CODE": tmp_path / "code",
        # Protected-root ownership is doubled; observation and file IPC are real.
        "_helpers": {'_readiness': lambda: SimpleNamespace(observe_task=readiness.observe_task,
            SnapshotChanged=readiness.SnapshotChanged, read_host_task_identity=lambda p: json.loads(p.read_bytes())['identity'])},
    }
    for path, name in ((host_path, "main"), (parent_path, "canonical_task")):
        node = next(n for n in ast.parse(path.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(path), "exec"),
             namespace)

    def place(directory, value=None):
        path = queue / directory / (task["id"] + ".json")
        path.write_text(json.dumps(task if value is None else value))
        return path

    def invoke(operation, **extra):
        request = {"operation": operation, "request_id": "request",
                   "native_context": {"HERDR_ENV": "1"}}
        if operation == "publish":
            request.update(completion_identity=expected,
                           completion_plan_hash="a" * 64,
                           completion_spec_hash=
                           "80802792c7b2790aac5a0ddc3557274e4030d822fb2f2ffa46551a6948a51e61")
        request.update(extra)
        path = control / "requests/request.json"
        path.write_text(json.dumps(request))
        path.chmod(0o600)
        descriptors = [os.open(os.devnull, os.O_RDONLY) for _ in range(2)]
        namespace["sys"].argv = ["host_action.py", str(path), *map(str, descriptors)]
        try:
            return namespace["main"]()
        finally:
            for fd in descriptors:
                try:
                    os.close(fd)
                except OSError:
                    pass

    return SimpleNamespace(task=task, expected=expected, place=place, invoke=invoke,
                           select=namespace["canonical_task"], observed=observed,
                           exec_error=ObservedExec, root=root, queue=queue)


@pytest.mark.parametrize('source,target', [('running','blocked'),('pending','running')])
@pytest.mark.parametrize('consumer', ['parent','host'])
def test_real_canonical_reader_survives_atomic_move(host_action_fixture, monkeypatch, source, target, consumer):
    f=host_action_fixture; old=f.place(source); new=f.queue/target/old.name
    original=os.stat; moved=[]
    def during_scan(path, *args, **kwargs):
        directory=Path(os.readlink('/proc/self/fd/'+str(kwargs['dir_fd']))) if 'dir_fd' in kwargs else Path(path).parent
        trigger=Path(path).name==old.name and directory.name=='running' and not moved
        try:return original(path,*args,**kwargs)
        finally:
            if trigger:old.rename(new);moved.append(True)
    monkeypatch.setattr(os,'stat',during_scan)
    if consumer=='parent':assert f.select()[0]==new
    else:
        with pytest.raises(f.exec_error):f.invoke('reconcile')
        assert f.observed[-1][2][-1]==str(new)
    assert moved==[True] and not old.exists()


@pytest.mark.parametrize("directory", ["running", "blocked", "done"])
@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_closed_verification_task_uses_same_canonical_path_as_parent(
        host_action_fixture, directory, operation):
    f = host_action_fixture
    path = f.place(directory)
    before = path.read_bytes()
    assert f.select()[0] == path
    if operation == "publish":
        assert f.invoke(operation) == {"pull_request": 999, "fixture_only": True}
        assert f.observed[-1][0] == "publish"
        assert f.observed[-1][1]["permit"]["identity"] == f.expected
    else:
        with pytest.raises(f.exec_error):
            f.invoke(operation)
        assert f.observed[-1][2][-2:] == [
            "agent-stack/bin/agent-task-worker", str(path)]
    assert path.read_bytes() == before


@pytest.mark.parametrize("state", [
    "terminal_unknown", "delivery_uncertain", "failed", "working", "completed"])
@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_blocked_non_verification_states_never_reach_host_effect(
        host_action_fixture, state, operation):
    f = host_action_fixture
    f.task["attempt_state"] = state
    path = f.place("blocked")
    before = path.read_bytes()
    with pytest.raises(AssertionError):
        f.invoke(operation)
    assert not f.observed and path.read_bytes() == before


@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_blocked_verification_requires_closed_session(host_action_fixture, operation):
    f = host_action_fixture
    f.task["execution_session"] = {}
    f.place("blocked")
    with pytest.raises(AssertionError):
        f.invoke(operation)
    assert not f.observed


@pytest.mark.parametrize("field,value", [
    ("run_token", "other-run"), ("idempotency_key", "other-key"),
    ("fencing_token", 9)])
@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_blocked_verification_keeps_original_identity_guard(
        host_action_fixture, field, value, operation):
    f = host_action_fixture
    f.task[field] = value
    f.place("blocked")
    with pytest.raises(ReadinessError, match='identity_changed'):
        f.invoke(operation)
    assert not f.observed


@pytest.mark.parametrize("other", ["running", "done", "pending", "failed"])
@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_duplicate_blocked_and_other_canonical_task_is_rejected(
        host_action_fixture, other, operation):
    f = host_action_fixture
    f.place("blocked")
    f.place(other)
    with pytest.raises(RuntimeError, match="canonical task count"):
        f.select()
    with pytest.raises(ReadinessError, match='canonical task count'):
        f.invoke(operation)
    assert not f.observed


@pytest.mark.parametrize("directory", ["pending", "failed"])
@pytest.mark.parametrize("operation", ["publish", "reconcile"])
def test_non_publishable_queue_directory_is_not_admitted(
        host_action_fixture, directory, operation):
    f = host_action_fixture
    f.place(directory)
    with pytest.raises(AssertionError):
        f.invoke(operation)
    assert not f.observed


def test_publish_retains_request_completion_identity_check(host_action_fixture):
    f = host_action_fixture
    f.place("blocked")
    changed = dict(f.expected, run_token="other-request")
    with pytest.raises(AssertionError):
        f.invoke("publish", completion_identity=changed)
    assert not f.observed


def test_dispatch_still_rejects_blocked_terminal_unknown(host_action_fixture):
    f = host_action_fixture
    f.task["attempt_state"] = "terminal_unknown"
    path = f.place("blocked")
    before = path.read_bytes()
    with pytest.raises(AssertionError):
        f.invoke("dispatch")
    assert not f.observed and path.read_bytes() == before


def test_pending_dispatch_contract_is_unchanged(host_action_fixture):
    f = host_action_fixture
    f.task["attempt_state"] = "pending"
    f.place("pending")
    (f.root / "resume-task-reviewed-approved38.json").write_text(
        __import__("json").dumps(f.task))
    with pytest.raises(f.exec_error):
        f.invoke("dispatch")
    assert f.observed[-1][2][-1] == "agent-stack/bin/agent-task-dispatcher"


@pytest.fixture
def parent_completion_fixture(tmp_path):
    """Run the actual coordinator loop with synthetic task files and transports."""
    import ast
    import json
    from types import SimpleNamespace
    from herdr.evidence import binding, digest

    repo = Path(__file__).resolve().parents[2]
    source = repo / "deploy/herdr/native_pilot/parent.py"
    queue, control = tmp_path / "queue", tmp_path / "control"
    for state in ("running", "blocked", "failed", "done", "pending", "results"):
        (queue / state).mkdir(parents=True)
    task = {"id": "synthetic-original-task", "run_token": "same-run",
            "idempotency_key": "same-key", "fencing_token": 8,
            "attempt_id": 0, "attempts": 0, "max_attempts": 1,
            "attempt_state": "verification_pending", "execution_session": {}}
    (tmp_path / 'same-identity-approved38.json').write_text(json.dumps({'identity': binding(task)}))
    events, stops = [], []
    config = {"directory": "blocked", "closed": False, "quiet": False,
              "release": True, "step": 2, "reconciliations": 1}
    clock = SimpleNamespace(now=0, sleeps=0)

    def path():
        return queue / config["directory"] / (task["id"] + ".json")

    def save(target, value):
        target.write_text(json.dumps(value))

    def sleep(seconds):
        clock.sleeps += 1
        clock.now += config["step"]
        if config["release"]:
            config["quiet"] = True
            task["execution_session"]["closed_at"] = "synthetic-closed"
            if path().exists():
                save(path(), task)

    server = SimpleNamespace(poll=lambda: 0 if stops else None,
                             wait=lambda **kw: 0)
    def call(args, **kw):
        if args[:2] == ["workspace", "create"]:
            return {"result": {"root_pane": {"pane_id": "coordinator"},
                               "workspace": {"workspace_id": "workspace"}}}
        if args[:2] == ["tab", "create"]:
            return {"result": {"root_pane": {"pane_id": "control"}}}
        if args == ["server", "stop"]:
            stops.append(True)
        return {}

    def host_action(operation, context, **data):
        events.append((operation, clock.sleeps))
        if operation == "publish":
            assert data["completion_identity"] == binding(task)
            assert task["execution_session"].get("closed_at") and config["quiet"]
            return {"pull_request": 999}
        if operation == "reconcile":
            if sum(e[0] == "reconcile" for e in events) == config["reconciliations"]:
                path().unlink()
                done = dict(task, verification_status="accepted")
                save(queue / "done" / (task["id"] + ".json"), done)
                (queue / "results" / (task["id"] + ".json")).write_text("{}")
        return {}

    def read_plan(kind, identity):
        assert kind == "plan" and identity == digest(binding(task))
        return {"identity": binding(task), "plan_hash": "a" * 64,
                "spec_hash": "b" * 64}

    def no_real_process(*args, **kwargs):
        raise AssertionError("unexpected real process transport")

    namespace = {
        "Path": Path, "json": json, "hashlib": __import__("hashlib"),
        "subprocess": SimpleNamespace(Popen=lambda *a, **kw: server,
            run=no_real_process, TimeoutExpired=subprocess.TimeoutExpired),
        "os": SimpleNamespace(killpg=no_real_process), "signal": __import__("signal"),
        "time": SimpleNamespace(monotonic=lambda: clock.now, sleep=sleep),
        "CONTROL": control, "HOME": tmp_path, "QUEUE": queue, "TASK": task["id"],
        "NATIVE": Path("/synthetic/native"), "SESSION": "synthetic", "ENV": {},
        "save": save, "call": call, "ready": lambda *a: {"shell_pid": 1},
        "process_environment": lambda p: {"HERDR_ENV": "1"},
        "progress": lambda *a, **kw: None, "host_action": host_action,
        "worker_quiet": lambda: config["quiet"], "budget_observation": lambda: {},
        "store_for": lambda *a: SimpleNamespace(read=read_plan),
        "binding": binding, "digest": digest,
        "ROOT": tmp_path,
        "_helpers": {'_readiness': lambda: SimpleNamespace(observe_task=readiness.observe_task,
            SnapshotChanged=readiness.SnapshotChanged, read_host_task_identity=lambda p: json.loads(p.read_bytes())['identity'])},
    }
    for name in ("canonical_task", "main"):
        node = next(n for n in ast.parse(source.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == name)
        exec(compile(ast.Module(body=[node], type_ignores=[]), str(source), "exec"),
             namespace)

    def invoke(**changes):
        config.update(changes)
        if config["closed"]:
            task["execution_session"]["closed_at"] = "synthetic-closed"
        save(path(), task)
        return namespace["main"]()

    return SimpleNamespace(invoke=invoke, task=task, events=events, stops=stops,
                           clock=clock, path=path, config=config)


@pytest.mark.parametrize("directory", ["blocked", "running"])
@pytest.mark.parametrize("closed,quiet", [(False, True), (True, False), (False, False)])
def test_parent_waits_for_original_worker_cleanup(
        parent_completion_fixture, directory, closed, quiet):
    f = parent_completion_fixture
    f.invoke(directory=directory, closed=closed, quiet=quiet)
    assert [e[0] for e in f.events] == ["dispatch", "publish", "reconcile"]
    assert all(tick >= 1 for op, tick in f.events if op != "dispatch")
    assert len(f.stops) == 1


@pytest.mark.parametrize("closed,quiet", [(False, True), (True, False), (False, False)])
def test_parent_cleanup_wait_retains_original_deadline(
        parent_completion_fixture, closed, quiet):
    f = parent_completion_fixture
    with pytest.raises(RuntimeError, match="bounded original task deadline"):
        f.invoke(closed=closed, quiet=quiet, release=False, step=1200)
    assert [e[0] for e in f.events] == ["dispatch"]
    assert f.clock.sleeps == 3 and f.path().exists() and len(f.stops) == 1


@pytest.mark.parametrize("state", [
    "terminal_unknown", "delivery_uncertain", "failed", "working", "completed"])
def test_parent_does_not_wait_for_non_verification_blocker(parent_completion_fixture, state):
    f = parent_completion_fixture
    f.task["attempt_state"] = state
    with pytest.raises(RuntimeError, match="original ordinary attempt stopped"):
        f.invoke()
    assert [e[0] for e in f.events] == ["dispatch"] and f.clock.sleeps == 0
    assert f.path().exists() and len(f.stops) == 1


@pytest.mark.parametrize("directory", ["failed", "pending"])
def test_parent_cleanup_wait_does_not_admit_other_queues(parent_completion_fixture, directory):
    f = parent_completion_fixture
    with pytest.raises(RuntimeError, match="no redispatch"):
        f.invoke(directory=directory)
    assert [e[0] for e in f.events] == ["dispatch"] and f.clock.sleeps == 0


def test_parent_publishes_once_during_reconciliation_wait(parent_completion_fixture):
    f = parent_completion_fixture
    f.invoke(reconciliations=2)
    assert [e[0] for e in f.events] == ["dispatch", "publish", "reconcile", "reconcile"]
    assert len(f.stops) == 1


def test_parent_snapshot_changes_keep_original_deadline(parent_completion_fixture,monkeypatch):
    f=parent_completion_fixture
    def changing(*args,**kwargs):raise readiness.SnapshotChanged('controlled changing snapshot')
    monkeypatch.setattr(readiness,'observe_task',changing)
    with pytest.raises(RuntimeError,match='bounded original task deadline'):
        f.invoke(step=1200)
    assert f.clock.sleeps==3 and [op for op,_ in f.events]==['dispatch']
    assert len(f.stops)==1
