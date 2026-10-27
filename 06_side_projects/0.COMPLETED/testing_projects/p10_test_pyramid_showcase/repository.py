"""SQLite product repository. Integration-tested with tmp_path."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    price REAL NOT NULL,
    stock INTEGER NOT NULL
);
"""


@dataclass
class Product:
    id: int
    name: str
    price: float
    stock: int


class ProductRepository:
    def __init__(self, db_path: str | Path) -> None:
        self._conn = sqlite3.connect(str(db_path))
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA)

    def add(self, name: str, price: float, stock: int) -> Product:
        cur = self._conn.execute(
            "INSERT INTO products(name, price, stock) VALUES (?, ?, ?)",
            (name, price, stock),
        )
        self._conn.commit()
        return Product(id=cur.lastrowid, name=name, price=price, stock=stock)

    def get(self, product_id: int) -> Product | None:
        row = self._conn.execute(
            "SELECT id, name, price, stock FROM products WHERE id = ?",
            (product_id,),
        ).fetchone()
        return Product(**dict(row)) if row else None

    def decrement_stock(self, product_id: int, quantity: int) -> bool:
        cur = self._conn.execute(
            "UPDATE products SET stock = stock - ? WHERE id = ? AND stock >= ?",
            (quantity, product_id, quantity),
        )
        self._conn.commit()
        return cur.rowcount == 1

    def close(self) -> None:
        self._conn.close()
