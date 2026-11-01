"""Application settings, read once from environment variables (or a local .env file)."""
import logging
import os
import secrets
from dataclasses import dataclass

log = logging.getLogger(__name__)


def _flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    return default if raw is None else raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    secret_key: str
    database_url: str
    production: bool
    log_level: str
    max_body_bytes: int = 32 * 1024


def load_settings() -> Settings:
    """Build Settings from the environment. Render sets RENDER=true, which switches on production hardening."""
    production = _flag("RENDER") or os.environ.get("APP_ENV", "").lower() == "production"
    secret = os.environ.get("SECRET_KEY", "").strip()
    if not secret:
        log.warning("SECRET_KEY is not set; using a random key for this process only.")
        secret = secrets.token_hex(32)
    database_url = os.environ.get("DATABASE_URL", "sqlite:///utsav.db")
    if database_url.startswith("postgres://"):  # older providers still use this prefix
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    return Settings(secret_key=secret, database_url=database_url, production=production,
                    log_level=os.environ.get("LOG_LEVEL", "INFO").upper())
