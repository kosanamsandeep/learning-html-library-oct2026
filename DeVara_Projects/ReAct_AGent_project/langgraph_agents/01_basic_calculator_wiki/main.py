"""Async FastAPI app for the LangGraph calc+wiki agent."""
from __future__ import annotations
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.logger import get_logger
from workflows import answer_question

log = get_logger("main")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    thread_id: str = Field("default", min_length=1, max_length=64)


class AskResponse(BaseModel):
    agent: str
    thread_id: str
    question: str
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("warming graph")
    from workflows.qa_workflow import _get_agent
    _get_agent()
    yield


app = FastAPI(title="LangGraph Calc+Wiki", version="1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict: return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    try:
        return AskResponse(**(await answer_question(req.question, req.thread_id)))
    except Exception as exc:  # noqa: BLE001
        log.exception("ask failed")
        raise HTTPException(500, str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8101, reload=False)
