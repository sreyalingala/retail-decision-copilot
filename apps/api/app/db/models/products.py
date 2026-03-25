from __future__ import annotations

from decimal import Decimal
from typing import Optional

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Product(Base, TimestampMixin):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(250), nullable=False)

    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    supplier_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("suppliers.id", ondelete="SET NULL"), index=True, nullable=True
    )

    unit_cost: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    base_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    is_active: Mapped[bool] = mapped_column(nullable=False, server_default="true")

    category: Mapped["Category"] = relationship(back_populates="products")
    supplier: Mapped["Supplier"] = relationship(back_populates="products")

    sales: Mapped[list["Sale"]] = relationship(back_populates="product")
    inventory_snapshots: Mapped[list["InventorySnapshot"]] = relationship(
        back_populates="product"
    )
    returns: Mapped[list["Return"]] = relationship(back_populates="product")
    replenishment_orders: Mapped[list["ReplenishmentOrder"]] = relationship(
        back_populates="product"
    )

