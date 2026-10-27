from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(
    title="Hello FastAPI",
    version="1.0.0",
    description="The smallest interesting FastAPI app — 3 routes that showcase auto-docs, validation, and typed responses.",
)


class Greeting(BaseModel):
    message: str
    name: str


@app.get("/", summary="Root", tags=["hello"])
def root() -> dict[str, str]:
    """Plain JSON response — the bare minimum FastAPI route."""
    return {"hello": "world"}


@app.get("/greet/{name}", response_model=Greeting, tags=["hello"])
def greet(name: str) -> Greeting:
    """Path parameter, typed response. Note how `name` is auto-validated to a string."""
    return Greeting(message=f"Hello, {name}!", name=name)


@app.get("/add", tags=["math"])
def add(a: int, b: int) -> dict[str, int]:
    """Query parameters with automatic type coercion. Try /add?a=2&b=foo to see auto-422."""
    return {"a": a, "b": b, "sum": a + b}
