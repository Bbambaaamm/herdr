import json
import os
import socket
import threading
from pathlib import Path

import pytest

from herdr.bootstrap_authority import (
    BootstrapAuthority,
    BootstrapAuthorityError,
    BootstrapExpectation,
    PeerProcess,
)


def _line(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode() + b"\n"


def test_host_authenticated_stage1_session_survives_exec_identity(tmp_path):
    stage0 = tmp_path / "stage0-python"
    pinned = tmp_path / "pinned-python"
    stage0.write_bytes(b"stage0")
    pinned.write_bytes(b"pinned")
    stage0_info = stage0.stat()
    pinned_info = pinned.stat()
    peer_pid = os.getpid()
    parent_pid = peer_pid + 10000
    parent_start = 777
    phase = {"stage2": False}

    def inspect(pid):
        if pid == parent_pid:
            return PeerProcess(parent_pid, 1, parent_start, 1, 1, ("shell",))
        if pid != peer_pid:
            raise AssertionError(pid)
        info = pinned_info if phase["stage2"] else stage0_info
        return PeerProcess(
            peer_pid,
            parent_pid,
            12345,
            info.st_dev,
            info.st_ino,
            (str(stage0), "-I", "-S", "/run/herdr-bootstrap/agent-hermes-policy-stage1"),
        )

    identity = {
        "consumer": "github:owner/repo",
        "agent_id": "agent",
        "parent_agent_id": "parent",
        "parent_task_id": "parent-task",
        "task_id": "task",
        "run_token": "run",
        "fencing_token": 7,
    }
    expectation = BootstrapExpectation(
        identity=identity,
        proof_sha256="a" * 64,
        stage1_sha256="d" * 64,
        stage2_sha256="b" * 64,
        python_sha256="c" * 64,
        bundle_sha256="e" * 64,
        parent_pid=parent_pid,
        parent_start_ticks=parent_start,
        stage1_device=11,
        stage1_inode=12,
        python_device=pinned_info.st_dev,
        python_inode=pinned_info.st_ino,
    )
    authority = BootstrapAuthority(
        stage0_path=stage0, require_root_owned_stage0=False,
        peer_inspector=inspect,
        stage1_inspector=lambda pid, path: (11, 12, "d" * 64),
        peer_authorizer=lambda peer, expected: True,
    )
    authority.register(expectation)
    server, client = socket.socketpair()
    thread = threading.Thread(target=authority.handle_connection, args=(server,))
    thread.start()
    try:
        client.sendall(_line({
            "op": "stage1",
            "identity": identity,
            "proof_sha256": "a" * 64,
            "stage1_sha256": "d" * 64,
            "stage2_sha256": "b" * 64,
            "python_sha256": "c" * 64,
            "bundle_sha256": "e" * 64,
        }))
        assert client.recv(64) == b"stage1-ok\n"
        phase["stage2"] = True
        client.sendall(_line({
            "op": "stage2",
            "identity": identity,
            "proof_sha256": "a" * 64,
            "bundle_sha256": "e" * 64,
        }))
        assert client.recv(64) == b"stage2-ok\n"
    finally:
        client.close()
        thread.join(2)
        server.close()
    assert not thread.is_alive()
    assert authority.pending() == 0
    from herdr.security import InvocationIdentity
    admitted = InvocationIdentity.from_dict(identity)
    receipt = authority.wait_for_continuation(admitted, timeout_seconds=0)
    assert receipt.peer_pid == peer_pid and receipt.process_start_ticks == 12345
    assert receipt.bundle_sha256 == "e" * 64
    assert receipt.stage1_sha256 == "d" * 64
    assert receipt.python_inode == pinned_info.st_ino
    assert receipt.to_json()["identity"] == identity
    with pytest.raises(TypeError):
        receipt.identity["run_token"] = "other"
    assert authority.continuation(admitted) is receipt
    with pytest.raises(BootstrapAuthorityError, match="consumed"):
        authority.register(expectation)


def test_bootstrap_authority_rejects_forged_sibling_process(tmp_path):
    stage0 = tmp_path / "stage0"
    pinned = tmp_path / "pinned"
    stage0.write_bytes(b"s")
    pinned.write_bytes(b"p")
    stage0_info = stage0.stat()
    pinned_info = pinned.stat()
    peer_pid = os.getpid()
    expected_parent = peer_pid + 20000

    def inspect(pid):
        if pid == expected_parent:
            return PeerProcess(expected_parent, 1, 9, 1, 1, ("shell",))
        return PeerProcess(
            peer_pid, expected_parent + 1, 10,
            stage0_info.st_dev, stage0_info.st_ino,
            (str(stage0), "-I", "-S", "/run/herdr-bootstrap/agent-hermes-policy-stage1"),
        )

    identity = {"consumer":"github:owner/repo","agent_id":"agent","parent_agent_id":"parent",
        "parent_task_id":"parent-task","task_id":"task","run_token":"run","fencing_token":1}
    authority = BootstrapAuthority(
        stage0_path=stage0, require_root_owned_stage0=False, peer_inspector=inspect,
        stage1_inspector=lambda pid, path: (21, 22, "d" * 64),
        peer_authorizer=lambda peer, expected: True,
    )
    authority.register(BootstrapExpectation(
        identity=identity,
        proof_sha256="a" * 64,
        stage1_sha256="d" * 64,
        stage2_sha256="b" * 64,
        python_sha256="c" * 64,
        bundle_sha256="e" * 64,
        parent_pid=expected_parent,
        parent_start_ticks=9,
        stage1_device=21,
        stage1_inode=22,
        python_device=pinned_info.st_dev,
        python_inode=pinned_info.st_ino,
    ))
    server, client = socket.socketpair()
    thread = threading.Thread(target=authority.handle_connection, args=(server,))
    thread.start()
    try:
        client.sendall(_line({
            "op": "stage1", "identity": identity,
            "proof_sha256": "a" * 64, "stage1_sha256": "d" * 64,
            "stage2_sha256": "b" * 64, "python_sha256": "c" * 64,
            "bundle_sha256": "e" * 64,
        }))
        assert client.recv(64) == b"denied\n"
    finally:
        client.close()
        thread.join(2)
        server.close()
    assert authority.pending() == 1


def test_bootstrap_authority_requires_host_peer_authorizer(tmp_path):
    stage0 = tmp_path / "stage0"
    stage0.write_bytes(b"x")
    with pytest.raises(BootstrapAuthorityError, match="host peer authorizer required"):
        BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False)


def test_bootstrap_authority_rejects_exact_argv_peer_not_confirmed_by_host(tmp_path):
    stage0 = tmp_path / "stage0"
    pinned = tmp_path / "pinned"
    stage0.write_bytes(b"s")
    pinned.write_bytes(b"p")
    s0 = stage0.stat()
    pin = pinned.stat()
    peer_pid = os.getpid()
    parent_pid = peer_pid + 30000
    identity = {"consumer":"github:owner/repo","agent_id":"agent","parent_agent_id":"parent",
        "parent_task_id":"parent-task","task_id":"task","run_token":"run","fencing_token":1}

    def inspect(pid):
        if pid == parent_pid:
            return PeerProcess(parent_pid, 1, 99, 1, 1, ("shell",))
        return PeerProcess(
            peer_pid, parent_pid, 100, s0.st_dev, s0.st_ino,
            (str(stage0), "-I", "-S", "/run/herdr-bootstrap/agent-hermes-policy-stage1"),
        )

    authority = BootstrapAuthority(
        stage0_path=stage0, require_root_owned_stage0=False,
        peer_inspector=inspect,
        stage1_inspector=lambda pid, path: (31, 32, "d" * 64),
        peer_authorizer=lambda peer, expected: False,
    )
    authority.register(BootstrapExpectation(
        identity=identity, proof_sha256="a" * 64, stage1_sha256="d" * 64,
        stage2_sha256="b" * 64, python_sha256="c" * 64, bundle_sha256="e" * 64,
        parent_pid=parent_pid, parent_start_ticks=99, stage1_device=31, stage1_inode=32,
        python_device=pin.st_dev, python_inode=pin.st_ino,
    ))
    server, client = socket.socketpair()
    thread = threading.Thread(target=authority.handle_connection, args=(server,))
    thread.start()
    try:
        client.sendall(_line({
            "op": "stage1", "identity": identity, "proof_sha256": "a" * 64,
            "stage1_sha256": "d" * 64, "stage2_sha256": "b" * 64,
            "python_sha256": "c" * 64, "bundle_sha256": "e" * 64,
        }))
        assert client.recv(64) == b"denied\n"
    finally:
        client.close(); thread.join(2); server.close()
    assert authority.pending() == 1


def test_bootstrap_authority_requires_exact_stage1_argv_position(tmp_path):
    stage0 = tmp_path / "stage0"
    pinned = tmp_path / "pinned"
    stage0.write_bytes(b"s"); pinned.write_bytes(b"p")
    s0, pin = stage0.stat(), pinned.stat()
    peer_pid, parent_pid = os.getpid(), os.getpid() + 40000
    identity = {"consumer":"github:owner/repo","agent_id":"agent","parent_agent_id":"parent",
        "parent_task_id":"parent-task","task_id":"task","run_token":"run","fencing_token":1}

    def inspect(pid):
        if pid == parent_pid:
            return PeerProcess(parent_pid, 1, 7, 1, 1, ("shell",))
        return PeerProcess(
            peer_pid, parent_pid, 8, s0.st_dev, s0.st_ino,
            (str(stage0), "-I", "-S", "/tmp/attacker.py",
             "/run/herdr-bootstrap/agent-hermes-policy-stage1"),
        )

    authority = BootstrapAuthority(
        stage0_path=stage0, require_root_owned_stage0=False, peer_inspector=inspect,
        stage1_inspector=lambda pid, path: (41, 42, "d" * 64),
        peer_authorizer=lambda peer, expected: True,
    )
    authority.register(BootstrapExpectation(
        identity=identity, proof_sha256="a" * 64, stage1_sha256="d" * 64,
        stage2_sha256="b" * 64, python_sha256="c" * 64, bundle_sha256="e" * 64,
        parent_pid=parent_pid, parent_start_ticks=7, stage1_device=41, stage1_inode=42,
        python_device=pin.st_dev, python_inode=pin.st_ino,
    ))
    server, client = socket.socketpair()
    thread = threading.Thread(target=authority.handle_connection, args=(server,))
    thread.start()
    try:
        client.sendall(_line({
            "op": "stage1", "identity": identity, "proof_sha256": "a" * 64,
            "stage1_sha256": "d" * 64, "stage2_sha256": "b" * 64,
            "python_sha256": "c" * 64, "bundle_sha256": "e" * 64,
        }))
        assert client.recv(64) == b"denied\n"
    finally:
        client.close(); thread.join(2); server.close()


def test_expectation_requires_full_frozen_identity(tmp_path):
    from dataclasses import replace
    identity={"consumer":"github:owner/repo","agent_id":"agent","parent_agent_id":"parent",
        "parent_task_id":"parent-task","task_id":"task","run_token":"run","fencing_token":1}
    expected=BootstrapExpectation(identity,"a"*64,"b"*64,"c"*64,"d"*64,"e"*64,1,2,3,4,5,6)
    identity["run_token"]="changed"
    assert expected.identity["run_token"]=="run"
    with pytest.raises(TypeError): expected.identity["run_token"]="changed"
    with pytest.raises(BootstrapAuthorityError,match="full admitted"):
        replace(expected,identity={"task_id":"task","run_token":"run","fencing_token":1})

def test_continuation_cannot_be_claimed_from_public_identity_without_exec(tmp_path):
    from herdr.security import InvocationIdentity
    stage0 = tmp_path / "stage0"
    stage0.write_bytes(b"x")
    authority = BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False, peer_authorizer=lambda *args: True)
    identity = InvocationIdentity("github:owner/repo","a","p","parent","task","run",1)
    assert authority.continuation(identity) is None
    with pytest.raises(BootstrapAuthorityError, match="unavailable"):
        authority.wait_for_continuation(identity, timeout_seconds=0.01)
    for timeout in (True, -1, float("inf"), 61):
        with pytest.raises(BootstrapAuthorityError, match="bounded"):
            authority.wait_for_continuation(identity, timeout_seconds=timeout)
    with pytest.raises(BootstrapAuthorityError, match="typed"):
        authority.continuation(identity.to_json())

def test_expired_consumed_launches_reclaim_capacity_without_replay(tmp_path):
    from dataclasses import replace
    stage0=tmp_path/"stage0";stage0.write_bytes(b"trusted")
    info=stage0.stat();pid=os.getpid();parent=pid+1234;now=[100.]
    def inspect(value):
        if value==parent: return PeerProcess(parent,1,7,1,1,("shell",))
        return PeerProcess(pid,parent,8,info.st_dev,info.st_ino,
            (str(stage0),"-I","-S","/run/herdr-bootstrap/agent-hermes-policy-stage1"))
    authority=BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False,peer_inspector=inspect,
        stage1_inspector=lambda *args:(3,4,"b"*64),peer_authorizer=lambda *args:True,
        clock=lambda:now[0])
    identity={"consumer":"github:owner/repo","agent_id":"agent","parent_agent_id":"parent",
              "parent_task_id":"parent-task","task_id":"task","run_token":"run","fencing_token":1}
    original=BootstrapExpectation(identity,"a"*64,"b"*64,"c"*64,"d"*64,"e"*64,
                                  parent,7,3,4,5,6,valid_until=100.5)
    server,client=socket.socketpair()
    try:
        for number in range(4100):
            expected=replace(original,identity={**identity,"run_token":f"run-{number}"},
                             valid_until=now[0]+0.5)
            authority.register(expected)
            authority._begin(server,{"op":"stage1","identity":dict(expected.identity),
                "proof_sha256":"a"*64,"stage1_sha256":"b"*64,"stage2_sha256":"c"*64,
                "python_sha256":"d"*64,"bundle_sha256":"e"*64})
            with pytest.raises(BootstrapAuthorityError,match="consumed"):
                authority.register(expected)
            now[0]+=1
        assert authority.pending()==0
        with pytest.raises(BootstrapAuthorityError,match="expired"):
            authority.register(original)
    finally:
        server.close();client.close()

def test_unregistered_stalled_socket_peer_is_rejected_before_read(tmp_path):
    stage0=tmp_path/"stage0";stage0.write_bytes(b"trusted")
    info=stage0.stat()
    authority=BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False,peer_authorizer=lambda *args:True,
        peer_inspector=lambda pid:PeerProcess(pid,1,1,info.st_dev,info.st_ino,
                           (str(stage0),"-I","-S","/run/herdr-bootstrap/agent-hermes-policy-stage1")))
    server,client=socket.socketpair()
    try:
        assert authority.dispatch_connection(server) is False
        client.settimeout(0.1)
        assert client.recv(1)==b""
        authority.close(timeout_seconds=0)
    finally: server.close();client.close()


def test_stalled_authenticated_peer_cannot_block_another_launch(tmp_path):
    import subprocess,sys,uuid
    from herdr.security import InvocationIdentity
    stage0=tmp_path/"stage0";stage0.write_bytes(b"system")
    pinned=tmp_path/"pinned";pinned.write_bytes(b"pinned")
    s0,pin=stage0.stat(),pinned.stat();parent=os.getpid();counts={};allowed={}
    def inspect(pid):
        if pid==parent: return PeerProcess(parent,1,7,1,1,("shell",))
        counts[pid]=counts.get(pid,0)+1
        info=pin if counts[pid]>=3 else s0
        return PeerProcess(pid,parent,8,info.st_dev,info.st_ino,
                 (str(stage0),"-I","-S","/run/herdr-bootstrap/agent-hermes-policy-stage1"))
    authority=BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False,peer_inspector=inspect,
        stage1_inspector=lambda *args:(3,4,"b"*64),
        peer_authorizer=lambda peer,expected:allowed.get(peer.pid)==dict(expected.identity))
    identities=[]
    for number in range(2):
        identity={"consumer":"github:owner/repo","agent_id":f"agent-{number}","parent_agent_id":"parent",
                  "parent_task_id":"parent-task","task_id":f"task-{number}","run_token":f"run-{number}","fencing_token":1}
        identities.append(identity)
        authority.register(BootstrapExpectation(identity,"a"*64,"b"*64,"c"*64,"d"*64,"e"*64,
                                parent,7,3,4,pin.st_dev,pin.st_ino))
    path=Path("/tmp")/("herdr-bootstrap-test-"+uuid.uuid4().hex+".sock")
    listener=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);listener.bind(str(path));listener.listen(2)
    def accept():
        for _ in range(2):
            connection,_=listener.accept()
            assert authority.dispatch_connection(connection)
    thread=threading.Thread(target=accept,daemon=True);thread.start()
    idle=active=None
    try:
        idle=subprocess.Popen([sys.executable,"-c",
            "import socket,sys,time;sys.stdin.buffer.read(1);s=socket.socket(socket.AF_UNIX);s.connect(sys.argv[1]);print('ready',flush=True);time.sleep(10)",
            str(path)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
        allowed[idle.pid]=identities[0];idle.stdin.write("x");idle.stdin.flush()
        assert idle.stdout.readline().strip()=="ready"
        request={"op":"stage1","identity":identities[1],"proof_sha256":"a"*64,
                 "stage1_sha256":"b"*64,"stage2_sha256":"c"*64,"python_sha256":"d"*64,
                 "bundle_sha256":"e"*64}
        continuation={"op":"stage2","identity":identities[1],"proof_sha256":"a"*64,"bundle_sha256":"e"*64}
        code="""import socket,sys
sys.stdin.buffer.read(1)
s=socket.socket(socket.AF_UNIX);s.settimeout(2);s.connect(sys.argv[1])
s.sendall(sys.argv[2].encode()+bytes([10]))
assert s.recv(64)==b'stage1-ok'+bytes([10])
s.sendall(sys.argv[3].encode()+bytes([10]))
assert s.recv(64)==b'stage2-ok'+bytes([10])
"""
        active=subprocess.Popen([sys.executable,"-c",code,str(path),json.dumps(request),json.dumps(continuation)],
                               stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        allowed[active.pid]=identities[1]
        out,error=active.communicate(input="x",timeout=3)
        assert active.returncode==0,error
        receipt=authority.wait_for_continuation(InvocationIdentity.from_dict(identities[1]),timeout_seconds=0)
        assert receipt.peer_pid==active.pid and idle.poll() is None
    finally:
        for process in (idle,active):
            if process is not None:
                if process.poll() is None: process.terminate();process.wait(timeout=2)
                for stream in (process.stdin,process.stdout,process.stderr):
                    if stream is not None and not stream.closed: stream.close()
        thread.join(2);listener.close();authority.close(timeout_seconds=3);path.unlink(missing_ok=True)

def test_unauthorized_bootstrap_peers_cannot_reserve_connection_capacity(tmp_path):
    stage0=tmp_path/"stage0";stage0.write_bytes(b"s")
    pinned=tmp_path/"pinned";pinned.write_bytes(b"p")
    s0,pin=stage0.stat(),pinned.stat();pid=os.getpid();parent=pid+10000
    phase={"allowed":False,"stage2":False}
    def inspect(value):
        if value==parent: return PeerProcess(parent,1,7,1,1,("shell",))
        info=pin if phase["stage2"] else s0
        return PeerProcess(pid,parent,8,info.st_dev,info.st_ino,
                 (str(stage0),"-I","-S","/run/herdr-bootstrap/agent-hermes-policy-stage1"))
    authority=BootstrapAuthority(stage0_path=stage0, require_root_owned_stage0=False,peer_inspector=inspect,
        stage1_inspector=lambda *args:(3,4,"b"*64),
        peer_authorizer=lambda *args:phase["allowed"])
    identity={"consumer":"github:owner/repo","agent_id":"a","parent_agent_id":"p",
              "parent_task_id":"parent","task_id":"task","run_token":"run","fencing_token":1}
    expected=BootstrapExpectation(identity,"a"*64,"b"*64,"c"*64,"d"*64,"e"*64,
                                   parent,7,3,4,pin.st_dev,pin.st_ino)
    authority.register(expected)
    for _ in range(20):
        server,client=socket.socketpair()
        try: assert authority.dispatch_connection(server) is False
        finally: server.close();client.close()
    phase["allowed"]=True;server,client=socket.socketpair()
    try:
        assert authority.dispatch_connection(server)
        client.settimeout(0.5)
        client.sendall(_line({"op":"stage1","identity":identity,"proof_sha256":"a"*64,
            "stage1_sha256":"b"*64,"stage2_sha256":"c"*64,"python_sha256":"d"*64,"bundle_sha256":"e"*64}))
        assert client.recv(64)==b"stage1-ok"+bytes([10])
        phase["stage2"]=True
        client.sendall(_line({"op":"stage2","identity":identity,"proof_sha256":"a"*64,"bundle_sha256":"e"*64}))
        assert client.recv(64)==b"stage2-ok"+bytes([10])
    finally:
        client.close();authority.close(timeout_seconds=2);server.close()


def test_production_authority_requires_actual_host_root_ownership(tmp_path,monkeypatch):
    stage0=tmp_path/"user-python";stage0.write_bytes(b"not a trusted system executable")
    import herdr.bootstrap_authority as module
    original=module.os.stat
    def non_root_owner(path,*args,**kwargs):
        info=original(path,*args,**kwargs)
        if Path(path)==stage0:
            fields=list(info);fields[4]=1001
            return os.stat_result(fields)
        return info
    monkeypatch.setattr(module.os,"stat",non_root_owner)
    with pytest.raises(BootstrapAuthorityError,match="root-owned"):
        BootstrapAuthority(stage0_path=stage0,peer_authorizer=lambda *args:True)
    # The real host interpreter meets this condition outside the remapped pane.
    authority=BootstrapAuthority(peer_authorizer=lambda *args:False)
    authority.close(timeout_seconds=0)
