"""
forecasting_service.py
Business logic for next-month spending forecasting (XGBRegressor model).

IMPORTANT: Only uses features listed in feature_info.json final_features.
Does NOT include next_month_spending (the target) or next_month_transaction_count
(future target information) as inputs.
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
from app.schemas.ml import ForecastingPredictionRequest, ForecastingPredictionResponse
from app.models.supporting import PredictionCache

logger = logging.getLogger(__name__)

DOMAIN = "forecasting"
CACHE_TTL_HOURS = 12  # Shorter TTL — spending patterns change


def _make_cache_key(user_id: Any, request: ForecastingPredictionRequest) -> str:
    payload = f"{user_id}:{DOMAIN}:{json.dumps(request.model_dump(), sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]


def _build_dataframe(request: ForecastingPredictionRequest) -> pd.DataFrame:
    """
    Build DataFrame matching forecasting feature_info.json final_features exactly.

    Features (in order from feature_info.json):
        month, total_signed_amount, total_absolute_amount, positive_amount,
        negative_amount, transaction_count, positive_transaction_count,
        negative_transaction_count, average_transaction_amount, unique_merchants,
        unique_cards, error_count, total_absolute_amount_lag_1,
        total_absolute_amount_rolling_3m, positive_amount_lag_1,
        positive_amount_rolling_3m, negative_amount_lag_1,
        negative_amount_rolling_3m, transaction_count_lag_1,
        transaction_count_rolling_3m
    """
    return pd.DataFrame([{
        "month": request.month,
        "total_signed_amount": request.total_signed_amount,
        "total_absolute_amount": request.total_absolute_amount,
        "positive_amount": request.positive_amount,
        "negative_amount": request.negative_amount,
        "transaction_count": request.transaction_count,
        "positive_transaction_count": request.positive_transaction_count,
        "negative_transaction_count": request.negative_transaction_count,
        "average_transaction_amount": request.average_transaction_amount,
        "unique_merchants": request.unique_merchants,
        "unique_cards": request.unique_cards,
        "error_count": request.error_count,
        "total_absolute_amount_lag_1": request.total_absolute_amount_lag_1,
        "total_absolute_amount_rolling_3m": request.total_absolute_amount_rolling_3m,
        "positive_amount_lag_1": request.positive_amount_lag_1,
        "positive_amount_rolling_3m": request.positive_amount_rolling_3m,
        "negative_amount_lag_1": request.negative_amount_lag_1,
        "negative_amount_rolling_3m": request.negative_amount_rolling_3m,
        "transaction_count_lag_1": request.transaction_count_lag_1,
        "transaction_count_rolling_3m": request.transaction_count_rolling_3m,
    }])


def predict_next_month_spending(
    request: ForecastingPredictionRequest,
    user_id: Any,
    db: Session,
) -> ForecastingPredictionResponse:
    """Predict next month's spending using the XGBRegressor pipeline."""
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
            logger.info("Forecasting prediction cache hit for user %s", user_id)
            data = cached.prediction_data
            return ForecastingPredictionResponse(
                prediction=data["prediction"],
                model_name=data["model_name"],
                model_version=data["model_version"],
                target=data["target"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
    except Exception as exc:
        logger.warning("Forecasting cache lookup failed: %s", exc)

    # ── Run inference ─────────────────────────────────────────────────────────
    pipeline = load_pipeline(DOMAIN)
    meta = load_metadata(DOMAIN)

    X = _build_dataframe(request)
    prediction_val = float(pipeline.predict(X)[0])
    prediction_val = max(0.0, prediction_val)  # spending can't be negative

    response = ForecastingPredictionResponse(
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
        logger.warning("Forecasting cache store failed: %s", exc)
        db.rollback()

    return response

def get_digital_twin_prediction(user_id: Any, db: Session) -> Dict[str, Any]:
    """
    Get the latest forecasting prediction for the Digital Twin.
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
            if cache.prediction_data and cache.prediction_data.get("target") == "next_month_spending":
                logger.info("Found valid cached forecasting prediction for user %s", user_id)
                data = cache.prediction_data.copy()
                data["status"] = "available"
                return data
    except Exception as exc:
        logger.warning("Failed to read forecasting cache: %s", exc)

    logger.info("Forecasting data is insufficient in DB to build prediction on-the-fly for user %s", user_id)
    return {
        "status": "insufficient_data",
        "prediction": None,
        "reason": "Missing required forecasting historical features (e.g., month_over_month_change, historical category ratios)"
    }
