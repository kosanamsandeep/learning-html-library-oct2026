"""Integration tests: drive the FastAPI app via TestClient.

These tests verify the HTTP contract: status codes, JSON shape, error responses.
They do NOT re-test pure rules already covered by the unit tests.
"""


def test_create_item_returns_201_and_payload(client):
    response = client.post("/items", json={"name": "Pen", "price": 1.50})

    assert response.status_code == 201
    body = response.json()
    assert body == {"id": 1, "name": "Pen", "price": 1.50}


def test_get_item_returns_200(client):
    client.post("/items", json={"name": "Pen", "price": 1.50})

    response = client.get("/items/1")

    assert response.status_code == 200
    assert response.json()["name"] == "Pen"


def test_get_missing_item_returns_404(client):
    response = client.get("/items/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "item not found"}


def test_list_returns_all_items(client):
    client.post("/items", json={"name": "a", "price": 1})
    client.post("/items", json={"name": "b", "price": 2})

    response = client.get("/items")

    assert response.status_code == 200
    assert [i["name"] for i in response.json()] == ["a", "b"]


def test_create_with_empty_name_returns_422_from_pydantic(client):
    # Pydantic validation rejects min_length=1 before reaching the service.
    response = client.post("/items", json={"name": "", "price": 1})
    assert response.status_code == 422


def test_create_with_negative_price_returns_422_from_pydantic(client):
    response = client.post("/items", json={"name": "x", "price": -1})
    assert response.status_code == 422


def test_delete_returns_204_and_removes_item(client):
    client.post("/items", json={"name": "x", "price": 1})

    response = client.delete("/items/1")
    assert response.status_code == 204

    assert client.get("/items/1").status_code == 404


def test_total_endpoint_returns_sum(client):
    client.post("/items", json={"name": "a", "price": 1.10})
    client.post("/items", json={"name": "b", "price": 2.40})

    response = client.get("/items/stats/total")
    assert response.status_code == 200
    assert response.json() == {"total_value": 3.50}


def test_each_test_starts_with_empty_store(client):
    # Proof that the fixture isolation works.
    response = client.get("/items")
    assert response.json() == []
