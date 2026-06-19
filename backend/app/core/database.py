"""SQLite database setup using SQLAlchemy 2.0."""

from __future__ import annotations

import json
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import (DeclarativeBase, Mapped, Session, mapped_column,
                            sessionmaker)

from .config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


class Project(Base):
    """A saved analysis project."""

    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), default="Untitled")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # JSON-encoded payloads.
    points_json: Mapped[str] = mapped_column(Text, default="[]")
    area_json: Mapped[str] = mapped_column(Text, default="{}")
    perimeter_json: Mapped[str] = mapped_column(Text, default="{}")
    analysis_json: Mapped[str] = mapped_column(Text, default="{}")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "points": json.loads(self.points_json or "[]"),
            "area": json.loads(self.area_json or "{}"),
            "perimeter": json.loads(self.perimeter_json or "{}"),
            "analysis": json.loads(self.analysis_json or "{}"),
        }


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
