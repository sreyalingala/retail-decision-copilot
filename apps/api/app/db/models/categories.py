from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Category(Base, TimestampMixin):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    category_name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    department: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    products: Mapped[list["Product"]] = relationship(back_populates="category")

