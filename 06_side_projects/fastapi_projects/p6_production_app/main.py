"""
P6 — Production-grade FastAPI service.

Everything from P1-P5 combined with the operational patterns you need to ship:
  * Settings from env via pydantic-settings.
  * Structured JSON logging.
  * Request-ID middleware (accept or generate, log it, propagate it).
  * Global exception handlers with a uniform error shape.
  * Lifespan that boots BOTH the DB engine and an httpx AsyncClient.
  * BackgroundTasks for fire-and-forget work (audit log).
  * /health (liveness) and /ready (readiness — checks DB).
  * One business endpoint that reads from DB and calls an upstream concurrently.

Run:
    uvicorn main:app --reload
Then:
    http://127.0.0.1:8000/docs
    http://127.0.0.1:8000/health
    http://127.0.0.1:8000/ready
"""

from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator
from functools import lru_cache

import httpx
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    HTTPException,
    Request,
    Response,
    status,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import String, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


# ============================================================
# 1. Settings
# ============================================================
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="APP_", extra="ignore"
    )

    app_name: str = "Production-Grade Service"
    debug: bool = False
    database_url: str = "sqlite+aiosqlite:///./prod_app.db"
    upstream_url: str = "https://api.github.com/zen"
    upstream_timeout: float = 3.0


@lru_cache
def get_settings() -> Settings:
    return Settings()


# ============================================================
# 2. Logging — structured JSON
# ============================================================
class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Propagate request_id if attached
        if hasattr(record, "request_id"):
            payload["request_id"] = record.request_id
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload)


def setup_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)


log = logging.getLogger("app")


# ============================================================
# 3. Database
# ============================================================
class Base(DeclarativeBase):
    pass


class WidgetRow(Base):
    __tablename__ = "widgets"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


engine = None
SessionLocal: async_sessionmaker[AsyncSession] | None = None


async def get_db() -> AsyncIterator[AsyncSession]:
    assert SessionLocal is not None, "DB not initialised — check lifespan"
    async with SessionLocal() as session:
        yield session


DB = Annotated[AsyncSession, Depends(get_db)]


# ============================================================
# 4. Custom exceptions + handlers (uniform error shape)
# ============================================================
class NotFound(Exception):
    def __init__(self, what: str) -> None:
        self.what = what


class ErrorOut(BaseModel):
    error: str
    detail: str
    request_id: str | None = None


# ============================================================
# 5. Lifespan — start/stop DB engine + HTTP client
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine, SessionLocal
    settings = get_settings()
    setup_logging()
    log.info("starting up")

    engine = create_async_engine(settings.database_url, echo=False)
    SessionLocal = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    app.state.http = httpx.AsyncClient(
        timeout=httpx.Timeout(settings.upstream_timeout, connect=1.0),
        limits=httpx.Limits(max_connections=50, max_keepalive_connections=10),
    )

    yield

    log.info("shutting down")
    await app.state.http.aclose()
    await engine.dispose()


# ============================================================
# 6. App
# ============================================================
app = FastAPI(
    title=get_settings().app_name,
    version="1.0.0",
    description="Production-grade FastAPI service with all the operational patterns.",
    lifespan=lifespan,
    responses={500: {"model": ErrorOut}},
)


# ============================================================
# 7. Middleware — request ID + access log
# ============================================================
@app.middleware("http")
async def request_id_and_access_log(request: Request, call_next):
    rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex
    request.state.request_id = rid
    started = time.perf_counter()
    try:
        response: Response = await call_next(request)
    except Exception:
        log.exception("unhandled error", extra={"request_id": rid})
        return JSONResponse(
            status_code=500,
            content=ErrorOut(
                error="internal_error", detail="unexpected", request_id=rid
            ).model_dump(),
            headers={"X-Request-ID": rid},
        )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    response.headers["X-Request-ID"] = rid
    log.info(
        f"{request.method} {request.url.path} -> {response.status_code} ({elapsed_ms} ms)",
        extra={"request_id": rid},
    )
    return response


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound) -> JSONResponse:
    rid = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=404,
        content=ErrorOut(
            error="not_found", detail=exc.what, request_id=rid
        ).model_dump(),
    )


# ============================================================
# 8. Health endpoints
# ============================================================
@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    """Liveness — am I a working process?"""
    return {"status": "ok"}


@app.get("/ready", tags=["meta"])
async def ready(db: DB) -> dict[str, str]:
    """Readiness — can I serve traffic? Checks the DB connection."""
    try:
        await db.execute(select(1))
    except Exception as e:  # pragma: no cover - defensive
        raise HTTPException(503, detail=f"db not reachable: {e}")
    return {"status": "ready"}


# ============================================================
# 9. Business endpoints
# ============================================================
class WidgetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WidgetOut(WidgetCreate):
    id: str


def _audit(rid: str, action: str, target: str) -> None:
    # In production: write to Kafka / S3 / dedicated audit DB.
    log.info(f"AUDIT {action} {target}", extra={"request_id": rid})


@app.post("/widgets", response_model=WidgetOut, status_code=201, tags=["widgets"])
async def create_widget(
    data: WidgetCreate,
    db: DB,
    request: Request,
    bg: BackgroundTasks,
) -> WidgetOut:
    row = WidgetRow(id=uuid.uuid4().hex, name=data.name)
    db.add(row)
    await db.commit()
    bg.add_task(_audit, request.state.request_id, "create_widget", row.id)
    return WidgetOut(id=row.id, name=row.name)


@app.get("/widgets/{widget_id}", response_model=WidgetOut, tags=["widgets"])
async def get_widget(widget_id: str, db: DB) -> WidgetOut:
    row = await db.get(WidgetRow, widget_id)
    if not row:
        raise NotFound(f"widget {widget_id}")
    return WidgetOut(id=row.id, name=row.name)


@app.get("/widgets/{widget_id}/enriched", tags=["widgets"])
async def enriched(widget_id: str, db: DB, request: Request) -> dict[str, str]:
    """
    Read from DB + call an upstream concurrently. Demonstrates that
    the DB query and the HTTP call can overlap inside one event loop tick.
    """
    settings = get_settings()
    client: httpx.AsyncClient = request.app.state.http

    async def fetch_zen() -> str:
        try:
            r = await client.get(settings.upstream_url)
            r.raise_for_status()
            return r.text
        except httpx.HTTPError:
            return "(upstream unavailable)"

    row = await db.get(WidgetRow, widget_id)
    if not row:
        raise NotFound(f"widget {widget_id}")

    zen = await fetch_zen()
    return {"id": row.id, "name": row.name, "zen_quote": zen}
