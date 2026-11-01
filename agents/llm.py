"""LLM access through LangChain. Every call is bounded and returns None on failure."""
import json
import logging
import os
import re
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr

from schemas import CreativeResult, Idea

log = logging.getLogger(__name__)

MAX_OUTPUT_TOKENS = 2000  # headroom for models that spend part of the limit on hidden reasoning


def get_llm() -> Any:
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        return None
    from langchain_openai import ChatOpenAI
    return ChatOpenAI(
        model=os.environ.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=SecretStr(key),
        base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        temperature=0.6, timeout=12, max_retries=0,
        max_tokens=MAX_OUTPUT_TOKENS,  # type: ignore[call-arg]  # alias of max_completion_tokens
    )


def parse_json(text: str) -> dict[str, Any] | None:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end <= start:
        return None
    try:
        value = json.loads(text[start:end + 1])
    except ValueError:
        return None
    return value if isinstance(value, dict) else None


def call(llm: Any, system: str, user: str) -> str | None:
    if llm is None:
        return None
    try:
        reply = llm.invoke([SystemMessage(content=system), HumanMessage(content=user)])
        return reply.content if isinstance(reply.content, str) else None
    except Exception as exc:  # network, auth, rate limit, timeout: all fall back
        log.warning("LLM call skipped: %s", type(exc).__name__)
        return None


def _s(value: object, limit: int) -> str:
    return str(value).strip()[:limit] if isinstance(value, (str, int, float)) else ""


def _clean_list(value: object, limit: int, max_items: int) -> list[str]:
    items = value if isinstance(value, list) else []
    return [text for text in (_s(item, limit) for item in items[:max_items]) if text]


def sanitize_creative(raw: object) -> CreativeResult | None:
    """Keep only the expected keys, types and lengths from model output; None if it is unusable."""
    if not isinstance(raw, dict):
        return None
    raw_ideas = raw.get("ideas")
    ideas = [Idea(title=_s(item.get("title"), 80), detail=_s(item.get("detail"), 240))
             for item in (raw_ideas[:6] if isinstance(raw_ideas, list) else [])
             if isinstance(item, dict) and _s(item.get("title"), 80)]
    summary = _s(raw.get("summary"), 500)
    if not summary or not ideas:
        return None
    return CreativeResult(summary=summary, ideas=ideas,
                          vendor_tips=_clean_list(raw.get("vendor_tips"), 200, 5),
                          risks=_clean_list(raw.get("risks"), 200, 5))
