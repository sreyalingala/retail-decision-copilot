from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Return(Base, TimestampMixin):
    __tablename__ = "returns"

    id: Mapped[int] = mapped_column(primary_key=True)

    return_date: Mapped[object] = mapped_column(Date, index=True, nullable=False)
    return_ts: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    sale_id: Mapped[int] = mapped_column(
        ForeignKey("sales.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    return_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    return_reason: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    refund_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, server_default="0"
    )

    sale: Mapped["Sale"] = relationship(back_populates="returns")
    store: Mapped["Store"] = relationship(back_populates="returns")
    product: Mapped["Product"] = relationship(back_populates="returns")

