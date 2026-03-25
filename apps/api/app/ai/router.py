from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, Optional

from app.ai.client import AnalysisRouteAIOutput, OpenAIRoutingClient
from app.core.config import settings
from app.sql.analytics.registry import ANALYSIS_CATALOG, AnalysisSpec, ParamSpec


DEFAULT_ANALYSIS_NAME = "revenue_by_month"
# Seed defaults (from seed_retail_analytics.py):
# start_date = 2025-10-01, snapshot_span_days = 120 => end_date = 2026-01-28
SEEDED_DEFAULT_START_DATE = date(2025, 10, 1)
SEEDED_DEFAULT_END_DATE = date(2026, 1, 28)


def _load_prompt() -> str:
    prompt_path = Path(__file__).parent / "prompts" / "analysis_router.md"
    return prompt_path.read_text(encoding="utf-8")


def _build_catalog_context() -> str:
    # Compact description for the model: each analysis with parameter list.
    # Keep it readable and deterministic.
    lines = [_load_prompt().strip(), "", "Catalog:"]
    for name, spec in sorted(ANALYSIS_CATALOG.items(), key=lambda x: x[0]):
        lines.append(f"- {name}: {spec.description}")
        if spec.parameters:
            for p in spec.parameters:
                req = "required" if p.required else "optional"
                lines.append(f"  - {p.name} ({req}): {p.description}")
    return "\n".join(lines)


def _default_params_for_analysis(analysis_name: str, *, end_date: date) -> Dict[str, Any]:
    spec = ANALYSIS_CATALOG[analysis_name]
    # Use deterministic seeded window so demo environments return rows.
    start_date = SEEDED_DEFAULT_START_DATE.isoformat()
    end_date_s = SEEDED_DEFAULT_END_DATE.isoformat()
    defaults: Dict[str, Any] = {}

    for p in spec.parameters:
        if p.name == "start_date":
            defaults[p.name] = start_date
        elif p.name == "end_date":
            defaults[p.name] = end_date_s
        elif p.name == "as_of_date":
            defaults[p.name] = end_date_s
        elif p.name == "top_n":
            defaults[p.name] = 10
        elif p.name == "margin_threshold":
            defaults[p.name] = 0.35
        elif p.name == "volume_threshold":
            defaults[p.name] = 100
        elif p.name == "return_rate_threshold":
            defaults[p.name] = 0.07
        elif p.name.endswith("_id"):
            defaults[p.name] = None
        else:
            # Generic safe default for unknown parameter kinds.
            defaults[p.name] = None

    return defaults


def _heuristic_route(question: str) -> Optional[Dict[str, Any]]:
    """
    Lightweight, interview-friendly routing heuristics for obvious intents.
    Runs before model call to reduce poor fallback behavior.
    """
    q = question.lower()

    promo_keywords = ["promotion", "promotions", "promo", "lift", "uplift", "discount effectiveness"]
    margin_keywords = ["margin", "hurt margin", "margin impact", "gross margin"]
    discount_keywords = ["discount", "discounts", "markdown"]

    if any(k in q for k in promo_keywords) and any(k in q for k in margin_keywords):
        analysis_name = "promotion_effectiveness"
        return {
            "analysis_name": analysis_name,
            "parameters": _default_params_for_analysis(
                analysis_name, end_date=SEEDED_DEFAULT_END_DATE
            ),
            "reasoning_short": "Heuristic routing: promotion + margin impact intent matched promotion_effectiveness.",
            "status": "heuristic",
        }

    if any(k in q for k in discount_keywords):
        analysis_name = "discount_impact"
        return {
            "analysis_name": analysis_name,
            "parameters": _default_params_for_analysis(
                analysis_name, end_date=SEEDED_DEFAULT_END_DATE
            ),
            "reasoning_short": "Heuristic routing: discount impact intent matched discount_impact.",
            "status": "heuristic",
        }

    return None


def _coerce_param_value(param: ParamSpec, value: Any) -> Any:
    if value is None:
        return None

    if param.name.endswith("_id"):
        try:
            return int(value)
        except Exception:
            return None

    if param.name in {"top_n", "volume_threshold"}:
        try:
            return int(value)
        except Exception:
            return None

    if param.name in {"margin_threshold", "return_rate_threshold"}:
        try:
            return float(value)
        except Exception:
            return None

    # date params
    if "date" in param.name:
        if not isinstance(value, str):
            return None
        try:
            parsed = date.fromisoformat(value)
            return parsed.isoformat()
        except Exception:
            return None

    # Fallback: keep as-is if scalar.
    if isinstance(value, (str, int, float, bool)):
        return value
    return None


def _validate_and_build_routing(
    ai_output: Any,
    *,
    question: str,
    end_date: date,
) -> Dict[str, Any]:
    """
    Strictly validate AI output against the supported analysis catalog.
    Returns a safe, catalog-aligned routing object.
    """

    fallback = _default_params_for_analysis(DEFAULT_ANALYSIS_NAME, end_date=end_date)
    fallback_reasoning = (
        "AI output invalid or unsupported; falling back to revenue_by_month with safe defaults."
    )

    if not isinstance(ai_output, AnalysisRouteAIOutput):
        return {
            "analysis_name": DEFAULT_ANALYSIS_NAME,
            "parameters": fallback,
            "reasoning_short": fallback_reasoning,
            "status": "fallback",
        }

    analysis_name = ai_output.analysis_name
    if analysis_name not in ANALYSIS_CATALOG:
        return {
            "analysis_name": DEFAULT_ANALYSIS_NAME,
            "parameters": fallback,
            "reasoning_short": f"Selected analysis_name not in catalog; falling back. Question: {question}",
            "status": "fallback",
        }

    spec: AnalysisSpec = ANALYSIS_CATALOG[analysis_name]
    allowed_params = {p.name for p in spec.parameters}

    ai_params = ai_output.parameters if isinstance(ai_output.parameters, dict) else {}

    # Filter unknown parameter names.
    filtered: Dict[str, Any] = {k: v for k, v in ai_params.items() if k in allowed_params}

    defaults = _default_params_for_analysis(analysis_name, end_date=end_date)

    # Coerce/filter to expected types.
    for p in spec.parameters:
        if p.name in filtered:
            defaults[p.name] = _coerce_param_value(p, filtered[p.name])
        elif p.required:
            # Required params get default if missing.
            defaults[p.name] = defaults.get(p.name)

    # Ensure required params are not None after coercion.
    missing_required = [
        p.name for p in spec.parameters if p.required and defaults.get(p.name) is None
    ]
    if missing_required:
        return {
            "analysis_name": DEFAULT_ANALYSIS_NAME,
            "parameters": fallback,
            "reasoning_short": f"AI parameters malformed; missing required: {', '.join(missing_required)}. Falling back.",
            "status": "fallback",
        }

    return {
        "analysis_name": analysis_name,
        "parameters": defaults,
        "reasoning_short": ai_output.reasoning_short or "Routed via AI analysis selection.",
        "status": "ok",
    }


def route_question_to_analysis(question: str) -> Dict[str, Any]:
    """
    Safe AI routing: select an analysis_name + parameters from the supported catalog.
    No SQL generation.
    """

    end_date = SEEDED_DEFAULT_END_DATE
    catalog_context = _build_catalog_context()

    heuristic = _heuristic_route(question)
    if heuristic is not None:
        return heuristic

    if not settings.OPENAI_API_KEY.strip():
        return {
            "analysis_name": DEFAULT_ANALYSIS_NAME,
            "parameters": _default_params_for_analysis(DEFAULT_ANALYSIS_NAME, end_date=end_date),
            "reasoning_short": "OPENAI_API_KEY is not set; using safe fallback analysis.",
            "status": "fallback",
        }

    # Isolate client creation so tests can mock select_analysis.
    client = OpenAIRoutingClient()

    ai_raw: Optional[AnalysisRouteAIOutput] = None
    try:
        ai_raw = client.select_analysis(
            question=question, catalog_context=catalog_context
        )
    except Exception:
        # Robust deterministic fallback if OpenAI fails.
        ai_raw = None

    return _validate_and_build_routing(ai_raw, question=question, end_date=end_date)

