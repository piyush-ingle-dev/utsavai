"""Security helpers: headers, HTTPS in production, cross-site write protection and edit tokens.

Threat model in short: plans are anonymous, so each plan has two secrets.
  * the plan id (in the URL) lets anyone read the plan;
  * the edit token (kept only in the creator's browser, stored as a SHA-256 hash) is required to change it.
"""
import hashlib
import hmac
import secrets
from collections.abc import Callable
from typing import Any
from urllib.parse import urlsplit

from flask import Flask, Response, abort, request
from flask_talisman import Talisman
from werkzeug.middleware.proxy_fix import ProxyFix

EDIT_HEADER = "X-Edit-Token"
WRITE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})

CSP = {
    "default-src": "'self'",
    "script-src": "'self'",
    "style-src": "'self'",
    "img-src": ["'self'", "data:"],
    "connect-src": "'self'",
    "object-src": "'none'",
    "base-uri": "'self'",
    "form-action": "'self'",
    "frame-ancestors": "'none'",
}


def new_edit_token() -> tuple[str, str]:
    """Return (token, sha256_hash). Only the hash is stored."""
    token = secrets.token_urlsafe(32)
    return token, _digest(token)


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def token_matches(token: str | None, stored_hash: str) -> bool:
    """Constant-time check of a presented token against the stored hash."""
    if not token:
        return False
    return hmac.compare_digest(_digest(token), stored_hash)


def reject_cross_site_writes() -> None:
    """Block state-changing requests that were started by another website.

    Browsers label every request with Sec-Fetch-Site; if it is missing (older browsers, scripts) we fall back
    to comparing the Origin header with our own host. Requests with neither header (curl, tests) are allowed.
    """
    if request.method not in WRITE_METHODS:
        return
    site = request.headers.get("Sec-Fetch-Site")
    if site is not None:
        if site not in {"same-origin", "none"}:
            abort(403)
        return
    origin = request.headers.get("Origin")
    if origin and urlsplit(origin).netloc != request.host:
        abort(403)


def exempt_from_https_redirect[ViewT: Callable[..., Any]](view: ViewT) -> ViewT:
    """Health checks come from inside the platform over plain HTTP, so they must not be redirected."""
    view.talisman_view_options = {"force_https": False}  # type: ignore[attr-defined]
    return view


def init_security(app: Flask, production: bool) -> None:
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)  # type: ignore[method-assign]
    Talisman(app, content_security_policy=CSP, frame_options="DENY",
             force_https=production, strict_transport_security=production,
             session_cookie_secure=production)
    app.before_request(reject_cross_site_writes)

    @app.after_request
    def no_store_for_api(response: Response) -> Response:
        if request.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response
