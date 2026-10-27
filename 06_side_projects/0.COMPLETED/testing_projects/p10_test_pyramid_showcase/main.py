"""FastAPI surface."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, Field

from repository import ProductRepository
from service import CheckoutService, OutOfStockError, UnknownProductError

_DB_PATH = Path(os.environ.get("P10_DB_PATH", "shop.sqlite"))
_repo: ProductRepository | None = None


def get_repo() -> ProductRepository:
    global _repo
    if _repo is None:
        _repo = ProductRepository(_DB_PATH)
    return _repo


def get_service(repo: ProductRepository = Depends(get_repo)) -> CheckoutService:
    return CheckoutService(repo)


class LineIn(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class CheckoutIn(BaseModel):
    items: list[LineIn]
    discount_percent: float = Field(default=0.0, ge=0, le=100)


class CheckoutOut(BaseModel):
    subtotal: float
    total: float


class ProductIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)
    stock: int = Field(ge=0)


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    stock: int


app = FastAPI(title="P10 Mini Shop")


@app.post("/products", response_model=ProductOut, status_code=201)
def create_product(
    p: ProductIn, repo: ProductRepository = Depends(get_repo)
) -> ProductOut:
    saved = repo.add(p.name, p.price, p.stock)
    return ProductOut(**saved.__dict__)


@app.get("/products/{pid}", response_model=ProductOut)
def get_product(pid: int, repo: ProductRepository = Depends(get_repo)) -> ProductOut:
    product = repo.get(pid)
    if product is None:
        raise HTTPException(404, "not found")
    return ProductOut(**product.__dict__)


@app.post("/checkout", response_model=CheckoutOut)
def checkout(
    payload: CheckoutIn, service: CheckoutService = Depends(get_service)
) -> CheckoutOut:
    try:
        result = service.checkout(
            [(line.product_id, line.quantity) for line in payload.items],
            payload.discount_percent,
        )
    except UnknownProductError as exc:
        raise HTTPException(404, str(exc)) from exc
    except OutOfStockError as exc:
        raise HTTPException(409, str(exc)) from exc
    return CheckoutOut(subtotal=result.subtotal, total=result.total)
