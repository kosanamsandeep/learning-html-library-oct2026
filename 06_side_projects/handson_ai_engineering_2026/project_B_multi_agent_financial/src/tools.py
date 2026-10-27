"""Tools for the financial analyst team. Each tool is a thin wrapper that the
LangGraph agents will invoke. Real provider calls are stubbed where they require
external API keys; swap with yfinance / Polygon / FMP in production.
"""
from __future__ import annotations
import json
import os
import logging
from datetime import datetime, timedelta
from typing import Any

import httpx
from langchain_core.tools import tool

log = logging.getLogger(__name__)


@tool
def get_price_history(ticker: str, days: int = 30) -> str:
    """Return JSON close-price history for the last `days` trading days."""
    try:
        import yfinance as yf  # optional
        end = datetime.utcnow()
        start = end - timedelta(days=days * 2)
        df = yf.download(ticker, start=start, end=end, progress=False)
        closes = df["Close"].tail(days).round(2).to_dict()
        return json.dumps({str(k.date()): float(v) for k, v in closes.items()})
    except Exception as e:
        log.warning("yfinance unavailable, returning stub: %s", e)
        return json.dumps({"stub": True, "ticker": ticker, "note": "install yfinance"})


@tool
def get_company_fundamentals(ticker: str) -> str:
    """Return key fundamentals (PE, EPS, market-cap, sector) as JSON."""
    try:
        import yfinance as yf
        info = yf.Ticker(ticker).info
        keys = ("trailingPE", "forwardPE", "trailingEps", "marketCap",
                "sector", "industry", "beta", "dividendYield")
        return json.dumps({k: info.get(k) for k in keys})
    except Exception as e:
        log.warning("fundamentals stubbed: %s", e)
        return json.dumps({"stub": True, "ticker": ticker})


@tool
def web_search_news(query: str, n: int = 5) -> str:
    """Search recent finance news. Uses Tavily if TAVILY_API_KEY is set."""
    api_key = os.getenv("TAVILY_API_KEY")
    if not api_key:
        return json.dumps([{"title": "stub headline", "url": "https://example.com",
                            "content": f"News stub for {query}"}])
    try:
        r = httpx.post("https://api.tavily.com/search",
                       json={"api_key": api_key, "query": query,
                             "max_results": n, "topic": "news"},
                       timeout=10)
        r.raise_for_status()
        return json.dumps(r.json().get("results", []))
    except Exception as e:
        log.error("Tavily failed: %s", e)
        return json.dumps([])


ALL_TOOLS: list[Any] = [get_price_history, get_company_fundamentals, web_search_news]
