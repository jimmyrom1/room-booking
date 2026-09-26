from flask import Flask, jsonify
from marshmallow import ValidationError
from psycopg import errors as pg_errors
from sqlalchemy.exc import IntegrityError
from werkzeug.exceptions import HTTPException

from .extensions import db


class ConflictError(Exception):
    """La petición es válida pero choca con el estado actual de los datos."""


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(ValidationError)
    def handle_validation(err: ValidationError):
        # normalized_messages() siempre devuelve {campo: [mensajes]}, también para los
        # ValidationError lanzados fuera de un esquema (p. ej. en rules.py).
        return jsonify(error="validation_error", details=err.normalized_messages()), 422

    @app.errorhandler(ConflictError)
    def handle_conflict(err: ConflictError):
        return jsonify(error="conflict", message=str(err)), 409

    @app.errorhandler(IntegrityError)
    def handle_integrity(err: IntegrityError):
        db.session.rollback()
        if isinstance(err.orig, pg_errors.ExclusionViolation):
            # Lo lanza la restricción EXCLUDE: otra reserva ocupa ya ese hueco.
            return jsonify(
                error="slot_taken", message="La sala ya está reservada en ese horario."
            ), 409
        return jsonify(error="conflict", message="Violación de integridad de datos."), 409

    @app.errorhandler(HTTPException)
    def handle_http(err: HTTPException):
        return jsonify(error=err.name.lower().replace(" ", "_"), message=err.description), err.code
