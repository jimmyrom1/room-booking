from marshmallow import EXCLUDE, Schema, fields, validate


class RegisterSchema(Schema):
    name = fields.Str(required=True, validate=validate.Length(min=2, max=120))
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True, validate=validate.Length(min=8, max=128))


class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True, load_only=True)


class UserSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    email = fields.Email()
    is_admin = fields.Bool()


class RoomSchema(Schema):
    id = fields.Int(dump_only=True)
    name = fields.Str(required=True, validate=validate.Length(min=1, max=80))
    capacity = fields.Int(required=True, validate=validate.Range(min=1, max=500))
    location = fields.Str(allow_none=True, validate=validate.Length(max=120))
    amenities = fields.List(
        fields.Str(validate=validate.Length(min=1, max=40)),
        load_default=list,
        validate=validate.Length(max=20),
    )
    is_active = fields.Bool(load_default=True)


class BookingInputSchema(Schema):
    room_id = fields.Int(required=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=120))
    # Se exige zona horaria explícita: "2026-10-05T10:00:00+02:00" o "...Z".
    starts_at = fields.AwareDateTime(required=True)
    ends_at = fields.AwareDateTime(required=True)


class BookingSchema(Schema):
    id = fields.Int()
    title = fields.Str()
    starts_at = fields.DateTime()
    ends_at = fields.DateTime()
    is_cancelled = fields.Bool()
    room = fields.Nested(RoomSchema(only=("id", "name", "location")))
    user = fields.Nested(UserSchema(only=("id", "name")))


class RangeQuerySchema(Schema):
    class Meta:
        # Se carga desde la query string, que trae más filtros (room_id, min_capacity...).
        unknown = EXCLUDE

    start = fields.AwareDateTime(required=True, data_key="from")
    end = fields.AwareDateTime(required=True, data_key="to")
