def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


def test_occasions(client):
    names = {o["name"] for o in client.get("/api/occasions").json()["occasions"]}
    assert {"Diwali", "Birthday", "Wedding"} <= names


def test_recommendations(client):
    body = client.get("/api/recommendations", params={"occasion": "Diwali", "limit": 5}).json()
    assert body["resolved_occasion"]["name"] == "Diwali" and body["returned"] == 5
    first = body["results"][0]
    for field in ("product_id", "vendor_id", "vendor_category_desc", "title", "snippet", "image", "price", "reasons"):
        assert field in first


def test_empty_result_is_not_an_error(client):
    response = client.get("/api/recommendations", params={"occasion": "xqzvw"})
    assert response.status_code == 200 and response.json()["results"] == []


def test_bad_requests_are_rejected(client):
    assert client.get("/api/recommendations").status_code == 422                                     # missing
    assert client.get("/api/recommendations", params={"occasion": "x", "limit": 1000}).status_code == 422  # too many
