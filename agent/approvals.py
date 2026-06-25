"""The approval queue — the safety heart of the system.

Every action the agent wants to take in the real world is written here first as a
ProposedAction with status 'pending'. Read/monitor actions whose type is in the
config's auto_approve_types may be auto-approved; everything else (sending email,
creating events, ordering, paying, calling) waits for an explicit human approval.

Storage is plain SQLite so it is trivial to inspect, back up, and migrate onto the
local box later.
"""
import os
import json
import sqlite3
import time
import uuid
from typing import Optional

DB_PATH = os.path.join("data", "agent.db")


class ApprovalQueue:
    def __init__(self, auto_approve_types: Optional[list] = None, db_path: str = DB_PATH):
        self.auto_approve_types = set(auto_approve_types or [])
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db_path = db_path
        self._init_db()

    def _conn(self):
        c = sqlite3.connect(self.db_path)
        c.row_factory = sqlite3.Row
        return c

    def _init_db(self):
        with self._conn() as c:
            c.execute(
                """CREATE TABLE IF NOT EXISTS proposals (
                    id TEXT PRIMARY KEY,
                    created REAL,
                    type TEXT,
                    connector TEXT,
                    summary TEXT,
                    payload TEXT,
                    status TEXT,
                    decided REAL,
                    result TEXT
                )"""
            )

    def propose(self, action: dict) -> dict:
        """Insert a proposed action. Auto-approve only if its type is allow-listed."""
        pid = str(uuid.uuid4())[:8]
        status = "approved" if action["type"] in self.auto_approve_types else "pending"
        row = {
            "id": pid,
            "created": time.time(),
            "type": action["type"],
            "connector": action.get("connector", ""),
            "summary": action.get("summary", ""),
            "payload": json.dumps(action.get("payload", {})),
            "status": status,
            "decided": None,
            "result": None,
        }
        with self._conn() as c:
            c.execute(
                "INSERT INTO proposals VALUES (:id,:created,:type,:connector,:summary,:payload,:status,:decided,:result)",
                row,
            )
        return {**row, "payload": action.get("payload", {})}

    def list(self, status: Optional[str] = None) -> list:
        q = "SELECT * FROM proposals"
        args = ()
        if status:
            q += " WHERE status = ?"
            args = (status,)
        q += " ORDER BY created DESC"
        with self._conn() as c:
            return [dict(r) for r in c.execute(q, args).fetchall()]

    def decide(self, pid: str, approved: bool) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE proposals SET status=?, decided=? WHERE id=? AND status='pending'",
                ("approved" if approved else "denied", time.time(), pid),
            )

    def get(self, pid: str) -> Optional[dict]:
        with self._conn() as c:
            r = c.execute("SELECT * FROM proposals WHERE id=?", (pid,)).fetchone()
            return dict(r) if r else None

    def mark_executed(self, pid: str, result: str) -> None:
        with self._conn() as c:
            c.execute(
                "UPDATE proposals SET status='executed', result=? WHERE id=?",
                (result, pid),
            )
