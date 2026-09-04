"""
response_parser.py
Safe parser and validator for AI-generated structured insights/recommendations.

Design (Step 6 — Structured AI Output):
    The Gemini model may optionally embed a structured JSON block in its response
    using the following sentinel comment format:

        <!-- INSIGHTS_JSON: [...] -->

    This block is invisible to users (it looks like an HTML comment) but is
    machine-parseable by this module. The AI produces both:
        1. Human-readable prose response (primary)
        2. Optional structured insights block (supplemental, for the API consumer)

    The parser:
        - Extracts the JSON block from the raw AI response text
        - Strips it from the visible response (so users see clean prose)
        - Validates each insight object using Pydantic (AIInsight schema)
        - Returns the validated list of insights (empty list on any failure)

Security / Robustness (Step 7 — Safety & Hardening):
    - NEVER trusts raw LLM output as inherently valid
    - Malformed JSON → returns [] (no crash)
    - Missing required fields → Pydantic provides defaults or skips the insight
    - Invalid enum values (e.g. priority="extreme") → coerced to None or skipped
    - Unexpected extra fields → ignored (model uses model_config extra="ignore")
    - Excessively large JSON block → truncated / skipped with a warning
    - Parse errors are logged at WARNING level (not propagated as exceptions)

The caller (route) receives a clean (insight-stripped) response text plus a
validated list of AIInsight objects. If the AI produces no structured block,
the caller gets an empty list — the prose response is always returned intact.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

# Sentinel comment the AI is instructed to use when returning structured insights
_INSIGHTS_SENTINEL_RE = re.compile(
    r"<!--\s*INSIGHTS_JSON:\s*(\[.*?\])\s*-->",
    re.DOTALL | re.IGNORECASE,
)

# Maximum bytes we will attempt to parse from the JSON block.
# Prevents the AI from producing a pathologically large block.
_MAX_INSIGHTS_JSON_BYTES: int = 32_768  # 32 KB

# Valid area values (open list — AI may use any domain name, we preserve it)
_KNOWN_AREAS = frozenset({
    "academic", "financial", "fitness",
    "lifestyle", "habits", "goals", "forecasting", "general",
})

# Valid priority values — anything else is coerced to None
_VALID_PRIORITIES = frozenset({"high", "medium", "low"})

# Valid type values
_VALID_TYPES = frozenset({
    "recommendation", "warning", "observation", "insight", "tip",
})


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic schema for a single insight (Step 6)
# ─────────────────────────────────────────────────────────────────────────────

class AIInsight(BaseModel):
    """
    A single structured insight or recommendation produced by the AI.

    All fields are optional/nullable to handle partial AI output gracefully.
    Validation normalises invalid values rather than raising hard errors.
    """

    model_config = {"extra": "ignore"}  # Silently ignore unexpected AI-generated fields

    area: str = Field(
        default="general",
        description=(
            "The Digital Twin domain this insight relates to. "
            "One of: academic, financial, fitness, lifestyle, habits, goals, forecasting, general."
        ),
        max_length=64,
    )

    type: str = Field(
        default="recommendation",
        description=(
            "The type of insight. "
            "One of: recommendation, warning, observation, insight, tip."
        ),
        max_length=64,
    )

    title: str = Field(
        default="",
        description="Short title for the insight (displayed in UI).",
        max_length=200,
    )

    description: str = Field(
        default="",
        description="Full description of the insight or recommendation.",
        max_length=2000,
    )

    priority: Optional[str] = Field(
        default=None,
        description=(
            "Priority level: 'high', 'medium', or 'low'. "
            "Null/None if data does not justify a priority assignment."
        ),
    )

    reason: str = Field(
        default="",
        description="Explanation of why this insight is being surfaced.",
        max_length=1000,
    )

    @field_validator("area", mode="before")
    @classmethod
    def normalise_area(cls, v: Any) -> str:
        """Accept any string area; empty/None defaults to 'general'."""
        if not v or not isinstance(v, str):
            return "general"
        return str(v).strip().lower()[:64] or "general"

    @field_validator("type", mode="before")
    @classmethod
    def normalise_type(cls, v: Any) -> str:
        """Coerce unknown type values to 'recommendation'."""
        if not v or not isinstance(v, str):
            return "recommendation"
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in _VALID_TYPES else "recommendation"

    @field_validator("priority", mode="before")
    @classmethod
    def normalise_priority(cls, v: Any) -> Optional[str]:
        """
        Coerce priority to 'high', 'medium', 'low', or None.

        Invalid values (e.g. 'extreme', 'urgent', '') → None.
        This prevents the AI from fabricating unsupported priority levels.
        """
        if v is None or v == "":
            return None
        if not isinstance(v, str):
            return None
        cleaned = str(v).strip().lower()
        return cleaned if cleaned in _VALID_PRIORITIES else None

    @field_validator("title", "description", "reason", mode="before")
    @classmethod
    def coerce_to_str(cls, v: Any) -> str:
        """Ensure string fields are always strings, never None/int/etc."""
        if v is None:
            return ""
        return str(v)


# ─────────────────────────────────────────────────────────────────────────────
# Parser functions
# ─────────────────────────────────────────────────────────────────────────────

def _extract_insights_json(raw_text: str) -> Optional[str]:
    """
    Extract the JSON array string from a sentinel comment block.

    Returns the raw JSON string if found, or None if the sentinel is absent.
    """
    match = _INSIGHTS_SENTINEL_RE.search(raw_text)
    if not match:
        return None

    json_str = match.group(1)

    if len(json_str.encode("utf-8")) > _MAX_INSIGHTS_JSON_BYTES:
        logger.warning(
            "AI-generated INSIGHTS_JSON block exceeds size limit (%d bytes). "
            "Ignoring structured insights.",
            _MAX_INSIGHTS_JSON_BYTES,
        )
        return None

    return json_str


def _strip_insights_block(raw_text: str) -> str:
    """
    Remove the <!-- INSIGHTS_JSON: [...] --> sentinel from the response text.

    Returns the clean prose text to show to the user.
    """
    cleaned = _INSIGHTS_SENTINEL_RE.sub("", raw_text)
    return cleaned.strip()


def _parse_insight_object(obj: Any, index: int) -> Optional[AIInsight]:
    """
    Parse and validate a single insight dict using Pydantic.

    Returns the validated AIInsight, or None if parsing fails.
    Invalid individual insights are skipped — they do not fail the whole batch.
    """
    if not isinstance(obj, dict):
        logger.warning(
            "Insight item %d is not a dict (got %s). Skipping.",
            index,
            type(obj).__name__,
        )
        return None

    try:
        return AIInsight.model_validate(obj)
    except Exception as exc:
        logger.warning(
            "Insight item %d failed Pydantic validation: %s. Skipping.",
            index,
            exc,
        )
        return None


def parse_insights_from_response(raw_text: str) -> tuple[str, List[AIInsight]]:
    """
    Parse structured insights from a raw AI response and return clean text.

    This is the main public API of this module.

    Steps:
        1. Search for the <!-- INSIGHTS_JSON: [...] --> sentinel block
        2. If found: extract the JSON, strip the sentinel from the prose
        3. Parse the JSON array into validated AIInsight objects
        4. Return (clean_prose_text, [validated_insights])

    If the AI produced no sentinel block, or if parsing fails at any step,
    the original text (stripped) is returned with an empty insights list.
    This function NEVER raises an exception — all failures produce (text, []).

    Args:
        raw_text: The raw string returned by Gemini.

    Returns:
        A tuple of:
            - clean_text: Prose response with the sentinel block removed.
            - insights:   List of validated AIInsight objects (may be empty).
    """
    if not raw_text or not raw_text.strip():
        return raw_text or "", []

    # Step 1: Look for the sentinel
    json_str = _extract_insights_json(raw_text)
    if json_str is None:
        # No structured block — return text as-is, no insights
        return raw_text.strip(), []

    # Step 2: Strip the sentinel from visible text
    clean_text = _strip_insights_block(raw_text)

    # Step 3: Parse JSON
    try:
        raw_list = json.loads(json_str)
    except json.JSONDecodeError as exc:
        logger.warning(
            "AI-generated INSIGHTS_JSON block contains malformed JSON: %s. "
            "Returning empty insights list.",
            exc,
        )
        return clean_text, []

    if not isinstance(raw_list, list):
        logger.warning(
            "AI-generated INSIGHTS_JSON is not a JSON array (got %s). "
            "Returning empty insights list.",
            type(raw_list).__name__,
        )
        return clean_text, []

    # Step 4: Validate each item individually
    insights: List[AIInsight] = []
    for i, obj in enumerate(raw_list):
        insight = _parse_insight_object(obj, i)
        if insight is not None:
            insights.append(insight)

    logger.debug(
        "Parsed %d valid insights from AI response (%d raw items).",
        len(insights),
        len(raw_list),
    )

    return clean_text, insights
