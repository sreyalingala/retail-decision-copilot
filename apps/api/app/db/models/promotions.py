from __future__ import annotations

from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Promotion(Base, TimestampMixin):
    __tablename__ = "promotions"

    id: Mapped[int] = mapped_column(primary_key=True)
    promotion_name: Mapped[str] = mapped_column(String(220), index=True, nullable=False)

    discount_type: Mapped[str] = mapped_column(String(30), nullable=False)
    discount_value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)

    start_date: Mapped[object] = mapped_column(Date, index=True, nullable=False)
    end_date: Mapped[object] = mapped_column(Date, index=True, nullable=False)

    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    __table_args__ = (
        CheckConstraint(
            "discount_type IN ('percentage','fixed_amount','bogo')",
            name="ck_promotions_discount_type",
        ),
    )

    sales: Mapped[list["Sale"]] = relationship(back_populates="promotion")

