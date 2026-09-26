from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import DDL, CheckConstraint, DateTime, ForeignKey, String, event, func
from sqlalchemy.dialects.postgresql import ARRAY, ExcludeConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db

# btree_gist permite mezclar "=" (room_id) y "&&" (rangos) en un mismo índice GiST.
event.listen(db.metadata, "before_create", DDL("CREATE EXTENSION IF NOT EXISTS btree_gist"))


def utcnow() -> datetime:
    return datetime.now(UTC)


class User(db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    bookings: Mapped[list[Booking]] = relationship(back_populates="user")

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Room(db.Model):
    __tablename__ = "rooms"
    __table_args__ = (CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    capacity: Mapped[int]
    location: Mapped[str | None] = mapped_column(String(120))
    amenities: Mapped[list[str]] = mapped_column(ARRAY(String(40)), default=list)
    is_active: Mapped[bool] = mapped_column(default=True)

    bookings: Mapped[list[Booking]] = relationship(back_populates="room")


class Booking(db.Model):
    __tablename__ = "bookings"
    __table_args__ = (CheckConstraint("ends_at > starts_at", name="ck_bookings_positive_duration"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id", ondelete="RESTRICT"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(120))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    room: Mapped[Room] = relationship(back_populates="bookings")
    user: Mapped[User] = relationship(back_populates="bookings")

    @property
    def is_cancelled(self) -> bool:
        return self.cancelled_at is not None


# La garantía central del sistema: dos reservas activas de la misma sala no pueden
# solaparse. Lo impone PostgreSQL, así que es inmune a condiciones de carrera.
# El rango es semiabierto [inicio, fin): una reserva puede empezar justo cuando acaba otra.
_bookings = Booking.__table__
_bookings.append_constraint(
    ExcludeConstraint(
        (_bookings.c.room_id, "="),
        (func.tstzrange(_bookings.c.starts_at, _bookings.c.ends_at, "[)"), "&&"),
        where=_bookings.c.cancelled_at.is_(None),
        using="gist",
        name="ex_bookings_no_overlap",
    )
)
