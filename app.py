from dotenv import load_dotenv
load_dotenv()

import os
import secrets
from datetime import date
from pathlib import Path

from flask import Flask, Response, abort, jsonify, request, send_from_directory
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

import planner
from agents.chat import answer
from agents.graph import generate_plan
from models import Plan, db

WEB_DIR = Path(__file__).parent / "web"

limiter = Limiter(key_func=get_remote_address, default_limits=["300 per hour"], storage_uri="memory://")

CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self'",
    "img-src": ["'self'", "data:"],
    "connect-src": "'self'",
    "object-src": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'none'",
}


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__, static_folder=str(WEB_DIR), static_url_path="")
    db_url = os.environ.get("DATABASE_URL", "sqlite:///utsav.db")
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql://", 1)
    app.config.update(SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
                      SQLALCHEMY_DATABASE_URI=db_url, MAX_CONTENT_LENGTH=32 * 1024)
    if config:
        app.config.update(config)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1)
    db.init_app(app)
    limiter.init_app(app)
    Talisman(app, content_security_policy=CSP, force_https=False, session_cookie_secure=False, frame_options="DENY")
    with app.app_context():
        db.create_all()
    register_routes(app)
    return app


def get_plan_or_404(plan_id: str) -> Plan:
    if len(plan_id) != 32 or not all(c in "0123456789abcdef" for c in plan_id):
        abort(404)
    plan = db.session.get(Plan, plan_id)
    if plan is None:
        abort(404)
    return plan


def json_body() -> dict:
    """The API only accepts JSON. A JSON content type cannot be sent cross-site by a plain HTML form,
    and the API has no cookies or logins, so there is no session for a cross-site request to abuse."""
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(415)
    return body


def progress(data: dict) -> tuple[int, int]:
    items = data["timeline"] + data["vendors"]
    return sum(1 for i in items if i["done"]), len(items)


def register_routes(app: Flask) -> None:
    def spa():
        if not (WEB_DIR / "index.html").exists():
            return jsonify(error="Frontend not built. Run: cd frontend && npm install && npm run build"), 503
        return send_from_directory(WEB_DIR, "index.html")

    app.add_url_rule("/", "index", spa)
    app.add_url_rule("/plan/<plan_id>", "plan_page", lambda plan_id: spa())

    @app.post("/api/plans")
    @limiter.limit("20 per minute")
    def create_plan():
        clean, errors = planner.clean_form(json_body())
        if errors:
            return jsonify(error="Please fix the highlighted fields.", errors=errors), 400
        data = generate_plan(clean)
        plan = Plan(event_type=clean["event_type"], title=clean["title"], event_date=clean["event_date"],
                    guests=clean["guests"], budget=clean["budget"], city=clean["city"],
                    theme=clean["theme"], preferences=clean["preferences"])
        plan.data = data
        db.session.add(plan)
        db.session.commit()
        return jsonify(id=plan.id), 201

    @app.get("/api/plans/<plan_id>")
    def get_plan(plan_id):
        plan = get_plan_or_404(plan_id)
        done, total = progress(plan.data)
        return jsonify(id=plan.id, title=plan.title, event_type=plan.event_type,
                       event_label=planner.EVENTS[plan.event_type]["label"],
                       event_date=plan.event_date.isoformat(), guests=plan.guests, budget=plan.budget,
                       city=plan.city, theme=plan.theme, completed=done, total=total, plan=plan.data)

    @app.post("/api/plans/<plan_id>/toggle")
    @limiter.limit("120 per minute")
    def toggle(plan_id):
        plan = get_plan_or_404(plan_id)
        item_id = json_body().get("id")
        data = plan.data
        for item in data["timeline"] + data["vendors"]:
            if item["id"] == item_id:
                item["done"] = not item["done"]
                plan.data = data
                db.session.commit()
                done, total = progress(data)
                return jsonify(id=item_id, done=item["done"], completed=done, total=total)
        return jsonify(error="Unknown item"), 404

    @app.post("/api/plans/<plan_id>/ask")
    @limiter.limit("20 per minute")
    def ask(plan_id):
        plan = get_plan_or_404(plan_id)
        question = str(json_body().get("question") or "").strip()[:300]
        if len(question) < 3:
            return jsonify(error="Please type a question."), 400
        return jsonify(answer(question, plan.event_type, plan.data["summary"]))

    @app.get("/api/plans/<plan_id>/calendar.ics")
    def calendar(plan_id):
        plan = get_plan_or_404(plan_id)
        esc = lambda t: str(t).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
        lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//UtsavAI//EN"]
        for item in plan.data["timeline"]:
            lines += ["BEGIN:VEVENT", f"UID:{plan.id}-{item['id']}@utsavai",
                      f"DTSTAMP:{date.today():%Y%m%d}T000000Z", f"DTSTART;VALUE=DATE:{item['due'].replace('-', '')}",
                      f"SUMMARY:{esc(plan.title + ': ' + item['task'])}", "END:VEVENT"]
        lines.append("END:VCALENDAR")
        return Response("\r\n".join(lines) + "\r\n", mimetype="text/calendar",
                        headers={"Content-Disposition": "attachment; filename=event-plan.ics"})

    @app.get("/healthz")
    @app.get("/api/health")
    @limiter.exempt
    def healthz():
        return jsonify(status="ok")

    @app.errorhandler(404)
    def not_found(_):
        return jsonify(error="Not found"), 404

    @app.errorhandler(415)
    def bad_type(_):
        return jsonify(error="Send a JSON body with Content-Type: application/json"), 415

    @app.errorhandler(429)
    def too_many(_):
        return jsonify(error="Too many requests. Please wait a minute."), 429

    @app.errorhandler(500)
    def server_error(_):
        return jsonify(error="Something went wrong on our side."), 500


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
