"""A tiny FastAPI items API with a clean separation between rule and transport.

- ItemStore   : in-memory data layer (could be swapped for a real DB).
- ItemService : pure business rules. Unit-testable without HTTP.
- app         : FastAPI surface. Integration-tested with TestClient.
"""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, FastAPI, HTTPException, status
from pydantic import BaseModel, Field


@dataclass
class Item:
    id: int
    name: str
    price: float


class ItemStore:
    def __init__(self) -> None:
        self._items: dict[int, Item] = {}
        self._next_id: int = 1

    def add(self, name: str, price: float) -> Item:
        item = Item(id=self._next_id, name=name, price=price)
        self._items[item.id] = item
        self._next_id += 1
        return item

    def get(self, item_id: int) -> Item | None:
        return self._items.get(item_id)

    def list_all(self) -> list[Item]:
        return list(self._items.values())

    def delete(self, item_id: int) -> bool:
        return self._items.pop(item_id, None) is not None


class ItemService:
    """Pure rules. Knows nothing about HTTP, JSON, FastAPI."""

    def __init__(self, store: ItemStore) -> None:
        self.store = store

    def create(self, name: str, price: float) -> Item:
        if not name.strip():
            raise ValueError("name must not be empty")
        if price < 0:
            raise ValueError("price must not be negative")
        return self.store.add(name.strip(), round(price, 2))

    def total_value(self) -> float:
        return round(sum(i.price for i in self.store.list_all()), 2)


# --- HTTP layer ------------------------------------------------------------


class ItemIn(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(ge=0)


class ItemOut(BaseModel):
    id: int
    name: str
    price: float


_default_store = ItemStore()


def get_service() -> ItemService:
    return ItemService(_default_store)


app = FastAPI(title="P7 Items API")


@app.post("/items", response_model=ItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: ItemIn, service: ItemService = Depends(get_service)
) -> ItemOut:
    try:
        item = service.create(payload.name, payload.price)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ItemOut(id=item.id, name=item.name, price=item.price)


@app.get("/items", response_model=list[ItemOut])
def list_items(service: ItemService = Depends(get_service)) -> list[ItemOut]:
    return [
        ItemOut(id=i.id, name=i.name, price=i.price) for i in service.store.list_all()
    ]


@app.get("/items/{item_id}", response_model=ItemOut)
def get_item(item_id: int, service: ItemService = Depends(get_service)) -> ItemOut:
    item = service.store.get(item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="item not found")
    return ItemOut(id=item.id, name=item.name, price=item.price)


@app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, service: ItemService = Depends(get_service)) -> None:
    if not service.store.delete(item_id):
        raise HTTPException(status_code=404, detail="item not found")


@app.get("/items/stats/total")
def total(service: ItemService = Depends(get_service)) -> dict[str, float]:
    return {"total_value": service.total_value()}
