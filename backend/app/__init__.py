"""Aplicação Flask do Achados e Perdidos."""
import os

from flask import Flask

from . import db


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        DATABASE=os.environ.get("DATABASE", os.path.join(app.instance_path, "achados.sqlite")),
        UPLOAD_DIR=os.environ.get("UPLOAD_DIR", os.path.join(app.instance_path, "uploads")),
        STAFF_TOKEN=os.environ.get("STAFF_TOKEN", ""),
        VISIBILITY_DAYS=int(os.environ.get("VISIBILITY_DAYS", "90")),
        MAX_CONTENT_LENGTH=6 * 1024 * 1024,
        ANTHROPIC_API_KEY=os.environ.get("ANTHROPIC_API_KEY", ""),
        ANTHROPIC_MODEL=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5"),
        FRONTEND_DIR=os.path.abspath(os.path.join(app.root_path, "..", "..", "frontend")),
    )
    if test_config:
        app.config.update(test_config)

    os.makedirs(os.path.dirname(app.config["DATABASE"]) or ".", exist_ok=True)
    os.makedirs(app.config["UPLOAD_DIR"], exist_ok=True)

    db.init_app(app)

    from .routes import bp

    app.register_blueprint(bp)
    return app
