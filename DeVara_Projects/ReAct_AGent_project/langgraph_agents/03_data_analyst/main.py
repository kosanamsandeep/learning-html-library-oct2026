"""Async FastAPI app — Multi-agent supervisor data analyst."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.bootstrap import load_csv_to_sqlite
from core.logger import get_logger
from workflows import ask_analyst

log = get_logger("main")


class AnalystRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field("default", min_length=1, max_length=64)


class AnalystResponse(BaseModel):
    agent: str
    thread_id: str
    question: str
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("loading CSV → SQLite")
    load_csv_to_sqlite()
    from workflows.analyst_workflow import _get_agent
    _get_agent()
    yield


app = FastAPI(title="LangGraph Data Analyst (Supervisor)", version="1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict: return {"status": "ok"}


@app.post("/ask", response_model=AnalystResponse)
async def ask(req: AnalystRequest) -> AnalystResponse:
    try:
        return AnalystResponse(**(await ask_analyst(req.question, req.thread_id)))
    except Exception as exc:  # noqa: BLE001
        log.exception("failed")
        raise HTTPException(500, str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8103, reload=False)
