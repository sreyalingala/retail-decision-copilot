from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class Store(Base, TimestampMixin):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(primary_key=True)
    region_id: Mapped[int] = mapped_column(
        ForeignKey("regions.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    store_name: Mapped[str] = mapped_column(String(200), nullable=False)
    store_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    city: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)

    stores: Mapped[list["Sale"]] = relationship(back_populates="store")
    region: Mapped["Region"] = relationship(back_populates="stores")

    inventory_snapshots: Mapped[list["InventorySnapshot"]] = relationship(
        back_populates="store"
    )
    replenishment_orders: Mapped[list["ReplenishmentOrder"]] = relationship(
        back_populates="store"
    )
    returns: Mapped[list["Return"]] = relationship(back_populates="store")

