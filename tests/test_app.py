from datetime import date, timedelta

import pytest

import planner
import security
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
    """Create a plan and return (plan_id, edit_token)."""
    r = client.post("/api/plans", json=body(**over))
    assert r.status_code == 201, r.json
    return r.json["id"], r.json["edit_token"]


def edit(token):
    return {security.EDIT_HEADER: token}


def test_health(client):
    assert client.get("/healthz").json == {"status": "ok"}
    assert client.get("/api/health").status_code == 200


@pytest.mark.parametrize("kind", ["wedding", "birthday", "community"])
def test_create_each_type(client, kind):
    pid, _ = make_plan(client, event_type=kind)
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


def test_oversized_body_rejected(client):
    assert client.post("/api/plans", json=body(preferences="x" * 40000)).status_code == 413


def test_near_date_compresses_timeline():
    items, rushed = planner.build_timeline("wedding", date.today() + timedelta(days=5))
    assert rushed > 0 and all(i["due"] >= date.today().isoformat() for i in items)


def test_low_budget_warning():
    clean, errors = planner.clean_form(body(budget=2000, guests=500))
    assert not errors and planner.build_warnings(clean, 0)


# ---- edit access ------------------------------------------------------------

def test_toggle_requires_edit_token(client):
    pid, token = make_plan(client)
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}).status_code == 403
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}, headers=edit("wrong")).status_code == 403
    r = client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}, headers=edit(token))
    assert r.json["done"] is True and r.json["completed"] == 1


def test_toggle_and_progress(client):
    pid, token = make_plan(client)
    h = edit(token)
    client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}, headers=h)
    assert client.get(f"/api/plans/{pid}").json["completed"] == 1
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}, headers=h).json["done"] is False
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "zzz"}, headers=h).status_code == 404


def test_can_edit_flag_and_token_not_leaked(client):
    pid, token = make_plan(client)
    assert client.get(f"/api/plans/{pid}").json["can_edit"] is False
    assert client.get(f"/api/plans/{pid}", headers=edit("nope")).json["can_edit"] is False
    page = client.get(f"/api/plans/{pid}", headers=edit(token))
    assert page.json["can_edit"] is True
    assert token not in page.get_data(as_text=True)


def test_token_helpers():
    token, digest = security.new_edit_token()
    assert security.token_matches(token, digest)
    assert not security.token_matches("other", digest)
    assert not security.token_matches("", digest) and not security.token_matches(None, digest)
    assert token != digest and len(digest) == 64


# ---- cross-site protection and headers ---------------------------------------

@pytest.mark.parametrize("site", ["cross-site", "same-site"])
def test_cross_site_writes_blocked(client, site):
    r = client.post("/api/plans", json=body(), headers={"Sec-Fetch-Site": site})
    assert r.status_code == 403


@pytest.mark.parametrize("site", ["same-origin", "none"])
def test_same_origin_writes_allowed(client, site):
    assert client.post("/api/plans", json=body(), headers={"Sec-Fetch-Site": site}).status_code == 201


def test_origin_header_fallback(client):
    assert client.post("/api/plans", json=body(), headers={"Origin": "https://evil.example"}).status_code == 403
    assert client.post("/api/plans", json=body(), headers={"Origin": "http://localhost"}).status_code == 201


def test_reads_are_not_blocked_cross_site(client):
    assert client.get("/healthz", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 200


def test_security_headers_and_no_store(client):
    r = client.get("/api/health")
    assert "script-src 'self'" in r.headers["Content-Security-Policy"]
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-store"


@pytest.fixture()
def prod_client(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    app = create_app({"PRODUCTION": True, "TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"})
    return app.test_client()


def test_production_forces_https_but_not_for_health(prod_client):
    assert prod_client.get("/").status_code == 302
    assert prod_client.get("/healthz").status_code == 200
    assert prod_client.get("/api/health").status_code == 200


def test_production_sets_hsts_over_https(prod_client):
    r = prod_client.get("/healthz", headers={"X-Forwarded-Proto": "https"})
    assert "max-age" in r.headers["Strict-Transport-Security"]


def test_ask_planner(client):
    pid, _ = make_plan(client, event_type="community")
    r = client.post(f"/api/plans/{pid}/ask", json={"question": "What permissions do we need for loudspeakers?"})
    assert r.status_code == 200 and r.json["sources"] and r.json["answer"]
    assert client.post(f"/api/plans/{pid}/ask", json={"question": "a"}).status_code == 400


def test_calendar(client):
    pid, _ = make_plan(client)
    ics = client.get(f"/api/plans/{pid}/calendar.ics")
    assert ics.mimetype == "text/calendar" and b"BEGIN:VEVENT" in ics.data


def test_bad_ids_404(client):
    for path in ("/api/plans/xyz", "/api/plans/" + "a" * 32, "/api/plans/..%2f..%2fetc"):
        assert client.get(path).status_code == 404


def test_stored_text_is_returned_as_data_not_markup(client):
    pid, _ = make_plan(client, title="<script>alert(1)</script>")
    assert client.get(f"/api/plans/{pid}").mimetype == "application/json"


def test_errors_are_json(client):
    r = client.get("/nope")
    assert r.status_code == 404 and r.json == {"error": "Not found."}


def test_old_database_is_upgraded(tmp_path, monkeypatch):
    import sqlite3

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    path = tmp_path / "old.db"
    con = sqlite3.connect(path)
    con.execute("CREATE TABLE plans (id VARCHAR(32) PRIMARY KEY, event_type VARCHAR(20), title VARCHAR(120), "
                "event_date DATE, guests INTEGER, budget INTEGER, city VARCHAR(80), theme VARCHAR(80), "
                "preferences TEXT, data_json TEXT, created_at DATETIME)")
    con.commit()
    con.close()
    app = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{path}"})
    client = app.test_client()
    pid, token = make_plan(client)
    assert client.post(f"/api/plans/{pid}/toggle", json={"id": "t0"}, headers=edit(token)).status_code == 200
