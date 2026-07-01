from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
  id TEXT PRIMARY KEY, email TEXT UNIQUE, name TEXT,
  password_hash TEXT, salt TEXT, plan TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS roles (
  id TEXT PRIMARY KEY, user_id TEXT, skill TEXT,
  title TEXT, location TEXT, headcount INTEGER,
  must_have TEXT, nice_to_have TEXT, seniority TEXT,
  status TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS pipeline (
  id TEXT PRIMARY KEY, user_id TEXT,
  role_id TEXT, candidate_id TEXT, name TEXT, language TEXT, location TEXT,
  fit REAL, verdict TEXT, stage TEXT, claims TEXT, notes TEXT,
  run_id TEXT, created_at REAL, updated_at REAL
);
CREATE TABLE IF NOT EXISTS messages (
  id TEXT PRIMARY KEY,
  pipeline_id TEXT, sender TEXT, channel TEXT, language TEXT, body TEXT, created_at REAL
);
CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY, user_id TEXT,
  role_id TEXT, goal TEXT, status TEXT,
  sourced INTEGER, screened INTEGER, sent INTEGER,
  cost_usd REAL, frontier_only_usd REAL, savings_x REAL,
  claims_verified INTEGER, claims_rejected INTEGER, by_tier TEXT, created_at REAL
);
CREATE INDEX IF NOT EXISTS idx_roles_user ON roles(user_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_role ON pipeline(role_id);
CREATE INDEX IF NOT EXISTS idx_pipeline_user ON pipeline(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_pc ON messages(pipeline_id);
CREATE INDEX IF NOT EXISTS idx_runs_user ON runs(user_id);
"""


class Database:
    """Thin SQLite wrapper. One connection guarded by a lock - plenty for a
    single-workspace product and avoids cross-thread surprises with the loop.
    """

    def __init__(self, path: str | Path) -> None:
        self.path = str(path)
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(self.path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)
            self._conn.commit()

    def execute(self, sql: str, params: tuple = ()) -> None:
        with self._lock:
            self._conn.execute(sql, params)
            self._conn.commit()

    def query(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        with self._lock:
            return list(self._conn.execute(sql, params).fetchall())

    def one(self, sql: str, params: tuple = ()) -> sqlite3.Row | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None
