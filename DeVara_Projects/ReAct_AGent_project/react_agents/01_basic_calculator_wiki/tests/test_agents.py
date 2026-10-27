import asyncio
import pytest
from agents.skills import calculate, wiki_summary


def test_calculator_ok():
    assert asyncio.run(calculate("23*45+1")) == "1036"


def test_calculator_bad():
    out = asyncio.run(calculate("not math"))
    assert "calculator error" in out


@pytest.mark.skip(reason="hits the network")
def test_wiki():
    out = asyncio.run(wiki_summary("Eiffel Tower"))
    assert "Eiffel" in out
