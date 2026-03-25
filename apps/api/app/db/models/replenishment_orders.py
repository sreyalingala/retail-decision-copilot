from __future__ import annotations

from datetime import date
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class ReplenishmentOrder(Base, TimestampMixin):
    __tablename__ = "replenishment_orders"

    id: Mapped[int] = mapped_column(primary_key=True)

    order_ts: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    expected_delivery_date: Mapped[date] = mapped_column(
        Date, index=True, nullable=False
    )
    actual_delivery_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    delay_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    supplier_id: Mapped[int] = mapped_column(
        ForeignKey("suppliers.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    ordered_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    store: Mapped["Store"] = relationship(back_populates="replenishment_orders")
    supplier: Mapped["Supplier"] = relationship(back_populates="replenishment_orders")
    product: Mapped["Product"] = relationship(back_populates="replenishment_orders")

