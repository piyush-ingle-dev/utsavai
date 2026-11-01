"""Static catalogue of event types: budget shares, timeline milestones, vendors and starter ideas.

Keeping this data apart from the planning logic (planner.py) means a new event type is a data change,
not a code change. Each timeline entry is (days_before_event, task, budget_category).
"""
from typing import TypedDict


class EventSpec(TypedDict):
    label: str
    min_per_head: int  # comfortable minimum spend per guest, in rupees
    splits: dict[str, float]  # budget category -> share; shares sum to 1.0
    timeline: list[tuple[int, str, str]]
    vendors: list[tuple[str, str, str]]  # (vendor, what to ask, budget category)
    ideas: list[tuple[str, str]]  # (title, detail)


EVENTS: dict[str, EventSpec] = {
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
