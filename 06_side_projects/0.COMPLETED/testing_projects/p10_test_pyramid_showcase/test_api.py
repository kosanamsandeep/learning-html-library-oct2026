"""API integration tests using FastAPI TestClient."""


def test_create_and_get_product(client):
    created = client.post("/products", json={"name": "Pen", "price": 5.0, "stock": 10})
    assert created.status_code == 201
    pid = created.json()["id"]

    fetched = client.get(f"/products/{pid}")
    assert fetched.status_code == 200
    assert fetched.json()["name"] == "Pen"


def test_checkout_endpoint_returns_totals(client):
    pen = client.post(
        "/products", json={"name": "Pen", "price": 5.0, "stock": 10}
    ).json()
    pad = client.post(
        "/products", json={"name": "Pad", "price": 25.0, "stock": 2}
    ).json()

    response = client.post(
        "/checkout",
        json={
            "items": [
                {"product_id": pen["id"], "quantity": 4},
                {"product_id": pad["id"], "quantity": 1},
            ],
            "discount_percent": 10,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["subtotal"] == 45.00
    assert body["total"] == 45.50


def test_checkout_missing_product_returns_404(client):
    response = client.post(
        "/checkout",
        json={
            "items": [{"product_id": 9999, "quantity": 1}],
        },
    )
    assert response.status_code == 404


def test_checkout_out_of_stock_returns_409(client):
    pen = client.post(
        "/products", json={"name": "Pen", "price": 5.0, "stock": 1}
    ).json()
    response = client.post(
        "/checkout",
        json={
            "items": [{"product_id": pen["id"], "quantity": 10}],
        },
    )
    assert response.status_code == 409
