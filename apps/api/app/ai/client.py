from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict

from openai import OpenAI

from app.core.config import settings


@dataclass(frozen=True)
class AnalysisRouteAIOutput:
    analysis_name: str
    parameters: Dict[str, Any]
    reasoning_short: str


class OpenAIRoutingClient:
    """
    Minimal wrapper around the OpenAI Responses API.

    This client is intentionally isolated so tests can mock it,
    and so we don't accidentally let the model generate SQL.
    """

    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def select_analysis(self, *, question: str, catalog_context: str) -> AnalysisRouteAIOutput:
        prompt = catalog_context

        # NOTE: We rely on strong prompting + JSON parsing.
        # Guardrails are enforced in the router via registry validation.
        system_text = (
            "You are a safe routing assistant. "
            "You must select an analysis_name from the provided catalog and "
            "provide parameters that match that analysis. "
            "You must NOT generate SQL."
        )

        user_text = (
            f"{prompt}\n\n"
            f"User question: {question}\n\n"
            "Return only a JSON object with keys: analysis_name, parameters, reasoning_short."
        )

        # Keep request shape minimal and broadly compatible across supported models/SDK versions.
        # Do not pass optional knobs that can trigger 400s for some model families.
        response = self._client.responses.create(
            model=settings.OPENAI_MODEL,
            input=[
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_text},
            ],
        )

        output_text = getattr(response, "output_text", None)
        if not output_text:
            # Fallback: attempt to reconstruct from output.
            output_text = str(response)

        payload = self._parse_json(output_text)
        return AnalysisRouteAIOutput(
            analysis_name=str(payload.get("analysis_name", "")),
            parameters=payload.get("parameters", {}) or {},
            reasoning_short=str(payload.get("reasoning_short", "")),
        )

    def _parse_json(self, output_text: str) -> Dict[str, Any]:
        # Robustly extract a JSON object from model output.
        first = output_text.find("{")
        last = output_text.rfind("}")
        if first == -1 or last == -1 or last <= first:
            raise ValueError("Model did not return a JSON object.")
        json_str = output_text[first : last + 1]
        return json.loads(json_str)

