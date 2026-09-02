"""
digital_twin_service.py
Aggregates the latest cached ML predictions and actual database state for a user.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.supporting import PredictionCache
from app.services.financial_service import get_financial_summary
from app.services.study_service import get_study_summary
from app.services.fitness_service import get_fitness_summary
from app.services.habit_service import get_habit_analytics
from app.services.goal_service import get_goal_summary
from app.schemas.digital_twin import DigitalTwinState, DomainState, MLPredictions

logger = logging.getLogger(__name__)

from app.services.ml.academic_service import get_digital_twin_prediction as get_academic_pred
from app.services.ml.financial_service import get_digital_twin_prediction as get_financial_pred
from app.services.ml.lifestyle_service import get_digital_twin_prediction as get_lifestyle_pred
from app.services.ml.forecasting_service import get_digital_twin_prediction as get_forecasting_pred

def get_current_predictions(db: Session, user_id: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    now = datetime.now(timezone.utc)
    
    try:
        result["academic"] = get_academic_pred(user_id, db)
    except Exception as exc:
        logger.exception("Failed to get academic prediction for Digital Twin: %s", exc)
        result["academic"] = {"status": "error", "prediction": None, "reason": str(exc)}

    try:
        result["financial"] = get_financial_pred(user_id, db)
    except Exception as exc:
        logger.exception("Failed to get financial prediction for Digital Twin: %s", exc)
        result["financial"] = {"status": "error", "prediction": None, "reason": str(exc)}

    try:
        result["lifestyle"] = get_lifestyle_pred(user_id, db)
    except Exception as exc:
        logger.exception("Failed to get lifestyle prediction for Digital Twin: %s", exc)
        result["lifestyle"] = {"status": "error", "prediction": None, "reason": str(exc)}

    try:
        result["forecasting"] = get_forecasting_pred(user_id, db)
    except Exception as exc:
        logger.exception("Failed to get forecasting prediction for Digital Twin: %s", exc)
        result["forecasting"] = {"status": "error", "prediction": None, "reason": str(exc)}

    # Fitness explicitly disabled as per requirements
    result["fitness"] = {
        "status": "model_unavailable",
        "prediction": None,
        "reason": "No trained fitness model exists"
    }
    
    result["retrieved_at"] = now.isoformat()
    return result

def get_digital_twin_state(db: Session, user_id: UUID) -> DigitalTwinState:
    now = datetime.now(timezone.utc)

    # 1. Financial State
    try:
        fin = get_financial_summary(db, user_id)
        total_inc = fin.total_income
        total_exp = fin.total_expenses
        fin_status = "stable"
        if total_inc > 0:
            savings_rate = (total_inc - total_exp) / total_inc
            if savings_rate > 0.2: fin_status = "healthy"
            elif savings_rate < 0: fin_status = "at-risk"
        elif total_exp > 0:
            fin_status = "critical"
        else:
            fin_status = "stable"
        
        fin_state = DomainState(
            status=fin_status,
            metrics={"total_income": total_inc, "total_expenses": total_exp, "total_savings": fin.total_savings},
            last_updated=now
        )
    except Exception:
        fin_state = DomainState(status="stable", metrics={}, last_updated=now)

    # 2. Academic/Study State
    try:
        std = get_study_summary(db, user_id)
        std_status = "stable"
        if std.average_performance_score >= 85: std_status = "healthy"
        elif std.average_performance_score < 60 and std.total_focus_hours > 0: std_status = "at-risk"
        
        acad_state = DomainState(
            status=std_status,
            metrics={"total_focus_hours": std.total_focus_hours, "average_performance": std.average_performance_score},
            last_updated=now
        )
    except Exception:
        acad_state = DomainState(status="stable", metrics={}, last_updated=now)

    # 3. Fitness State
    try:
        fit = get_fitness_summary(db, user_id)
        fit_status = "stable"
        if fit.total_workouts >= 3: fit_status = "healthy"
        elif fit.total_workouts == 0: fit_status = "declining"
        
        fit_state = DomainState(
            status=fit_status,
            metrics={"total_workouts": fit.total_workouts, "total_duration": fit.total_duration_minutes, "calories": fit.total_calories},
            last_updated=now
        )
    except Exception:
        fit_state = DomainState(status="stable", metrics={}, last_updated=now)

    # 4. Lifestyle/Habits State
    try:
        hab = get_habit_analytics(db, user_id)
        hab_status = "stable"
        if hab.overall_completion_rate >= 80: hab_status = "healthy"
        elif hab.overall_completion_rate < 50 and hab.total_habits_logged > 0: hab_status = "declining"
        
        life_state = DomainState(
            status=hab_status,
            metrics={"completion_rate": hab.overall_completion_rate, "current_streak": hab.current_streak},
            last_updated=now
        )
    except Exception:
        life_state = DomainState(status="stable", metrics={}, last_updated=now)

    # 5. Goals State
    try:
        gls = get_goal_summary(db, user_id)
        gls_status = "stable"
        if gls.completed_goals > 0: gls_status = "improving"
        if gls.at_risk_goals > 0: gls_status = "at-risk"
        
        goal_state = DomainState(
            status=gls_status,
            metrics={"active_goals": gls.active_goals, "completed_goals": gls.completed_goals, "at_risk": gls.at_risk_goals},
            last_updated=now
        )
    except Exception:
        goal_state = DomainState(status="stable", metrics={}, last_updated=now)

    # ML Predictions
    preds = get_current_predictions(db, user_id)
    ml_preds = MLPredictions(**preds)

    # Overall Status Calculation
    statuses = [fin_state.status, acad_state.status, fit_state.status, life_state.status, goal_state.status]
    if "critical" in statuses: overall = "critical"
    elif "at-risk" in statuses: overall = "at-risk"
    elif "declining" in statuses: overall = "declining"
    elif "healthy" in statuses and "improving" in statuses: overall = "healthy"
    else: overall = "stable"

    return DigitalTwinState(
        user_id=str(user_id),
        overall_state=overall,
        financial=fin_state,
        academic=acad_state,
        fitness=fit_state,
        lifestyle_habits=life_state,
        goals=goal_state,
        ml_predictions=ml_preds,
        generated_at=now
    )
