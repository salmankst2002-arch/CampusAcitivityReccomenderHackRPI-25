# app/__init__.py
import os
from flask import Flask, jsonify
from flask_cors import CORS

from .extensions import db, migrate


def create_app(config_object=None):
    """
    Flask application factory.
    If config_object is provided, use it; otherwise use DevConfig by default.
    """
    app = Flask(__name__, instance_relative_config=True)

    # ---- Load configuration ----
    if config_object is not None:
        app.config.from_object(config_object)
    else:
        from config import DevConfig
        app.config.from_object(DevConfig)

    # Ensure instance folder exists (for SQLite DB, etc.)
    try:
        os.makedirs(app.instance_path, exist_ok=True)
    except OSError:
        pass

    # ---- Initialize extensions ----
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so that Flask-Migrate can detect them
    from . import models  # noqa: F401

    # ---- Register blueprints ----
    from .main.routes import main_bp
    app.register_blueprint(main_bp)

    from .api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from .calendar.routes import calendar_bp
    app.register_blueprint(calendar_bp, url_prefix="/calendar")

    try:
        from .auth.routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix="/auth")
    except ImportError:
        # Allow running even if auth blueprint is not implemented yet
        pass

    from .events import events_bp
    app.register_blueprint(events_bp, url_prefix="/api")

    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # ---- Health check route ----
    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "app": "CampusMatching backend"})

    return app
