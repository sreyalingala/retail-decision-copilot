from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, func, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Region(Base, TimestampMixin):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    timezone: Mapped[str] = mapped_column(String(64), default="UTC", server_default="UTC")
    created_by: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    stores: Mapped[list["Store"]] = relationship(back_populates="region")

