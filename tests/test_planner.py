"""Unit and property-based tests for the rule engine."""
from datetime import date, timedelta

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

import planner
from catalog import EVENTS
from planner import ValidationFailure

EVENT_KEYS = st.sampled_from(sorted(EVENTS))


# ---- properties: these must hold for ANY valid input ---------------------------

@given(kind=EVENT_KEYS, budget=st.integers(planner.MIN_BUDGET, planner.MAX_BUDGET))
def test_budget_always_sums_exactly_and_is_never_negative(kind, budget):
    rows = planner.allocate_budget(kind, budget)
    assert sum(r["amount"] for r in rows) == budget
    assert all(r["amount"] >= 0 for r in rows)
    assert [r["category"] for r in rows] == list(EVENTS[kind]["splits"])


@given(kind=EVENT_KEYS, days_ahead=st.integers(0, planner.MAX_DAYS_AHEAD))
def test_timeline_is_sorted_complete_and_never_in_the_past(kind, days_ahead):
    today = date.today()
    items, rushed = planner.build_timeline(kind, today + timedelta(days=days_ahead), today)
    assert len(items) == len(EVENTS[kind]["timeline"])
    assert [i["due"] for i in items] == sorted(i["due"] for i in items)
    assert all(i["due"] >= today.isoformat() for i in items)
    assert rushed == sum(1 for i in items if i["late"])
    assert len({i["id"] for i in items}) == len(items)


@given(guests=st.integers(1, planner.MAX_GUESTS), budget=st.integers(planner.MIN_BUDGET, 10**7), kind=EVENT_KEYS)
@settings(max_examples=60)
def test_full_plan_is_consistent_for_any_valid_form(guests, budget, kind):
    clean, errors = planner.clean_form({"event_type": kind, "event_date": (date.today() + timedelta(days=40)).isoformat(),
                                        "guests": guests, "budget": budget})
    assert errors == {} and clean is not None
    plan = planner.build_plan(clean)
    assert sum(r["amount"] for r in plan["budget"]) == budget
    assert plan["summary"] and plan["timeline"] and plan["vendors"]
    assert all(not item["done"] for item in plan["timeline"] + plan["vendors"])


@given(text=st.text(max_size=300))
def test_free_text_fields_are_always_trimmed_to_their_limits(text):
    clean, _ = planner.clean_form({"event_type": "birthday", "event_date": date.today().isoformat(), "guests": 10,
                                   "budget": 5000, "title": text, "city": text, "theme": text, "preferences": text})
    assert clean is not None
    assert len(clean["title"]) <= planner.TITLE_MAX and len(clean["city"]) <= planner.SHORT_TEXT_MAX
    assert len(clean["preferences"]) <= planner.PREFERENCES_MAX


# ---- validators ----------------------------------------------------------------

@pytest.mark.parametrize("raw", ["wedding", " Wedding ", "BIRTHDAY", "community"])
def test_event_type_accepts_known_values_case_insensitively(raw):
    assert planner._parse_event_type(raw) in EVENTS


@pytest.mark.parametrize("raw", ["", None, "rocket", 5, ["wedding"]])
def test_event_type_rejects_unknown_values(raw):
    with pytest.raises(ValidationFailure):
        planner._parse_event_type(raw)


@pytest.mark.parametrize(("raw", "expected"), [(150, 150), ("150", 150), ("5,00,000", 500000), (150.0, 150), (" 7 ", 7)])
def test_int_parser_accepts_common_formats(raw, expected):
    assert planner._parse_int(raw, "Guests", 1, 10**7) == expected


@pytest.mark.parametrize("raw", [True, False, None, "", "abc", 1.5, "1e3", 0, -5, 10**9])
def test_int_parser_rejects_bad_values(raw):
    with pytest.raises(ValidationFailure):
        planner._parse_int(raw, "Guests", 1, 5000)


def test_date_parser_boundaries():
    today = date.today()
    assert planner._parse_date(today.isoformat()) == today
    assert planner._parse_date((today + timedelta(days=planner.MAX_DAYS_AHEAD)).isoformat())
    for bad in ((today - timedelta(days=1)).isoformat(), (today + timedelta(days=planner.MAX_DAYS_AHEAD + 1)).isoformat(),
                "31/12/2026", "", None):
        with pytest.raises(ValidationFailure):
            planner._parse_date(bad)


def test_clean_form_reports_every_bad_field_at_once():
    clean, errors = planner.clean_form({"event_type": "x", "event_date": "no", "guests": 0, "budget": "a"})
    assert clean is None and set(errors) == {"event_type", "event_date", "guests", "budget"}


def test_default_title_is_the_event_label():
    clean, _ = planner.clean_form({"event_type": "wedding", "event_date": date.today().isoformat(),
                                   "guests": 10, "budget": 5000})
    assert clean is not None and clean["title"] == "Wedding"


# ---- personalisation and warnings ----------------------------------------------

def _clean(**over):
    base = {"event_type": "birthday", "event_date": date.today() + timedelta(days=30), "guests": 50, "budget": 50000,
            "title": "T", "city": "", "theme": "", "preferences": "", **over}
    return base


def test_ideas_use_theme_and_city_when_given():
    titles = [i["title"] for i in planner.build_ideas(_clean(theme="Retro", city="Nagpur"))]
    assert titles[0] == "Build around the 'Retro' theme" and titles[-1] == "Use local flavour from Nagpur"
    assert len(planner.build_ideas(_clean())) == len(EVENTS["birthday"]["ideas"])


def test_warnings_for_tight_budget_and_close_date():
    warnings = planner.build_warnings(_clean(budget=1000, guests=500), rushed=3)
    assert any("per guest" in w for w in warnings) and any("compressed" in w for w in warnings)
    assert planner.build_warnings(_clean(), rushed=0) == []
    assert "1 day away" in planner.build_warnings(_clean(event_date=date.today() + timedelta(days=1)), rushed=1)[0]
