def test_only_admins_manage_rooms(client, user):
    res = client.post("/api/rooms", json={"name": "X", "capacity": 2}, headers=user)
    assert res.status_code == 403


def test_create_and_list_rooms(client, admin, user, room):
    client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    names = [r["name"] for r in client.get("/api/rooms", headers=user).get_json()]
    assert names == ["Atlántico", "Teide"]


def test_room_validation_and_unique_name(client, admin, room):
    bad = client.post("/api/rooms", json={"name": "", "capacity": 0}, headers=admin)
    assert bad.status_code == 422
    dup = client.post("/api/rooms", json={"name": "Atlántico", "capacity": 3}, headers=admin)
    assert dup.status_code == 409


def test_filter_by_capacity_and_amenity(client, admin, room):
    client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    big = client.get("/api/rooms?min_capacity=8", headers=admin).get_json()
    assert [r["name"] for r in big] == ["Atlántico"]
    projector = client.get("/api/rooms?amenity=proyector", headers=admin).get_json()
    assert [r["name"] for r in projector] == ["Atlántico"]


def test_availability_search(client, admin, user, room, book, at):
    client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    assert book("10:00", "11:00", user).status_code == 201

    def free(start, end):
        url = "/api/rooms"
        res = client.get(url, query_string={"from": at(start), "to": at(end)}, headers=user)
        return [r["name"] for r in res.get_json()]

    assert free("10:30", "11:30") == ["Teide"]
    assert free("11:00", "12:00") == ["Atlántico", "Teide"]  # rango semiabierto
    assert free("09:00", "10:00") == ["Atlántico", "Teide"]


def test_delete_unused_room_but_deactivate_room_with_history(client, admin, user, room, book):
    book("10:00", "11:00", user)
    res = client.delete(f"/api/rooms/{room['id']}", headers=admin)
    assert res.status_code == 200 and res.get_json()["is_active"] is False
    assert client.get("/api/rooms", headers=user).get_json() == []
    inactive = client.get("/api/rooms?include_inactive=1", headers=admin).get_json()
    assert [r["name"] for r in inactive] == ["Atlántico"]

    other = client.post("/api/rooms", json={"name": "Nueva", "capacity": 2}, headers=admin)
    assert client.delete(f"/api/rooms/{other.get_json()['id']}", headers=admin).status_code == 204


def test_cannot_book_inactive_room(client, admin, user, room, book):
    client.put(
        f"/api/rooms/{room['id']}",
        json={"name": "Atlántico", "capacity": 10, "is_active": False},
        headers=admin,
    )
    assert book("10:00", "11:00", user).status_code == 404


def test_availability_combined_with_capacity(client, admin, user, room, book, at):
    client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    book("10:00", "11:00", user)
    res = client.get(
        "/api/rooms",
        query_string={"from": at("10:00"), "to": at("11:00"), "min_capacity": 3},
        headers=user,
    )
    assert res.status_code == 200
    assert [r["name"] for r in res.get_json()] == ["Teide"]
