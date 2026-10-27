"""
P3 — Async database with SQLAlchemy 2.0 + aiosqlite.

What changes vs P2:
  * Storage is a real SQL database (SQLite by default; switch the URL for Postgres).
  * Every route is `async def`.
  * Every DB call uses `await`.
  * Session is provided via a FastAPI dependency that yields and closes.
  * Tables are created on startup using FastAPI's `lifespan`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Annotated, AsyncIterator
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import String, Boolean, select
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

DATABASE_URL = "sqlite+aiosqlite:///./todos.db"


# -------------------- SQLAlchemy --------------------
class Base(DeclarativeBase):
    pass


class TodoRow(Base):
    __tablename__ = "todos"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    done: Mapped[bool] = mapped_column(Boolean, default=False)


engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncIterator[AsyncSession]:
    """One session per request. Closed automatically."""
    async with SessionLocal() as session:
        yield session


DB = Annotated[AsyncSession, Depends(get_db)]


# -------------------- API models --------------------
class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TodoOut(TodoCreate):
    id: str


# -------------------- App + lifespan --------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup: create tables. In real apps use Alembic migrations.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # On shutdown: close the connection pool cleanly.
    await engine.dispose()


app = FastAPI(
    title="Async DB Todos",
    version="1.0.0",
    description="Async SQLAlchemy with SQLite. Swap DATABASE_URL for Postgres in production.",
    lifespan=lifespan,
)


# -------------------- Routes --------------------
@app.get("/todos", response_model=list[TodoOut], tags=["todos"])
async def list_todos(db: DB) -> list[TodoOut]:
    result = await db.execute(select(TodoRow))
    rows = result.scalars().all()
    return [TodoOut(id=r.id, title=r.title, done=r.done) for r in rows]


@app.post("/todos", response_model=TodoOut, status_code=201, tags=["todos"])
async def create_todo(data: TodoCreate, db: DB) -> TodoOut:
    row = TodoRow(id=uuid4().hex, title=data.title, done=data.done)
    db.add(row)
    await db.commit()
    return TodoOut(id=row.id, title=row.title, done=row.done)


@app.get("/todos/{todo_id}", response_model=TodoOut, tags=["todos"])
async def get_todo(todo_id: str, db: DB) -> TodoOut:
    row = await db.get(TodoRow, todo_id)
    if not row:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"todo {todo_id} not found"
        )
    return TodoOut(id=row.id, title=row.title, done=row.done)


@app.delete("/todos/{todo_id}", status_code=204, tags=["todos"])
async def delete_todo(todo_id: str, db: DB) -> None:
    row = await db.get(TodoRow, todo_id)
    if not row:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"todo {todo_id} not found"
        )
    await db.delete(row)
    await db.commit()
