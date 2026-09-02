"""
routes/ml.py — FastAPI ML prediction endpoints.

Endpoints:
    POST /api/ml/academic/predict
    POST /api/ml/lifestyle/predict
    POST /api/ml/financial/predict
    POST /api/ml/forecasting/predict
    GET  /api/ml/models          — Model availability status
    GET  /api/ml/digital-twin    — Current Digital Twin state

All prediction endpoints require valid JWT authentication.
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.ml import (
    AcademicPredictionRequest,
    AcademicPredictionResponse,
    LifestylePredictionRequest,
    LifestylePredictionResponse,
    FinancialPredictionRequest,
    FinancialPredictionResponse,
    ForecastingPredictionRequest,
    ForecastingPredictionResponse,
)
from app.services.ml.model_loader import get_model_status
from app.services.ml.academic_service import predict_exam_score
from app.services.ml.lifestyle_service import predict_sleep_disorder
from app.services.ml.financial_service import predict_disposable_income
from app.services.ml.forecasting_service import predict_next_month_spending
from app.services.digital_twin_service import get_current_predictions

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ml",
    tags=["Machine Learning Predictions"],
)


# ─────────────────────────────────────────────────────────────────────────────
# MODEL STATUS — no auth required (health check)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/models", summary="ML model availability status")
def ml_models_status() -> Dict[str, Any]:
    """
    Return availability and metadata for all ML models.
    Fitness is explicitly excluded from this phase.
    """
    return get_model_status()


# ─────────────────────────────────────────────────────────────────────────────
# ACADEMIC — Predict exam_score
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/academic/predict",
    response_model=AcademicPredictionResponse,
    summary="Predict exam score (Academic model)",
)
def academic_predict(
    request: AcademicPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AcademicPredictionResponse:
    """
    Predict the student exam score using the GradientBoostingRegressor model.

    Requires authentication. The authenticated user's UUID is used for
    prediction caching.
    """
    try:
        return predict_exam_score(request, current_user.user_id, db)
    except FileNotFoundError as exc:
        logger.error("Academic model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Academic model is not available. Please contact the administrator.",
        )
    except RuntimeError as exc:
        logger.error("Academic prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to a model error.",
        )
    except Exception as exc:
        logger.exception("Unexpected error in academic prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# LIFESTYLE — Classify sleep_disorder
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/lifestyle/predict",
    response_model=LifestylePredictionResponse,
    summary="Predict sleep disorder risk (Lifestyle model)",
)
def lifestyle_predict(
    request: LifestylePredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> LifestylePredictionResponse:
    """
    Classify sleep disorder risk using the LogisticRegression lifestyle model.

    Possible predictions: 'None', 'Insomnia', 'Sleep Apnea' (from training data).
    """
    try:
        return predict_sleep_disorder(request, current_user.user_id, db)
    except FileNotFoundError as exc:
        logger.error("Lifestyle model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Lifestyle model is not available.",
        )
    except RuntimeError as exc:
        logger.error("Lifestyle prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to a model error.",
        )
    except Exception as exc:
        logger.exception("Unexpected error in lifestyle prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL — Predict disposable_income
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/financial/predict",
    response_model=FinancialPredictionResponse,
    summary="Predict disposable income (Financial model)",
)
def financial_predict(
    request: FinancialPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> FinancialPredictionResponse:
    """
    Predict monthly disposable income using the RandomForestRegressor financial model.
    """
    try:
        return predict_disposable_income(request, current_user.user_id, db)
    except FileNotFoundError as exc:
        logger.error("Financial model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Financial model is not available.",
        )
    except RuntimeError as exc:
        logger.error("Financial prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to a model error.",
        )
    except Exception as exc:
        logger.exception("Unexpected error in financial prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# FORECASTING — Predict next_month_spending
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/forecasting/predict",
    response_model=ForecastingPredictionResponse,
    summary="Predict next month spending (Forecasting model)",
)
def forecasting_predict(
    request: ForecastingPredictionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ForecastingPredictionResponse:
    """
    Predict next month's total spending using the XGBRegressor forecasting model.

    Inputs must be current-month aggregated transaction data plus lag/rolling features
    from prior months. The target (next_month_spending) itself is NOT an input.
    """
    try:
        return predict_next_month_spending(request, current_user.user_id, db)
    except FileNotFoundError as exc:
        logger.error("Forecasting model not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Forecasting model is not available.",
        )
    except RuntimeError as exc:
        logger.error("Forecasting prediction failed: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Prediction failed due to a model error.",
        )
    except Exception as exc:
        logger.exception("Unexpected error in forecasting prediction: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during prediction.",
        )


# ─────────────────────────────────────────────────────────────────────────────
# DIGITAL TWIN STATE
# ─────────────────────────────────────────────────────────────────────────────

from app.schemas.digital_twin import DigitalTwinState
from app.services.digital_twin_service import get_digital_twin_state as get_dt_state

@router.get(
    "/digital-twin",
    response_model=DigitalTwinState,
    summary="Get current Digital Twin prediction state",
)
def get_digital_twin_state(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DigitalTwinState:
    """
    Return the comprehensive Digital Twin state aggregated from all domains
    and latest cached ML predictions for the authenticated user.
    """
    return get_dt_state(db, current_user.user_id)
