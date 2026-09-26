from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import current_user, jwt_required
from marshmallow import ValidationError
from sqlalchemy import any_, exists, literal, select

from ..auth import admin_required
from ..errors import ConflictError
from ..extensions import db
from ..models import Booking, Room
from ..queries import overlaps
from ..schemas import RangeQuerySchema, RoomSchema

bp = Blueprint("rooms", __name__)
schema = RoomSchema()


@bp.get("")
@jwt_required()
def list_rooms():
    """Lista salas. Con ?from=&to= devuelve solo las libres en esa franja."""
    stmt = select(Room).order_by(Room.name)
    if not (current_user.is_admin and request.args.get("include_inactive")):
        stmt = stmt.where(Room.is_active)
    if min_capacity := request.args.get("min_capacity", type=int):
        stmt = stmt.where(Room.capacity >= min_capacity)
    if amenity := request.args.get("amenity"):
        stmt = stmt.where(literal(amenity) == any_(Room.amenities))
    if "from" in request.args or "to" in request.args:
        window = RangeQuerySchema().load(request.args)
        if window["end"] <= window["start"]:
            raise ValidationError("Debe ser posterior a 'from'.", "to")
        busy = exists().where(Booking.room_id == Room.id, overlaps(window["start"], window["end"]))
        stmt = stmt.where(~busy)
    return jsonify(schema.dump(db.session.scalars(stmt).all(), many=True))


@bp.get("/<int:room_id>")
@jwt_required()
def get_room(room_id: int):
    return jsonify(schema.dump(db.get_or_404(Room, room_id)))


@bp.post("")
@admin_required
def create_room():
    data = schema.load(request.get_json(silent=True) or {})
    _ensure_name_available(data["name"])
    room = Room(**data)
    db.session.add(room)
    db.session.commit()
    return jsonify(schema.dump(room)), 201


@bp.put("/<int:room_id>")
@admin_required
def update_room(room_id: int):
    room = db.get_or_404(Room, room_id)
    data = schema.load(request.get_json(silent=True) or {})
    if data["name"] != room.name:
        _ensure_name_available(data["name"])
    for key, value in data.items():
        setattr(room, key, value)
    db.session.commit()
    return jsonify(schema.dump(room))


@bp.delete("/<int:room_id>")
@admin_required
def delete_room(room_id: int):
    """Borra la sala si nunca se ha usado; si tiene historial, la desactiva."""
    room = db.get_or_404(Room, room_id)
    has_bookings = db.session.scalar(select(exists().where(Booking.room_id == room_id)))
    if has_bookings:
        room.is_active = False
        db.session.commit()
        return jsonify(schema.dump(room))
    db.session.delete(room)
    db.session.commit()
    return "", 204


def _ensure_name_available(name: str) -> None:
    if db.session.scalar(select(Room.id).where(Room.name == name)):
        raise ConflictError(f"Ya existe una sala llamada «{name}».")


def get_active_room_or_404(room_id: int) -> Room:
    room = db.session.get(Room, room_id)
    if room is None or not room.is_active:
        abort(404, description="La sala no existe o no está disponible.")
    return room
