"""
academic_service.py
Business logic for academic exam score prediction.

Uses the pre-trained GradientBoostingRegressor pipeline.
Caches predictions in the PredictionCache table.
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
from app.schemas.ml import AcademicPredictionRequest, AcademicPredictionResponse
from app.models.supporting import PredictionCache

logger = logging.getLogger(__name__)

DOMAIN = "academic"
CACHE_TTL_HOURS = 24


def _make_cache_key(user_id: Any, request: AcademicPredictionRequest) -> str:
    """Deterministic cache key based on user + inputs."""
    payload = f"{user_id}:{DOMAIN}:{json.dumps(request.model_dump(), sort_keys=True, default=str)}"
    return hashlib.sha256(payload.encode()).hexdigest()[:64]


def _build_dataframe(request: AcademicPredictionRequest) -> pd.DataFrame:
    """Build a single-row DataFrame matching the feature order from feature_info.json."""
    return pd.DataFrame([{
        "age": request.age,
        "gender": request.gender,
        "major": request.major,
        "study_hours_per_day": request.study_hours_per_day,
        "social_media_hours": request.social_media_hours,
        "netflix_hours": request.netflix_hours,
        "part_time_job": request.part_time_job,
        "attendance_percentage": request.attendance_percentage,
        "sleep_hours": request.sleep_hours,
        "diet_quality": request.diet_quality,
        "exercise_frequency": request.exercise_frequency,
        "parental_education_level": request.parental_education_level,
        "internet_quality": request.internet_quality,
        "mental_health_rating": request.mental_health_rating,
        "extracurricular_participation": request.extracurricular_participation,
        "previous_gpa": request.previous_gpa,
        "semester": request.semester,
        "stress_level": request.stress_level,
        "dropout_risk": request.dropout_risk,
        "social_activity": request.social_activity,
        "screen_time": request.screen_time,
        "study_environment": request.study_environment,
        "access_to_tutoring": request.access_to_tutoring,
        "family_income_range": request.family_income_range,
        "parental_support_level": request.parental_support_level,
        "motivation_level": request.motivation_level,
        "exam_anxiety_score": request.exam_anxiety_score,
        "learning_style": request.learning_style,
        "time_management_score": request.time_management_score,
        "study_efficiency": request.study_efficiency,
        "digital_distraction_hours": request.digital_distraction_hours,
        "wellbeing_score": request.wellbeing_score,
    }])


def predict_exam_score(
    request: AcademicPredictionRequest,
    user_id: Any,
    db: Session,
) -> AcademicPredictionResponse:
    """
    Run academic exam score prediction.

    1. Check PredictionCache for a recent cached result.
    2. If cache miss, run inference.
    3. Store result in PredictionCache.
    """
    cache_key = _make_cache_key(user_id, request)
    now = datetime.now(timezone.utc)

    # ── Cache lookup ───────────────────────────────────────────────────────────
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
            logger.info("Academic prediction cache hit for user %s", user_id)
            data = cached.prediction_data
            return AcademicPredictionResponse(
                prediction=data["prediction"],
                model_name=data["model_name"],
                model_version=data["model_version"],
                target=data["target"],
                timestamp=datetime.fromisoformat(data["timestamp"]),
            )
    except Exception as exc:
        logger.warning("Cache lookup failed: %s", exc)

    # ── Run inference ──────────────────────────────────────────────────────────
    pipeline = load_pipeline(DOMAIN)
    meta = load_metadata(DOMAIN)

    X = _build_dataframe(request)
    prediction_val = float(pipeline.predict(X)[0])
    prediction_val = max(0.0, min(100.0, prediction_val))  # clamp to [0, 100]

    response = AcademicPredictionResponse(
        prediction=round(prediction_val, 2),
        model_name=meta["model_name"],
        model_version=meta.get("version", "1.0"),
        target=meta["target"],
        timestamp=now,
    )

    # ── Store in cache ─────────────────────────────────────────────────────────
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
        logger.warning("Failed to store prediction in cache: %s", exc)
        db.rollback()

    return response

def get_digital_twin_prediction(user_id: Any, db: Session) -> Dict[str, Any]:
    """
    Get the latest academic prediction for the Digital Twin.
    1. Try to find a valid cached prediction from the UI.
    2. If none, attempt to build from DB (which typically fails due to 30+ missing features).
    3. Return insufficient_data if it cannot be built.
    """
    now = datetime.now(timezone.utc)
    
    # 1. Check cache via target inside prediction_data
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
            if cache.prediction_data and cache.prediction_data.get("target") == "exam_score":
                logger.info("Found valid cached academic prediction for user %s", user_id)
                data = cache.prediction_data.copy()
                data["status"] = "available"
                return data
    except Exception as exc:
        logger.warning("Failed to read academic cache: %s", exc)

    # 2. Try to build from DB
    # We would need 32 features (age, gender, major, netflix_hours, etc.)
    # Since we only have study_hours and performance_score in StudyActivity,
    # it is impossible to build a full AcademicPredictionRequest without guessing.
    logger.info("Academic data is insufficient in DB to build prediction on-the-fly for user %s", user_id)
    return {
        "status": "insufficient_data",
        "prediction": None,
        "reason": "Missing required academic features (e.g., demographics, habits, major)"
    }
