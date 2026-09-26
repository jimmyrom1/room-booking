import os
from datetime import time, timedelta


class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", "postgresql+psycopg://booking:booking@localhost:5432/booking"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # La API siempre habla en UTC, sea cual sea la zona horaria del servidor PostgreSQL.
    SQLALCHEMY_ENGINE_OPTIONS = {"connect_args": {"options": "-c timezone=UTC"}}
    JSON_SORT_KEYS = False
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-only-secret-change-me-in-production-0123")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)

    # Reglas de negocio de las reservas
    OFFICE_TIMEZONE = os.getenv("OFFICE_TIMEZONE", "Europe/Madrid")
    OPENING_TIME = time(8, 0)
    CLOSING_TIME = time(21, 0)
    SLOT_MINUTES = 15
    MAX_BOOKING = timedelta(hours=4)
    MAX_DAYS_AHEAD = 60


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "TEST_DATABASE_URL",
        "postgresql+psycopg://booking:booking@localhost:5432/booking_test",
    )
