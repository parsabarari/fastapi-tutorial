import pytest


def test_read_items_empty(client):
    response = client.get("/items/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_item(client):
    response = client.post(
        "/items/",
        json={"id": 1, "name": "Widget", "price": 9.99, "description": "A thing", "tax": 0.5},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Widget"
    assert data["id"] == 1


def test_read_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item doesn't exist"


def test_full_crud_flow(client):
    # create
    create_resp = client.post("/items/", json={"id": 2, "name": "Gadget", "price": 19.99})
    assert create_resp.status_code == 200

    # read
    get_resp = client.get("/items/2")
    assert get_resp.status_code == 200
    assert get_resp.json()["name"] == "Gadget"

    # update
    update_resp = client.put(
        "/items/2", json={"name": "Gadget Pro", "price": 29.99}
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["name"] == "Gadget Pro"

    # delete
    delete_resp = client.delete("/items/2")
    assert delete_resp.status_code == 200

    # confirm gone
    assert client.get("/items/2").status_code == 404


@pytest.mark.parametrize("missing_id", [1, 42, 9999])
def test_update_missing_item_returns_404(client, missing_id):
    response = client.put(
        f"/items/{missing_id}", json={"name": "Ghost", "price": 1.0}
    )
    assert response.status_code == 404


def test_create_then_list_multiple_items(client):
    client.post("/items/", json={"id": 1, "name": "A", "price": 1.0})
    client.post("/items/", json={"id": 2, "name": "B", "price": 2.0})

    response = client.get("/items/")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"A", "B"}