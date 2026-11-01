"""Database model. One table, one row per saved plan."""
import json
import uuid
from datetime import UTC, date, datetime
from typing import cast

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from schemas import PlanData


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Plan(db.Model):  # type: ignore[name-defined]  # Flask-SQLAlchemy builds Model at runtime
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    edit_token_hash: Mapped[str] = mapped_column(String(64))
    event_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120))
    event_date: Mapped[date] = mapped_column(Date)
    guests: Mapped[int] = mapped_column(Integer)
    budget: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String(80), default="")
    theme: Mapped[str] = mapped_column(String(80), default="")
    preferences: Mapped[str] = mapped_column(Text, default="")
    data_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @property
    def data(self) -> PlanData:
        """The generated plan (budget, timeline, vendors, ideas, trace) as a dict."""
        return cast(PlanData, json.loads(self.data_json))

    @data.setter
    def data(self, value: PlanData) -> None:
        self.data_json = json.dumps(value)
