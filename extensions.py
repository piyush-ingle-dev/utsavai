"""Shared Flask extension instances, created here so blueprints can import them without cycles."""
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["300 per hour"], storage_uri="memory://")
