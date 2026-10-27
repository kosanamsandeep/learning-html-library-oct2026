import asyncio
from agents.skills import save_report


def test_save():
    p = asyncio.run(save_report("# hello"))
    assert p.endswith(".md")
