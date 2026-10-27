"""One end-to-end test for the critical journey: add product, checkout, see totals."""

import httpx


def test_user_can_checkout(live_url):
    with httpx.Client(base_url=live_url) as c:
        # Seed catalog
        pen = c.post(
            "/products", json={"name": "Pen", "price": 5.0, "stock": 10}
        ).json()
        pad = c.post(
            "/products", json={"name": "Pad", "price": 25.0, "stock": 2}
        ).json()

        # Checkout
        response = c.post(
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
        assert response.json() == {"subtotal": 45.00, "total": 45.50}

        # Stock was actually decremented
        assert c.get(f"/products/{pen['id']}").json()["stock"] == 6
        assert c.get(f"/products/{pad['id']}").json()["stock"] == 1
