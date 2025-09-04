def _token(client):
    r = client.post("/api/v2/auth/login", json={"user_id": 42})
    assert r.status_code == 200
    return r.get_json()["access_token"]


def test_v2_auth_and_crud(client):
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    # create
    r = client.post("/api/v2/posts", json={"userId": 2, "title": "A", "body": "B"}, headers=headers)
    assert r.status_code == 201
    pid = r.get_json()["id"]

    # list (cached)
    r = client.get("/api/v2/posts", headers=headers)
    assert r.status_code == 200

    # get
    r = client.get(f"/api/v2/posts/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.get_json()["title"] == "A"

    # update
    r = client.patch(f"/api/v2/posts/{pid}", json={"title": "AA"}, headers=headers)
    assert r.status_code == 200
    assert r.get_json()["title"] == "AA"

    # delete
    r = client.delete(f"/api/v2/posts/{pid}", headers=headers)
    assert r.status_code == 200
