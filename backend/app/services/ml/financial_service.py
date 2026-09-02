"""
financial_service.py
Business logic for disposable income prediction (financial model).

Uses the pre-trained RandomForestRegressor pipeline.
"""
from __future__ import annotations

import hashlib
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from app.services.ml.model_loader import load_pipeline, load_metadata
from app.schemas.ml import FinancialPredictionRequest, FinancialPredictionResponse
from app.models.supporting import PredictionCache

logger = logging.getLogger(__name__)

DOMAIN = "financial"
CACHE_TTL_HOURS = 24


def _make_cache_key(user_id: Any, request: FinancialPredictionRequest) -> str:
    payload = f"{user_id}:{DOMAIN}:{json.dumps(request.model_dump(), sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]


def _build_dataframe(request: FinancialPredictionRequest) -> pd.DataFrame:
    """Build DataFrame matching financial feature_info.json final_features order."""
    return pd.DataFrame([{
        "income": request.income,
        "age": request.age,
        "dependents": request.dependents,
        "occupation": request.occupation,
        "city_tier": request.city_tier,
        "desired_savings_percentage": request.desired_savings_percentage,
        "desired_savings": request.desired_savings,
    }])


def predict_disposable_income(
    request: FinancialPredictionRequest,
    user_id: Any,
    db: Session,
) -> FinancialPredictionResponse:
    """Predict disposable income using the financial RandomForestRegressor model."""
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
            logger.info("Financial prediction cache hit for user %s", user_id)
            data = cached.prediction_data
            return FinancialPredictionResponse(
                prediction=data["prediction"],
                model_name=data["model_name"],
                model_version=data["model_version"],
                target=data["target"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
    except Exception as exc:
        logger.warning("Financial cache lookup failed: %s", exc)

    # ── Run inference ─────────────────────────────────────────────────────────
    pipeline = load_pipeline(DOMAIN)
    meta = load_metadata(DOMAIN)

    X = _build_dataframe(request)
    prediction_val = float(pipeline.predict(X)[0])

    response = FinancialPredictionResponse(
        prediction=round(prediction_val, 2),
        model_name=meta["model_name"],
        model_version=meta.get("version", "1.0"),
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
        logger.warning("Financial cache store failed: %s", exc)
        db.rollback()

    return response

def get_digital_twin_prediction(user_id: Any, db: Session) -> Dict[str, Any]:
    """
    Get the latest financial prediction for the Digital Twin.
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
            if cache.prediction_data and cache.prediction_data.get("target") == "disposable_income":
                logger.info("Found valid cached financial prediction for user %s", user_id)
                data = cache.prediction_data.copy()
                data["status"] = "available"
                return data
    except Exception as exc:
        logger.warning("Failed to read financial cache: %s", exc)

    logger.info("Financial data is insufficient in DB to build prediction on-the-fly for user %s", user_id)
    return {
        "status": "insufficient_data",
        "prediction": None,
        "reason": "Missing required financial demographic features (e.g., dependents, city_tier, desired_savings_percentage)"
    }
