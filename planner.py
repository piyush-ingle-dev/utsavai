"""Rule-based planning engine.

Everything that involves numbers or dates lives here, so the plan is always
correct and always available, even if the AI service is slow or down.
"""
from datetime import date, timedelta

MAX_GUESTS = 5000
MIN_BUDGET = 1000
MAX_BUDGET = 1_000_000_000

EVENTS = {
    "wedding": {
        "label": "Wedding",
        "min_per_head": 800,
        "splits": {
            "Venue": 0.25, "Catering": 0.30, "Decor & Flowers": 0.10,
            "Photo & Video": 0.08, "Attire & Beauty": 0.08,
            "Music & Entertainment": 0.05, "Invitations & Gifts": 0.03,
            "Travel & Stay": 0.03, "Contingency": 0.08,
        },
        "timeline": [
            (270, "Fix the budget, a guest list range and two preferred dates", "Planning"),
            (240, "Visit and book the venue", "Venue"),
            (210, "Book photographer and videographer", "Photo & Video"),
            (180, "Taste menus and finalise the caterer", "Catering"),
            (150, "Order outfits and book the makeup artist", "Attire & Beauty"),
            (120, "Lock the theme and book decorator and florist", "Decor & Flowers"),
            (90, "Send save-the-dates and plan guest travel and stay", "Travel & Stay"),
            (75, "Book DJ or band and plan sangeet performances", "Music & Entertainment"),
            (60, "Print and send invitations", "Invitations & Gifts"),
            (30, "Chase RSVPs and confirm the final headcount with the caterer", "Catering"),
            (14, "Final outfit fittings and written confirmation from every vendor", "Planning"),
            (7, "Share the day-of schedule with family and vendors", "Planning"),
            (2, "Settle advances and pack an emergency kit", "Contingency"),
            (0, "Event day: name one person to answer all vendor questions", "Planning"),
        ],
        "vendors": [
            ("Venue", "Capacity, power backup, parking, overtime charges, rain plan", "Venue"),
            ("Caterer", "Tasting, per-plate rate, taxes, extra-plate policy, live counters", "Catering"),
            ("Decorator and florist", "Mood board, setup time, teardown, what is rented vs owned", "Decor & Flowers"),
            ("Photographer and videographer", "Team size, delivery time, raw files, backup storage", "Photo & Video"),
            ("Makeup artist", "Trial date, travel charges, touch-up on the day", "Attire & Beauty"),
            ("DJ or band", "Sound check time, playlist control, power needs", "Music & Entertainment"),
            ("Priest or officiant", "Muhurat timing, ritual items list, duration", "Planning"),
            ("Guest transport", "Pickup schedule, vehicle count, driver contacts", "Travel & Stay"),
            ("Invitation printer", "Proof approval, delivery date, digital version", "Invitations & Gifts"),
        ],
        "ideas": [
            ("Pre-wedding family dinner", "A small, low-cost evening to let both families relax before the big days."),
            ("Welcome kits for outstation guests", "Water, snacks, the schedule and a local map in one bag at check-in."),
            ("Memory wall", "Printed photos of the couple through the years, which also fills dead time at the entrance."),
        ],
    },
    "birthday": {
        "label": "Birthday",
        "min_per_head": 300,
        "splits": {
            "Venue": 0.20, "Food & Cake": 0.35, "Decor & Balloons": 0.12,
            "Entertainment": 0.12, "Return Gifts": 0.08, "Photography": 0.05,
            "Invitations": 0.02, "Contingency": 0.06,
        },
        "timeline": [
            (45, "Set the date, guest list and budget", "Planning"),
            (35, "Book the venue", "Venue"),
            (28, "Pick a theme and order the cake and decor", "Decor & Balloons"),
            (21, "Send invitations", "Invitations"),
            (14, "Book the entertainer or plan party games", "Entertainment"),
            (10, "Finalise the food menu", "Food & Cake"),
            (7, "Confirm RSVPs and order return gifts", "Return Gifts"),
            (2, "Confirm vendors and buy last-minute supplies", "Contingency"),
            (0, "Party day: set up two hours early and assign a photo buddy", "Photography"),
        ],
        "vendors": [
            ("Venue or hall", "Booking hours, decoration rules, food from outside allowed or not", "Venue"),
            ("Cake baker", "Flavour, eggless options, delivery time, candles and knife", "Food & Cake"),
            ("Caterer", "Per-plate rate, kids menu, serving staff, disposables", "Food & Cake"),
            ("Decorator", "Theme props, balloon arch, setup and cleanup time", "Decor & Balloons"),
            ("Entertainer or game host", "Age fit, duration, own equipment", "Entertainment"),
            ("Photographer", "Hours covered, edited photos delivery date", "Photography"),
        ],
        "ideas": [
            ("Photo booth corner", "A plain backdrop plus a few props gives guests something to do and you great pictures."),
            ("Return gifts with a purpose", "Seed packets, notebooks or small books instead of plastic toys."),
            ("Timed schedule", "Keep it to arrival, games, food, cake. Short parties feel more lively."),
        ],
    },
    "community": {
        "label": "Community event",
        "min_per_head": 100,
        "splits": {
            "Venue & Permissions": 0.15, "Food & Prasad": 0.30, "Decor & Pandal": 0.18,
            "Sound & Lighting": 0.12, "Programs & Performers": 0.10,
            "Printing & Promotion": 0.05, "Volunteer Needs": 0.04, "Contingency": 0.06,
        },
        "timeline": [
            (60, "Form a committee and assign one owner per area", "Planning"),
            (50, "Apply for permissions (local body, police, society NOC)", "Venue & Permissions"),
            (45, "Fix the budget and start collecting contributions", "Planning"),
            (35, "Book the venue or pandal, sound and lighting", "Sound & Lighting"),
            (28, "Finalise the programme and performers", "Programs & Performers"),
            (21, "Print posters and promote on WhatsApp groups", "Printing & Promotion"),
            (14, "Confirm food vendor and publish the volunteer roster", "Food & Prasad"),
            (7, "Safety plan: fire extinguisher, first aid, crowd flow, exits", "Volunteer Needs"),
            (2, "Rehearsal and equipment check", "Sound & Lighting"),
            (0, "Event day: briefing with all volunteers one hour before the doors open", "Volunteer Needs"),
        ],
        "vendors": [
            ("Venue or pandal contractor", "Fire safety, load limits, power connection, cleanup", "Venue & Permissions"),
            ("Food and prasad vendor", "Quantity per head, hygiene, serving counters, waste plan", "Food & Prasad"),
            ("Decorator", "Theme, eco-friendly material, setup and removal time", "Decor & Pandal"),
            ("Sound and lighting", "Backup mic, generator, volume limits set by local rules", "Sound & Lighting"),
            ("Performers or speakers", "Slot timing, travel, any fee, green room", "Programs & Performers"),
            ("Printer", "Poster size, proof, delivery before promotion starts", "Printing & Promotion"),
        ],
        "ideas": [
            ("Eco-friendly setup", "Cloth banners, natural colours and steel plates cut waste and cost."),
            ("Volunteer shifts", "Two-hour shifts with a named lead keep people fresh and accountable."),
            ("Feedback QR code", "A simple form at the exit gives next year's committee real data."),
        ],
    },
}


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
                         "detail": "Pick two signature colours and one hero element, then let every vendor see the same mood board."})
    if clean.get("city"):
        ideas.append({"title": f"Use local flavour from {clean['city']}",
                      "detail": "A regional dish, a local artist or a nearby heritage spot makes the event feel specific, not generic."})
    return ideas


def build_warnings(clean: dict, rushed: int) -> list[str]:
    warnings = []
    ev = EVENTS[clean["event_type"]]
    per_head = clean["budget"] / clean["guests"]
    if per_head < ev["min_per_head"]:
        warnings.append(
            f"Your budget works out to about Rs {per_head:,.0f} per guest. For a {ev['label'].lower()} "
            f"that is tight (a comfortable floor is around Rs {ev['min_per_head']:,}). Consider fewer guests or a simpler menu.")
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
