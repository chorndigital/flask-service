def test_v1_crud(client):
    # create
    r = client.post("/api/v1/posts", json={"userId": 1, "title": "T", "body": "B"})
    assert r.status_code == 201
    pid = r.get_json()["id"]

    # list
    r = client.get("/api/v1/posts")
    assert r.status_code == 200
    assert isinstance(r.get_json(), list)

    # get
    r = client.get(f"/api/v1/posts/{pid}")
    assert r.status_code == 200
    assert r.get_json()["title"] == "T"

    # update
    r = client.patch(f"/api/v1/posts/{pid}", json={"title": "T2"})
    assert r.status_code == 200
    assert r.get_json()["title"] == "T2"

    # delete
    r = client.delete(f"/api/v1/posts/{pid}")
    assert r.status_code == 200
