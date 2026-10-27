"""Bootstrap helper: load CSV → SQLite, generate demo CSV if missing."""
from __future__ import annotations

import sqlite3
from pathlib import Path
import pandas as pd

from core.config import settings


def ensure_demo_csv() -> Path:
    p = Path(settings.csv_path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame({
            "region":  ["N", "S", "E", "W", "N", "S"] * 4,
            "product": ["A", "B", "A", "C", "B", "A"] * 4,
            "units":   [12, 7, 15, 9, 6, 11] * 4,
            "revenue": [120, 90, 150, 110, 70, 130] * 4,
        }).to_csv(p, index=False)
    return p


def load_csv_to_sqlite(table: str = "data") -> Path:
    csv_path = ensure_demo_csv()
    db = Path(settings.db_path)
    db.parent.mkdir(parents=True, exist_ok=True)
    db.unlink(missing_ok=True)
    df = pd.read_csv(csv_path)
    with sqlite3.connect(db) as conn:
        df.to_sql(table, conn, index=False)
    return db
