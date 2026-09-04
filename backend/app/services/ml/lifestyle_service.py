"""
lifestyle_service.py
Business logic for sleep disorder classification (lifestyle model).

Uses the pre-trained GradientBoostingClassifier pipeline.

The model predicts one of three classes:
    Normal      — no significant sleep disorder risk detected
    Insomnia    — pattern consistent with insomnia-related profile
    Sleep Apnea — pattern consistent with sleep apnea-related profile

These are project-level classification labels, NOT clinical diagnoses.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict

import pandas as pd
from sqlalchemy.orm import Session

from app.services.ml.model_loader import load_pipeline, load_metadata
from app.schemas.ml import LifestylePredictionRequest, LifestylePredictionResponse
from app.models.supporting import PredictionCache

logger = logging.getLogger(__name__)

DOMAIN = "lifestyle"
CACHE_TTL_HOURS = 24

# Valid Lifestyle ML prediction classes (3-class classifier)
LIFESTYLE_VALID_CLASSES = {"Normal", "Insomnia", "Sleep Apnea"}


def _make_cache_key(user_id: Any, request: LifestylePredictionRequest) -> str:
    payload = f"{user_id}:{DOMAIN}:{json.dumps(request.model_dump(), sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]


def _build_dataframe(request: LifestylePredictionRequest) -> pd.DataFrame:
    """Build DataFrame matching lifestyle feature_info.json final_features order."""
    return pd.DataFrame([{
        "gender": request.gender,
        "age": request.age,
        "occupation": request.occupation,
        "sleep_hours": request.sleep_hours,
        "sleep_quality": request.sleep_quality,
        "physical_activity_level": request.physical_activity_level,
        "stress_level": request.stress_level,
        "bmi_category": request.bmi_category,
        "blood_pressure": request.blood_pressure,
        "heart_rate": request.heart_rate,
        "daily_steps": request.daily_steps,
        "activity_sleep_balance": request.activity_sleep_balance,
        "lifestyle_risk_score": request.lifestyle_risk_score,
    }])


def predict_sleep_disorder(
    request: LifestylePredictionRequest,
    user_id: Any,
    db: Session,
) -> LifestylePredictionResponse:
    """Classify sleep disorder risk using the GradientBoostingClassifier lifestyle model.

    Returns one of: Normal | Insomnia | Sleep Apnea
    These are model classification labels, not clinical diagnoses.
    """
    cache_key = _make_cache_key(user_id, request)
    now = datetime.now(timezone.utc)

    # ── Cache lookup ──────────────────────────────────────────────────────────
    try:
        cached = (
            db.query(PredictionCache)
            .filter(
                PredictionCache.user_id == user_id,
                PredictionCache.cache_key == cache_key,
                PredictionCache.expires_at > now,
            )
            .first()
        )
        if cached:
            logger.info("Lifestyle prediction cache hit for user %s", user_id)
            data = cached.prediction_data
            return LifestylePredictionResponse(
                prediction=data["prediction"],
                model_name=data["model_name"],
                model_version=data["model_version"],
                target=data["target"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
    except Exception as exc:
        logger.warning("Lifestyle cache lookup failed: %s", exc)

    # ── Run inference ─────────────────────────────────────────────────────────
    pipeline = load_pipeline(DOMAIN)
    meta = load_metadata(DOMAIN)

    X = _build_dataframe(request)
    raw_prediction = pipeline.predict(X)[0]
    prediction_str = str(raw_prediction)

    response = LifestylePredictionResponse(
        prediction=prediction_str,
        model_name=meta["model_name"],
        model_version=meta.get("version", "2.0"),
        target=meta["target"],
        timestamp=now,
    )

    # ── Store in cache ────────────────────────────────────────────────────────
    try:
        expires = now + timedelta(hours=CACHE_TTL_HOURS)
        prediction_data = {
            "prediction": response.prediction,
            "model_name": response.model_name,
            "model_version": response.model_version,
            "target": response.target,
            "timestamp": response.timestamp.isoformat(),
        }

        existing = db.query(PredictionCache).filter(
            PredictionCache.cache_key == cache_key
        ).first()

        if existing:
            existing.prediction_data = prediction_data
            existing.expires_at = expires
        else:
            entry = PredictionCache(
                user_id=user_id,
                cache_key=cache_key,
                model_name=meta["model_name"],
                prediction_data=prediction_data,
                expires_at=expires,
            )
            db.add(entry)
        db.commit()
    except Exception as exc:
        logger.warning("Lifestyle cache store failed: %s", exc)
        db.rollback()

    return response


def get_digital_twin_prediction(user_id: Any, db: Session) -> Dict[str, Any]:
    """
    Get the latest lifestyle sleep-disorder classification prediction for the Digital Twin.

    Returns one of:
        {"status": "available", "prediction": "Normal"|"Insomnia"|"Sleep Apnea", ...}
        {"status": "insufficient_data", "prediction": None, "reason": "..."}
        {"status": "model_unavailable", "prediction": None, "reason": "..."}

    The prediction field, when available, is the model's classification label.
    This is NOT a clinical diagnosis.
    """
    now = datetime.now(timezone.utc)

    try:
        recent_caches = (
            db.query(PredictionCache)
            .filter(
                PredictionCache.user_id == user_id,
                PredictionCache.expires_at > now
            )
            .order_by(PredictionCache.created_at.desc())
            .all()
        )
        for cache in recent_caches:
            if cache.prediction_data and cache.prediction_data.get("target") == "sleep_disorder":
                logger.info("Found valid cached lifestyle prediction for user %s", user_id)
                data = cache.prediction_data.copy()
                data["status"] = "available"
                return data
    except Exception as exc:
        logger.warning("Failed to read lifestyle cache: %s", exc)

    logger.info("Lifestyle data is insufficient in DB to build prediction on-the-fly for user %s", user_id)
    return {
        "status": "insufficient_data",
        "prediction": None,
        "reason": "Missing required lifestyle features (e.g., blood_pressure, occupation, sleep_quality). "
                  "Use the Lifestyle ML form to generate a sleep-disorder classification prediction.",
    }
