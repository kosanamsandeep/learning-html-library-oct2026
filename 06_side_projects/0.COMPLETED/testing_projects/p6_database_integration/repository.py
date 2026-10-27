"""TodoRepository backed by SQLite.

This is what integration tests target: real SQL, real schema, real connection.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);
"""


@dataclass
class Todo:
    id: int
    title: str
    done: bool


class TodoRepository:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = str(db_path)
        self._connection = sqlite3.connect(self.db_path)
        self._connection.row_factory = sqlite3.Row
        self._connection.executescript(SCHEMA)

    def add(self, title: str) -> Todo:
        title = title.strip()
        if not title:
            raise ValueError("title must not be empty")
        cur = self._connection.execute(
            "INSERT INTO todos(title, done) VALUES (?, 0)", (title,)
        )
        self._connection.commit()
        return Todo(id=cur.lastrowid, title=title, done=False)

    def get(self, todo_id: int) -> Todo | None:
        row = self._connection.execute(
            "SELECT id, title, done FROM todos WHERE id = ?", (todo_id,)
        ).fetchone()
        return self._row_to_todo(row) if row else None

    def list_all(self) -> list[Todo]:
        rows = self._connection.execute(
            "SELECT id, title, done FROM todos ORDER BY id"
        ).fetchall()
        return [self._row_to_todo(r) for r in rows]

    def mark_done(self, todo_id: int) -> bool:
        cur = self._connection.execute(
            "UPDATE todos SET done = 1 WHERE id = ?", (todo_id,)
        )
        self._connection.commit()
        return cur.rowcount == 1

    def delete(self, todo_id: int) -> bool:
        cur = self._connection.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
        self._connection.commit()
        return cur.rowcount == 1

    def close(self) -> None:
        self._connection.close()

    @staticmethod
    def _row_to_todo(row: sqlite3.Row) -> Todo:
        return Todo(id=row["id"], title=row["title"], done=bool(row["done"]))
