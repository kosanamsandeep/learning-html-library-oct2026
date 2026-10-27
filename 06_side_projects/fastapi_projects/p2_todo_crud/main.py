"""
P2 — Todo CRUD with Pydantic models + Dependency Injection.

Notice:
  * Separate Pydantic models for Create / Update / Out — never reuse one model for everything.
  * A "repository" dependency lets us swap storage backends without touching routes.
  * Tags + summary + response_model make Swagger genuinely useful.
"""

from __future__ import annotations

from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field


# -------------------- Models --------------------
class TodoBase(BaseModel):
    title: str = Field(min_length=1, max_length=200, examples=["Buy milk"])
    done: bool = False


class TodoCreate(TodoBase):
    pass


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


class TodoOut(TodoBase):
    id: str


# -------------------- Repository (in-memory) --------------------
class InMemoryTodoRepo:
    def __init__(self) -> None:
        self._items: dict[str, TodoOut] = {}

    def list(self, done: bool | None = None) -> list[TodoOut]:
        items = list(self._items.values())
        if done is not None:
            items = [t for t in items if t.done is done]
        return items

    def get(self, todo_id: str) -> TodoOut | None:
        return self._items.get(todo_id)

    def create(self, data: TodoCreate) -> TodoOut:
        todo = TodoOut(id=uuid4().hex, **data.model_dump())
        self._items[todo.id] = todo
        return todo

    def update(self, todo_id: str, patch: TodoUpdate) -> TodoOut | None:
        existing = self._items.get(todo_id)
        if not existing:
            return None
        updated = existing.model_copy(update=patch.model_dump(exclude_none=True))
        self._items[todo_id] = updated
        return updated

    def delete(self, todo_id: str) -> bool:
        return self._items.pop(todo_id, None) is not None


_repo_singleton = InMemoryTodoRepo()


def get_repo() -> InMemoryTodoRepo:
    """Dependency provider — override in tests to inject a fake repo."""
    return _repo_singleton


Repo = Annotated[InMemoryTodoRepo, Depends(get_repo)]


# -------------------- App + routes --------------------
app = FastAPI(
    title="Todo CRUD",
    version="1.0.0",
    description="CRUD over todos with Pydantic validation and dependency injection.",
)


@app.get("/todos", response_model=list[TodoOut], tags=["todos"], summary="List todos")
def list_todos(
    repo: Repo,
    done: bool | None = Query(default=None, description="Filter by completion state"),
) -> list[TodoOut]:
    return repo.list(done=done)


@app.post("/todos", response_model=TodoOut, status_code=201, tags=["todos"])
def create_todo(data: TodoCreate, repo: Repo) -> TodoOut:
    return repo.create(data)


@app.get("/todos/{todo_id}", response_model=TodoOut, tags=["todos"])
def get_todo(todo_id: str, repo: Repo) -> TodoOut:
    todo = repo.get(todo_id)
    if not todo:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"todo {todo_id} not found"
        )
    return todo


@app.patch("/todos/{todo_id}", response_model=TodoOut, tags=["todos"])
def update_todo(todo_id: str, patch: TodoUpdate, repo: Repo) -> TodoOut:
    updated = repo.update(todo_id, patch)
    if not updated:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"todo {todo_id} not found"
        )
    return updated


@app.delete("/todos/{todo_id}", status_code=204, tags=["todos"])
def delete_todo(todo_id: str, repo: Repo) -> None:
    if not repo.delete(todo_id):
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, detail=f"todo {todo_id} not found"
        )
