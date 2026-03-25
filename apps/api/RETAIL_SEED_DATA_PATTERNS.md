# Retail Seed Data Patterns

This project uses deterministic synthetic data to support realistic analyst-style SQL queries without requiring external datasets.

## Patterns intentionally added

## Sales behavior
- Seasonality across months (higher demand in Nov/Dec, moderate in summer) plus weekend uplift.
- Regional demand variation via per-store regional multipliers.
- Category-level pricing differences and margin “profiles” (some categories are consistently higher gross margin than others).
- Promotions that sometimes increase revenue volume (demand uplift) while typically reducing margin (discount reduces gross margin).

## Returns behavior
- Product-specific return propensities: some SKUs/categories are more return-prone than others.
- Promotions slightly increase return probability, so promotion effectiveness is not just about revenue lift.

## Inventory + replenishment behavior
- Inventory snapshots are generated across multiple dates for a realistic store assortments (not every store carries every SKU).
- Stockout risk is modeled by driving some store/SKU pairs to sit near or below `reorder_point` more often.
- Replenishment orders include a supplier delay distribution:
  - some suppliers are “chronic delay” suppliers with heavier delay tails
  - most deliveries are on time, but a meaningful fraction are late

## Determinism & reproducibility
- The seed uses a fixed random seed by default (`SEED_RANDOM_SEED`, default `42`).
- You can override dataset scale using environment variables (see below).

## Example SQL queries (interesting outputs)

### 1) Net revenue and gross margin by month and category
```sql
SELECT
  c.category_name,
  date_trunc('month', s.sale_date)::date AS month,
  SUM(s.net_revenue) AS net_revenue,
  SUM(s.gross_margin) AS gross_margin
FROM sales s
JOIN products p ON p.id = s.product_id
JOIN categories c ON c.id = p.category_id
GROUP BY 1, 2
ORDER BY 1, 2;
```

### 2) Discount impact: promo vs non-promo
```sql
SELECT
  CASE WHEN s.promotion_id IS NULL THEN 'non_promo' ELSE 'promo' END AS promo_flag,
  COUNT(*) AS sale_rows,
  AVG(s.discount_amount / NULLIF(s.gross_revenue, 0)) AS avg_discount_rate,
  SUM(s.net_revenue) AS net_revenue,
  SUM(s.gross_margin) AS gross_margin
FROM sales s
GROUP BY 1
ORDER BY 1;
```

### 3) Stockout risk by store + category (how many snapshot dates were low-stock)
```sql
SELECT
  st.store_name,
  c.category_name,
  COUNT(*) FILTER (WHERE inv.stock_on_hand < inv.reorder_point) AS low_stock_snapshot_dates
FROM inventory_snapshots inv
JOIN stores st ON st.id = inv.store_id
JOIN products p ON p.id = inv.product_id
JOIN categories c ON c.id = p.category_id
GROUP BY 1, 2
ORDER BY low_stock_snapshot_dates DESC
LIMIT 20;
```

### 4) Supplier delay analysis (average and P90)
```sql
SELECT
  sup.supplier_name,
  AVG(ro.delay_days) AS avg_delay_days,
  PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY ro.delay_days) AS p90_delay_days,
  COUNT(*) AS orders
FROM replenishment_orders ro
JOIN suppliers sup ON sup.id = ro.supplier_id
GROUP BY 1
ORDER BY avg_delay_days DESC;
```

### 5) Return rate by category
```sql
SELECT
  c.category_name,
  SUM(r.return_quantity)::numeric / NULLIF(SUM(s.quantity_sold), 0) AS return_rate
FROM returns r
JOIN sales s ON s.id = r.sale_id
JOIN products p ON p.id = r.product_id
JOIN categories c ON c.id = p.category_id
GROUP BY 1
ORDER BY return_rate DESC;
```

## Seed scale knobs (optional)
- `SEED_RESET` (default `true`)
- `SEED_RANDOM_SEED` (default `42`)
- `SEED_SALES_ROWS` (default `120000`)
- `SEED_PRODUCTS` (default `1200`)
- `SEED_SNAPSHOT_DATES` (default `12`)
- `SEED_ASSORTMENT_FRACTION` (default `0.35`)

If you want a faster local seed while testing, you can reduce:
- `SEED_SALES_ROWS` to `50000`
- `SEED_PRODUCTS` to `800`

