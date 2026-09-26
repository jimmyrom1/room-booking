"""Reglas de negocio de las reservas, como funciones puras para poder testearlas aisladas."""

from dataclasses import dataclass
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from marshmallow import ValidationError


@dataclass(frozen=True)
class BookingPolicy:
    timezone: ZoneInfo
    opening: time
    closing: time
    slot_minutes: int
    max_duration: timedelta
    max_days_ahead: int

    @classmethod
    def from_config(cls, config) -> "BookingPolicy":
        return cls(
            timezone=ZoneInfo(config["OFFICE_TIMEZONE"]),
            opening=config["OPENING_TIME"],
            closing=config["CLOSING_TIME"],
            slot_minutes=config["SLOT_MINUTES"],
            max_duration=config["MAX_BOOKING"],
            max_days_ahead=config["MAX_DAYS_AHEAD"],
        )

    def validate(self, starts_at: datetime, ends_at: datetime, now: datetime) -> None:
        """Lanza ValidationError con un mensaje por campo si la franja no es reservable."""
        start = starts_at.astimezone(self.timezone)
        end = ends_at.astimezone(self.timezone)

        if end <= start:
            raise ValidationError("Debe terminar después de empezar.", "ends_at")
        if starts_at <= now:
            raise ValidationError("No se puede reservar en el pasado.", "starts_at")
        if starts_at - now > timedelta(days=self.max_days_ahead):
            raise ValidationError(
                f"Solo se puede reservar con {self.max_days_ahead} días de antelación.",
                "starts_at",
            )
        for field, value in (("starts_at", start), ("ends_at", end)):
            if value.minute % self.slot_minutes or value.second or value.microsecond:
                raise ValidationError(
                    f"Las horas van en tramos de {self.slot_minutes} minutos.", field
                )
        if end - start > self.max_duration:
            hours = int(self.max_duration.total_seconds() // 3600)
            raise ValidationError(f"La duración máxima es de {hours} horas.", "ends_at")
        if start.date() != end.date() or start.time() < self.opening or end.time() > self.closing:
            raise ValidationError(
                f"Horario de la oficina: {self.opening:%H:%M}–{self.closing:%H:%M}.", "starts_at"
            )
        if start.weekday() >= 5:
            raise ValidationError("La oficina cierra los fines de semana.", "starts_at")

    def open_hours_between(self, start: datetime, end: datetime) -> float:
        """Horas de apertura (días laborables) en el intervalo, para calcular la ocupación."""
        day = start.astimezone(self.timezone).date()
        last = end.astimezone(self.timezone).date()
        seconds = 0.0
        while day <= last:
            if day.weekday() < 5:
                opens = datetime.combine(day, self.opening, self.timezone)
                closes = datetime.combine(day, self.closing, self.timezone)
                overlap = min(closes, end) - max(opens, start)
                seconds += max(overlap.total_seconds(), 0)
            day += timedelta(days=1)
        return seconds / 3600
