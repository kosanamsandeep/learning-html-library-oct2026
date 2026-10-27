"""FastAPI async entry point for the ReAct calculator + wiki agent."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.logger import get_logger
from workflows import answer_question

log = get_logger("main")


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)


class AskResponse(BaseModel):
    agent: str
    question: str
    answer: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup: warming agent")
    # Import + instantiate eagerly so first request isn't slow
    from workflows.qa_workflow import _get_agent
    _get_agent()
    yield
    log.info("shutdown")


app = FastAPI(
    title="ReAct Calc+Wiki Agent",
    version="1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(req: AskRequest) -> AskResponse:
    try:
        result = await answer_question(req.question)
        return AskResponse(**result)
    except Exception as exc:  # noqa: BLE001
        log.exception("ask failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8001, reload=False)
