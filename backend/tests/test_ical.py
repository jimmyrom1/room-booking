from datetime import UTC, datetime
from types import SimpleNamespace

from app.ical import bookings_to_ics

NOW = datetime(2026, 9, 27, 10, 0, tzinfo=UTC)


def _booking(**overrides):
    """Objeto con la misma forma que un Booking: la función no necesita la base de datos."""
    data = {
        "id": 7,
        "title": "Revisión de sprint",
        "starts_at": datetime.fromisoformat("2026-09-28T10:00:00+02:00"),
        "ends_at": datetime.fromisoformat("2026-09-28T11:30:00+02:00"),
        "is_cancelled": False,
        "room": SimpleNamespace(name="Atlántico", location="Planta 2"),
        "user": SimpleNamespace(name="Ana"),
    }
    data.update(overrides)
    return SimpleNamespace(**data)


def _lines(ics: str) -> list[str]:
    return ics.split("\r\n")


def test_event_is_in_utc_with_a_stable_uid_and_a_reminder():
    ics = bookings_to_ics([_booking()], calendar_name="Mis reservas", now=NOW)
    lines = _lines(ics)

    assert lines[0] == "BEGIN:VCALENDAR"
    assert "UID:booking-7@room-booking" in lines
    assert "DTSTART:20260928T080000Z" in lines  # 10:00 en Madrid (CEST) = 08:00 UTC
    assert "DTEND:20260928T093000Z" in lines
    assert "DTSTAMP:20260927T100000Z" in lines
    assert "LOCATION:Atlántico (Planta 2)" in lines
    assert "STATUS:CONFIRMED" in lines
    assert "TRIGGER:-PT15M" in lines
    assert ics.endswith("END:VCALENDAR\r\n")


def test_every_line_ends_with_crlf():
    ics = bookings_to_ics([_booking()], calendar_name="X", now=NOW)
    assert "\n" not in ics.replace("\r\n", "")


def test_special_characters_are_escaped():
    booking = _booking(title="Kick-off; cliente, fase 1\nsegunda línea\\fin")
    ics = bookings_to_ics([booking], calendar_name="Equipo, ventas", now=NOW)
    assert "SUMMARY:Kick-off\\; cliente\\, fase 1\\nsegunda línea\\\\fin" in _lines(ics)
    assert "X-WR-CALNAME:Equipo\\, ventas" in _lines(ics)


def test_long_lines_are_folded_at_75_octets_without_splitting_utf8():
    booking = _booking(title="Planificación trimestral " + "ñ" * 60)
    ics = bookings_to_ics([booking], calendar_name="X", now=NOW)

    lines = _lines(ics)
    assert all(len(line.encode()) <= 75 for line in lines)
    # Al desplegar (quitar CRLF + espacio) se recupera el título completo.
    unfolded = ics.replace("\r\n ", "")
    assert f"SUMMARY:{booking.title}" in _lines(unfolded)


def test_cancelled_booking_is_marked_and_has_no_alarm():
    ics = bookings_to_ics([_booking(is_cancelled=True)], calendar_name="X", now=NOW)
    assert "STATUS:CANCELLED" in _lines(ics)
    assert "BEGIN:VALARM" not in ics


def test_empty_calendar_is_still_valid():
    lines = _lines(bookings_to_ics([], calendar_name="Vacío", now=NOW))
    assert lines[:2] == ["BEGIN:VCALENDAR", "VERSION:2.0"]
    assert "BEGIN:VEVENT" not in lines


def test_my_bookings_ics_only_has_my_active_upcoming_bookings(client, user, other_user, book):
    mine = book("10:00", "11:00", user).get_json()
    cancelled = book("12:00", "13:00", user).get_json()
    client.delete(f"/api/bookings/{cancelled['id']}", headers=user)
    book("15:00", "16:00", other_user)

    res = client.get("/api/bookings/mine.ics", headers=user)

    assert res.status_code == 200
    assert res.mimetype == "text/calendar"
    assert 'filename="mis-reservas.ics"' in res.headers["Content-Disposition"]
    body = res.get_data(as_text=True)
    assert body.count("BEGIN:VEVENT") == 1
    assert f"UID:booking-{mine['id']}@room-booking" in body


def test_single_booking_ics(client, user, book):
    booking = book("10:00", "11:00", user).get_json()
    res = client.get(f"/api/bookings/{booking['id']}.ics", headers=user)
    assert res.status_code == 200
    assert "SUMMARY:Reunión" in res.get_data(as_text=True)


def test_ics_requires_login(client):
    assert client.get("/api/bookings/mine.ics").status_code == 401
    assert client.get("/api/bookings/1.ics").status_code == 401
