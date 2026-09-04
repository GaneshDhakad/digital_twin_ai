"""
context_builder.py
Converts an existing DigitalTwinState into a structured AI-ready context dict.

CRITICAL DATA INTEGRITY RULES:
- Never replace null/None predictions with 0, 0.0, or any fabricated value.
- Never convert "insufficient_data" or "model_unavailable" into a numeric.
- Prediction status values are preserved exactly as produced by the ML services.
- The DigitalTwinState remains the single source of truth — no DB queries here.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from app.schemas.digital_twin import DigitalTwinState, DomainState

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _build_domain_context(state: DomainState) -> Dict[str, Any]:
    """Convert a single DomainState into a plain dict for the AI context."""
    return {
        "status": state.status,
        "metrics": dict(state.metrics),
        "last_updated": state.last_updated.isoformat() if state.last_updated else None,
    }


def _build_prediction_context(pred: Optional[Dict[str, Any]], domain_label: str) -> Dict[str, Any]:
    """
    Safely convert an ML prediction dict into AI context.

    Rules:
    - If pred is None, return status=unavailable, prediction=null.
    - If pred has status=insufficient_data, preserve it exactly.
    - If pred has status=model_unavailable, preserve it exactly.
    - If pred has status=available and a numeric/string prediction, preserve it.
    - NEVER replace null with 0 or any fabricated value.
    """
    if pred is None:
        return {
            "status": "unavailable",
            "prediction": None,
            "reason": f"No prediction data available for {domain_label}",
        }

    status = pred.get("status", "unknown")

    # Unavailable / insufficient / model_unavailable — preserve faithfully
    if status in ("insufficient_data", "model_unavailable", "error", "unavailable", "unknown"):
        context: Dict[str, Any] = {
            "status": status,
            "prediction": None,  # Always null — never substitute a fake value
        }
        if "reason" in pred:
            context["reason"] = pred["reason"]
        return context

    # Available — preserve the actual prediction value (numeric or string)
    if status == "available":
        raw_prediction = pred.get("prediction")

        # Safety check: if "available" but prediction is somehow None, downgrade to insufficient_data
        if raw_prediction is None:
            logger.warning(
                "Prediction for %s has status=available but prediction=None. "
                "Downgrading to insufficient_data to avoid null confusion.",
                domain_label,
            )
            return {
                "status": "insufficient_data",
                "prediction": None,
                "reason": "Prediction value missing despite available status",
            }

        context = {
            "status": "available",
            "prediction": raw_prediction,  # Numeric or string — preserved as-is
        }

        # Include metadata when present
        for key in ("model_name", "model_version", "target", "timestamp"):
            if key in pred and pred[key] is not None:
                context[key] = pred[key]

        return context

    # Fallback for unexpected status values
    logger.warning("Unexpected ML prediction status '%s' for %s", status, domain_label)
    return {
        "status": status,
        "prediction": None,
        "reason": f"Unexpected prediction status: {status}",
    }


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def build_ai_context(twin_state: DigitalTwinState) -> Dict[str, Any]:
    """
    Convert a DigitalTwinState (the source of truth) into a structured AI context dict.

    The returned structure is passed to the AssistantService to construct the LLM prompt.

    Data integrity:
    - null predictions remain null
    - numeric predictions remain numeric
    - prediction statuses are preserved exactly
    - no fabricated values are introduced
    """
    ml = twin_state.ml_predictions

    # Build ML predictions context — each domain handled independently
    ml_context: Dict[str, Any] = {
        "academic": _build_prediction_context(
            dict(ml.academic) if ml.academic else None,
            "academic",
        ),
        "financial": _build_prediction_context(
            dict(ml.financial) if ml.financial else None,
            "financial",
        ),
        "forecasting": _build_prediction_context(
            dict(ml.forecasting) if ml.forecasting else None,
            "forecasting",
        ),
        "lifestyle": _build_prediction_context(
            dict(ml.lifestyle) if ml.lifestyle else None,
            "lifestyle",
        ),
        "fitness": _build_prediction_context(
            dict(ml.fitness) if ml.fitness else None,
            "fitness",
        ),
    }

    # Attach retrieval timestamp if present
    if ml.retrieved_at:
        ml_context["retrieved_at"] = ml.retrieved_at

    context: Dict[str, Any] = {
        "user": {
            "user_id": twin_state.user_id,
        },
        "digital_twin": {
            "overall_state": twin_state.overall_state,
            "generated_at": twin_state.generated_at.isoformat() if twin_state.generated_at else None,
            "academic": _build_domain_context(twin_state.academic),
            "financial": _build_domain_context(twin_state.financial),
            "fitness": _build_domain_context(twin_state.fitness),
            "lifestyle_habits": _build_domain_context(twin_state.lifestyle_habits),
            "goals": _build_domain_context(twin_state.goals),
        },
        "ml_predictions": ml_context,
    }

    logger.debug(
        "Built AI context for user %s — overall_state=%s",
        twin_state.user_id,
        twin_state.overall_state,
    )
    return context
