"""Expresiones SQL reutilizables sobre rangos de tiempo."""

from datetime import datetime

from sqlalchemy import ColumnElement, func, literal

from .models import Booking


def booking_range() -> ColumnElement:
    return func.tstzrange(Booking.starts_at, Booking.ends_at, "[)")


def overlaps(start: datetime, end: datetime) -> ColumnElement[bool]:
    """Reserva activa que se solapa con [start, end). Usa el mismo índice GiST del EXCLUDE."""
    requested = func.tstzrange(literal(start), literal(end), "[)")
    return booking_range().op("&&")(requested) & Booking.cancelled_at.is_(None)
