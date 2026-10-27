import asyncio
from core.bootstrap import load_csv_to_sqlite
from agents.skills import list_tables


def test_bootstrap():
    load_csv_to_sqlite()
    out = asyncio.run(list_tables.ainvoke({"_": ""}))
    assert "data" in out
