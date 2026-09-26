from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS

from .auth import register_jwt_callbacks
from .cli import register_cli
from .config import Config
from .errors import register_error_handlers
from .extensions import db, jwt, migrate


def create_app(config_class: type[Config] = Config) -> Flask:
    load_dotenv()
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    from .routes.auth import bp as auth_bp
    from .routes.bookings import bp as bookings_bp
    from .routes.health import bp as health_bp
    from .routes.rooms import bp as rooms_bp
    from .routes.stats import bp as stats_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(rooms_bp, url_prefix="/api/rooms")
    app.register_blueprint(bookings_bp, url_prefix="/api/bookings")
    app.register_blueprint(stats_bp, url_prefix="/api/stats")

    register_jwt_callbacks()
    register_error_handlers(app)
    register_cli(app)
    return app
