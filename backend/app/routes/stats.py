from flask import Blueprint, current_app, jsonify, request
from marshmallow import ValidationError
from sqlalchemy import and_, func, literal, select

from ..auth import admin_required
from ..extensions import db
from ..models import Booking, Room
from ..rules import BookingPolicy
from ..schemas import RangeQuerySchema

bp = Blueprint("stats", __name__)


@bp.get("/occupancy")
@admin_required
def occupancy():
    """Horas reservadas y % de ocupación por sala en [from, to), recortando en los bordes."""
    window = RangeQuerySchema().load(request.args)
    start, end = window["start"], window["end"]
    if end <= start:
        raise ValidationError("Debe ser posterior a 'from'.", "to")

    clipped_seconds = func.extract(
        "epoch",
        func.least(Booking.ends_at, literal(end))
        - func.greatest(Booking.starts_at, literal(start)),
    )
    # FILTER descarta las filas del OUTER JOIN sin reserva: LEAST/GREATEST ignoran los NULL
    # y, sin él, una sala vacía sumaría la ventana entera.
    booked_seconds = func.sum(clipped_seconds).filter(Booking.id.is_not(None))
    booked_hours = func.coalesce(booked_seconds, 0) / 3600
    stmt = (
        select(Room.id, Room.name, Room.capacity, booked_hours.label("hours"))
        .outerjoin(
            Booking,
            and_(
                Booking.room_id == Room.id,
                Booking.cancelled_at.is_(None),
                Booking.starts_at < end,
                Booking.ends_at > start,
            ),
        )
        .where(Room.is_active)
        .group_by(Room.id)
        .order_by(booked_hours.desc(), Room.name)
    )

    open_hours = BookingPolicy.from_config(current_app.config).open_hours_between(start, end)
    rooms = [
        {
            "room_id": row.id,
            "name": row.name,
            "capacity": row.capacity,
            "booked_hours": round(float(row.hours), 2),
            "occupancy": round(float(row.hours) / open_hours, 4) if open_hours else 0,
        }
        for row in db.session.execute(stmt)
    ]
    return jsonify(open_hours=round(open_hours, 2), rooms=rooms)
