"""Rule-based planning engine.

Everything that involves numbers or dates lives here, so the plan is always
correct and always available, even if the AI service is slow or down.
"""
from collections.abc import Callable, Mapping
from datetime import date, timedelta
from typing import Any

from catalog import EVENTS
from schemas import BudgetLine, CleanForm, Idea, PlanData, TimelineItem, VendorItem

MAX_GUESTS = 5000
MIN_BUDGET = 1000
MAX_BUDGET = 1_000_000_000
MAX_DAYS_AHEAD = 3 * 365
TITLE_MAX = 120
SHORT_TEXT_MAX = 80
PREFERENCES_MAX = 500


class ValidationFailure(ValueError):
    """A problem with one user input. The message is shown next to that field."""


# ---- input validation -------------------------------------------------------

def _text(value: object) -> str:
    return str(value).strip() if value is not None else ""


def _parse_event_type(raw: object) -> str:
    event_type = _text(raw).lower()
    if event_type not in EVENTS:
        raise ValidationFailure("Choose a wedding, birthday or community event.")
    return event_type


def _parse_date(raw: object) -> date:
    try:
        chosen = date.fromisoformat(_text(raw))
    except ValueError:
        raise ValidationFailure("Enter a valid date.") from None
    today = date.today()
    if chosen < today:
        raise ValidationFailure("The date should be today or later.")
    if chosen > today + timedelta(days=MAX_DAYS_AHEAD):
        raise ValidationFailure("Pick a date within the next three years.")
    return chosen


def _parse_int(raw: object, label: str, low: int, high: int) -> int:
    """Accept 150, "150", "5,00,000" or 150.0 but not True, 1.5 or text."""
    message = f"{label} must be a whole number between {low:,} and {high:,}."
    if isinstance(raw, bool):
        raise ValidationFailure(message)
    try:
        value = int(raw) if isinstance(raw, float) and raw.is_integer() else int(_text(raw).replace(",", ""))
    except ValueError:
        raise ValidationFailure(message) from None
    if not low <= value <= high:
        raise ValidationFailure(message)
    return value


def clean_form(form: Mapping[str, Any]) -> tuple[CleanForm | None, dict[str, str]]:
    """Validate raw input (JSON or form data).

    Returns (clean_values, {}) on success, or (None, {field: message}) when any field is invalid.
    """
    errors: dict[str, str] = {}

    def read[T](name: str, parse: Callable[[object], T]) -> T | None:
        try:
            return parse(form.get(name))
        except ValidationFailure as failure:
            errors[name] = str(failure)
            return None

    event_type = read("event_type", _parse_event_type)
    event_date = read("event_date", _parse_date)
    guests = read("guests", lambda raw: _parse_int(raw, "Guests", 1, MAX_GUESTS))
    budget = read("budget", lambda raw: _parse_int(raw, "Budget", MIN_BUDGET, MAX_BUDGET))
    if event_type is None or event_date is None or guests is None or budget is None:
        return None, errors

    return CleanForm(
        event_type=event_type,
        title=_text(form.get("title"))[:TITLE_MAX] or EVENTS[event_type]["label"],
        event_date=event_date,
        guests=guests,
        budget=budget,
        city=_text(form.get("city"))[:SHORT_TEXT_MAX],
        theme=_text(form.get("theme"))[:SHORT_TEXT_MAX],
        preferences=_text(form.get("preferences"))[:PREFERENCES_MAX],
    ), {}


# ---- plan building ----------------------------------------------------------

def allocate_budget(event_type: str, budget: int) -> list[BudgetLine]:
    """Split the budget by category. The rounding gap goes to the last category (Contingency) so totals match."""
    splits = EVENTS[event_type]["splits"]
    rows = [BudgetLine(category=c, pct=round(p * 100), amount=int(budget * p)) for c, p in splits.items()]
    rows[-1]["amount"] += budget - sum(row["amount"] for row in rows)
    return rows


def build_timeline(event_type: str, event_date: date, today: date | None = None) -> tuple[list[TimelineItem], int]:
    """Return dated tasks and how many were squeezed into 'today' because the event is close."""
    today = today or date.today()
    items: list[TimelineItem] = []
    rushed = 0
    for index, (days_before, task, category) in enumerate(EVENTS[event_type]["timeline"]):
        due = event_date - timedelta(days=days_before)
        late = due < today
        if late:
            due, rushed = today, rushed + 1
        items.append(TimelineItem(id=f"t{index}", task=task, category=category,
                                  due=due.isoformat(), late=late, done=False))
    items.sort(key=lambda item: (item["due"], item["id"]))
    return items, rushed


def build_vendors(event_type: str) -> list[VendorItem]:
    return [VendorItem(id=f"v{index}", vendor=vendor, ask=ask, category=category, done=False)
            for index, (vendor, ask, category) in enumerate(EVENTS[event_type]["vendors"])]


def build_ideas(clean: CleanForm) -> list[Idea]:
    """Starter ideas for the event type, personalised with the theme and city when given."""
    ideas = [Idea(title=title, detail=detail) for title, detail in EVENTS[clean["event_type"]]["ideas"]]
    if clean["theme"]:
        ideas.insert(0, Idea(
            title=f"Build around the '{clean['theme']}' theme",
            detail="Pick two signature colours and one hero element, "
                   "then let every vendor see the same mood board."))
    if clean["city"]:
        ideas.append(Idea(
            title=f"Use local flavour from {clean['city']}",
            detail="A regional dish, a local artist or a nearby heritage spot "
                   "makes the event feel specific, not generic."))
    return ideas


def build_warnings(clean: CleanForm, rushed: int) -> list[str]:
    warnings = []
    spec = EVENTS[clean["event_type"]]
    per_head = clean["budget"] / clean["guests"]
    if per_head < spec["min_per_head"]:
        warnings.append(
            f"Your budget works out to about Rs {per_head:,.0f} per guest. For a {spec['label'].lower()} "
            f"that is tight (a comfortable floor is around Rs {spec['min_per_head']:,}). "
            "Consider fewer guests or a simpler menu.")
    if rushed:
        days_left = (clean["event_date"] - date.today()).days
        warnings.append(
            f"Your date is {days_left} day{'s' if days_left != 1 else ''} away, so {rushed} early "
            "task(s) are compressed into the first days. Book the venue and caterer first.")
    return warnings


def build_summary(clean: CleanForm) -> str:
    label = EVENTS[clean["event_type"]]["label"].lower()
    days_left = (clean["event_date"] - date.today()).days
    per_head = clean["budget"] / clean["guests"]
    return (f"A {label} for {clean['guests']:,} guests on {clean['event_date']:%d %b %Y} "
            f"({days_left} days to go) with a budget of Rs {clean['budget']:,}, about Rs {per_head:,.0f} per guest.")


def build_plan(clean: CleanForm) -> PlanData:
    """The rule-based plan. The agents later replace the narrative parts (summary, ideas, tips, risks)."""
    timeline, rushed = build_timeline(clean["event_type"], clean["event_date"])
    return PlanData(
        source="rules",
        summary=build_summary(clean),
        budget=allocate_budget(clean["event_type"], clean["budget"]),
        timeline=timeline,
        vendors=build_vendors(clean["event_type"]),
        ideas=build_ideas(clean),
        vendor_tips=[],
        risks=[],
        warnings=build_warnings(clean, rushed),
    )
