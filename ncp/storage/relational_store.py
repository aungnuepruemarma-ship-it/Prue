"""Relational store — sqlite3-backed structured persistence.

Fills the spec's "postgres" slot with a stdlib backend; the schema-light
API (tables inferred from row dicts) keeps a real PostgreSQL adapter
drop-in behind the same interface.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from pathlib import Path
from typing import Any


class RelationalStore:
    """Dict-in, dict-out table storage over sqlite3."""

    def __init__(self, path: str = ":memory:"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.RLock()

    def _ensure_table(self, table: str, row: dict[str, Any]) -> None:
        cols = ", ".join(f'"{k}"' for k in row)
        self._conn.execute(f'CREATE TABLE IF NOT EXISTS "{table}" ({cols})')
        existing = {r[1] for r in self._conn.execute(f'PRAGMA table_info("{table}")')}
        for key in row:
            if key not in existing:
                self._conn.execute(f'ALTER TABLE "{table}" ADD COLUMN "{key}"')

    @staticmethod
    def _encode(value: Any) -> Any:
        if isinstance(value, (dict, list, tuple)):
            return json.dumps(value)
        return value

    @staticmethod
    def _decode(value: Any) -> Any:
        if isinstance(value, str) and value[:1] in "[{":
            try:
                return json.loads(value)
            except (ValueError, TypeError):
                return value
        return value

    def insert(self, table: str, row: dict[str, Any]) -> None:
        with self._lock:
            self._ensure_table(table, row)
            keys = list(row)
            placeholders = ", ".join("?" for _ in keys)
            columns = ", ".join(f'"{k}"' for k in keys)
            self._conn.execute(
                f'INSERT INTO "{table}" ({columns}) VALUES ({placeholders})',
                [self._encode(row[k]) for k in keys],
            )
            self._conn.commit()

    def query(self, table: str, where: dict[str, Any] | None = None, limit: int | None = None) -> list[dict[str, Any]]:
        with self._lock:
            sql = f'SELECT * FROM "{table}"'
            params: list[Any] = []
            if where:
                sql += " WHERE " + " AND ".join(f'"{k}" = ?' for k in where)
                params = [self._encode(v) for v in where.values()]
            if limit:
                sql += f" LIMIT {int(limit)}"
            try:
                rows = self._conn.execute(sql, params).fetchall()
            except sqlite3.OperationalError:  # table does not exist yet
                return []
            return [{k: self._decode(r[k]) for k in r.keys()} for r in rows]

    def count(self, table: str, where: dict[str, Any] | None = None) -> int:
        return len(self.query(table, where))

    def execute(self, sql: str, params: tuple = ()) -> list[tuple]:
        with self._lock:
            cursor = self._conn.execute(sql, params)
            self._conn.commit()
            return cursor.fetchall()

    def close(self) -> None:
        self._conn.close()
