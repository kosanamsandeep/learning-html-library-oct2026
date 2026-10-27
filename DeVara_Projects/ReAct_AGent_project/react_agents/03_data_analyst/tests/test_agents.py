import asyncio
from core.bootstrap import load_csv_to_sqlite
from agents.skills import list_tables, run_sql


def test_db_round_trip():
    load_csv_to_sqlite()
    tables = asyncio.run(list_tables())
    assert "data" in tables
    rows = asyncio.run(run_sql("SELECT COUNT(*) FROM data"))
    assert "(" in rows
