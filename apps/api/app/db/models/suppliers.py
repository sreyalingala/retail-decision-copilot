from __future__ import annotations

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Supplier(Base, TimestampMixin):
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    supplier_lead_time_days: Mapped[int] = mapped_column(nullable=False)

    products: Mapped[list["Product"]] = relationship(back_populates="supplier")
    replenishment_orders: Mapped[list["ReplenishmentOrder"]] = relationship(
        back_populates="supplier"
    )

