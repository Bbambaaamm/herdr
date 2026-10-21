"""Bridge readiness regressions; real children/sockets, no task/provider execution."""
from pathlib import Path
from types import SimpleNamespace
import os, socket, struct, subprocess, sys, time, uuid
import pytest
from tests.agent_stack.test_automatic_host_entrypoints import load

@pytest.fixture
def startup(tmp_path,monkeypatch):
    worker=load('bridge_deadline_'+uuid.uuid4().hex,'agent-task-worker')
    worker.LOGS=tmp_path/'logs'
    path=tmp_path/'task.json';path.write_text('{}')
    task={'id':'bridge-startup-'+uuid.uuid4().hex,'run_token':uuid.uuid4().hex,'task_file':str(path)}
    session={'agent_name':'offline-startup-test','pane_id':'synthetic-pane','pane_marker':'synthetic-marker'}
    monkeypatch.setattr(worker,'persist_execution_session',lambda task:None)
    return worker,task,session

@pytest.fixture
def simulated(startup,monkeypatch):
    worker,task,session=startup
    state={'time':0.0,'ready_after':0.0,'peer_pid':123,'peer_uid':os.getuid(),'credentials':None}
    process=SimpleNamespace(pid=123,poll=lambda:None)
    monkeypatch.setattr(worker,'host_entrypoint_command',lambda *a,**kw:['/synthetic/python',*a[1]])
    monkeypatch.setattr(worker.subprocess,'Popen',lambda *a,**kw:process)
    monkeypatch.setattr(worker,'process_start_ticks',lambda pid:44)
    monkeypatch.setattr(worker.time,'monotonic',lambda:state['time'])
    monkeypatch.setattr(worker.time,'sleep',lambda value:state.__setitem__('time',state['time']+value))
    class Socket:
        def __enter__(self):return self
        def __exit__(self,*args):pass
        def settimeout(self,value):assert 0<value<=0.1
        def connect(self,address):
            if state['time']<state['ready_after']:raise ConnectionRefusedError()
        def getsockopt(self,*args):
            return state['credentials'] if state['credentials'] is not None else struct.pack('3i',state['peer_pid'],state['peer_uid'],os.getgid())
    monkeypatch.setattr(worker.socket,'socket',lambda *args:Socket())
    return worker,task,session,state,process

def test_startup_after_the_former_three_second_window_is_admitted(simulated):
    worker,task,session,state,_=simulated;state['ready_after']=4.5
    worker.start_bridge(task,session)
    assert 4.5<=state['time']<5 and session['bridge_pid']==123
    assert session['bridge_launch']['process_start_ticks']==44

def test_startup_timeout_is_a_real_monotonic_deadline_and_retains_identity(simulated):
    worker,task,session,state,_=simulated;state['ready_after']=999
    with pytest.raises(RuntimeError,match='durable_bridge_unavailable:startup_timeout'):worker.start_bridge(task,session)
    assert state['time']==pytest.approx(60.0)
    assert session['bridge_pid']==123 and session['bridge_launch']['process_start_ticks']==44

@pytest.mark.parametrize('fault',['pid','uid','malformed','start-ticks'])
def test_ready_socket_requires_exact_child_peer_identity(simulated,monkeypatch,fault):
    worker,task,session,state,_=simulated
    if fault=='pid':state['peer_pid']=999
    elif fault=='uid':state['peer_uid']=os.getuid()+1
    elif fault=='malformed':state['credentials']=b'bad'
    else:
        ticks=iter([44,45]);monkeypatch.setattr(worker,'process_start_ticks',lambda pid:next(ticks))
    with pytest.raises(RuntimeError,match='durable_bridge_identity_unverified'):worker.start_bridge(task,session)
    assert session['bridge_pid']==123

def test_process_exit_is_reported_without_waiting_for_deadline(simulated):
    worker,task,session,state,process=simulated;process.poll=lambda:7
    with pytest.raises(RuntimeError,match='durable_bridge_unavailable:process_exited:7'):worker.start_bridge(task,session)
    assert state['time']==0

def test_exit_during_ready_handshake_is_not_accepted(simulated):
    worker,task,session,state,process=simulated
    statuses=iter([None,9]);process.poll=lambda:next(statuses)
    with pytest.raises(RuntimeError,match='exited_during_readiness'):worker.start_bridge(task,session)

def test_real_delayed_bridge_process_becomes_ready_after_three_seconds(startup,monkeypatch):
    worker,task,session=startup
    address='\0'+worker.bridge_socket_name(task)[1:]
    code='import socket,time;time.sleep(3.4);s=socket.socket(socket.AF_UNIX);s.bind('+repr(address)+');s.listen(1);c,_=s.accept();c.close();time.sleep(30)'
    # Command selection is an explicit double; child PID/start ticks, kernel
    # peer credentials, readiness socket and pidfd cleanup are real.
    monkeypatch.setattr(worker,'host_entrypoint_command',lambda entry,args,**kw:[sys.executable,'-I','-B','-c',code,*args])
    actual=subprocess.Popen;children=[]
    def spawn(*args,**kw):
        p=actual(*args,**kw);children.append(p);return p
    monkeypatch.setattr(worker.subprocess,'Popen',spawn)
    started=time.monotonic()
    try:
        worker.start_bridge(task,session)
        assert time.monotonic()-started>=3.4
        assert session['bridge_pid']==children[0].pid and worker.bridge_alive(session)
        worker.stop_bridge(session)
        children[0].wait(timeout=5)
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
            child.wait(timeout=5)

def test_real_unready_child_times_out_and_can_be_cleaned_without_respawn(startup,monkeypatch):
    worker,task,session=startup
    monkeypatch.setattr(worker,'BRIDGE_STARTUP_TIMEOUT_SECONDS',0.1)
    monkeypatch.setattr(worker,'host_entrypoint_command',lambda entry,args,**kw:[sys.executable,'-I','-B','-c','import time;time.sleep(30)',*args])
    actual=subprocess.Popen;children=[]
    def spawn(*args,**kw):
        p=actual(*args,**kw);children.append(p);return p
    monkeypatch.setattr(worker.subprocess,'Popen',spawn)
    try:
        with pytest.raises(RuntimeError,match='startup_timeout'):worker.start_bridge(task,session)
        assert len(children)==1 and children[0].poll() is None
        worker.stop_bridge(session);children[0].wait(timeout=5)
    finally:
        for child in children:
            if child.poll() is None:child.terminate()
            child.wait(timeout=5)
