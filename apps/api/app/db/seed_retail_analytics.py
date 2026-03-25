from __future__ import annotations

import os
import time
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import sqlalchemy as sa
from sqlalchemy import insert
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.models import (
    Category,
    InventorySnapshot,
    Promotion,
    Product,
    ReplenishmentOrder,
    Region,
    Return,
    Sale,
    Store,
    Supplier,
)


# Keep the dataset deterministic across runs.
DEFAULT_RANDOM_SEED = 42


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return int(raw)


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return float(raw)


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class SeedScales:
    regions: int
    stores: int
    categories: int
    suppliers: int
    products: int
    promotions: int
    sales_rows: int
    snapshot_dates: int
    snapshot_span_days: int
    assortment_fraction: float
    return_rate_base: float
    chronic_delay_fraction: float


def _date_range(start: date, days: int) -> List[date]:
    return [start + timedelta(days=i) for i in range(days)]


def _seasonality_factor(d: date) -> float:
    # Simple seasonal + weekly pattern. Values are roughly centered around 1.0.
    month = d.month
    # Higher demand in Nov/Dec (holiday season) and moderate in summer.
    month_factor = {
        1: 0.95,
        2: 0.98,
        3: 1.02,
        4: 1.03,
        5: 1.05,
        6: 1.06,
        7: 1.04,
        8: 1.03,
        9: 1.00,
        10: 1.07,
        11: 1.18,
        12: 1.25,
    }.get(month, 1.0)
    weekend_boost = 1.06 if d.weekday() >= 5 else 1.0
    # Gentle intra-year wobble.
    wobble = 1.0 + 0.04 * ((d.toordinal() % 30) / 30.0 - 0.5)
    return month_factor * weekend_boost * wobble


def _quantize_money(x: float, places: str = "0.01") -> Decimal:
    # Quantize deterministically for numeric columns (Numeric(12,2) / Numeric(12,4)).
    return Decimal(str(x)).quantize(Decimal(places))


def _chunked(seq: Sequence[Dict[str, Any]], chunk_size: int) -> Iterable[List[Dict[str, Any]]]:
    for i in range(0, len(seq), chunk_size):
        yield seq[i : i + chunk_size]


def _count_rows(conn: sa.Connection) -> Dict[str, int]:
    tables = [
        Region.__tablename__,
        Store.__tablename__,
        Category.__tablename__,
        Supplier.__tablename__,
        Product.__tablename__,
        Promotion.__tablename__,
        Sale.__tablename__,
        InventorySnapshot.__tablename__,
        Return.__tablename__,
        ReplenishmentOrder.__tablename__,
    ]
    out: Dict[str, int] = {}
    for t in tables:
        out[t] = conn.execute(sa.text(f"SELECT COUNT(*) FROM {t}")).scalar_one()
    return out


def _truncate_all(conn: sa.Connection) -> None:
    # Truncate in a dependency-friendly order.
    # CASCADE is safe here because the schema doesn't define cross-links beyond the modeled FKs.
    conn.execute(
        sa.text(
            """
            TRUNCATE TABLE
              replenishment_orders,
              returns,
              inventory_snapshots,
              sales,
              promotions,
              products,
              suppliers,
              categories,
              stores,
              regions
            RESTART IDENTITY CASCADE
            """
        )
    )


def _weighted_choice(rng: Any, items: Sequence[int], weights: Sequence[float]) -> int:
    return rng.choices(items, weights=weights, k=1)[0]


def seed_retail_analytics(engine: Engine, *, reset: bool = True) -> Dict[str, int]:
    """
    Seed a deterministic synthetic retail dataset.

    Environment variables to tune scale:
      - SEED_RANDOM_SEED
      - SEED_REGIONS, SEED_STORES, SEED_CATEGORIES, SEED_SUPPLIERS, SEED_PRODUCTS
      - SEED_PROMOTIONS, SEED_SALES_ROWS
      - SEED_SNAPSHOT_DATES, SEED_SNAPSHOT_SPAN_DAYS
      - SEED_ASSORTMENT_FRACTION
      - SEED_RETURN_RATE_BASE
      - SEED_CHRONIC_DELAY_FRACTION
      - SEED_RESET (if calling from a CLI wrapper; this function is passed `reset`)
    """

    import random

    rng = random.Random(_env_int("SEED_RANDOM_SEED", DEFAULT_RANDOM_SEED))

    scales = SeedScales(
        regions=_env_int("SEED_REGIONS", 6),
        stores=_env_int("SEED_STORES", 40),
        categories=_env_int("SEED_CATEGORIES", 14),
        suppliers=_env_int("SEED_SUPPLIERS", 110),
        products=_env_int("SEED_PRODUCTS", 1200),
        promotions=_env_int("SEED_PROMOTIONS", 60),
        sales_rows=_env_int("SEED_SALES_ROWS", 120_000),
        snapshot_dates=_env_int("SEED_SNAPSHOT_DATES", 12),
        snapshot_span_days=_env_int("SEED_SNAPSHOT_SPAN_DAYS", 120),
        assortment_fraction=_env_float("SEED_ASSORTMENT_FRACTION", 0.35),
        return_rate_base=_env_float("SEED_RETURN_RATE_BASE", 0.055),
        chronic_delay_fraction=_env_float("SEED_CHRONIC_DELAY_FRACTION", 0.12),
    )

    # Use fixed dates to make the dataset stable across calendar years.
    # It still produces realistic seasonality patterns.
    start_date = date(2025, 10, 1)
    all_dates = _date_range(start_date, scales.snapshot_span_days)
    end_date = all_dates[-1]

    # Choose snapshot dates evenly across the span.
    if scales.snapshot_dates <= 0:
        raise ValueError("SEED_SNAPSHOT_DATES must be > 0")
    snapshot_dates: List[date] = [
        all_dates[round(i * (len(all_dates) - 1) / (scales.snapshot_dates - 1))]
        for i in range(scales.snapshot_dates)
    ]

    t0 = time.monotonic()
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with engine.begin() as conn:
        if reset:
            _truncate_all(conn)

        # -----------------------
        # Dimensions: regions
        # -----------------------
        region_names = [
            "Northeast",
            "Southeast",
            "Midwest",
            "Southwest",
            "West",
            "Central",
        ]
        timezones = ["America/New_York", "America/Chicago", "America/Los_Angeles"]
        regions_values = [
            {
                "id": i + 1,
                "region_name": region_names[i % len(region_names)],
                "timezone": timezones[i % len(timezones)],
                "created_by": "seed",
            }
            for i in range(scales.regions)
        ]
        conn.execute(insert(Region).values(regions_values))

        # -----------------------
        # Dimensions: stores
        # -----------------------
        city_names = [
            "Arden",
            "Benton",
            "Cedar",
            "Dover",
            "Everett",
            "Fairview",
            "Garland",
            "Hawthorne",
            "Jamestown",
            "Kingsport",
        ]
        state_names = ["NY", "IL", "CA", "TX", "FL", "WA", "CO", "MA", "NC"]

        region_store_weights = [1.0 + rng.random() * 0.6 for _ in range(scales.regions)]
        region_ids = list(range(1, scales.regions + 1))
        region_product_demand_skews = [0.85 + rng.random() * 0.4 for _ in range(scales.regions)]

        stores_values: List[Dict[str, Any]] = []
        store_region_id: Dict[int, int] = {}
        for store_id in range(1, scales.stores + 1):
            region_id = _weighted_choice(rng, region_ids, region_store_weights)
            store_name = f"{region_names[region_id - 1]} Store {store_id}"
            store_code = f"S{region_id:02d}{store_id:04d}"
            city = city_names[(store_id - 1) % len(city_names)]
            state = state_names[(store_id - 1) % len(state_names)]
            store_region_id[store_id] = region_id
            stores_values.append(
                {
                    "id": store_id,
                    "region_id": region_id,
                    "store_name": store_name,
                    "store_code": store_code,
                    "city": city,
                    "state": state,
                }
            )

        conn.execute(insert(Store).values(stores_values))

        # -----------------------
        # Dimensions: categories
        # -----------------------
        base_categories = [
            ("Grocery", "Food & Beverage", 1.0, 0.28),  # name, dept, price_mult, margin_rate
            ("Apparel", "Apparel", 0.95, 0.42),
            ("Electronics", "Tech", 1.25, 0.20),
            ("Home & Kitchen", "Home", 1.05, 0.35),
            ("Beauty", "Personal Care", 1.0, 0.55),
            ("Sports", "Fitness", 0.95, 0.30),
            ("Toys", "Kids", 0.90, 0.45),
            ("Automotive", "Auto", 1.0, 0.25),
            ("Office Supplies", "Office", 0.88, 0.22),
            ("Seasonal", "Seasonal", 1.0, 0.38),
            ("Pet Supplies", "Pet", 0.92, 0.48),
            ("Outdoor", "Outdoor", 1.05, 0.32),
            ("Health", "Health & Wellness", 1.02, 0.50),
            ("Books", "Media", 0.80, 0.26),
            ("Stationery", "Office", 0.78, 0.24),
        ]
        chosen_categories = base_categories[: scales.categories]
        categories_values: List[Dict[str, Any]] = []
        category_price_mult: Dict[int, float] = {}
        category_margin_rate: Dict[int, float] = {}

        for idx, (name, dept, price_mult, margin_rate) in enumerate(chosen_categories):
            category_id = idx + 1
            categories_values.append(
                {
                    "id": category_id,
                    "category_name": name,
                    "department": dept,
                }
            )
            category_price_mult[category_id] = price_mult
            category_margin_rate[category_id] = margin_rate

        conn.execute(insert(Category).values(categories_values))

        # -----------------------
        # Dimensions: suppliers
        # -----------------------
        chronic_supplier_ids = set(
            rng.sample(list(range(1, scales.suppliers + 1)), k=max(5, int(scales.suppliers * scales.chronic_delay_fraction)))
        )

        supplier_names = [
            "NorthGate Supply",
            "BlueRiver Wholesale",
            "Copperline Imports",
            "Ironwood Trading",
            "SilverPeak Logistics",
            "MapleSpring Goods",
            "Sunfield Procurement",
            "Atlas Wholesale",
            "Delta Source",
            "Harbor & Co.",
        ]
        suppliers_values: List[Dict[str, Any]] = []
        supplier_lead_time_days: Dict[int, int] = {}
        for supplier_id in range(1, scales.suppliers + 1):
            base = 2 + int(rng.random() * 6)  # 2..8 days
            if supplier_id in chronic_supplier_ids:
                lead = base + 6 + int(rng.random() * 10)  # chronic: 8..22+
            else:
                lead = base + int(rng.random() * 6)  # 2..14
            supplier_lead_time_days[supplier_id] = lead
            suppliers_values.append(
                {
                    "id": supplier_id,
                    "supplier_name": f"{supplier_names[(supplier_id - 1) % len(supplier_names)]} #{supplier_id}",
                    "supplier_lead_time_days": lead,
                }
            )

        conn.execute(insert(Supplier).values(suppliers_values))

        # -----------------------
        # Dimensions: products
        # -----------------------
        brands = ["Aster", "Cedar&Co", "Orion", "Lumen", "Everwell", "Nova", "KiteWorks"]
        product_types = ["Pro", "Classic", "Plus", "Essential", "Everyday", "Elite", "Value"]

        products_values: List[Dict[str, Any]] = []
        product_return_rate: Dict[int, float] = {}
        product_popularity_weight: Dict[int, float] = {}
        product_supplier_id: Dict[int, int] = {}
        product_category_id: Dict[int, int] = {}
        product_base_price: Dict[int, Decimal] = {}
        product_unit_cost: Dict[int, Decimal] = {}

        # Return rates vary by category: electronics and apparel tend to be higher.
        category_return_bias: Dict[int, float] = {}
        for cat_id, cat_name in enumerate([c[0] for c in chosen_categories], start=1):
            if cat_name in {"Electronics", "Apparel"}:
                category_return_bias[cat_id] = 1.55
            elif cat_name in {"Toys", "Outdoor"}:
                category_return_bias[cat_id] = 1.30
            else:
                category_return_bias[cat_id] = 1.00

        for product_id in range(1, scales.products + 1):
            category_id = _weighted_choice(
                rng, list(category_price_mult.keys()), [1.0] * len(category_price_mult)
            )
            supplier_id = _weighted_choice(
                rng, list(range(1, scales.suppliers + 1)), [1.0] * scales.suppliers
            )

            price_mult = category_price_mult[category_id]
            margin_rate = category_margin_rate[category_id]

            # Unit cost and base price with realistic markup ranges.
            # Low margin categories have lower markup.
            markup = 1.0 + (margin_rate * 0.9) + rng.random() * 0.25
            unit_cost = _quantize_money(8 + rng.random() * 120, "0.01")
            base_price = _quantize_money(float(unit_cost) * markup * price_mult, "0.01")

            # Some products are more return-prone (e.g., certain categories and "Pro" lines).
            is_high_return_line = rng.random() < 0.18
            return_bias = category_return_bias.get(category_id, 1.0)
            return_rate = scales.return_rate_base * return_bias * (1.0 + (0.8 if is_high_return_line else 0.0))
            return_rate = min(return_rate, 0.22)  # cap for realism

            # Popularity impacts which products show up in sales and inventory risk.
            popularity = 0.5 + rng.random() * 1.7

            sku = f"SKU-{category_id:02d}-{product_id:06d}"
            products_values.append(
                {
                    "id": product_id,
                    "sku": sku,
                    "product_name": f"{brands[(product_id - 1) % len(brands)]} {product_types[(product_id - 1) % len(product_types)]} {sku[-3:]}",
                    "category_id": category_id,
                    "supplier_id": supplier_id,
                    "unit_cost": unit_cost,
                    "base_price": base_price,
                    "is_active": True,
                }
            )
            product_return_rate[product_id] = return_rate
            product_popularity_weight[product_id] = popularity
            product_supplier_id[product_id] = supplier_id
            product_category_id[product_id] = category_id
            product_base_price[product_id] = base_price
            product_unit_cost[product_id] = unit_cost

        conn.execute(insert(Product).values(products_values))

        # -----------------------
        # Dimensions: promotions
        # -----------------------
        promotion_types = ["percentage", "fixed_amount", "bogo"]
        promotions_values: List[Dict[str, Any]] = []
        promotion_category_affinity: Dict[int, int] = {}
        promotion_discount_type: Dict[int, str] = {}
        promotion_discount_value: Dict[int, Decimal] = {}
        promotion_start_end: Dict[int, Tuple[date, date]] = {}

        for promo_idx in range(scales.promotions):
            promo_id = promo_idx + 1
            promo_type = rng.choice(promotion_types)

            # Choose a category affinity so promotions meaningfully impact discount/margin/returns.
            affinity_category = rng.choice(list(category_price_mult.keys()))
            promotion_category_affinity[promo_id] = affinity_category

            if promo_type == "percentage":
                discount_value = Decimal(str(rng.uniform(5.0, 25.0))).quantize(Decimal("0.0001"))
            elif promo_type == "fixed_amount":
                discount_value = Decimal(str(rng.uniform(2.0, 12.0))).quantize(Decimal("0.0001"))
            else:
                # BOGO: represent as a "percent-of-free" proxy.
                discount_value = Decimal(str(rng.uniform(25.0, 60.0))).quantize(Decimal("0.0001"))

            # Pick an active window within the overall date span.
            window_start_offset = rng.randint(0, max(0, len(all_dates) - 21))
            window_end_offset = min(window_start_offset + rng.randint(7, 21), len(all_dates) - 1)
            start_d = all_dates[window_start_offset]
            end_d = all_dates[window_end_offset]

            promotions_values.append(
                {
                    "id": promo_id,
                    "promotion_name": f"Promo #{promo_id} ({promo_type})",
                    "discount_type": promo_type,
                    "discount_value": discount_value,
                    "start_date": start_d,
                    "end_date": end_d,
                    "is_active": True,
                }
            )
            promotion_discount_type[promo_id] = promo_type
            promotion_discount_value[promo_id] = discount_value
            promotion_start_end[promo_id] = (start_d, end_d)

        conn.execute(insert(Promotion).values(promotions_values))

        # -----------------------
        # Facts: sales + returns
        # -----------------------
        store_ids = list(range(1, scales.stores + 1))
        store_weights = [1.0 + rng.random() * 0.9 for _ in store_ids]
        store_risk_factor: Dict[int, float] = {
            sid: 0.75 + rng.random() * 0.65 for sid in store_ids
        }

        # Regional demand variation.
        store_demand_multiplier: Dict[int, float] = {}
        for sid in store_ids:
            region_id = store_region_id[sid]
            region_skew = region_product_demand_skews[region_id - 1]
            store_demand_multiplier[sid] = region_skew * store_risk_factor[sid]

        product_ids = list(range(1, scales.products + 1))
        product_weights = [product_popularity_weight[pid] for pid in product_ids]

        # Date weights based on seasonality.
        date_weights = [_seasonality_factor(d) for d in all_dates]
        date_to_index = {d: idx for idx, d in enumerate(all_dates)}
        active_promotions_by_date_index: List[List[int]] = []
        for d in all_dates:
            active_ids: List[int] = []
            for pid, (sd, ed) in promotion_start_end.items():
                if sd <= d <= ed:
                    active_ids.append(pid)
            active_promotions_by_date_index.append(active_ids)

        sale_chunk_size = 5000
        sale_id_counter = 1
        return_id_counter = 1

        sale_values_chunk: List[Dict[str, Any]] = []
        return_values_chunk: List[Dict[str, Any]] = []

        # Return reason weights (base). Category will bias these slightly.
        return_reason_options: List[Tuple[str, float]] = [
            ("Damaged", 0.22),
            ("Defective", 0.18),
            ("Wrong Item", 0.10),
            ("Not as Described", 0.20),
            ("Changed Mind", 0.30),
        ]

        def _choose_return_reason(category_id: int) -> str:
            weights: List[float] = []
            for reason, w in return_reason_options:
                if category_id in {3, 2}:  # Electronics/Apparel in our initial category list
                    if reason in {"Defective", "Damaged"}:
                        weights.append(w * 1.35)
                    else:
                        weights.append(w)
                else:
                    weights.append(w)
            reasons = [r for r, _ in return_reason_options]
            return rng.choices(reasons, weights=weights, k=1)[0]

        def _compute_discount_total(
            promo_id: int,
            promo_type: str,
            promo_value: Decimal,
            gross_revenue: Decimal,
            quantity_sold: int,
        ) -> Decimal:
            if promo_type == "percentage":
                # promo_value is a percent (e.g., 15.0000 == 15%).
                disc = gross_revenue * promo_value / Decimal(100)
            elif promo_type == "fixed_amount":
                # promo_value is a per-unit discount.
                disc = promo_value * Decimal(quantity_sold)
            else:
                # BOGO: treat promo_value as percent-of-free, apply a factor ~0.5.
                disc = gross_revenue * (promo_value / Decimal(100)) / Decimal(2)
            disc = disc.quantize(Decimal("0.01"))
            # Avoid absurd discounts (portfolio realism).
            if disc > gross_revenue * Decimal("0.70"):
                disc = (gross_revenue * Decimal("0.70")).quantize(Decimal("0.01"))
            return disc

        # Generate sales and returns in deterministic chunks.
        for _ in range(scales.sales_rows):
            d = rng.choices(all_dates, weights=date_weights, k=1)[0]
            d_idx = date_to_index[d]
            sid = _weighted_choice(rng, store_ids, store_weights)
            pid = _weighted_choice(rng, product_ids, product_weights)

            category_id = product_category_id[pid]
            base_price = product_base_price[pid]
            unit_cost = product_unit_cost[pid]

            price_mult = category_price_mult.get(category_id, 1.0)
            qty_lambda = (
                product_popularity_weight[pid]
                * store_demand_multiplier[sid]
                * _seasonality_factor(d)
                * price_mult
                / max(1.0, float(base_price))
                * 180.0
            )

            qty = max(1, min(18, int(rng.gauss(qty_lambda, max(0.6, qty_lambda * 0.22)))))
            qty = int(max(1, qty))

            active_promos = active_promotions_by_date_index[d_idx]
            promo_id: Optional[int] = None
            promo_type: Optional[str] = None
            promo_value: Optional[Decimal] = None

            # Prefer promos whose affinity matches this product category.
            matching_promos: List[int] = [
                p for p in active_promos if promotion_category_affinity.get(p) == category_id
            ]

            if matching_promos:
                if rng.random() < 0.28:
                    promo_id = rng.choice(matching_promos)
            elif active_promos:
                if rng.random() < 0.06:
                    promo_id = rng.choice(active_promos)

            if promo_id is not None:
                promo_type = promotion_discount_type[promo_id]
                promo_value = promotion_discount_value[promo_id]

            # If a promo applies, demand uplifts (revenue up) but margin can fall.
            uplift = 0.0
            if promo_type is not None:
                if promo_type == "percentage":
                    uplift = rng.uniform(0.05, 0.16)
                elif promo_type == "fixed_amount":
                    uplift = rng.uniform(0.03, 0.12)
                else:
                    uplift = rng.uniform(0.06, 0.22)
            if uplift > 0:
                qty = max(1, min(20, int(round(qty * (1.0 + uplift) + rng.gauss(0, 0.7)))))

            unit_price = (base_price * Decimal(str(0.9 + rng.random() * 0.25))).quantize(
                Decimal("0.01")
            )

            gross_revenue = (unit_price * qty).quantize(Decimal("0.01"))
            discount_amount = Decimal("0.00")
            if promo_id is not None and promo_type is not None and promo_value is not None:
                discount_amount = _compute_discount_total(
                    promo_id=promo_id,
                    promo_type=promo_type,
                    promo_value=promo_value,
                    gross_revenue=gross_revenue,
                    quantity_sold=qty,
                )

            net_revenue = (gross_revenue - discount_amount).quantize(Decimal("0.01"))
            gross_margin = ((unit_price - unit_cost) * qty - discount_amount).quantize(
                Decimal("0.01")
            )

            sale_row: Dict[str, Any] = {
                "id": sale_id_counter,
                "sale_date": d,
                "store_id": sid,
                "product_id": pid,
                "promotion_id": promo_id,
                "quantity_sold": qty,
                "unit_price": unit_price,
                "discount_amount": discount_amount,
                "gross_revenue": gross_revenue,
                "net_revenue": net_revenue,
                "gross_margin": gross_margin,
            }

            sale_values_chunk.append(sale_row)

            # Returns: product-specific behavior, slightly higher during promos.
            return_probability = product_return_rate[pid]
            if promo_id is not None:
                return_probability *= 1.18
            return_probability *= 0.72  # keep returns realistic (~3-7%)
            return_probability *= 1.0 + (store_risk_factor[sid] - 0.75) * 0.08
            return_probability = min(return_probability, 0.25)

            if rng.random() < return_probability:
                if qty == 1:
                    return_qty = 1
                else:
                    # Higher-return products tend to return a larger fraction.
                    q_frac_base = rng.uniform(0.12, 0.38)
                    if product_return_rate[pid] > scales.return_rate_base * 1.35:
                        q_frac_base += rng.uniform(0.05, 0.18)
                    return_qty = max(1, min(qty, int(round(qty * q_frac_base + rng.gauss(0, 0.6)))))

                discount_per_unit = (discount_amount / qty) if qty > 0 else Decimal("0.00")
                refund_amount = (unit_price * return_qty - discount_per_unit * return_qty).quantize(
                    Decimal("0.01")
                )

                return_values_chunk.append(
                    {
                        "id": return_id_counter,
                        "return_date": d,
                        "sale_id": sale_id_counter,
                        "store_id": sid,
                        "product_id": pid,
                        "return_quantity": return_qty,
                        "return_reason": _choose_return_reason(category_id),
                        "refund_amount": refund_amount,
                    }
                )
                return_id_counter += 1

            sale_id_counter += 1

            if len(sale_values_chunk) >= sale_chunk_size:
                conn.execute(insert(Sale).values(sale_values_chunk))
                if return_values_chunk:
                    conn.execute(insert(Return).values(return_values_chunk))
                sale_values_chunk = []
                return_values_chunk = []

        # Insert any remaining sale rows.
        if sale_values_chunk:
            conn.execute(insert(Sale).values(sale_values_chunk))
            if return_values_chunk:
                conn.execute(insert(Return).values(return_values_chunk))

        # -----------------------
        # Inventory snapshots + replenishment orders
        # -----------------------
        inventory_id_counter = 1
        order_id_counter = 1

        inv_chunk_size = 10000
        order_chunk_size = 5000
        inventory_values_chunk: List[Dict[str, Any]] = []
        order_values_chunk: List[Dict[str, Any]] = []

        assortment_size_per_store = max(60, int(scales.products * scales.assortment_fraction))

        for sid in store_ids:
            # Choose a store assortment deterministically (sampling with replacement + de-dupe).
            chosen: set[int] = set()
            while len(chosen) < assortment_size_per_store:
                pid = _weighted_choice(rng, product_ids, product_weights)
                chosen.add(pid)

            for pid in sorted(chosen):
                supplier_id = product_supplier_id[pid]
                lead_days = supplier_lead_time_days[supplier_id]
                category_id = product_category_id[pid]

                base_price = product_base_price[pid]
                # Inventory demand estimate from popularity + regional demand + seasonality.
                avg_daily_units = (
                    product_popularity_weight[pid]
                    * store_demand_multiplier[sid]
                    * category_price_mult.get(category_id, 1.0)
                    / max(1.0, float(base_price))
                    * 9.0
                )
                avg_daily_units = max(0.2, avg_daily_units)

                reorder_point = max(2, int(round(avg_daily_units * lead_days * 0.9)))
                target_stock_level = max(reorder_point + 5, int(round(avg_daily_units * lead_days * 2.4)))

                # Risk: high-return + risky stores + chronic-delay suppliers -> lower stock more often.
                supplier_chronic = supplier_id in chronic_supplier_ids
                risk_score = (
                    (store_risk_factor[sid] - 0.75) * 1.2
                    + product_return_rate[pid] * 2.4
                    + (0.35 if supplier_chronic else 0.0)
                )
                chronic_stockout = rng.random() < min(0.65, 0.15 + risk_score * 0.18)

                # Some SKUs are naturally "tight" in this synthetic dataset.
                tight_sku = rng.random() < min(0.40, 0.10 + product_return_rate[pid] * 1.8)

                for sd in snapshot_dates:
                    season_factor = _seasonality_factor(sd)
                    target_adj = target_stock_level * (1.0 + 0.08 * (season_factor - 1.0))

                    # Decide whether this snapshot hits a low-stock event.
                    low_prob = 0.12
                    if chronic_stockout:
                        low_prob += 0.35
                    if tight_sku:
                        low_prob += 0.10
                    if supplier_chronic:
                        low_prob += 0.08

                    if rng.random() < low_prob:
                        # Stock dips below reorder point.
                        dip_depth = rng.randint(0, max(1, int(reorder_point * (0.15 + rng.random() * 0.35))))
                        stock_on_hand = max(0, reorder_point - dip_depth)
                    else:
                        # Stock around target, with mild variability.
                        spread = max(1, int(target_adj * (0.15 + rng.random() * 0.25)))
                        stock_on_hand = max(
                            0,
                            int(round(target_adj - rng.random() * spread + rng.gauss(0, max(1, spread * 0.05)))),
                        )

                    inventory_values_chunk.append(
                        {
                            "id": inventory_id_counter,
                            "snapshot_date": sd,
                            "store_id": sid,
                            "product_id": pid,
                            "stock_on_hand": stock_on_hand,
                            "reorder_point": reorder_point,
                            "target_stock_level": target_stock_level,
                        }
                    )
                    inventory_id_counter += 1

                    # Create replenishment orders when stock is near/below reorder point.
                    order_trigger_prob = 0.25
                    if stock_on_hand <= reorder_point:
                        order_trigger_prob = 0.55
                    elif stock_on_hand <= int(reorder_point * 1.05):
                        order_trigger_prob = 0.35

                    # Chronic suppliers are more likely to generate late deliveries, affecting risk.
                    if rng.random() < order_trigger_prob and stock_on_hand <= int(reorder_point * 1.05):
                        expected_delivery = sd + timedelta(days=lead_days)
                        if supplier_chronic:
                            delay_days = int(
                                rng.triangular(0, max(1, lead_days // 2), lead_days + 10)
                            )
                        else:
                            delay_days = int(rng.triangular(0, 2, 9))
                            if rng.random() < 0.10:
                                delay_days += rng.randint(1, 8)

                        expected_delivery = expected_delivery
                        actual_delivery = expected_delivery + timedelta(days=delay_days)

                        ordered_quantity = max(1, int(round(target_stock_level - stock_on_hand + rng.randint(0, 10))))
                        if supplier_chronic and delay_days > lead_days // 2:
                            fill_rate = rng.uniform(0.55, 0.9)
                        else:
                            fill_rate = rng.uniform(0.75, 1.0)
                        received_quantity = max(
                            0, min(ordered_quantity, int(round(ordered_quantity * fill_rate)))
                        )

                        order_values_chunk.append(
                            {
                                "id": order_id_counter,
                                "expected_delivery_date": expected_delivery,
                                "actual_delivery_date": actual_delivery,
                                "delay_days": delay_days,
                                "store_id": sid,
                                "supplier_id": supplier_id,
                                "product_id": pid,
                                "ordered_quantity": ordered_quantity,
                                "received_quantity": received_quantity,
                            }
                        )
                        order_id_counter += 1

                    if len(inventory_values_chunk) >= inv_chunk_size:
                        conn.execute(insert(InventorySnapshot).values(inventory_values_chunk))
                        inventory_values_chunk = []

                    if len(order_values_chunk) >= order_chunk_size:
                        conn.execute(insert(ReplenishmentOrder).values(order_values_chunk))
                        order_values_chunk = []

        if inventory_values_chunk:
            conn.execute(insert(InventorySnapshot).values(inventory_values_chunk))
        if order_values_chunk:
            conn.execute(insert(ReplenishmentOrder).values(order_values_chunk))

        return _count_rows(conn)


def run_seed_from_env() -> Dict[str, int]:
    engine = sa.create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    reset = _env_bool("SEED_RESET", True)
    return seed_retail_analytics(engine, reset=reset)

