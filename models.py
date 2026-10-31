"""Database model. One table, one row per saved plan."""
import json
import uuid
from datetime import date, datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date, DateTime, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)


class Plan(db.Model):
    __tablename__ = "plans"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=lambda: uuid.uuid4().hex)
    event_type: Mapped[str] = mapped_column(String(20))
    title: Mapped[str] = mapped_column(String(120))
    event_date: Mapped[date] = mapped_column(Date)
    guests: Mapped[int] = mapped_column(Integer)
    budget: Mapped[int] = mapped_column(Integer)
    city: Mapped[str] = mapped_column(String(80), default="")
    theme: Mapped[str] = mapped_column(String(80), default="")
    preferences: Mapped[str] = mapped_column(Text, default="")
    data_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    @property
    def data(self) -> dict:
        return json.loads(self.data_json)

    @data.setter
    def data(self, value: dict) -> None:
        self.data_json = json.dumps(value)
