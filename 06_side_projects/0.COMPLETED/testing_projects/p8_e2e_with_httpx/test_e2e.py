"""End-to-end tests against a real uvicorn process over a real socket."""


def test_create_link_returns_code(client):
    response = client.post("/links", json={"url": "https://example.com"})

    assert response.status_code == 201
    body = response.json()
    assert "code" in body
    assert body["short_url"].endswith(body["code"])


def test_following_a_short_link_redirects(client):
    code = client.post("/links", json={"url": "https://example.com"}).json()["code"]

    response = client.get(f"/{code}")

    assert response.status_code == 302
    assert response.headers["location"] == "https://example.com/"


def test_unknown_code_returns_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404


def test_stats_counts_created_links(client):
    client.post("/links", json={"url": "https://a.test"})
    client.post("/links", json={"url": "https://b.test"})

    response = client.get("/stats")
    assert response.status_code == 200
    assert response.json() == {"total": 2}


def test_full_user_journey(client):
    """The kind of test the product owner would describe in plain English."""
    # 1) User creates a short link
    created = client.post("/links", json={"url": "https://example.com/article"}).json()
    code = created["code"]

    # 2) User shares the short link; somebody opens it
    follow = client.get(f"/{code}")
    assert follow.status_code == 302
    assert follow.headers["location"] == "https://example.com/article"

    # 3) Owner checks stats
    stats = client.get("/stats").json()
    assert stats["total"] == 1
