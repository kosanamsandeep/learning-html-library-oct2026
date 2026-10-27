"""Async FastAPI entry point for the Research Assistant."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.logger import get_logger
from workflows import research_topic

log = get_logger("main")


class ResearchRequest(BaseModel):
    topic: str = Field(..., min_length=3, max_length=500)


class ResearchResponse(BaseModel):
    agent: str
    topic: str
    result: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("warming agent")
    from workflows.research_workflow import _get_agent
    _get_agent()
    yield


app = FastAPI(title="ReAct Research Assistant", version="1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict: return {"status": "ok"}


@app.post("/research", response_model=ResearchResponse)
async def research(req: ResearchRequest) -> ResearchResponse:
    try:
        return ResearchResponse(**(await research_topic(req.topic)))
    except Exception as exc:  # noqa: BLE001
        log.exception("research failed")
        raise HTTPException(500, str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8002, reload=False)
