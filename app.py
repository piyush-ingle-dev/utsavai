"""Application factory. Run locally with `python app.py`; gunicorn serves `app:app`."""
import logging
import os
from collections.abc import Callable
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(override=True)  # read .env for local runs; on Render the real environment variables are used

from flask import Flask, jsonify, send_from_directory  # noqa: E402
from flask.typing import ResponseReturnValue  # noqa: E402
from sqlalchemy import inspect, text  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

import api  # noqa: E402
import security  # noqa: E402
from config import load_settings  # noqa: E402
from extensions import limiter  # noqa: E402
from models import db  # noqa: E402

WEB_DIR = Path(__file__).parent / "web"


def create_app(overrides: dict | None = None) -> Flask:
    """Build the Flask app. `overrides` replaces config values (used by tests)."""
    settings = load_settings()
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s %(message)s")

    app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
    app.config.update(SECRET_KEY=settings.secret_key, SQLALCHEMY_DATABASE_URI=settings.database_url,
                      MAX_CONTENT_LENGTH=settings.max_body_bytes, PRODUCTION=settings.production)
    app.config.update(overrides or {})

    db.init_app(app)
    limiter.init_app(app)
    security.init_security(app, production=app.config["PRODUCTION"])
    app.register_blueprint(api.bp)
    register_web(app)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
        upgrade_schema()
    return app


def upgrade_schema() -> None:
    """Add columns introduced after the first release to databases created by an older version.

    Old plans get an empty edit-token hash, which no token can match, so they stay readable but become view-only.
    """
    columns = {column["name"] for column in inspect(db.engine).get_columns("plans")}
    if "edit_token_hash" not in columns:
        with db.engine.begin() as connection:
            connection.execute(text("ALTER TABLE plans ADD COLUMN edit_token_hash VARCHAR(64) NOT NULL DEFAULT ''"))


def register_web(app: Flask) -> None:
    """Serve the built React app for "/" and "/plan/<id>" (the browser router handles the rest)."""

    def spa() -> ResponseReturnValue:
        if not (WEB_DIR / "index.html").exists():
            return jsonify(error="Frontend not built. Run: cd frontend && npm install && npm run build"), 503
        return send_from_directory(WEB_DIR, "index.html")

    app.add_url_rule("/", "index", spa)
    app.add_url_rule("/plan/<plan_id>", "plan_page", lambda plan_id: spa())

    @app.get("/healthz")
    @limiter.exempt
    @security.exempt_from_https_redirect
    def healthz() -> ResponseReturnValue:
        return jsonify(status="ok")


def register_error_handlers(app: Flask) -> None:
    messages = {
        403: "You do not have permission to do that.",
        404: "Not found.",
        413: "That request is too large.",
        415: "Send a JSON body with Content-Type: application/json.",
        429: "Too many requests. Please wait a minute.",
        500: "Something went wrong on our side.",
    }
    def make_handler(message: str) -> Callable[[HTTPException], ResponseReturnValue]:
        def handler(error: HTTPException) -> ResponseReturnValue:
            return jsonify(error=message), getattr(error, "code", None) or 500
        return handler

    for code, message in messages.items():
        app.register_error_handler(code, make_handler(message))


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))  # noqa: S104  # nosec B104 - containers must listen on all interfaces
