"""End-to-end browser test of the real app (Flask + built React bundle).

Needs Playwright and a browser:  pip install playwright && playwright install chromium
Run with:                        pytest -m e2e
"""
import threading

import pytest
from werkzeug.serving import make_server

from app import create_app

pytestmark = pytest.mark.e2e
sync_api = pytest.importorskip("playwright.sync_api")


@pytest.fixture(scope="module")
def base_url():
    app = create_app({"SQLALCHEMY_DATABASE_URI": "sqlite://", "TESTING": True})
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()


@pytest.fixture(scope="module")
def browser():
    with sync_api.sync_playwright() as playwright:
        chromium = playwright.chromium.launch()
        yield chromium
        chromium.close()


def create_plan(page, base_url):
    page.goto(base_url)
    page.fill("#guests", "120")
    page.fill("#budget", "400000")
    page.fill("#preferences", "Pure veg menu")
    page.click("button:has-text('Create my plan')")
    page.wait_for_selector("h1:has-text('Wedding')")


def test_owner_can_create_tick_and_keep_progress_after_reload(browser, base_url):
    page = browser.new_context().new_page()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    create_plan(page, base_url)

    assert "/plan/" in page.url and page.title() == "Wedding | UtsavAI"
    assert page.evaluate("document.activeElement.id") == "main"
    page.check(".checklist input >> nth=0")
    page.wait_for_selector("text=1 of")
    page.reload()
    page.wait_for_selector("h1:has-text('Wedding')")
    assert page.is_checked(".checklist input >> nth=0")
    assert page.inner_text("main").count("How this plan was made") == 1
    assert errors == []


def test_visitor_with_only_the_link_sees_a_read_only_plan(browser, base_url):
    owner = browser.new_context().new_page()
    create_plan(owner, base_url)

    visitor = browser.new_context().new_page()
    visitor.goto(owner.url)
    visitor.wait_for_selector("h1:has-text('Wedding')")
    assert visitor.locator(".checklist input:enabled").count() == 0
    assert "View only" in visitor.inner_text("main")


def test_form_shows_server_validation_errors(browser, base_url):
    page = browser.new_context().new_page()
    page.goto(base_url)
    page.click("button:has-text('Create my plan')")
    page.wait_for_selector("[role=alert]")
    assert page.get_attribute("#guests", "aria-invalid") == "true"
