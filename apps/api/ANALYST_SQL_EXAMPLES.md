# Retail Analytics — Analyst-Grade SQL Examples

This file documents the reusable PostgreSQL SQL analytics layer implemented in:
- `apps/api/app/sql/analytics/queries.py`
- `apps/api/app/services/analytics/analytics_service.py`

Parameter naming convention (used across many queries):
- `:start_date`, `:end_date`
- optional `:region_id`, `:store_id`, `:category_id`, `:product_id`
- `:top_n` (ranking limits)
- thresholds like `:margin_threshold`, `:volume_threshold`, `:return_rate_threshold`
- inventory-based queries often use `:as_of_date`

Note: the dataset uses these key tables:
- `sales` (net_revenue, gross_revenue, gross_margin, discount_amount)
- `returns` (return_quantity, refund_amount)
- `inventory_snapshots` (stock_on_hand, reorder_point, target_stock_level)
- `replenishment_orders` (expected_delivery_date, actual_delivery_date, delay_days)
- dimensions: `regions`, `stores`, `categories`, `products`, `suppliers`, `promotions`

---

## 1) Revenue by day

What it answers: Net revenue aggregated for each sales day (with optional store/category/region filters).  
Why it matters: Helps spot daily anomalies, merchandising effects, and event-driven spikes.

```sql
-- Revenue by day
WITH base AS (
  SELECT
    s.sale_date AS period_date,
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
```

## 2) Revenue by week

What it answers: Net revenue aggregated by calendar week.  
Why it matters: Makes weekly ops performance and campaign pacing easy to compare.

```sql
-- Revenue by week
WITH base AS (
  SELECT
    date_trunc('week', s.sale_date)::date AS period_date,
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
```

## 3) Revenue by month

What it answers: Monthly net revenue trend.  
Why it matters: The base input for month-over-month comparisons and capacity planning.

```sql
-- Revenue by month
WITH base AS (
  SELECT
    date_trunc('month', s.sale_date)::date AS period_date,
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
```

---

## 4) Gross margin by category

What it answers: Total gross margin, gross margin rate, and top categories by margin.  
Why it matters: Identifies where profitability is actually coming from.

```sql
-- Gross margin by categories
WITH base AS (
  SELECT
    d.category_name AS dimension_name,
    s.gross_revenue,
    s.gross_margin
  FROM sales s
  JOIN products p ON p.id = s.product_id
  JOIN categories d ON d.id = p.category_id
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
```

## 5) Gross margin by store

What it answers: Margin contribution by store.  
Why it matters: Supports store-level playbooks (price/mix changes, merchandising shifts).

```sql
-- Gross margin by stores
WITH base AS (
  SELECT
    d.store_name AS dimension_name,
    s.gross_revenue,
    s.gross_margin
  FROM sales s
  JOIN products p ON p.id = s.product_id
  JOIN stores d ON d.id = s.store_id
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
```

## 6) Gross margin by product

What it answers: Product profitability with margin rate.  
Why it matters: Enables product rationalization and targeted promo planning.

```sql
-- Gross margin by products
WITH base AS (
  SELECT
    d.product_name AS dimension_name,
    s.gross_revenue,
    s.gross_margin
  FROM sales s
  JOIN products p ON p.id = s.product_id
  JOIN products d ON d.id = s.product_id
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
```

---

## 7) Discount impact analysis (promo vs non-promo)

What it answers: How discount rate buckets correlate with net revenue and margin, split into promo vs non-promo.  
Why it matters: Validates whether discounts drive profitable growth or erode margin.

```sql
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
    NTILE(4) OVER (
      PARTITION BY promo_flag
      ORDER BY discount_amount / NULLIF(gross_revenue, 0)
    ) AS discount_bucket,
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
```

## 8) Promotion effectiveness (promo vs prior window)

What it answers: For each promotion, whether net revenue and gross margin move up or down compared to the preceding comparable window.  
Why it matters: Helps marketing/merch decide which promos are worth running again.

```sql
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
     s.sale_date BETWEEN pw.start_date AND pw.end_date
     OR
     s.sale_date BETWEEN (pw.start_date - pw.window_days)
                      AND (pw.start_date - INTERVAL '1 day')
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
```

---

## 9) Stockout risk ranking (store/product)

What it answers: Ranks store/product pairs by the fraction of snapshots where stock was below reorder point.  
Why it matters: Prioritizes inventory interventions with data-backed risk.

```sql
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
```

## 10) Products close to reorder point (latest snapshot as-of date)

What it answers: Latest inventory snapshot per store/product as of a date, filtered where stock is at/below reorder point.  
Why it matters: Supports “what should we replenish right now?” decisions.

```sql
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
```

---

## 11) Sell-through rate (store/product)

What it answers: How much inventory was “sold through” during a period relative to beginning stock (from latest snapshot <= start date).  
Why it matters: Indicates demand strength and inventory efficiency.

```sql
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
```

---

## 12) Return rate by category

What it answers: Return rate computed as returned quantity / sold quantity for each category.  
Why it matters: Flags problematic categories and promo side-effects.

```sql
-- Return rate by categories
WITH base AS (
  SELECT
    c.category_name AS dimension_name,
    SUM(s.quantity_sold) AS qty_sold,
    COALESCE(SUM(r.return_quantity), 0) AS qty_returned
  FROM sales s
  LEFT JOIN returns r ON r.sale_id = s.id
  JOIN products p ON p.id = s.product_id
  JOIN categories c ON c.id = p.category_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:store_id IS NULL OR s.store_id = :store_id)
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
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
```

## 13) Return rate by product

What it answers: Return rates at SKU/product level, useful for targeted improvements.  
Why it matters: Helps reduce customer dissatisfaction and refund costs.

```sql
-- Return rate by products
WITH base AS (
  SELECT
    p.product_name AS dimension_name,
    SUM(s.quantity_sold) AS qty_sold,
    COALESCE(SUM(r.return_quantity), 0) AS qty_returned
  FROM sales s
  LEFT JOIN returns r ON r.sale_id = s.id
  JOIN products p ON p.id = s.product_id
  WHERE s.sale_date BETWEEN :start_date AND :end_date
    AND (:store_id IS NULL OR s.store_id = :store_id)
    AND (:region_id IS NULL OR EXISTS (
      SELECT 1 FROM stores st WHERE st.id = s.store_id AND st.region_id = :region_id
    ))
    AND (:product_id IS NULL OR p.id = :product_id)
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
```

---

## 14) Supplier delay analysis

What it answers: Supplier average delay, P90 delay, and on-time fraction.  
Why it matters: Supports procurement/vendor performance decisions.

```sql
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
```

---

## 15) Top performing products (by net revenue)

What it answers: Best products by net revenue with margin-rate context.  
Why it matters: Helps focus marketing and merchandising on proven winners.

```sql
-- Top performing products by net_revenue
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
ORDER BY net_revenue DESC
LIMIT :top_n;
```

## 16) Bottom performing products (by net revenue)

What it answers: Lowest net revenue products with margin-rate context.  
Why it matters: Pinpoints SKUs that may need assortment changes or better inventory planning.

```sql
-- Bottom performing products by net_revenue
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
ORDER BY net_revenue ASC
LIMIT :top_n;
```

---

## 17) Store vs region comparison

What it answers: Store net revenue vs region average (with deviation scoring) and store ranks within region.  
Why it matters: Distinguishes “region is down” effects from store-level under/over performance.

```sql
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
```

---

## 18) Month-over-month revenue change

What it answers: Monthly net revenue change and % change vs prior month using LAG.  
Why it matters: Produces the standard executive trend line for performance reviews.

```sql
-- Month over month revenue change (net revenue)
WITH monthly AS (
  SELECT
    date_trunc('month', sale_date)::date AS period_date,
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
```

## 19) Week-over-week revenue change

What it answers: Weekly revenue change and % change vs the prior week.  
Why it matters: Good for tracking promo impact and operational stability.

```sql
-- Week over week revenue change (net revenue)
WITH monthly AS (
  SELECT
    date_trunc('week', sale_date)::date AS period_date,
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
```

---

## 20) Category contribution to total revenue (monthly share)

What it answers: For each month, what share of total net revenue each category contributed.  
Why it matters: Shows whether growth is broad-based or driven by one category.

```sql
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
```

---

## 21) Low-margin high-volume products

What it answers: Products with low gross margin rate and high sales volume in the period.  
Why it matters: Identifies “attention SKUs” that may be profitable volume-wise but harmful to margin.

```sql
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
```

## 22) Products with high returns and low margin

What it answers: Products with return rate above a threshold and gross margin rate below a threshold.  
Why it matters: Flags SKUs where customer experience and profitability both deteriorate.

```sql
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
```

---

## SQL Patterns Highlight (what reviewers will notice)

- CTEs: nearly every query starts with a `WITH base AS (...)` or similar to keep logic readable.
- Window functions:
  - `RANK() OVER (...)` for rankings
  - `NTILE(4) OVER (...)` for discount buckets
  - `ROW_NUMBER() OVER (...)` to pick the latest inventory snapshot per store/product
  - `LAG(...) OVER (...)` for month-over-month and week-over-week change
- Time comparisons:
  - period aggregation (`date_trunc`) and `LAG` for trend deltas
  - promotion effectiveness comparing promo windows to preceding windows
- Margin logic:
  - gross margin rate computed as `SUM(gross_margin) / SUM(gross_revenue)`
  - explicit discount amount tracking for discount impact and promo effectiveness
- Inventory logic:
  - stockout risk uses snapshot-based low-stock counting: `COUNT(*) FILTER (WHERE ...)`
  - “products close to reorder point” picks the latest snapshot and compares `stock_on_hand` to `reorder_point`
  - sell-through uses snapshot-based beginning stock as the baseline

