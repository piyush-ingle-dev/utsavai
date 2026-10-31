from datetime import date, timedelta

import pytest

import planner
from app import create_app


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    return app.test_client()


def body(**over):
    base = {"event_type": "wedding", "title": "Test", "event_date": (date.today() + timedelta(days=90)).isoformat(),
            "guests": 150, "budget": 500000, "city": "Nagpur", "theme": "Royal", "preferences": "Pure veg"}
    base.update(over)
    return base


def make_plan(client, **over):
    r = client.post("/api/plans", json=body(**over))
    assert r.status_code == 201, r.json
    return r.json["id"]


def test_health(client):
    assert client.get("/healthz").json == {"status": "ok"}
    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("kind", ["wedding", "birthday", "community"])
def test_create_each_type(client, kind):
    pid = make_plan(client, event_type=kind)
    data = client.get(f"/api/plans/{pid}").json
    assert data["event_type"] == kind
    assert sum(r["amount"] for r in data["plan"]["budget"]) == 500000
    assert len(data["plan"]["ideas"]) >= 3
    assert [s["agent"] for s in data["plan"]["trace"]][:2] == ["Researcher", "Planner"]


@pytest.mark.parametrize("budget", [1000, 99999, 1234567, 777777])
@pytest.mark.parametrize("kind", list(planner.EVENTS))
def test_budget_adds_up(kind, budget):
    assert sum(r["amount"] for r in planner.allocate_budget(kind, budget)) == budget
    assert round(sum(planner.EVENTS[kind]["splits"].values()), 6) == 1.0


def test_validation_errors(client):
    for bad in (body(guests=0), body(budget="abc"), body(event_date="2001-01-01"), body(event_type="rocket"),
                body(event_date="nope"), body(guests=99999), body(budget=True), body(guests=None)):
        r = client.post("/api/plans", json=bad)
        assert r.status_code == 400 and r.json["errors"]


def test_accepts_strings_and_commas(client):
    assert client.post("/api/plans", json=body(budget="5,00,000", guests="150")).status_code == 201


def test_requires_json(client):
    assert client.post("/api/plans", data="x=1").status_code == 415
    assert client.post("/api/plans", json=["a"]).status_code == 415


def test_near_date_compresses_timeline():
    items, rushed = planner.build_timeline("wedding", date.today() + timedelta(days=5))
    assert rushed > 0 and all(i["due"] >= date.today().isoformat() for i in items)


def test_low_budget_warning():
    clean, errors = planner.clean_form(body(budget=2000, guests=500))
    assert not errors and planner.build_warnings(clean, 0)


def test_toggle_and_progress(client):
    pid = make_plan(client)
    r = client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"})
    assert r.json["done"] is True and r.json["completed"] == 1
    assert client.get(f"/api/plans/{pid}").json["completed"] == 1
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}).json["done"] is False
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "zzz"}).status_code == 404


def test_ask_planner(client):
    pid = make_plan(client, event_type="community")
    r = client.post(f"/api/plans/{pid}/ask", json={"question": "What permissions do we need for loudspeakers?"})
    assert r.status_code == 200 and r.json["sources"] and r.json["answer"]
    assert client.post(f"/api/plans/{pid}/ask", json={"question": "a"}).status_code == 400


def test_calendar(client):
    pid = make_plan(client)
    ics = client.get(f"/api/plans/{pid}/calendar.ics")
    assert ics.mimetype == "text/calendar" and b"BEGIN:VEVENT" in ics.data


def test_bad_ids_404(client):
    for path in ("/api/plans/xyz", "/api/plans/" + "a" * 32, "/api/plans/..%2f..%2fetc"):
        assert client.get(path).status_code == 404


def test_security_headers(client):
    r = client.get("/healthz")
    assert "script-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"


def test_stored_text_is_returned_as_data_not_markup(client):
    pid = make_plan(client, title="<script>alert(1)</script>")
    assert client.get(f"/api/plans/{pid}").mimetype == "application/json"
