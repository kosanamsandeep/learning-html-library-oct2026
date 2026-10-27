import asyncio
from agents.skills import web_search


def test_web_search_returns_string():
    out = asyncio.run(web_search("python language", max_results=2))
    assert isinstance(out, str)
