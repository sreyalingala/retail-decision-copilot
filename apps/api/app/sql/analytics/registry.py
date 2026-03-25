from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from app.sql.analytics.queries import ANALYST_ANALYSIS_QUERIES


@dataclass(frozen=True)
class ParamSpec:
    name: str
    required: bool
    description: str


@dataclass(frozen=True)
class AnalysisSpec:
    analysis_name: str
    description: str
    parameters: List[ParamSpec]


def _p(name: str, required: bool, description: str) -> ParamSpec:
    return ParamSpec(name=name, required=required, description=description)


# Registry used by the analytics API to validate analysis_name and expose metadata.
ANALYSIS_CATALOG: Dict[str, AnalysisSpec] = {
    # Revenue
    "revenue_by_day": AnalysisSpec(
        analysis_name="revenue_by_day",
        description="Aggregate net revenue by sale day.",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("store_id", False, "Optional store filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    "revenue_by_week": AnalysisSpec(
        analysis_name="revenue_by_week",
        description="Aggregate net revenue by calendar week.",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("store_id", False, "Optional store filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    "revenue_by_month": AnalysisSpec(
        analysis_name="revenue_by_month",
        description="Aggregate net revenue by calendar month.",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("store_id", False, "Optional store filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    # Margin
    "gross_margin_by_category": AnalysisSpec(
        analysis_name="gross_margin_by_category",
        description="Gross margin and margin rate by category (ranked).",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Top N categories to return."),
        ],
    ),
    "gross_margin_by_store": AnalysisSpec(
        analysis_name="gross_margin_by_store",
        description="Gross margin and margin rate by store (ranked).",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("store_id", False, "Optional store filter."),
            _p("top_n", True, "Top N stores to return."),
        ],
    ),
    "gross_margin_by_product": AnalysisSpec(
        analysis_name="gross_margin_by_product",
        description="Gross margin and margin rate by product (ranked).",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("product_id", False, "Optional product filter."),
            _p("top_n", True, "Top N products to return."),
        ],
    ),
    # Discount / Promotions
    "discount_impact": AnalysisSpec(
        analysis_name="discount_impact",
        description="Discount impact buckets comparing promo vs non-promo sales.",
        parameters=[
            _p("start_date", True, "Start of date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of date window (YYYY-MM-DD)."),
            _p("store_id", False, "Optional store filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    "promotion_effectiveness": AnalysisSpec(
        analysis_name="promotion_effectiveness",
        description="Promotion effectiveness vs a prior comparable window (lift + margin change).",
        parameters=[
            _p("start_date", True, "Start of date window for candidate promos."),
            _p("end_date", True, "End of date window for candidate promos."),
            _p("top_n", True, "Top N promotions to return."),
        ],
    ),
    # Inventory
    "stockout_risk_ranking": AnalysisSpec(
        analysis_name="stockout_risk_ranking",
        description="Rank store/product pairs by fraction of snapshot dates below reorder point.",
        parameters=[
            _p("start_date", True, "Start of snapshot date window (YYYY-MM-DD)."),
            _p("end_date", True, "End of snapshot date window (YYYY-MM-DD)."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Top N risky pairs to return."),
        ],
    ),
    "products_close_to_reorder_point": AnalysisSpec(
        analysis_name="products_close_to_reorder_point",
        description="Show the latest snapshot as of a date for store/product pairs at/below reorder point.",
        parameters=[
            _p("as_of_date", True, "Snapshot cutoff date (YYYY-MM-DD)."),
            _p("top_n", True, "Top N products to return."),
        ],
    ),
    "sell_through_rate": AnalysisSpec(
        analysis_name="sell_through_rate",
        description="Sell-through rate computed as sales quantity divided by beginning stock (snapshot-based).",
        parameters=[
            _p("start_date", True, "Start of sales window (YYYY-MM-DD)."),
            _p("end_date", True, "End of sales window (YYYY-MM-DD)."),
            _p("top_n", True, "Top N sell-through products to return."),
        ],
    ),
    # Returns
    "return_rate_by_category": AnalysisSpec(
        analysis_name="return_rate_by_category",
        description="Return rate by category over a date window.",
        parameters=[
            _p("start_date", True, "Start of sales/returns window."),
            _p("end_date", True, "End of sales/returns window."),
            _p("store_id", False, "Optional store filter."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Top N categories by return rate."),
        ],
    ),
    "return_rate_by_product": AnalysisSpec(
        analysis_name="return_rate_by_product",
        description="Return rate by product over a date window.",
        parameters=[
            _p("start_date", True, "Start of sales/returns window."),
            _p("end_date", True, "End of sales/returns window."),
            _p("store_id", False, "Optional store filter."),
            _p("region_id", False, "Optional region filter."),
            _p("product_id", False, "Optional product filter."),
            _p("top_n", True, "Top N products by return rate."),
        ],
    ),
    # Suppliers
    "supplier_delay_analysis": AnalysisSpec(
        analysis_name="supplier_delay_analysis",
        description="Supplier delay analysis (avg delay, P90, and on-time fraction).",
        parameters=[
            _p("start_date", True, "Start of order timestamp window."),
            _p("end_date", True, "End of order timestamp window."),
            _p("supplier_id", False, "Optional supplier filter."),
            _p("top_n", True, "Top N suppliers by avg delay."),
        ],
    ),
    # Performance
    "top_products": AnalysisSpec(
        analysis_name="top_products",
        description="Top-performing products by net revenue over a window.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Top N products."),
        ],
    ),
    "bottom_products": AnalysisSpec(
        analysis_name="bottom_products",
        description="Bottom-performing products by net revenue over a window.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Bottom N products."),
        ],
    ),
    "store_vs_region_comparison": AnalysisSpec(
        analysis_name="store_vs_region_comparison",
        description="Compare each store’s revenue vs its region average (ranked).",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("region_id", False, "Optional region filter."),
            _p("category_id", False, "Optional category filter."),
            _p("top_n", True, "Top N rows to return."),
        ],
    ),
    # Time comparisons
    "month_over_month_revenue_change": AnalysisSpec(
        analysis_name="month_over_month_revenue_change",
        description="Month-over-month net revenue change using LAG.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    "week_over_week_revenue_change": AnalysisSpec(
        analysis_name="week_over_week_revenue_change",
        description="Week-over-week net revenue change using LAG.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("top_n", False, "Optional limit (not used by this query)."),
        ],
    ),
    "category_contribution_to_total_revenue": AnalysisSpec(
        analysis_name="category_contribution_to_total_revenue",
        description="Monthly revenue share by category (ranked).",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("top_n", True, "Top N category-month rows to return."),
        ],
    ),
    # Cuts
    "low_margin_high_volume_products": AnalysisSpec(
        analysis_name="low_margin_high_volume_products",
        description="Products with low margin rate and high volume.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("margin_threshold", True, "Max gross_margin_rate for inclusion (0-1)."),
            _p("volume_threshold", True, "Min quantity_sold for inclusion."),
            _p("top_n", True, "Top N products to return."),
        ],
    ),
    "high_returns_low_margin_products": AnalysisSpec(
        analysis_name="high_returns_low_margin_products",
        description="Products with high return rate and low gross margin rate.",
        parameters=[
            _p("start_date", True, "Start of sales window."),
            _p("end_date", True, "End of sales window."),
            _p("return_rate_threshold", True, "Min return_rate for inclusion (0-1)."),
            _p("margin_threshold", True, "Max gross_margin_rate for inclusion (0-1)."),
            _p("top_n", True, "Top N products to return."),
        ],
    ),
}


SUPPORTED_ANALYSES = sorted(set(ANALYST_ANALYSIS_QUERIES.keys()) | set(ANALYSIS_CATALOG.keys()))

