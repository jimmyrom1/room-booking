from functools import wraps

from flask import jsonify
from flask_jwt_extended import current_user, verify_jwt_in_request

from .extensions import db, jwt
from .models import User


def register_jwt_callbacks() -> None:
    @jwt.user_identity_loader
    def user_identity(user: User) -> str:
        return str(user.id)

    @jwt.user_lookup_loader
    def user_lookup(_header, payload) -> User | None:
        return db.session.get(User, int(payload["sub"]))

    @jwt.user_lookup_error_loader
    def user_not_found(_header, _payload):
        return jsonify(error="unauthorized", message="El usuario ya no existe."), 401

    @jwt.unauthorized_loader
    def missing_token(reason: str):
        return jsonify(error="unauthorized", message="Necesitas iniciar sesión."), 401

    @jwt.invalid_token_loader
    def invalid_token(reason: str):
        return jsonify(error="unauthorized", message="Sesión no válida."), 401

    @jwt.expired_token_loader
    def expired_token(_header, _payload):
        return jsonify(error="token_expired", message="La sesión ha caducado."), 401


def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        if not current_user.is_admin:
            return jsonify(error="forbidden", message="Solo para administradores."), 403
        return fn(*args, **kwargs)

    return wrapper
