from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token, current_user, jwt_required
from sqlalchemy import func, select

from ..errors import ConflictError
from ..extensions import db
from ..models import User
from ..schemas import LoginSchema, RegisterSchema, UserSchema

bp = Blueprint("auth", __name__)
user_schema = UserSchema()


def _token_response(user: User, status: int = 200):
    token = create_access_token(identity=user)
    return jsonify(access_token=token, user=user_schema.dump(user)), status


@bp.post("/register")
def register():
    data = RegisterSchema().load(request.get_json(silent=True) or {})
    email = data["email"].lower()
    if db.session.scalar(select(User.id).where(User.email == email)):
        raise ConflictError("Ya existe una cuenta con ese email.")
    # El primer usuario registrado es administrador: así se arranca sin tocar la BD a mano.
    is_first = db.session.scalar(select(func.count(User.id))) == 0
    user = User(name=data["name"], email=email, is_admin=is_first)
    user.set_password(data["password"])
    db.session.add(user)
    db.session.commit()
    return _token_response(user, 201)


@bp.post("/login")
def login():
    data = LoginSchema().load(request.get_json(silent=True) or {})
    user = db.session.scalar(select(User).where(User.email == data["email"].lower()))
    # Mismo mensaje tanto si el email no existe como si la contraseña falla.
    if user is None or not user.check_password(data["password"]):
        return jsonify(error="invalid_credentials", message="Email o contraseña incorrectos."), 401
    return _token_response(user)


@bp.get("/me")
@jwt_required()
def me():
    return jsonify(user_schema.dump(current_user))
