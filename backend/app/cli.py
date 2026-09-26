import random
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import click
from flask import Flask, current_app

from .extensions import db
from .models import Booking, Room, User

ROOMS = [
    ("Atlántico", 12, "Planta 2", ["proyector", "videoconferencia", "pizarra"]),
    ("Mediterráneo", 8, "Planta 2", ["pantalla", "videoconferencia"]),
    ("Cantábrico", 6, "Planta 1", ["pantalla", "pizarra"]),
    ("Teide", 4, "Planta 1", ["pantalla"]),
    ("Mulhacén", 2, "Planta 1", ["cabina", "insonorizada"]),
    ("Auditorio", 40, "Planta baja", ["proyector", "micrófono", "streaming"]),
]

TITLES = [
    "Daily del equipo",
    "Entrevista",
    "Revisión de sprint",
    "Reunión con cliente",
    "Formación interna",
    "1:1",
    "Planificación trimestral",
    "Demo de producto",
]

DEMO_PASSWORD = "demo1234"


def _weekdays_from(start: date, count: int) -> list[date]:
    days, day = [], start
    while len(days) < count:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    return days


def register_cli(app: Flask) -> None:
    @app.cli.command("seed")
    @click.option("--seed", default=42, help="Semilla para que los datos sean reproducibles.")
    def seed(seed: int) -> None:
        """Crea usuarios, salas y reservas de ejemplo (solo si la base de datos está vacía)."""
        if db.session.query(User.id).first():
            click.echo("La base de datos ya tiene datos; no se carga nada.")
            return

        rng = random.Random(seed)
        tz = ZoneInfo(current_app.config["OFFICE_TIMEZONE"])

        admin = User(name="Admin Demo", email="admin@demo.local", is_admin=True)
        ana = User(name="Ana García", email="ana@demo.local")
        luis = User(name="Luis Martín", email="luis@demo.local")
        for user in (admin, ana, luis):
            user.set_password(DEMO_PASSWORD)
        rooms = [Room(name=n, capacity=c, location=loc, amenities=a) for n, c, loc, a in ROOMS]
        db.session.add_all([admin, ana, luis, *rooms])

        # Dos semanas laborables hacia atrás (para estadísticas) y dos hacia delante.
        today = datetime.now(tz).date()
        days = _weekdays_from(today - timedelta(days=14), 20)
        now = datetime.now(tz)
        count = 0
        for day in days:
            for room in rooms:
                hour = 9
                while hour < 19:
                    if rng.random() < 0.45:
                        length = rng.choice([1, 1, 2])
                        starts = datetime.combine(day, time(hour, 0), tz)
                        ends = starts + timedelta(hours=length)
                        if starts > now or ends < now:  # sin reservas "en curso" a medias
                            db.session.add(
                                Booking(
                                    room=room,
                                    user=rng.choice([ana, luis, admin]),
                                    title=rng.choice(TITLES),
                                    starts_at=starts,
                                    ends_at=ends,
                                )
                            )
                            count += 1
                        hour += length
                    hour += 1
        db.session.commit()
        click.echo(
            f"Creados 3 usuarios (contraseña: {DEMO_PASSWORD}), {len(rooms)} salas "
            f"y {count} reservas."
        )
