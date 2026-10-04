"""Host-owned one-use approval authority for guarded Hermes processes.

The host registers verified grants before starting panes. The database and
socket must live outside every model-writable mount. Never run this broker
inside a guarded Hermes process.
"""
from __future__ import annotations

import json
import socket
import sqlite3
import struct
import threading
from pathlib import Path

from herdr.security import SecurityGrant


class ApprovalLedger:
    def __init__(self, path: Path) -> None:
        self.path = path
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS approvals (grant_hash TEXT, approval_id TEXT PRIMARY KEY, tool TEXT, args_sha256 TEXT, consumed INTEGER NOT NULL DEFAULT 0)")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA journal_mode=WAL")
        return db

    def register(self, grant: SecurityGrant) -> None:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            for item in grant.approvals:
                db.execute("INSERT OR IGNORE INTO approvals (grant_hash, approval_id, tool, args_sha256) VALUES (?, ?, ?, ?)",
                           (grant.hash, item.approval_id, item.tool, item.args_sha256))
                bound = db.execute("SELECT grant_hash, tool, args_sha256 FROM approvals WHERE approval_id=?",
                                   (item.approval_id,)).fetchone()
                if bound != (grant.hash, item.tool, item.args_sha256):
                    db.rollback()
                    raise ValueError("approval ID already bound to another grant")
            db.commit()

    def consume(self, grant_hash: str, approval_id: str, tool: str, args_sha256: str) -> str:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            cursor = db.execute("UPDATE approvals SET consumed=1 WHERE grant_hash=? AND approval_id=? AND tool=? AND args_sha256=? AND consumed=0",
                                (grant_hash, approval_id, tool, args_sha256))
            if cursor.rowcount == 1:
                db.commit()
                return "consumed"
            db.rollback()
            return "replayed"


def serve_approvals(listener: socket.socket, ledger: ApprovalLedger, *,
                    peer_authorizer=None, stop_event=None) -> None:
    """Serve independently after exact host peer admission; no raw client takes a slot."""
    if not callable(peer_authorizer):
        raise ValueError("host approval peer authorizer required")
    stop_event=stop_event or threading.Event()
    slots=threading.BoundedSemaphore(16)
    threads=set();lock=threading.Lock()
    listener.settimeout(0.1)
    def handle(connection,pid):
        try:
            with connection:
                connection.settimeout(2)
                request=bytearray()
                answer="unavailable"
                try:
                    while len(request)<2048 and b"\n" not in request:
                        chunk=connection.recv(2048-len(request))
                        if not chunk: break
                        request.extend(chunk)
                    if b"\n" not in request: raise ValueError("unterminated approval")
                    line,tail=bytes(request).split(b"\n",1)
                    if tail: raise ValueError("multiple approval messages")
                    payload=json.loads(line)
                    if (not isinstance(payload,dict)
                            or set(payload)!={"grant_hash","approval_id","tool","args_sha256"}
                            or any(not isinstance(value,str) or not 0<len(value)<=512
                                   for value in payload.values())
                            or peer_authorizer(pid,payload["grant_hash"]) is not True):
                        raise ValueError("invalid or unauthorized approval request")
                    answer=ledger.consume(**payload)
                except (ValueError,TypeError,OSError,sqlite3.Error):
                    pass
                try: connection.sendall((answer+"\n").encode("ascii"))
                except OSError: pass
        finally:
            with lock: threads.discard(threading.current_thread())
            slots.release()
    try:
        while not stop_event.is_set():
            try: connection,_=listener.accept()
            except socket.timeout: continue
            try:
                credentials=connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,struct.calcsize("3i"))
                pid,_uid,_gid=struct.unpack("3i",credentials)
                if pid<=0 or peer_authorizer(pid,None) is not True:
                    connection.close();continue
            except Exception:
                connection.close();continue
            if not slots.acquire(blocking=False):
                connection.close();continue
            thread=threading.Thread(target=handle,args=(connection,pid),daemon=True,
                                    name="herdr-approval-peer")
            with lock: threads.add(thread)
            try: thread.start()
            except BaseException:
                with lock: threads.discard(thread)
                slots.release();connection.close()
                raise
    finally:
        with lock: remaining=tuple(threads)
        for thread in remaining: thread.join(2.1)
