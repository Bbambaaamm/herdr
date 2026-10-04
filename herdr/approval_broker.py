"""Host-owned one-use approval authority for guarded Hermes processes.

The host registers verified grants before starting panes. The database and
socket must live outside every model-writable mount. Never run this broker
inside a guarded Hermes process.
"""
from __future__ import annotations

import json
import socket
import sqlite3
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


def serve_approvals(listener: socket.socket, ledger: ApprovalLedger) -> None:
    """Serve a host-created Unix listener; host controls mount and peer access."""
    while True:
        connection, _ = listener.accept()
        with connection:
            connection.settimeout(2)
            try:
                request = bytearray()
                while len(request) < 2048 and not request.endswith(b"\n"):
                    chunk = connection.recv(2048 - len(request))
                    if not chunk:
                        break
                    request.extend(chunk)
                payload = json.loads(request)
                if set(payload) != {"grant_hash", "approval_id", "tool", "args_sha256"}:
                    raise ValueError("invalid request")
                answer = ledger.consume(**payload)
            except (ValueError, TypeError, OSError, sqlite3.Error):
                answer = "unavailable"
            connection.sendall((answer + "\n").encode("ascii"))
