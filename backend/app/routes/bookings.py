from datetime import timedelta

from flask import Blueprint, Response, abort, current_app, jsonify, request
from flask_jwt_extended import current_user, jwt_required
from marshmallow import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import joinedload

from ..errors import ConflictError
from ..extensions import db
from ..ical import bookings_to_ics
from ..models import Booking, utcnow
from ..queries import overlaps
from ..rules import BookingPolicy
from ..schemas import BookingInputSchema, BookingSchema, RangeQuerySchema
from .rooms import get_active_room_or_404

bp = Blueprint("bookings", __name__)
schema = BookingSchema()
MAX_CALENDAR_RANGE = timedelta(days=42)


def _with_relations(stmt):
    return stmt.options(joinedload(Booking.room), joinedload(Booking.user))


@bp.get("")
@jwt_required()
def calendar():
    """Reservas activas en una franja (para pintar el calendario). ?from=&to=[&room_id=]"""
    window = RangeQuerySchema().load(request.args)
    start, end = window["start"], window["end"]
    if not timedelta(0) < end - start <= MAX_CALENDAR_RANGE:
        raise ValidationError("El rango debe ser positivo y de 6 semanas como máximo.", "to")

    stmt = _with_relations(select(Booking)).where(overlaps(start, end)).order_by(Booking.starts_at)
    if room_id := request.args.get("room_id", type=int):
        stmt = stmt.where(Booking.room_id == room_id)
    return jsonify(schema.dump(db.session.scalars(stmt).all(), many=True))


@bp.get("/mine")
@jwt_required()
def my_bookings():
    now = utcnow()
    past = request.args.get("scope") == "past"
    stmt = _with_relations(select(Booking)).where(Booking.user_id == current_user.id)
    if past:
        stmt = stmt.where(Booking.ends_at <= now).order_by(Booking.starts_at.desc()).limit(50)
    else:
        stmt = stmt.where(Booking.ends_at > now).order_by(Booking.starts_at)
    return jsonify(schema.dump(db.session.scalars(stmt).all(), many=True))


@bp.get("/mine.ics")
@jwt_required()
def my_bookings_ics():
    """Mis próximas reservas activas como archivo .ics para importar en cualquier calendario."""
    stmt = (
        _with_relations(select(Booking))
        .where(Booking.user_id == current_user.id)
        .where(Booking.ends_at > utcnow(), Booking.cancelled_at.is_(None))
        .order_by(Booking.starts_at)
    )
    bookings = db.session.scalars(stmt).all()
    return _ics_response(bookings, "Mis reservas de salas", "mis-reservas.ics")


@bp.get("/<int:booking_id>.ics")
@jwt_required()
def booking_ics(booking_id: int):
    booking = _get_booking(booking_id)
    return _ics_response([booking], booking.title, f"reserva-{booking.id}.ics")


def _ics_response(bookings, calendar_name: str, filename: str) -> Response:
    body = bookings_to_ics(bookings, calendar_name=calendar_name, now=utcnow())
    return Response(
        body,
        mimetype="text/calendar",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@bp.post("")
@jwt_required()
def create_booking():
    data = BookingInputSchema().load(request.get_json(silent=True) or {})
    room = get_active_room_or_404(data["room_id"])
    BookingPolicy.from_config(current_app.config).validate(
        data["starts_at"], data["ends_at"], now=utcnow()
    )
    booking = Booking(user=current_user, room=room, **data)
    db.session.add(booking)
    # Sin comprobación previa de disponibilidad: el EXCLUDE de PostgreSQL es la única
    # fuente de verdad y el IntegrityError se traduce a 409 en errors.py.
    db.session.commit()
    return jsonify(schema.dump(booking)), 201


@bp.get("/<int:booking_id>")
@jwt_required()
def get_booking(booking_id: int):
    return jsonify(schema.dump(_get_booking(booking_id)))


@bp.delete("/<int:booking_id>")
@jwt_required()
def cancel_booking(booking_id: int):
    booking = _get_booking(booking_id)
    if booking.user_id != current_user.id and not current_user.is_admin:
        abort(403, description="Solo puedes cancelar tus propias reservas.")
    if booking.is_cancelled:
        raise ConflictError("La reserva ya estaba cancelada.")
    if booking.starts_at <= utcnow():
        raise ConflictError("No se puede cancelar una reserva que ya ha empezado.")
    booking.cancelled_at = utcnow()
    db.session.commit()
    return jsonify(schema.dump(booking))


def _get_booking(booking_id: int) -> Booking:
    booking = db.session.scalar(_with_relations(select(Booking)).where(Booking.id == booking_id))
    if booking is None:
        abort(404, description="Reserva no encontrada.")
    return booking
