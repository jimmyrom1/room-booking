from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

import pytest
from sqlalchemy import text

from app import create_app
from app.config import TestConfig
from app.extensions import db

TZ = ZoneInfo("Europe/Madrid")


@pytest.fixture(scope="session")
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.drop_all()
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    db.session.rollback()
    tables = ", ".join(t.name for t in db.metadata.sorted_tables)
    db.session.execute(text(f"TRUNCATE {tables} RESTART IDENTITY CASCADE"))
    db.session.commit()
    db.session.remove()  # vacía el identity map: los ids vuelven a empezar en 1


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, name, email):
    res = client.post(
        "/api/auth/register", json={"name": name, "email": email, "password": "secreta123"}
    )
    assert res.status_code == 201, res.get_json()
    return {"Authorization": f"Bearer {res.get_json()['access_token']}"}


@pytest.fixture
def admin(client):
    """El primer usuario registrado es administrador."""
    return _register(client, "Admin", "admin@test.local")


@pytest.fixture
def user(client, admin):
    return _register(client, "Ana", "ana@test.local")


@pytest.fixture
def other_user(client, admin):
    return _register(client, "Luis", "luis@test.local")


@pytest.fixture
def room(client, admin):
    res = client.post(
        "/api/rooms",
        json={"name": "Atlántico", "capacity": 10, "amenities": ["proyector"]},
        headers=admin,
    )
    assert res.status_code == 201
    return res.get_json()


@pytest.fixture
def next_monday():
    """Un lunes futuro (siempre laborable y dentro del plazo de reserva)."""
    today = datetime.now(TZ).date()
    return today + timedelta(days=7 - today.weekday())


@pytest.fixture
def at(next_monday):
    """at("10:30") → ISO del próximo lunes a esa hora en Madrid; at("10:30", day=1) → martes."""

    def _at(hhmm: str, day: int = 0) -> str:
        h, m = map(int, hhmm.split(":"))
        return datetime.combine(next_monday + timedelta(days=day), time(h, m), TZ).isoformat()

    return _at


@pytest.fixture
def book(client, room, at):
    def _book(start: str, end: str, headers, room_id=None, day=0):
        return client.post(
            "/api/bookings",
            json={
                "room_id": room_id or room["id"],
                "title": "Reunión",
                "starts_at": at(start, day),
                "ends_at": at(end, day),
            },
            headers=headers,
        )

    return _book
