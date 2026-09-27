"""Exportación de reservas a iCalendar (RFC 5545), sin dependencias externas.

Es una función pura, como rules.py: recibe reservas y devuelve texto. Así se testea sin base de
datos y el formato (escapado, plegado de líneas, CRLF) se comprueba línea a línea.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from .models import Booking

PRODID = "-//room-booking//Reserva de salas//ES"
UID_DOMAIN = "room-booking"
REMINDER_MINUTES = 15
_MAX_LINE_OCTETS = 75


def bookings_to_ics(bookings: Iterable[Booking], *, calendar_name: str, now: datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(calendar_name)}",
    ]
    for booking in bookings:
        lines += _event(booking, now)
    lines.append("END:VCALENDAR")
    # El estándar exige CRLF, también después de la última línea.
    return "".join(_fold(line) + "\r\n" for line in lines)


def _event(booking: Booking, now: datetime) -> list[str]:
    room = booking.room
    location = room.name + (f" ({room.location})" if room.location else "")
    lines = [
        "BEGIN:VEVENT",
        # UID estable: si se vuelve a importar el archivo, el calendario actualiza el evento
        # en lugar de duplicarlo.
        f"UID:booking-{booking.id}@{UID_DOMAIN}",
        f"DTSTAMP:{_utc(now)}",
        f"DTSTART:{_utc(booking.starts_at)}",
        f"DTEND:{_utc(booking.ends_at)}",
        f"SUMMARY:{_escape(booking.title)}",
        f"LOCATION:{_escape(location)}",
        f"DESCRIPTION:{_escape(f'Sala {room.name} · reservada por {booking.user.name}')}",
        f"STATUS:{'CANCELLED' if booking.is_cancelled else 'CONFIRMED'}",
    ]
    if not booking.is_cancelled:
        lines += [
            "BEGIN:VALARM",
            "ACTION:DISPLAY",
            f"DESCRIPTION:{_escape(booking.title)}",
            f"TRIGGER:-PT{REMINDER_MINUTES}M",
            "END:VALARM",
        ]
    lines.append("END:VEVENT")
    return lines


def _utc(value: datetime) -> str:
    """20260928T080000Z: en UTC, así cada calendario lo muestra en la zona de quien lo abre."""
    return value.astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _escape(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Parte las líneas de más de 75 octetos (no caracteres) sin cortar un carácter UTF-8."""
    if len(line.encode()) <= _MAX_LINE_OCTETS:
        return line
    parts, current, size = [], "", 0
    for char in line:
        char_size = len(char.encode())
        # La primera línea admite 75 octetos; las de continuación, 74 más el espacio inicial.
        limit = _MAX_LINE_OCTETS if not parts else _MAX_LINE_OCTETS - 1
        if size + char_size > limit:
            parts.append(current)
            current, size = "", 0
        current += char
        size += char_size
    parts.append(current)
    return "\r\n ".join(parts)
