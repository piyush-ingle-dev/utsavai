"""REST API blueprint: everything under /api."""
import logging
from datetime import date

from flask import Blueprint, Response, abort, jsonify, request

import planner
import security
from agents.chat import answer
from agents.graph import generate_plan
from extensions import limiter
from models import Plan, db

log = logging.getLogger(__name__)
bp = Blueprint("api", __name__, url_prefix="/api")

_HEX = frozenset("0123456789abcdef")


def get_plan_or_404(plan_id: str) -> Plan:
    """Load a plan, treating anything that is not a 32-character hex id as not found."""
    if len(plan_id) != 32 or not set(plan_id) <= _HEX:
        abort(404)
    plan = db.session.get(Plan, plan_id)
    if plan is None:
        abort(404)
    return plan


def json_body() -> dict:
    """Return the JSON object in the request, or answer 415.

    JSON-only input cannot be sent by a plain cross-site HTML form, one more layer on top of
    the cross-site check in security.py.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        abort(415)
    return body


def require_edit_access(plan: Plan) -> None:
    if not security.token_matches(request.headers.get(security.EDIT_HEADER), plan.edit_token_hash):
        abort(403)


def progress(data: dict) -> tuple[int, int]:
    """(completed, total) across timeline tasks and vendor checks."""
    items = data["timeline"] + data["vendors"]
    return sum(1 for item in items if item["done"]), len(items)


@bp.post("/plans")
@limiter.limit("20 per minute")
def create_plan():
    clean, errors = planner.clean_form(json_body())
    if errors:
        return jsonify(error="Please fix the highlighted fields.", errors=errors), 400
    data = generate_plan(clean)
    token, token_hash = security.new_edit_token()
    plan = Plan(edit_token_hash=token_hash, event_type=clean["event_type"], title=clean["title"],
                event_date=clean["event_date"], guests=clean["guests"], budget=clean["budget"],
                city=clean["city"], theme=clean["theme"], preferences=clean["preferences"])
    plan.data = data
    db.session.add(plan)
    db.session.commit()
    log.info("plan created id=%s type=%s source=%s", plan.id, plan.event_type, data["source"])
    return jsonify(id=plan.id, edit_token=token), 201


@bp.get("/plans/<plan_id>")
def get_plan(plan_id: str):
    plan = get_plan_or_404(plan_id)
    done, total = progress(plan.data)
    can_edit = security.token_matches(request.headers.get(security.EDIT_HEADER), plan.edit_token_hash)
    return jsonify(id=plan.id, title=plan.title, event_type=plan.event_type,
                   event_label=planner.EVENTS[plan.event_type]["label"],
                   event_date=plan.event_date.isoformat(), guests=plan.guests, budget=plan.budget,
                   city=plan.city, theme=plan.theme, completed=done, total=total,
                   can_edit=can_edit, plan=plan.data)


@bp.post("/plans/<plan_id>/toggle")
@limiter.limit("120 per minute")
def toggle(plan_id: str):
    plan = get_plan_or_404(plan_id)
    require_edit_access(plan)
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


@bp.post("/plans/<plan_id>/ask")
@limiter.limit("20 per minute")
def ask(plan_id: str):
    plan = get_plan_or_404(plan_id)
    question = str(json_body().get("question") or "").strip()[:300]
    if len(question) < 3:
        return jsonify(error="Please type a question."), 400
    return jsonify(answer(question, plan.event_type, plan.data["summary"]))


def _ics_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


@bp.get("/plans/<plan_id>/calendar.ics")
def calendar(plan_id: str):
    plan = get_plan_or_404(plan_id)
    stamp = f"{date.today():%Y%m%d}T000000Z"
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//UtsavAI//EN"]
    for item in plan.data["timeline"]:
        lines += ["BEGIN:VEVENT", f"UID:{plan.id}-{item['id']}@utsavai", f"DTSTAMP:{stamp}",
                  f"DTSTART;VALUE=DATE:{item['due'].replace('-', '')}",
                  f"SUMMARY:{_ics_escape(plan.title + ': ' + item['task'])}", "END:VEVENT"]
    lines.append("END:VCALENDAR")
    return Response("\r\n".join(lines) + "\r\n", mimetype="text/calendar",
                    headers={"Content-Disposition": "attachment; filename=event-plan.ics"})


@bp.get("/health")
@limiter.exempt
@security.exempt_from_https_redirect
def health():
    return jsonify(status="ok")
