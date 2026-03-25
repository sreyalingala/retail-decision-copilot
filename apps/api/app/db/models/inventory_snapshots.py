from __future__ import annotations

from sqlalchemy import Date, ForeignKey, Integer, TIMESTAMP, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.models.timestamp import TimestampMixin


class InventorySnapshot(Base, TimestampMixin):
    __tablename__ = "inventory_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True)

    snapshot_date: Mapped[object] = mapped_column(Date, index=True, nullable=False)
    snapshot_ts: Mapped[object] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )

    store_id: Mapped[int] = mapped_column(
        ForeignKey("stores.id", ondelete="RESTRICT"), index=True, nullable=False
    )
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), index=True, nullable=False
    )

    stock_on_hand: Mapped[int] = mapped_column(Integer, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False)
    target_stock_level: Mapped[int] = mapped_column(Integer, nullable=False)

    store: Mapped["Store"] = relationship(back_populates="inventory_snapshots")
    product: Mapped["Product"] = relationship(back_populates="inventory_snapshots")

