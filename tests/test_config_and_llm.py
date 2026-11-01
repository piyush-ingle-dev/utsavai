"""Configuration, LLM helper and error-path tests."""
import logging

import pytest

import config
from agents import llm as llm_mod
from app import create_app

# ---- config --------------------------------------------------------------------

def test_settings_defaults(monkeypatch):
    for name in ("SECRET_KEY", "DATABASE_URL", "RENDER", "APP_ENV", "LOG_LEVEL"):
        monkeypatch.delenv(name, raising=False)
    s = config.load_settings()
    assert s.database_url == "sqlite:///utsav.db" and not s.production and s.log_level == "INFO"
    assert len(s.secret_key) == 64


def test_secret_key_is_read_from_environment(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", "abc")
    assert config.load_settings().secret_key == "abc"


def test_warns_when_secret_key_missing(monkeypatch, caplog):
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with caplog.at_level(logging.WARNING):
        config.load_settings()
    assert "SECRET_KEY" in caplog.text


@pytest.mark.parametrize(("name", "value"), [("RENDER", "true"), ("RENDER", "1"), ("APP_ENV", "production")])
def test_production_is_detected(monkeypatch, name, value):
    monkeypatch.setenv(name, value)
    assert config.load_settings().production


def test_legacy_postgres_url_is_rewritten(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host/db")
    assert config.load_settings().database_url == "postgresql://u:p@host/db"


# ---- llm helpers ---------------------------------------------------------------

def test_get_llm_is_none_without_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    assert llm_mod.get_llm() is None
    assert llm_mod.call(None, "s", "u") is None


def test_get_llm_uses_environment(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    monkeypatch.setenv("OPENAI_MODEL", "some-model")
    model = llm_mod.get_llm()
    assert model.model_name == "some-model" and model.max_retries == 0


@pytest.mark.parametrize("text", ["", "no json here", "{broken", "{not: valid}", "[1, 2]", "}{"])
def test_parse_json_rejects_unusable_text(text):
    assert llm_mod.parse_json(text) is None


def test_parse_json_extracts_object_from_chatty_reply():
    assert llm_mod.parse_json('Sure! Here you go: {"a": 1} hope that helps') == {"a": 1}


@pytest.mark.parametrize("raw", [None, "x", [], {"summary": "s"}, {"ideas": [{"title": "t"}]},
                                 {"summary": "s", "ideas": "not a list"}, {"summary": "s", "ideas": [5, None]}])
def test_sanitize_rejects_malformed_output(raw):
    assert llm_mod.sanitize_creative(raw) is None


def test_sanitize_truncates_and_filters():
    raw = {"summary": "s" * 900, "ideas": [{"title": "t" * 200, "detail": "d" * 500}] * 9,
           "vendor_tips": ["a"] * 9 + ["", None, {"x": 1}], "risks": "oops"}
    out = llm_mod.sanitize_creative(raw)
    assert len(out["summary"]) == 500 and len(out["ideas"]) == 6
    assert len(out["ideas"][0]["title"]) == 80 and len(out["ideas"][0]["detail"]) == 240
    assert out["vendor_tips"] == ["a"] * 5 and out["risks"] == []


# ---- app wiring ----------------------------------------------------------------

def test_frontend_missing_returns_helpful_503(monkeypatch, tmp_path):
    import app as app_module

    monkeypatch.setattr(app_module, "WEB_DIR", tmp_path)
    client = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"}).test_client()
    response = client.get("/")
    assert response.status_code == 503 and "npm run build" in response.json["error"]


def test_spa_routes_serve_the_frontend(monkeypatch):
    client = create_app({"TESTING": True, "SQLALCHEMY_DATABASE_URI": "sqlite://"}).test_client()
    for path in ("/", "/plan/" + "a" * 32):
        response = client.get(path)
        assert response.status_code == 200 and b"<div id=\"root\">" in response.data
