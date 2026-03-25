"""retail analytics schema

Create the base retail analytics tables (regions/stores/categories/suppliers/products/
promotions/sales/inventory_snapshots/returns/replenishment_orders).
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision = "0002_retail_analytics_schema"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Dimensions ---
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("region_name", sa.String(length=120), nullable=False),
        sa.Column("timezone", sa.String(length=64), server_default=sa.text("'UTC'"), nullable=False),
        sa.Column("created_by", sa.String(length=64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("region_name", name="uq_regions_region_name"),
    )

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("store_name", sa.String(length=200), nullable=False),
        sa.Column("store_code", sa.String(length=50), nullable=False),
        sa.Column("city", sa.String(length=120), nullable=True),
        sa.Column("state", sa.String(length=120), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["region_id"], ["regions.id"], ondelete="RESTRICT"),
        sa.UniqueConstraint("store_code", name="uq_stores_store_code"),
    )
    op.create_index("ix_stores_region_id", "stores", ["region_id"], unique=False)

    op.create_table(
        "categories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category_name", sa.String(length=200), nullable=False),
        sa.Column("department", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("category_name", name="uq_categories_category_name"),
    )

    op.create_table(
        "suppliers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_name", sa.String(length=200), nullable=False),
        sa.Column("supplier_lead_time_days", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("supplier_name", name="uq_suppliers_supplier_name"),
    )

    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sku", sa.String(length=80), nullable=False),
        sa.Column("product_name", sa.String(length=250), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=True),
        sa.Column("unit_cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("base_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="SET NULL"),
        sa.UniqueConstraint("sku", name="uq_products_sku"),
    )
    op.create_index("ix_products_category_id", "products", ["category_id"], unique=False)
    op.create_index("ix_products_supplier_id", "products", ["supplier_id"], unique=False)

    # --- Promotions ---
    op.create_table(
        "promotions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("promotion_name", sa.String(length=220), nullable=False),
        sa.Column("discount_type", sa.String(length=30), nullable=False),
        sa.Column("discount_value", sa.Numeric(12, 4), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "discount_type IN ('percentage','fixed_amount','bogo')",
            name="ck_promotions_discount_type",
        ),
    )
    op.create_index("ix_promotions_promotion_name", "promotions", ["promotion_name"], unique=False)
    op.create_index("ix_promotions_start_date", "promotions", ["start_date"], unique=False)
    op.create_index("ix_promotions_end_date", "promotions", ["end_date"], unique=False)

    # --- Facts ---
    op.create_table(
        "sales",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("sale_date", sa.Date(), nullable=False),
        sa.Column("sale_ts", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("promotion_id", sa.Integer(), nullable=True),
        sa.Column("quantity_sold", sa.Integer(), nullable=False),
        sa.Column("unit_price", sa.Numeric(12, 2), nullable=False),
        sa.Column("discount_amount", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("gross_revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("net_revenue", sa.Numeric(12, 2), nullable=False),
        sa.Column("gross_margin", sa.Numeric(12, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["promotion_id"], ["promotions.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_sales_sale_date", "sales", ["sale_date"], unique=False)
    op.create_index("ix_sales_store_id", "sales", ["store_id"], unique=False)
    op.create_index("ix_sales_product_id", "sales", ["product_id"], unique=False)
    op.create_index("ix_sales_promotion_id", "sales", ["promotion_id"], unique=False)

    op.create_table(
        "inventory_snapshots",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column(
            "snapshot_ts",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("stock_on_hand", sa.Integer(), nullable=False),
        sa.Column("reorder_point", sa.Integer(), nullable=False),
        sa.Column("target_stock_level", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_inventory_snapshots_snapshot_date",
        "inventory_snapshots",
        ["snapshot_date"],
        unique=False,
    )
    op.create_index(
        "ix_inventory_snapshots_store_id", "inventory_snapshots", ["store_id"], unique=False
    )
    op.create_index(
        "ix_inventory_snapshots_product_id",
        "inventory_snapshots",
        ["product_id"],
        unique=False,
    )

    op.create_table(
        "returns",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("return_date", sa.Date(), nullable=False),
        sa.Column("return_ts", sa.TIMESTAMP(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("return_quantity", sa.Integer(), nullable=False),
        sa.Column("return_reason", sa.String(length=120), nullable=True),
        sa.Column("refund_amount", sa.Numeric(12, 2), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["sale_id"], ["sales.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_returns_return_date", "returns", ["return_date"], unique=False)
    op.create_index("ix_returns_sale_id", "returns", ["sale_id"], unique=False)
    op.create_index("ix_returns_store_id", "returns", ["store_id"], unique=False)
    op.create_index("ix_returns_product_id", "returns", ["product_id"], unique=False)

    op.create_table(
        "replenishment_orders",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "order_ts",
            sa.TIMESTAMP(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("expected_delivery_date", sa.Date(), nullable=False),
        sa.Column("actual_delivery_date", sa.Date(), nullable=True),
        sa.Column("delay_days", sa.Integer(), nullable=True),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("supplier_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("ordered_quantity", sa.Integer(), nullable=False),
        sa.Column("received_quantity", sa.Integer(), server_default=sa.text("0"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["supplier_id"], ["suppliers.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["product_id"], ["products.id"], ondelete="RESTRICT"),
    )
    op.create_index(
        "ix_replenishment_orders_order_ts",
        "replenishment_orders",
        ["order_ts"],
        unique=False,
    )
    op.create_index(
        "ix_replenishment_orders_expected_delivery_date",
        "replenishment_orders",
        ["expected_delivery_date"],
        unique=False,
    )
    op.create_index(
        "ix_replenishment_orders_store_id",
        "replenishment_orders",
        ["store_id"],
        unique=False,
    )
    op.create_index(
        "ix_replenishment_orders_supplier_id",
        "replenishment_orders",
        ["supplier_id"],
        unique=False,
    )
    op.create_index(
        "ix_replenishment_orders_product_id",
        "replenishment_orders",
        ["product_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("replenishment_orders")
    op.drop_table("returns")
    op.drop_table("inventory_snapshots")
    op.drop_table("sales")
    op.drop_table("promotions")
    op.drop_table("products")
    op.drop_table("suppliers")
    op.drop_table("categories")
    op.drop_table("stores")
    op.drop_table("regions")

