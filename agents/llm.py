"""LLM access through LangChain. Every call is bounded and returns None on failure."""
import json
import logging
import os
import re

from langchain_core.messages import HumanMessage, SystemMessage

log = logging.getLogger(__name__)


def get_llm():
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=key,
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.6, timeout=12, max_retries=0, max_tokens=800,
    )


def parse_json(text: str) -> dict | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def call(llm, system: str, user: str) -> str | None:
    if llm is None:
        return None
    try:
        reply = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return reply.content if isinstance(reply.content, str) else None
    except Exception as exc:  # network, auth, rate limit, timeout: all fall back
        log.warning("LLM call skipped: %s", type(exc).__name__)
        return None


def _s(value, limit):
    return str(value).strip()[:limit] if isinstance(value, (str, int, float)) else ""


def sanitize_creative(raw) -> dict | None:
    """Keep only the expected keys, types and lengths from model output."""
    if not isinstance(raw, dict):
        return None
    ideas = [{"title": _s(i["title"], 80), "detail": _s(i.get("detail"), 240)}
             for i in (raw.get("ideas") or [])[:6] if isinstance(i, dict) and _s(i.get("title"), 80)]
    out = {
        "summary": _s(raw.get("summary"), 500),
        "ideas": ideas,
        "vendor_tips": [t for t in (_s(x, 200) for x in (raw.get("vendor_tips") or [])[:5]) if t],
        "risks": [t for t in (_s(x, 200) for x in (raw.get("risks") or [])[:5]) if t],
    }
    return out if out["summary"] and out["ideas"] else None
