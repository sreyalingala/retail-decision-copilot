from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


def _col_idx(columns: List[str], name: str) -> Optional[int]:
    try:
        return columns.index(name)
    except ValueError:
        return None


def _pick_top_row(
    columns: List[str],
    rows: List[List[Any]],
    preferred_metrics: List[str],
) -> Tuple[Optional[List[Any]], Optional[str]]:
    if not rows:
        return None, None
    for m in preferred_metrics:
        if m in columns:
            return rows[0], m
    return rows[0], columns[0] if columns else None


def generate_business_explanation_and_actions(
    *,
    question: str,
    selected_analysis_name: str,
    selected_parameters: Dict[str, Any],
    columns: List[str],
    rows: List[List[Any]],
) -> Tuple[str, List[str]]:
    """
    Simple deterministic explanation + actions grounded in the returned result rows.
    """

    if not rows:
        return (
            "The analysis ran successfully but returned no rows for the selected filters.",
            ["Try widening the time window or removing restrictive filters."],
        )

    top_row, top_metric = _pick_top_row(
        columns,
        rows,
        preferred_metrics=[
            "net_revenue",
            "gross_margin",
            "gross_revenue",
            "gross_margin_rate",
            "return_rate",
            "low_stock_rate",
            "avg_delay_days",
            "net_revenue_lift",
            "sell_through_rate",
            "revenue_share",
        ],
    )
    top_value = None
    if top_metric and top_row is not None:
        idx = _col_idx(columns, top_metric)
        if idx is not None:
            top_value = top_row[idx]

    # Helpers to read common dimensions from the row.
    def get_first_of(names: List[str]) -> Optional[Any]:
        for n in names:
            idx = _col_idx(columns, n)
            if idx is not None:
                return top_row[idx]
        return None

    dimension_store = get_first_of(["store_name"])
    dimension_product = get_first_of(["product_name", "dimension_name"])
    dimension_category = get_first_of(["category_name", "dimension_name"])
    dimension_supplier = get_first_of(["supplier_name"])

    start_date = selected_parameters.get("start_date")
    end_date = selected_parameters.get("end_date")

    # Build explanation based on analysis.
    if selected_analysis_name in {"revenue_by_day", "revenue_by_week", "revenue_by_month"}:
        unit = selected_analysis_name.replace("revenue_by_", "")
        exp = f"Across {unit} between {start_date} and {end_date}, the top period by net revenue returned {top_value}."
        actions = [
            "Check whether promotional timing aligns with the highest-revenue periods.",
            "Investigate stores/products contributing most to the top period.",
        ]
        return exp, actions

    if selected_analysis_name in {
        "gross_margin_by_category",
        "gross_margin_by_store",
        "gross_margin_by_product",
    }:
        exp = (
            f"The analysis ranks profitability by gross margin. "
            f"The top result is {dimension_category or dimension_store or dimension_product} "
            f"with gross margin {top_value}."
        )
        actions = [
            "Review pricing and mix for the top-margin entity.",
            "Identify low-margin items that may be dragging overall profitability.",
        ]
        return exp, actions

    if selected_analysis_name == "stockout_risk_ranking":
        exp = (
            f"Stockout risk ranking identifies the highest low-stock rate pairs between {start_date} and {end_date}. "
            f"Top risk pair: {dimension_store or 'store'} / {dimension_product or 'product'} "
            f"with low_stock_rate={top_value}."
        )
        actions = [
            "Prioritize replenishment for the highest low-stock rate store/product pairs.",
            "Validate reorder_point and target_stock_level assumptions for these pairs.",
            "Cross-check with supplier delay performance for likely root causes.",
        ]
        return exp, actions

    if selected_analysis_name == "products_close_to_reorder_point":
        exp = (
            "This view shows products closest to (or below) reorder point using the latest snapshot as-of the provided date. "
            f"The most urgent item returned in this result set has stock_on_hand-to-reorder ratio={top_value}."
        )
        actions = [
            "Create replenishment actions for items at/below reorder point.",
            "Confirm expected inventory arrival dates before approving ordering volumes.",
        ]
        return exp, actions

    if selected_analysis_name == "supplier_delay_analysis":
        exp = (
            f"Supplier delay analysis highlights vendors with the highest average delay in the selected order window. "
            f"Top supplier: {dimension_supplier or 'supplier'} with avg_delay_days={top_value}."
        )
        actions = [
            "Consider increasing safety stock for chronically delayed suppliers.",
            "Investigate carrier/process factors driving delay and enforce SLA checks.",
        ]
        return exp, actions

    if selected_analysis_name in {"return_rate_by_category", "return_rate_by_product"}:
        exp = (
            "Return rate analysis estimates how frequently customers return items relative to units sold. "
            f"Top result has return_rate={top_value} for {dimension_category or dimension_product}."
        )
        actions = [
            "Review product quality drivers for the highest return-rate entity.",
            "Compare return behavior with promotions to detect discount-related effects.",
        ]
        return exp, actions

    if selected_analysis_name == "promotion_effectiveness":
        exp = (
            "Promotion effectiveness compares the net revenue in each promotion window to a prior comparable window. "
            f"The top promotion by net_revenue_lift has a lift of {top_value}."
        )
        actions = [
            "Retain promotions with positive lift and monitor gross margin erosion.",
            "Inspect which categories/products drive lift and returns during promo periods.",
        ]
        return exp, actions

    # Generic fallback for any other analysis name.
    exp = f"This analysis produced results for {selected_analysis_name}. Top value in the first row is {top_value}."
    actions = ["Review the top-ranked rows and drill into contributing stores/products."]  # grounded in output ordering
    return exp, actions

