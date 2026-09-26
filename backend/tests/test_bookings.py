from concurrent.futures import ThreadPoolExecutor

import pytest


def test_create_booking(client, user, room, book):
    res = book("10:00", "11:30", user)
    assert res.status_code == 201
    data = res.get_json()
    assert data["room"]["name"] == "Atlántico"
    assert data["user"]["name"] == "Ana"
    assert data["is_cancelled"] is False


@pytest.mark.parametrize(
    ("start", "end"),
    [("10:00", "11:00"), ("10:30", "10:45"), ("09:00", "10:15"), ("10:45", "12:00")],
)
def test_overlapping_bookings_are_rejected(user, other_user, book, start, end):
    assert book("10:00", "11:00", user).status_code == 201
    res = book(start, end, other_user)
    assert res.status_code == 409
    assert res.get_json()["error"] == "slot_taken"


def test_back_to_back_bookings_are_allowed(user, other_user, book):
    assert book("10:00", "11:00", user).status_code == 201
    assert book("11:00", "12:00", other_user).status_code == 201
    assert book("09:00", "10:00", other_user).status_code == 201


def test_same_slot_in_different_rooms_is_fine(client, admin, user, book):
    other = client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    assert book("10:00", "11:00", user).status_code == 201
    assert book("10:00", "11:00", user, room_id=other.get_json()["id"]).status_code == 201


def test_no_double_booking_under_concurrency(app, user, room, at):
    """16 peticiones simultáneas por la misma franja: exactamente una gana."""
    payload = {
        "room_id": room["id"],
        "title": "Carrera",
        "starts_at": at("12:00"),
        "ends_at": at("13:00"),
    }

    def attempt(_):
        with app.test_client() as c:
            return c.post("/api/bookings", json=payload, headers=user).status_code

    with ThreadPoolExecutor(max_workers=16) as pool:
        codes = list(pool.map(attempt, range(16)))
    assert codes.count(201) == 1
    assert codes.count(409) == 15


@pytest.mark.parametrize(
    ("start", "end", "field"),
    [
        ("11:00", "10:00", "ends_at"),  # termina antes de empezar
        ("10:10", "11:00", "starts_at"),  # fuera de tramos de 15 min
        ("09:00", "14:00", "ends_at"),  # más de 4 horas
        ("07:00", "08:30", "starts_at"),  # antes de abrir
        ("20:30", "21:30", "starts_at"),  # después de cerrar
    ],
)
def test_business_rules(book, user, start, end, field):
    res = book(start, end, user)
    assert res.status_code == 422
    assert field in res.get_json()["details"]


def test_weekend_is_rejected(book, user):
    res = book("10:00", "11:00", user, day=5)  # sábado
    assert res.status_code == 422


def test_booking_in_the_past_is_rejected(client, user, room):
    res = client.post(
        "/api/bookings",
        json={
            "room_id": room["id"],
            "title": "Tarde",
            "starts_at": "2020-01-06T10:00:00+01:00",
            "ends_at": "2020-01-06T11:00:00+01:00",
        },
        headers=user,
    )
    assert res.status_code == 422
    assert "starts_at" in res.get_json()["details"]


def test_naive_datetimes_are_rejected(client, user, room):
    res = client.post(
        "/api/bookings",
        json={
            "room_id": room["id"],
            "title": "Sin zona",
            "starts_at": "2030-01-07T10:00:00",
            "ends_at": "2030-01-07T11:00:00",
        },
        headers=user,
    )
    assert res.status_code == 422


def test_cancel_frees_the_slot(client, user, other_user, book):
    booking = book("10:00", "11:00", user).get_json()
    res = client.delete(f"/api/bookings/{booking['id']}", headers=user)
    assert res.status_code == 200 and res.get_json()["is_cancelled"] is True
    assert book("10:00", "11:00", other_user).status_code == 201
    again = client.delete(f"/api/bookings/{booking['id']}", headers=user)
    assert again.status_code == 409


def test_only_owner_or_admin_can_cancel(client, admin, user, other_user, book):
    booking = book("10:00", "11:00", user).get_json()
    assert client.delete(f"/api/bookings/{booking['id']}", headers=other_user).status_code == 403
    assert client.delete(f"/api/bookings/{booking['id']}", headers=admin).status_code == 200


def test_cannot_cancel_started_booking(app, client, user, book):
    from datetime import UTC, datetime, timedelta

    from app.extensions import db
    from app.models import Booking

    booking = book("10:00", "11:00", user).get_json()
    row = db.session.get(Booking, booking["id"])
    row.starts_at = datetime.now(UTC) - timedelta(minutes=5)
    db.session.commit()
    assert client.delete(f"/api/bookings/{booking['id']}", headers=user).status_code == 409


def test_calendar_returns_active_bookings_in_range(client, user, book, at):
    book("10:00", "11:00", user)
    cancelled = book("12:00", "13:00", user).get_json()
    client.delete(f"/api/bookings/{cancelled['id']}", headers=user)
    book("10:00", "11:00", user, day=1)

    res = client.get(
        "/api/bookings", query_string={"from": at("00:00"), "to": at("23:45")}, headers=user
    )
    assert [b["starts_at"][11:16] for b in res.get_json()] == ["08:00"]  # 10:00 Madrid = 08:00Z


def test_calendar_range_is_limited(client, user, at):
    res = client.get(
        "/api/bookings", query_string={"from": at("10:00", 60), "to": at("10:00")}, headers=user
    )
    assert res.status_code == 422


def test_my_bookings(client, user, other_user, book):
    book("10:00", "11:00", user)
    book("12:00", "13:00", other_user)
    mine = client.get("/api/bookings/mine", headers=user).get_json()
    assert [b["user"]["name"] for b in mine] == ["Ana"]
    assert client.get("/api/bookings/mine?scope=past", headers=user).get_json() == []


def test_calendar_can_be_filtered_by_room(client, admin, user, book, at):
    other = client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    other_id = other.get_json()["id"]
    book("10:00", "11:00", user)
    book("10:00", "11:00", user, room_id=other_id)
    res = client.get(
        "/api/bookings",
        query_string={"from": at("00:00"), "to": at("23:45"), "room_id": other_id},
        headers=user,
    )
    assert res.status_code == 200
    assert [b["room"]["name"] for b in res.get_json()] == ["Teide"]
