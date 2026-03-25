from __future__ import annotations

from typing import Dict, Literal, Optional, Tuple

from sqlalchemy import text


SQLGrain = Literal["day", "week", "month"]


# A central catalog of analyst-grade SQL analyses.
# Each entry is parameterized with named placeholders so the service layer can pass values safely.
ANALYST_ANALYSIS_QUERIES: Dict[
    str, Dict[str, str]
] = {
    # Revenue
    "revenue_by_day": {"grain": "day"},
    "revenue_by_week": {"grain": "week"},
    "revenue_by_month": {"grain": "month"},
    # Margin
    "gross_margin_by_category": {},
    "gross_margin_by_store": {},
    "gross_margin_by_product": {},
    # Discount / Promo
    "discount_impact": {},
    "promotion_effectiveness": {},
    # Inventory
    "stockout_risk_ranking": {},
    "products_close_to_reorder_point": {},
    "sell_through_rate": {},
    # Returns
    "return_rate_by_category": {},
    "return_rate_by_product": {},
    # Suppliers
    "supplier_delay_analysis": {},
    # Performance
    "top_products": {},
    "bottom_products": {},
    "store_vs_region_comparison": {},
    # Time comparisons
    "month_over_month_revenue_change": {},
    "week_over_week_revenue_change": {},
    "category_contribution_to_total_revenue": {},
    # Margin/volume/returns cuts
    "low_margin_high_volume_products": {},
    "high_returns_low_margin_products": {},
}


def get_analysis_sql(name: str) -> str:
    """
    Return the SQL string for a named analysis.

    The SQL is written for PostgreSQL and uses named placeholders:
    - :start_date, :end_date
    - optional :region_id, :store_id, :category_id, :product_id, etc.
    - optional :top_n, :margin_threshold, :volume_threshold, :return_rate_threshold, :as_of_date
    """

    if name == "revenue_by_day":
        return _revenue_by_period_sql("day")
    if name == "revenue_by_week":
        return _revenue_by_period_sql("week")
    if name == "revenue_by_month":
        return _revenue_by_period_sql("month")

    if name == "gross_margin_by_category":
        return _gross_margin_by("categories")
    if name == "gross_margin_by_store":
        return _gross_margin_by("stores")
    if name == "gross_margin_by_product":
        return _gross_margin_by("products")

    if name == "discount_impact":
        return _discount_impact_sql()
    if name == "promotion_effectiveness":
        return _promotion_effectiveness_sql()

    if name == "stockout_risk_ranking":
        return _stockout_risk_ranking_sql()
    if name == "products_close_to_reorder_point":
        return _products_close_to_reorder_point_sql()
    if name == "sell_through_rate":
        return _sell_through_rate_sql()

    if name == "return_rate_by_category":
        return _return_rate_by("categories")
    if name == "return_rate_by_product":
        return _return_rate_by("products")

    if name == "supplier_delay_analysis":
        return _supplier_delay_analysis_sql()

    if name == "top_products":
        return _top_bottom_products_sql(direction="top")
    if name == "bottom_products":
        return _top_bottom_products_sql(direction="bottom")

    if name == "store_vs_region_comparison":
        return _store_vs_region_comparison_sql()

    if name == "month_over_month_revenue_change":
        return _period_over_period_sql(grain="month")
    if name == "week_over_week_revenue_change":
        return _period_over_period_sql(grain="week")

    if name == "category_contribution_to_total_revenue":
        return _category_contribution_sql()

    if name == "low_margin_high_volume_products":
        return _low_margin_high_volume_sql()
    if name == "high_returns_low_margin_products":
        return _high_returns_low_margin_sql()

    raise KeyError(f"Unknown analysis name: {name}")


def _revenue_by_period_sql(grain: SQLGrain) -> str:
    # Revenue by day/week/month (net revenue).
    # We parameterize filters using optional IDs.
    period_expr = {
        "day": "s.sale_date",
        "week": "date_trunc('week', s.sale_date)::date",
        "month": "date_trunc('month', s.sale_date)::date",
    }[grain]

    return f"""
-- Revenue by {grain}
WITH base AS (
  SELECT
    {period_expr} AS period_date,
    s.sale_date,
    s.store_id,
    s.product_id,
    s.promotion_id,
    s.net_revenue
  FROM sales s
  JOIN products p ON p.id = s.product_id
  JOIN categories c ON c.id = p.category_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:store_id IS NULL OR s.store_id = :store_id)
    AND (:category_id IS NULL OR c.id = :category_id)
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st
      WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
)
SELECT
  period_date,
  SUM(net_revenue) AS net_revenue,
  COUNT(*) AS sale_rows
FROM base
GROUP BY 1
ORDER BY 1;
""".strip()


def _gross_margin_by(dimension_table: Literal["categories", "stores", "products"]) -> str:
    # Gross margin aggregation with margin rate for interview-friendly interpretation.
    if dimension_table == "categories":
        join = "JOIN categories d ON d.id = p.category_id"
        select_name = "d.category_name AS dimension_name"
        group_key = "d.category_name"
        id_col = "d.id"
        optional_filter = "(:category_id IS NULL OR d.id = :category_id)"
    elif dimension_table == "stores":
        join = "JOIN stores d ON d.id = s.store_id"
        select_name = "d.store_name AS dimension_name"
        group_key = "d.store_name"
        id_col = "d.id"
        optional_filter = "(:store_id IS NULL OR d.id = :store_id)"
    else:
        join = "JOIN products d ON d.id = s.product_id"
        select_name = "d.product_name AS dimension_name"
        group_key = "d.product_name"
        id_col = "d.id"
        optional_filter = "(:product_id IS NULL OR d.id = :product_id)"

    return f"""
-- Gross margin by {dimension_table}
WITH base AS (
  SELECT
    {select_name},
    s.gross_revenue,
    s.gross_margin
  FROM sales s
  JOIN products p ON p.id = s.product_id
  {join}
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
)
SELECT
  dimension_name,
  SUM(gross_revenue) AS gross_revenue,
  SUM(gross_margin) AS gross_margin,
  (SUM(gross_margin) / NULLIF(SUM(gross_revenue), 0))::numeric(10,4) AS gross_margin_rate
FROM base
GROUP BY 1
HAVING SUM(gross_revenue) > 0
ORDER BY gross_margin DESC
LIMIT :top_n;
""".strip()


def _discount_impact_sql() -> str:
    # Discount impact: compare promo vs non-promo and discount rate relationship.
    return """
-- Discount impact analysis (promo vs non-promo)
WITH labeled AS (
  SELECT
    CASE WHEN promotion_id IS NULL THEN 'non_promo' ELSE 'promo' END AS promo_flag,
    discount_amount,
    gross_revenue,
    net_revenue,
    gross_margin
  FROM sales
  WHERE sale_date BETWEEN :start_date AND :end_date
    AND (:store_id IS NULL OR store_id = :store_id)
    AND (:category_id IS NULL OR product_id IN (
      SELECT p.id FROM products p WHERE p.category_id = :category_id
    ))
),
bucketed AS (
  SELECT
    promo_flag,
    -- Bucket discount rate to make interpretation easier in results.
    NTILE(4) OVER (PARTITION BY promo_flag ORDER BY discount_amount / NULLIF(gross_revenue, 0)) AS discount_bucket,
    gross_revenue,
    net_revenue,
    gross_margin,
    discount_amount
  FROM labeled
)
SELECT
  promo_flag,
  discount_bucket,
  COUNT(*) AS sale_rows,
  AVG(discount_amount / NULLIF(gross_revenue, 0)) AS avg_discount_rate,
  SUM(net_revenue) AS net_revenue,
  SUM(gross_margin) AS gross_margin,
  (SUM(gross_margin) / NULLIF(SUM(gross_revenue), 0))::numeric(10,4) AS gross_margin_rate
FROM bucketed
GROUP BY 1,2
ORDER BY promo_flag, discount_bucket;
""".strip()


def _promotion_effectiveness_sql() -> str:
    # Promo effectiveness: compute promo-period metrics and preceding-period metrics per promotion.
    # Uses CTE + window-ish logic (length derived via date arithmetic).
    return """
-- Promotion effectiveness (promo window vs prior window)
WITH promo_windows AS (
  SELECT
    p.id AS promotion_id,
    p.promotion_name,
    p.discount_type,
    p.discount_value,
    p.start_date,
    p.end_date,
    (p.end_date - p.start_date) AS window_days
  FROM promotions p
  WHERE p.start_date <= :end_date
    AND p.end_date >= :start_date
),
sales_in_windows AS (
  SELECT
    pw.promotion_id,
    pw.promotion_name,
    pw.discount_type,
    pw.discount_value,
    s.sale_date,
    s.net_revenue,
    s.gross_margin
  FROM promo_windows pw
  JOIN sales s
    ON s.promotion_id = pw.promotion_id
   AND (
     -- Promo window
     s.sale_date BETWEEN pw.start_date AND pw.end_date
     OR
     -- Prior window of identical length immediately preceding the promo start
     s.sale_date BETWEEN (pw.start_date - pw.window_days) AND (pw.start_date - INTERVAL '1 day')
   )
  WHERE s.sale_date BETWEEN :start_date AND :end_date
),
period_sums AS (
  SELECT
    promotion_id,
    promotion_name,
    discount_type,
    discount_value,
    CASE
      WHEN sale_date BETWEEN start_date AND end_date THEN 'promo'
      ELSE 'prior'
    END AS period_flag,
    SUM(net_revenue) AS period_net_revenue,
    SUM(gross_margin) AS period_gross_margin
  FROM (
    SELECT
      siw.*,
      pw.start_date,
      pw.end_date
    FROM sales_in_windows siw
    JOIN promo_windows pw ON pw.promotion_id = siw.promotion_id
  ) x
  GROUP BY 1,2,3,4,5
),
pivoted AS (
  SELECT
    promotion_id,
    promotion_name,
    discount_type,
    discount_value,
    MAX(period_net_revenue) FILTER (WHERE period_flag='promo') AS promo_net_revenue,
    MAX(period_net_revenue) FILTER (WHERE period_flag='prior') AS prior_net_revenue,
    MAX(period_gross_margin) FILTER (WHERE period_flag='promo') AS promo_gross_margin,
    MAX(period_gross_margin) FILTER (WHERE period_flag='prior') AS prior_gross_margin
  FROM period_sums
  GROUP BY 1,2,3,4
)
SELECT
  promotion_name,
  discount_type,
  discount_value,
  prior_net_revenue,
  promo_net_revenue,
  (promo_net_revenue - prior_net_revenue) AS net_revenue_lift,
  (promo_gross_margin - prior_gross_margin) AS gross_margin_change,
  CASE
    WHEN prior_net_revenue = 0 THEN NULL
    ELSE (promo_net_revenue - prior_net_revenue) / prior_net_revenue
  END::numeric(10,4) AS net_revenue_lift_rate
FROM pivoted
ORDER BY net_revenue_lift DESC NULLS LAST
LIMIT :top_n;
""".strip()


def _stockout_risk_ranking_sql() -> str:
    # Risk score: fraction of snapshot dates where stock_on_hand < reorder_point.
    return """
-- Stockout risk ranking (store/product)
WITH base AS (
  SELECT
    inv.store_id,
    inv.product_id,
    COUNT(*) AS snapshot_rows,
    COUNT(*) FILTER (WHERE inv.stock_on_hand < inv.reorder_point) AS low_stock_rows
  FROM inventory_snapshots inv
  JOIN stores st ON st.id = inv.store_id
  JOIN products p ON p.id = inv.product_id
  WHERE inv.snapshot_date BETWEEN :start_date AND :end_date
    AND (:region_id IS NULL OR st.region_id = :region_id)
    AND (:category_id IS NULL OR p.category_id = :category_id)
  GROUP BY 1,2
),
scored AS (
  SELECT
    store_id,
    product_id,
    low_stock_rows::numeric / NULLIF(snapshot_rows,0) AS low_stock_rate
  FROM base
)
SELECT
  st.store_name,
  p.product_name,
  (s.low_stock_rate)::numeric(10,4) AS low_stock_rate,
  RANK() OVER (ORDER BY s.low_stock_rate DESC) AS risk_rank
FROM scored s
JOIN stores st ON st.id = s.store_id
JOIN products p ON p.id = s.product_id
ORDER BY risk_rank
LIMIT :top_n;
""".strip()


def _products_close_to_reorder_point_sql() -> str:
    # For each store/product, pick the latest snapshot <= :as_of_date and filter those near reorder point.
    return """
-- Products close to reorder point (latest snapshot as of :as_of_date)
WITH latest AS (
  SELECT
    inv.*,
    ROW_NUMBER() OVER (
      PARTITION BY inv.store_id, inv.product_id
      ORDER BY inv.snapshot_date DESC, inv.snapshot_ts DESC
    ) AS rn
  FROM inventory_snapshots inv
  WHERE inv.snapshot_date <= :as_of_date
),
filtered AS (
  SELECT *
  FROM latest
  WHERE rn = 1
    AND stock_on_hand <= reorder_point
)
SELECT
  st.store_name,
  c.category_name,
  p.product_name,
  f.stock_on_hand,
  f.reorder_point,
  f.target_stock_level,
  (f.stock_on_hand::numeric / NULLIF(f.reorder_point,0))::numeric(10,4) AS stock_to_reorder_ratio
FROM filtered f
JOIN stores st ON st.id = f.store_id
JOIN products p ON p.id = f.product_id
JOIN categories c ON c.id = p.category_id
ORDER BY stock_to_reorder_ratio ASC, st.store_name, p.product_name
LIMIT :top_n;
""".strip()


def _sell_through_rate_sql() -> str:
    # Sell-through: quantity_sold in period divided by beginning inventory.
    # Uses snapshot as the "beginning inventory" baseline via latest snapshot <= start_date.
    return """
-- Sell-through rate (store/product)
WITH beginning AS (
  SELECT
    inv.store_id,
    inv.product_id,
    inv.stock_on_hand AS beginning_stock_on_hand,
    ROW_NUMBER() OVER (
      PARTITION BY inv.store_id, inv.product_id
      ORDER BY inv.snapshot_date DESC, inv.snapshot_ts DESC
    ) AS rn
  FROM inventory_snapshots inv
  WHERE inv.snapshot_date <= :start_date
),
begin_filtered AS (
  SELECT *
  FROM beginning
  WHERE rn = 1
),
period_sales AS (
  SELECT
    s.store_id,
    s.product_id,
    SUM(s.quantity_sold) AS quantity_sold,
    SUM(s.net_revenue) AS net_revenue
  FROM sales s
  WHERE s.sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1,2
)
SELECT
  st.store_name,
  p.product_name,
  bf.beginning_stock_on_hand,
  ps.quantity_sold,
  (ps.quantity_sold::numeric / NULLIF(bf.beginning_stock_on_hand,0))::numeric(10,4) AS sell_through_rate,
  ps.net_revenue
FROM begin_filtered bf
JOIN period_sales ps
  ON ps.store_id = bf.store_id AND ps.product_id = bf.product_id
JOIN stores st ON st.id = ps.store_id
JOIN products p ON p.id = ps.product_id
ORDER BY sell_through_rate DESC
LIMIT :top_n;
""".strip()


def _return_rate_by(dimension_table: Literal["categories", "products"]) -> str:
    # Return rate = sum(return_quantity) / sum(quantity_sold) for a period.
    if dimension_table == "categories":
        group_sel = "c.category_name AS dimension_name"
        joins = """
  JOIN products p ON p.id = s.product_id
  JOIN categories c ON c.id = p.category_id
        """
        group_by = "c.category_name"
        where_filter = "AND (:category_id IS NULL OR c.id = :category_id)"
    else:
        group_sel = "p.product_name AS dimension_name"
        joins = """
  JOIN products p ON p.id = s.product_id
        """
        group_by = "p.product_name"
        where_filter = "AND (:product_id IS NULL OR p.id = :product_id)"

    return f"""
-- Return rate by {dimension_table}
WITH base AS (
  SELECT
    {group_sel},
    SUM(s.quantity_sold) AS qty_sold,
    COALESCE(SUM(r.return_quantity), 0) AS qty_returned
  FROM sales s
  LEFT JOIN returns r ON r.sale_id = s.id
  {joins}
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:store_id IS NULL OR s.store_id = :store_id)
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
    {where_filter}
  GROUP BY 1
)
SELECT
  dimension_name,
  qty_sold,
  qty_returned,
  (qty_returned::numeric / NULLIF(qty_sold,0))::numeric(10,4) AS return_rate
FROM base
WHERE qty_sold > 0
ORDER BY return_rate DESC
LIMIT :top_n;
""".strip()


def _supplier_delay_analysis_sql() -> str:
    return """
-- Supplier delay analysis
WITH base AS (
  SELECT
    ro.supplier_id,
    AVG(ro.delay_days)::numeric(10,4) AS avg_delay_days,
    PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ro.delay_days) AS p90_delay_days,
    SUM(CASE WHEN ro.delay_days IS NULL OR ro.delay_days <= 0 THEN 1 ELSE 0 END)::numeric
      / NULLIF(COUNT(*),0) AS on_time_rate
  FROM replenishment_orders ro
  JOIN suppliers sup ON sup.id = ro.supplier_id
  WHERE ro.order_ts BETWEEN :start_date AND :end_date
    AND (:supplier_id IS NULL OR ro.supplier_id = :supplier_id)
  GROUP BY 1
)
SELECT
  sup.supplier_name,
  b.avg_delay_days,
  b.p90_delay_days,
  b.on_time_rate,
  ro_counts.order_count
FROM base b
JOIN suppliers sup ON sup.id = b.supplier_id
JOIN (
  SELECT supplier_id, COUNT(*) AS order_count
  FROM replenishment_orders
  WHERE order_ts BETWEEN :start_date AND :end_date
  GROUP BY 1
) ro_counts ON ro_counts.supplier_id = b.supplier_id
ORDER BY b.avg_delay_days DESC NULLS LAST
LIMIT :top_n;
""".strip()


def _top_bottom_products_sql(direction: Literal["top", "bottom"]) -> str:
    # Top/bottom by net_revenue with gross_margin_rate breakdown.
    order_dir = "DESC" if direction == "top" else "ASC"
    return f"""
-- {direction.capitalize()} performing products by net_revenue
WITH base AS (
  SELECT
    p.id AS product_id,
    p.product_name,
    SUM(s.net_revenue) AS net_revenue,
    SUM(s.gross_revenue) AS gross_revenue,
    SUM(s.gross_margin) AS gross_margin,
    SUM(s.quantity_sold) AS quantity_sold
  FROM sales s
  JOIN products p ON p.id = s.product_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:category_id IS NULL OR p.category_id = :category_id)
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
  GROUP BY 1,2
)
SELECT
  product_name,
  net_revenue,
  quantity_sold,
  gross_margin,
  (gross_margin::numeric / NULLIF(gross_revenue,0))::numeric(10,4) AS gross_margin_rate
FROM base
ORDER BY net_revenue {order_dir}
LIMIT :top_n;
""".strip()


def _store_vs_region_comparison_sql() -> str:
    # Compare store revenue to region average, using z-score-like deviation via percentile or ratio.
    return """
-- Store vs region comparison
WITH store_rev AS (
  SELECT
    st.id AS store_id,
    st.store_name,
    r.id AS region_id,
    r.region_name,
    SUM(s.net_revenue) AS net_revenue
  FROM sales s
  JOIN stores st ON st.id = s.store_id
  JOIN regions r ON r.id = st.region_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:category_id IS NULL OR s.product_id IN (
      SELECT p.id FROM products p WHERE p.category_id = :category_id
    ))
  GROUP BY 1,2,3,4
),
region_stats AS (
  SELECT
    region_id,
    AVG(net_revenue) AS region_avg_revenue,
    STDDEV_SAMP(net_revenue) AS region_rev_stddev
  FROM store_rev
  GROUP BY 1
),
scored AS (
  SELECT
    sr.*,
    rs.region_avg_revenue,
    rs.region_rev_stddev,
    (sr.net_revenue - rs.region_avg_revenue) / NULLIF(rs.region_rev_stddev, 0) AS revenue_z_score,
    (sr.net_revenue / NULLIF(rs.region_avg_revenue, 0)) AS revenue_vs_region_avg
  FROM store_rev sr
  JOIN region_stats rs ON rs.region_id = sr.region_id
)
SELECT
  region_name,
  store_name,
  net_revenue,
  revenue_vs_region_avg,
  revenue_z_score,
  RANK() OVER (PARTITION BY region_id ORDER BY net_revenue DESC) AS region_store_rank
FROM scored
WHERE (:region_id IS NULL OR region_id = :region_id)
ORDER BY region_name, region_store_rank
LIMIT :top_n;
""".strip()


def _period_over_period_sql(grain: Literal["week", "month"]) -> str:
    # Period-over-period revenue change using LAG.
    date_expr = (
        "date_trunc('month', sale_date)::date" if grain == "month" else "date_trunc('week', sale_date)::date"
    )
    return f"""
-- {grain.capitalize()} over {grain} revenue change (net revenue)
WITH monthly AS (
  SELECT
    {date_expr} AS period_date,
    SUM(net_revenue) AS net_revenue
  FROM sales
  WHERE sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1
),
with_lag AS (
  SELECT
    period_date,
    net_revenue,
    LAG(net_revenue) OVER (ORDER BY period_date) AS prior_net_revenue
  FROM monthly
)
SELECT
  period_date,
  net_revenue,
  prior_net_revenue,
  (net_revenue - prior_net_revenue) AS net_revenue_change,
  CASE
    WHEN prior_net_revenue IS NULL OR prior_net_revenue = 0 THEN NULL
    ELSE (net_revenue - prior_net_revenue) / prior_net_revenue
  END::numeric(10,4) AS net_revenue_change_rate
FROM with_lag
ORDER BY period_date;
""".strip()


def _category_contribution_sql() -> str:
    # Category contribution to total revenue for each month (share).
    return """
-- Category contribution to total revenue (monthly share)
WITH month_totals AS (
  SELECT
    date_trunc('month', s.sale_date)::date AS month_date,
    SUM(s.net_revenue) AS total_net_revenue
  FROM sales s
  WHERE s.sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1
),
category_totals AS (
  SELECT
    date_trunc('month', s.sale_date)::date AS month_date,
    c.category_name,
    SUM(s.net_revenue) AS category_net_revenue
  FROM sales s
  JOIN products p ON p.id = s.product_id
  JOIN categories c ON c.id = p.category_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1,2
),
shares AS (
  SELECT
    ct.month_date,
    ct.category_name,
    ct.category_net_revenue,
    mt.total_net_revenue,
    (ct.category_net_revenue / NULLIF(mt.total_net_revenue, 0))::numeric(10,4) AS revenue_share
  FROM category_totals ct
  JOIN month_totals mt ON mt.month_date = ct.month_date
)
SELECT
  month_date,
  category_name,
  category_net_revenue,
  revenue_share,
  RANK() OVER (PARTITION BY month_date ORDER BY revenue_share DESC) AS category_share_rank
FROM shares
ORDER BY month_date, category_share_rank
LIMIT :top_n;
""".strip()


def _low_margin_high_volume_sql() -> str:
    # Products with low gross margin rate and high volume.
    return """
-- Low-margin high-volume products
WITH base AS (
  SELECT
    p.id AS product_id,
    p.product_name,
    SUM(s.gross_revenue) AS gross_revenue,
    SUM(s.gross_margin) AS gross_margin,
    SUM(s.quantity_sold) AS quantity_sold,
    (SUM(s.gross_margin) / NULLIF(SUM(s.gross_revenue), 0))::numeric(10,6) AS gross_margin_rate
  FROM sales s
  JOIN products p ON p.id = s.product_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1,2
)
SELECT
  product_name,
  gross_margin_rate::numeric(10,4) AS gross_margin_rate,
  quantity_sold,
  gross_margin,
  gross_revenue,
  RANK() OVER (ORDER BY quantity_sold DESC) AS volume_rank
FROM base
WHERE gross_margin_rate <= :margin_threshold
  AND quantity_sold >= :volume_threshold
ORDER BY quantity_sold DESC, gross_margin_rate ASC
LIMIT :top_n;
""".strip()


def _high_returns_low_margin_sql() -> str:
    # Products with high return rate and low gross margin rate.
    return """
-- Products with high returns and low margin
WITH sales_base AS (
  SELECT
    s.product_id,
    SUM(s.quantity_sold) AS qty_sold,
    SUM(s.gross_revenue) AS gross_revenue,
    SUM(s.gross_margin) AS gross_margin
  FROM sales s
  WHERE s.sale_date BETWEEN :start_date AND :end_date
  GROUP BY 1
),
returns_base AS (
  SELECT
    r.product_id,
    SUM(r.return_quantity) AS qty_returned
  FROM returns r
  WHERE r.return_date BETWEEN :start_date AND :end_date
  GROUP BY 1
),
joined AS (
  SELECT
    sb.product_id,
    sb.qty_sold,
    COALESCE(rb.qty_returned, 0) AS qty_returned,
    sb.gross_revenue,
    sb.gross_margin,
    (sb.gross_margin / NULLIF(sb.gross_revenue, 0))::numeric(10,6) AS gross_margin_rate,
    (COALESCE(rb.qty_returned, 0) / NULLIF(sb.qty_sold, 0))::numeric(10,6) AS return_rate
  FROM sales_base sb
  LEFT JOIN returns_base rb ON rb.product_id = sb.product_id
)
SELECT
  p.product_name,
  return_rate::numeric(10,4) AS return_rate,
  gross_margin_rate::numeric(10,4) AS gross_margin_rate,
  qty_sold,
  qty_returned,
  gross_margin,
  gross_revenue
FROM joined j
JOIN products p ON p.id = j.product_id
WHERE j.return_rate >= :return_rate_threshold
  AND j.gross_margin_rate <= :margin_threshold
ORDER BY return_rate DESC, gross_margin_rate ASC
LIMIT :top_n;
""".strip()

