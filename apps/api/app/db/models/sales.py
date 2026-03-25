from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Sale(Base, TimestampMixin):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(primary_key=True)

    # For analyst-style filters (WHERE sale_date BETWEEN ...)
    sale_date: Mapped[object] = mapped_column(Date, index=True, nullable=False)
    sale_ts: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    promotion_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("promotions.id", ondelete="SET NULL"), index=True, nullable=True
    )

    quantity_sold: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    discount_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )

    # Denormalized monetary measures to simplify portfolio queries.
    gross_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    net_revenue: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    gross_margin: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    store: Mapped["Store"] = relationship(back_populates="sales")
    product: Mapped["Product"] = relationship(back_populates="sales")
    promotion: Mapped["Promotion"] = relationship(back_populates="sales")

