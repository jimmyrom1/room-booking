def test_first_user_is_admin_and_next_ones_are_not(client, admin, user):
    assert client.get("/api/auth/me", headers=admin).get_json()["is_admin"] is True
    assert client.get("/api/auth/me", headers=user).get_json()["is_admin"] is False


def test_register_validates_input(client):
    res = client.post("/api/auth/register", json={"name": "A", "email": "x", "password": "123"})
    assert res.status_code == 422
    assert set(res.get_json()["details"]) == {"name", "email", "password"}


def test_register_rejects_duplicate_email_case_insensitive(client, admin):
    res = client.post(
        "/api/auth/register",
        json={"name": "Otro", "email": "ADMIN@test.local", "password": "secreta123"},
    )
    assert res.status_code == 409


def test_login(client, admin):
    ok = client.post(
        "/api/auth/login", json={"email": "admin@test.local", "password": "secreta123"}
    )
    assert ok.status_code == 200 and ok.get_json()["access_token"]

    bad = client.post("/api/auth/login", json={"email": "admin@test.local", "password": "mala"})
    unknown = client.post("/api/auth/login", json={"email": "nadie@x.com", "password": "mala"})
    assert bad.status_code == unknown.status_code == 401
    # No se revela si el email existe.
    assert bad.get_json() == unknown.get_json()


def test_password_is_hashed(app, admin):
    from app.models import User

    stored = User.query.one().password_hash
    assert "secreta123" not in stored and stored.startswith("scrypt:")


def test_protected_endpoints_require_token(client):
    assert client.get("/api/rooms").status_code == 401
    bad = client.get("/api/rooms", headers={"Authorization": "Bearer basura"})
    assert bad.status_code == 401


def test_health(client):
    assert client.get("/api/health").get_json() == {"status": "ok"}


def test_seed_creates_consistent_demo_data(app, client):
    runner = app.test_cli_runner()
    assert "Creados 3 usuarios" in runner.invoke(args=["seed"]).output
    assert "ya tiene datos" in runner.invoke(args=["seed"]).output
    res = client.post("/api/auth/login", json={"email": "ana@demo.local", "password": "demo1234"})
    assert res.status_code == 200
