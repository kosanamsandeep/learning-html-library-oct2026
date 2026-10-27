import asyncio
from agents.skills import calculator


def test_calculator():
    out = asyncio.run(calculator.ainvoke({"expression": "23*45+1"}))
    assert out == "1036"
