from datetime import UTC, datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.config import Config
from app.rules import BookingPolicy

TZ = ZoneInfo("Europe/Madrid")
policy = BookingPolicy.from_config(vars(Config))


def madrid(y, m, d, hh=0, mm=0):
    return datetime(y, m, d, hh, mm, tzinfo=TZ)


def test_occupancy_is_admin_only(client, user, at):
    res = client.get(
        "/api/stats/occupancy", query_string={"from": at("00:00"), "to": at("23:45")}, headers=user
    )
    assert res.status_code == 403


def test_occupancy_per_room(client, admin, user, room, book, at):
    client.post("/api/rooms", json={"name": "Teide", "capacity": 4}, headers=admin)
    book("09:00", "11:00", user)
    book("15:00", "16:30", user)
    cancelled = book("17:00", "18:00", user).get_json()
    client.delete(f"/api/bookings/{cancelled['id']}", headers=user)

    res = client.get(
        "/api/stats/occupancy",
        query_string={"from": at("08:00"), "to": at("21:00")},
        headers=admin,
    ).get_json()
    assert res["open_hours"] == 13
    assert res["rooms"][0] == {
        "room_id": room["id"],
        "name": "Atlántico",
        "capacity": 10,
        "booked_hours": 3.5,
        "occupancy": round(3.5 / 13, 4),
    }
    assert res["rooms"][1]["booked_hours"] == 0


def test_occupancy_clips_bookings_at_the_window_edges(client, admin, user, room, book, at):
    book("10:00", "12:00", user)
    res = client.get(
        "/api/stats/occupancy",
        query_string={"from": at("11:00"), "to": at("21:00")},
        headers=admin,
    ).get_json()
    assert res["rooms"][0]["booked_hours"] == 1


@pytest.mark.parametrize(
    ("start", "end", "hours"),
    [
        (madrid(2026, 10, 5), madrid(2026, 10, 6), 13),  # lunes completo
        (madrid(2026, 10, 5), madrid(2026, 10, 12), 65),  # semana: 5 × 13, sin finde
        (madrid(2026, 10, 10), madrid(2026, 10, 12), 0),  # fin de semana
        (madrid(2026, 10, 5, 12), madrid(2026, 10, 5, 14), 2),  # dentro del horario
        (madrid(2026, 10, 5, 20), madrid(2026, 10, 6, 9), 2),  # cierre + apertura
    ],
)
def test_open_hours_between(start, end, hours):
    assert policy.open_hours_between(start, end) == hours


def test_policy_accepts_other_timezones_in_input():
    now = datetime(2026, 10, 1, tzinfo=UTC)
    # 08:00Z en octubre = 10:00 en Madrid → válido
    start = datetime.combine(datetime(2026, 10, 5).date(), time(8, 0), UTC)
    policy.validate(start, start + timedelta(hours=1), now=now)
