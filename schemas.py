"""Typed shapes for the data that flows between the planner, the agents, the API and the database.

These are TypedDicts, so they cost nothing at runtime and are stored as plain JSON, but mypy can check
every function that reads or builds a plan.
"""
from datetime import date
from typing import NotRequired, TypedDict


class CleanForm(TypedDict):
    """Validated event details submitted by the user."""

    event_type: str
    title: str
    event_date: date
    guests: int
    budget: int
    city: str
    theme: str
    preferences: str


class BudgetLine(TypedDict):
    category: str
    pct: int
    amount: int


class TimelineItem(TypedDict):
    id: str
    task: str
    category: str
    due: str  # ISO date
    late: bool  # True when the original deadline had already passed
    done: bool


class VendorItem(TypedDict):
    id: str
    vendor: str
    ask: str
    category: str
    done: bool


class Idea(TypedDict):
    title: str
    detail: str


class TraceStep(TypedDict):
    agent: str
    detail: str


class GuideNote(TypedDict):
    """One retrieved knowledge-base passage."""

    title: str
    kind: str  # idea | tip | risk
    text: str


class PlanData(TypedDict):
    """A finished plan, as stored in the database and returned by the API."""

    source: str  # rules | rules+rag | ai+rag
    summary: str
    budget: list[BudgetLine]
    timeline: list[TimelineItem]
    vendors: list[VendorItem]
    ideas: list[Idea]
    vendor_tips: list[str]
    risks: list[str]
    warnings: list[str]
    trace: NotRequired[list[TraceStep]]


class CreativeResult(TypedDict):
    """The narrative parts of a plan, written by the LLM and validated by agents.llm.sanitize_creative."""

    summary: str
    ideas: list[Idea]
    vendor_tips: list[str]
    risks: list[str]
