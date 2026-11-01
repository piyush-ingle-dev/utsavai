"""Rule-based planning engine.

Everything that involves numbers or dates lives here, so the plan is always
correct and always available, even if the AI service is slow or down.
"""
from datetime import date, timedelta

from catalog import EVENTS

MAX_GUESTS = 5000
MIN_BUDGET = 1000
MAX_BUDGET = 1_000_000_000

def _text(value) -> str:
    return str(value).strip() if value is not None else ""


def _to_int(value) -> int:
    if isinstance(value, bool):
        raise ValueError
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return int(_text(value).replace(",", ""))


def clean_form(form) -> tuple[dict, dict]:
    """Validate raw input (form data or JSON). Returns (clean_values, errors)."""
    errors: dict[str, str] = {}
    clean: dict = {}

    event_type = _text(form.get("event_type")).lower()
    if event_type not in EVENTS:
        errors["event_type"] = "Choose a wedding, birthday or community event."
    clean["event_type"] = event_type

    title = _text(form.get("title"))[:120]
    clean["title"] = title or (EVENTS[event_type]["label"] if event_type in EVENTS else "My event")

    try:
        d = date.fromisoformat(_text(form.get("event_date")))
        if d < date.today():
            errors["event_date"] = "The date should be today or later."
        elif d > date.today() + timedelta(days=3 * 365):
            errors["event_date"] = "Pick a date within the next three years."
        clean["event_date"] = d
    except ValueError:
        errors["event_date"] = "Enter a valid date."
        clean["event_date"] = None

    for key, lo, hi, label in (
        ("guests", 1, MAX_GUESTS, "Guests"),
        ("budget", MIN_BUDGET, MAX_BUDGET, "Budget"),
    ):
        try:
            val = _to_int(form.get(key))
            if not lo <= val <= hi:
                raise ValueError
            clean[key] = val
        except ValueError:
            errors[key] = f"{label} must be a whole number between {lo:,} and {hi:,}."
            clean[key] = None

    clean["city"] = _text(form.get("city"))[:80]
    clean["theme"] = _text(form.get("theme"))[:80]
    clean["preferences"] = _text(form.get("preferences"))[:500]
    return clean, errors


def allocate_budget(event_type: str, budget: int) -> list[dict]:
    """Split the budget by category. The rounding gap goes to Contingency so totals match exactly."""
    splits = EVENTS[event_type]["splits"]
    rows = [{"category": c, "pct": round(p * 100), "amount": int(budget * p)} for c, p in splits.items()]
    gap = budget - sum(r["amount"] for r in rows)
    rows[-1]["amount"] += gap
    return rows


def build_timeline(event_type: str, event_date: date, today: date | None = None) -> tuple[list[dict], int]:
    """Return timeline items and how many were squeezed into 'now' because the date is close."""
    today = today or date.today()
    items, rushed = [], 0
    for i, (days, task, category) in enumerate(EVENTS[event_type]["timeline"]):
        due = event_date - timedelta(days=days)
        late = due < today
        if late:
            due, rushed = today, rushed + 1
        items.append({"id": f"t{i}", "task": task, "category": category,
                      "due": due.isoformat(), "late": late, "done": False})
    items.sort(key=lambda x: (x["due"], x["id"]))
    return items, rushed


def build_vendors(event_type: str) -> list[dict]:
    return [{"id": f"v{i}", "vendor": v, "ask": ask, "category": cat, "done": False}
            for i, (v, ask, cat) in enumerate(EVENTS[event_type]["vendors"])]


def build_ideas(clean: dict) -> list[dict]:
    ideas = [{"title": t, "detail": d} for t, d in EVENTS[clean["event_type"]]["ideas"]]
    if clean.get("theme"):
        ideas.insert(0, {"title": f"Build around the '{clean['theme']}' theme",
                         "detail": "Pick two signature colours and one hero element, "
                                "then let every vendor see the same mood board."})
    if clean.get("city"):
        ideas.append({"title": f"Use local flavour from {clean['city']}",
                      "detail": "A regional dish, a local artist or a nearby heritage spot "
                                "makes the event feel specific, not generic."})
    return ideas


def build_warnings(clean: dict, rushed: int) -> list[str]:
    warnings = []
    ev = EVENTS[clean["event_type"]]
    per_head = clean["budget"] / clean["guests"]
    if per_head < ev["min_per_head"]:
        warnings.append(
            f"Your budget works out to about Rs {per_head:,.0f} per guest. For a {ev['label'].lower()} "
            f"that is tight (a comfortable floor is around Rs {ev['min_per_head']:,}). "
            "Consider fewer guests or a simpler menu.")
    days_left = (clean["event_date"] - date.today()).days
    if rushed:
        warnings.append(
            f"Your date is {days_left} day{'s' if days_left != 1 else ''} away, so {rushed} early "
            "task(s) are compressed into the first days. Book the venue and caterer first.")
    return warnings


def build_summary(clean: dict) -> str:
    ev = EVENTS[clean["event_type"]]
    days_left = (clean["event_date"] - date.today()).days
    return (f"A {ev['label'].lower()} for {clean['guests']:,} guests on {clean['event_date']:%d %b %Y} "
            f"({days_left} days to go) with a budget of Rs {clean['budget']:,}, about Rs "
            f"{clean['budget'] / clean['guests']:,.0f} per guest.")


def build_plan(clean: dict) -> dict:
    timeline, rushed = build_timeline(clean["event_type"], clean["event_date"])
    return {
        "source": "rules",
        "summary": build_summary(clean),
        "budget": allocate_budget(clean["event_type"], clean["budget"]),
        "timeline": timeline,
        "vendors": build_vendors(clean["event_type"]),
        "ideas": build_ideas(clean),
        "vendor_tips": [],
        "risks": [],
        "warnings": build_warnings(clean, rushed),
    }
