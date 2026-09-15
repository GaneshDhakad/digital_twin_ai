import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.simulations import Simulation
from app.schemas.simulation import SimulationRequest, SimulationResponse, ScenarioResult
from app.services.digital_twin_service import get_digital_twin_state

logger = logging.getLogger(__name__)

HORIZON_MONTHS: Dict[str, float] = {
    "7_days": 7.0 / 30.0,
    "1_month": 1.0,
    "3_months": 3.0,
    "1_year": 12.0,
    "2_years": 24.0,
}

HORIZON_LABELS: Dict[str, str] = {
    "7_days": "Next 7 Days",
    "1_month": "1 Month",
    "3_months": "3 Months",
    "1_year": "1 Year",
    "2_years": "2 Years",
}


def generate_financial_scenarios(
    dt_state: Any, params: Dict[str, Any], selected_horizon: str = "1_month"
) -> Tuple[List[ScenarioResult], Dict[str, Any], Dict[str, Any]]:
    income = float(dt_state.financial.metrics.get("total_income", 5000) or 5000)
    expenses = float(dt_state.financial.metrics.get("total_expenses", 3000) or 3000)
    monthly_savings = income - expenses

    extra_expense = float(params.get("extra_expense", 0))
    savings_delta = float(params.get("savings_delta", params.get("impact", 0)))
    new_monthly_savings = monthly_savings + savings_delta - extra_expense

    horizon_impacts: Dict[str, Any] = {}
    for h_key, months in HORIZON_MONTHS.items():
        base_val = round(monthly_savings * months, 2)
        exp_val = round(new_monthly_savings * months, 2)
        best_val = round(new_monthly_savings * months * (1.0 + 0.12 * (months ** 0.25)), 2)
        worst_val = round(new_monthly_savings * months * (1.0 - 0.20 * (months ** 0.25)), 2)
        horizon_impacts[h_key] = {
            "label": HORIZON_LABELS[h_key],
            "baseline": base_val,
            "expected": exp_val,
            "best": best_val,
            "worst": worst_val,
            "delta": round(exp_val - base_val, 2),
            "unit": "$",
        }

    active_h = selected_horizon if selected_horizon in HORIZON_MONTHS else "1_month"
    h_months = HORIZON_MONTHS[active_h]
    h_data = horizon_impacts[active_h]

    # 1. Current Path
    current_val = h_data["baseline"]
    expected_val = h_data["expected"]
    best_val = h_data["best"]
    worst_val = h_data["worst"]
    risk_val = round(expected_val - (expenses * min(h_months, 3.0)), 2)

    scenarios = [
        ScenarioResult(
            scenario_name="Current Path",
            projected_outcomes={
                "savings": current_val,
                "12_month_savings": round(monthly_savings * 12, 2),
            },
            risk_level="Low" if current_val >= 0 else "High",
            warnings=[] if current_val >= 0 else ["Baseline cashflow is negative."],
        ),
        ScenarioResult(
            scenario_name="Expected Case",
            projected_outcomes={
                "savings": expected_val,
                "12_month_savings": round(new_monthly_savings * 12, 2),
            },
            risk_level="Low" if expected_val > 0 else "High",
            warnings=[] if expected_val >= 0 else ["Projected scenario produces cash deficit."],
        ),
        ScenarioResult(
            scenario_name="Best Case",
            projected_outcomes={
                "savings": best_val,
                "12_month_savings": round(new_monthly_savings * 1.15 * 12, 2),
            },
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Worst Case",
            projected_outcomes={
                "savings": worst_val,
                "12_month_savings": round(new_monthly_savings * 0.80 * 12, 2),
            },
            risk_level="High" if worst_val <= 0 else "Medium",
            warnings=["Under high cost variance, savings buffer is compromised."] if worst_val <= 0 else [],
        ),
        ScenarioResult(
            scenario_name="Risk Scenario",
            projected_outcomes={
                "savings": risk_val,
                "12_month_savings": round((new_monthly_savings * 9) - (expenses * 3), 2),
            },
            risk_level="Critical" if risk_val < 0 else "High",
            warnings=["Emergency Fund Guardrail: Savings depleted if emergency income pause occurs."] if risk_val < 0 else [],
        ),
    ]

    key_metrics = {
        "monthly_income": income,
        "monthly_expenses": expenses,
        "baseline_savings": current_val,
        "projected_savings": expected_val,
        "net_impact": h_data["delta"],
        "runway_months": round(max(0.0, expected_val) / max(expenses, 1.0), 1),
    }

    return scenarios, horizon_impacts, key_metrics


def generate_forecasting_scenarios(
    dt_state: Any, params: Dict[str, Any], selected_horizon: str = "1_month"
) -> Tuple[List[ScenarioResult], Dict[str, Any], Dict[str, Any]]:
    base_spending = float(dt_state.financial.metrics.get("total_expenses", 3000) or 3000)
    
    # Check if ML forecasting prediction is available
    if hasattr(dt_state, "ml_predictions") and dt_state.ml_predictions:
        fore_pred = getattr(dt_state.ml_predictions, "forecasting", None)
        if isinstance(fore_pred, dict) and fore_pred.get("prediction"):
            try:
                base_spending = float(fore_pred["prediction"])
            except Exception:
                pass

    spending_shift_pct = float(params.get("spending_shift_pct", params.get("impact", -5.0)))
    inflation_rate = float(params.get("inflation_rate", 3.2))

    horizon_impacts: Dict[str, Any] = {}
    for h_key, months in HORIZON_MONTHS.items():
        inf_factor = 1.0 + (inflation_rate / 100.0) * (months / 12.0)
        base_val = round(base_spending * months * inf_factor, 2)
        
        adj_factor = 1.0 + (spending_shift_pct / 100.0)
        exp_val = round(base_spending * adj_factor * months * inf_factor, 2)
        best_val = round(exp_val * 0.90, 2)
        worst_val = round(exp_val * 1.18, 2)

        horizon_impacts[h_key] = {
            "label": HORIZON_LABELS[h_key],
            "baseline": base_val,
            "expected": exp_val,
            "best": best_val,
            "worst": worst_val,
            "delta": round(exp_val - base_val, 2),
            "unit": "$",
        }

    active_h = selected_horizon if selected_horizon in HORIZON_MONTHS else "1_month"
    h_data = horizon_impacts[active_h]
    current_val = h_data["baseline"]
    expected_val = h_data["expected"]
    best_val = h_data["best"]
    worst_val = h_data["worst"]
    risk_val = round(expected_val * 1.35, 2)

    scenarios = [
        ScenarioResult(
            scenario_name="Current Path",
            projected_outcomes={"spending": current_val, "score": current_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Expected Case",
            projected_outcomes={"spending": expected_val, "score": expected_val},
            risk_level="Medium" if spending_shift_pct > 10 else "Low",
            warnings=["Discretionary expense acceleration detected."] if spending_shift_pct > 10 else [],
        ),
        ScenarioResult(
            scenario_name="Best Case",
            projected_outcomes={"spending": best_val, "score": best_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Worst Case",
            projected_outcomes={"spending": worst_val, "score": worst_val},
            risk_level="High" if worst_val > current_val * 1.25 else "Medium",
            warnings=["Inflation pressure and unplanned spending breach tolerance."] if worst_val > current_val * 1.25 else [],
        ),
        ScenarioResult(
            scenario_name="Risk Scenario",
            projected_outcomes={"spending": risk_val, "score": risk_val},
            risk_level="Critical",
            warnings=["Major spending shock: Discretionary burn rate unsustainable long-term."],
        ),
    ]

    key_metrics = {
        "base_spending": current_val,
        "projected_spending": expected_val,
        "spending_delta": h_data["delta"],
        "spending_shift_pct": spending_shift_pct,
    }

    return scenarios, horizon_impacts, key_metrics


def generate_academic_scenarios(
    dt_state: Any, params: Dict[str, Any], selected_horizon: str = "1_month"
) -> Tuple[List[ScenarioResult], Dict[str, Any], Dict[str, Any]]:
    base_score = 75.0
    if hasattr(dt_state, "academic") and dt_state.academic:
        base_score = float(dt_state.academic.metrics.get("avg_focus_score", 75.0) or 75.0)
    
    study_hours_delta = float(params.get("study_hours_delta", params.get("impact", 1.5)))
    focus_boost = float(params.get("focus_boost", 5.0))

    horizon_impacts: Dict[str, Any] = {}
    for h_key, months in HORIZON_MONTHS.items():
        base_val = round(base_score, 1)
        # Non-linear gain plateauing smoothly
        gain = (study_hours_delta * 2.8 + focus_boost * 0.4) * (min(months, 3.0) ** 0.45)
        exp_val = round(min(99.0, max(40.0, base_score + gain)), 1)
        best_val = round(min(100.0, exp_val + 6.0), 1)
        worst_val = round(max(35.0, base_score - abs(study_hours_delta) * 1.2), 1)

        horizon_impacts[h_key] = {
            "label": HORIZON_LABELS[h_key],
            "baseline": base_val,
            "expected": exp_val,
            "best": best_val,
            "worst": worst_val,
            "delta": round(exp_val - base_val, 1),
            "unit": "pts",
        }

    active_h = selected_horizon if selected_horizon in HORIZON_MONTHS else "1_month"
    h_data = horizon_impacts[active_h]
    current_val = h_data["baseline"]
    expected_val = h_data["expected"]
    best_val = h_data["best"]
    worst_val = h_data["worst"]
    risk_val = round(max(30.0, expected_val - 20.0), 1)

    scenarios = [
        ScenarioResult(
            scenario_name="Current Path",
            projected_outcomes={"score": current_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Expected Case",
            projected_outcomes={"score": expected_val},
            risk_level="Low" if expected_val >= 70 else "Medium",
            warnings=[] if expected_val >= 70 else ["Target score below proficiency threshold."],
        ),
        ScenarioResult(
            scenario_name="Best Case",
            projected_outcomes={"score": best_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Worst Case",
            projected_outcomes={"score": worst_val},
            risk_level="High" if worst_val < 60 else "Medium",
            warnings=["Inconsistent study habits cause score drop."] if worst_val < 60 else [],
        ),
        ScenarioResult(
            scenario_name="Risk Scenario",
            projected_outcomes={"score": risk_val},
            risk_level="Critical" if risk_val < 50 else "High",
            warnings=["Severe cramming burnout or exam failure event."] if study_hours_delta > 3.5 else ["Risk scenario modeled."],
        ),
    ]

    key_metrics = {
        "baseline_score": current_val,
        "projected_score": expected_val,
        "score_delta": h_data["delta"],
        "study_hours_delta": study_hours_delta,
    }

    return scenarios, horizon_impacts, key_metrics


def generate_lifestyle_scenarios(
    dt_state: Any, params: Dict[str, Any], selected_horizon: str = "1_month"
) -> Tuple[List[ScenarioResult], Dict[str, Any], Dict[str, Any]]:
    base_vitality = 72.0
    if hasattr(dt_state, "lifestyle_habits") and dt_state.lifestyle_habits:
        base_vitality = float(dt_state.lifestyle_habits.metrics.get("completion_rate", 72.0) or 72.0)

    sleep_delta = float(params.get("sleep_delta", params.get("impact", 1.0)))
    workout_days = float(params.get("workout_days", 3.0))

    horizon_impacts: Dict[str, Any] = {}
    for h_key, months in HORIZON_MONTHS.items():
        base_val = round(base_vitality, 1)
        vitality_gain = (sleep_delta * 4.5 + workout_days * 2.2) * (min(months, 4.0) ** 0.4)
        exp_val = round(min(98.0, max(25.0, base_vitality + vitality_gain)), 1)
        best_val = round(min(100.0, exp_val + 7.5), 1)
        worst_val = round(max(20.0, base_vitality - abs(sleep_delta) * 2.8), 1)

        horizon_impacts[h_key] = {
            "label": HORIZON_LABELS[h_key],
            "baseline": base_val,
            "expected": exp_val,
            "best": best_val,
            "worst": worst_val,
            "delta": round(exp_val - base_val, 1),
            "unit": "index",
        }

    active_h = selected_horizon if selected_horizon in HORIZON_MONTHS else "1_month"
    h_data = horizon_impacts[active_h]
    current_val = h_data["baseline"]
    expected_val = h_data["expected"]
    best_val = h_data["best"]
    worst_val = h_data["worst"]
    risk_val = round(max(15.0, expected_val - 25.0), 1)

    scenarios = [
        ScenarioResult(
            scenario_name="Current Path",
            projected_outcomes={"score": current_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Expected Case",
            projected_outcomes={"score": expected_val},
            risk_level="Low" if expected_val >= 65 else "Medium",
            warnings=[] if expected_val >= 65 else ["Vitality index indicates sleep/energy deficit."],
        ),
        ScenarioResult(
            scenario_name="Best Case",
            projected_outcomes={"score": best_val},
            risk_level="Low",
            warnings=[],
        ),
        ScenarioResult(
            scenario_name="Worst Case",
            projected_outcomes={"score": worst_val},
            risk_level="High" if worst_val < 50 else "Medium",
            warnings=["Chronic sleep disruption threatens circadian rhythm."] if worst_val < 50 else [],
        ),
        ScenarioResult(
            scenario_name="Risk Scenario",
            projected_outcomes={"score": risk_val},
            risk_level="Critical",
            warnings=["Systemic fatigue and elevated metabolic disorder risk."],
        ),
    ]

    key_metrics = {
        "baseline_vitality": current_val,
        "projected_vitality": expected_val,
        "vitality_delta": h_data["delta"],
        "sleep_delta": sleep_delta,
    }

    return scenarios, horizon_impacts, key_metrics


def generate_generic_scenarios(
    decision_type: str, dt_state: Any, params: Dict[str, Any], selected_horizon: str = "1_month"
) -> Tuple[List[ScenarioResult], Dict[str, Any], Dict[str, Any]]:
    base_val = 100.0
    modifier = float(params.get("impact", 5.0))

    horizon_impacts: Dict[str, Any] = {}
    for h_key, months in HORIZON_MONTHS.items():
        b = round(base_val, 1)
        e = round(base_val + modifier * (months ** 0.3), 1)
        best = round(e + abs(modifier) * 0.5, 1)
        worst = round(base_val - abs(modifier), 1)
        horizon_impacts[h_key] = {
            "label": HORIZON_LABELS[h_key],
            "baseline": b,
            "expected": e,
            "best": best,
            "worst": worst,
            "delta": round(e - b, 1),
            "unit": "pts",
        }

    active_h = selected_horizon if selected_horizon in HORIZON_MONTHS else "1_month"
    h_data = horizon_impacts[active_h]

    scenarios = [
        ScenarioResult(scenario_name="Current Path", projected_outcomes={"score": h_data["baseline"]}, risk_level="Low"),
        ScenarioResult(scenario_name="Expected Case", projected_outcomes={"score": h_data["expected"]}, risk_level="Low"),
        ScenarioResult(scenario_name="Best Case", projected_outcomes={"score": h_data["best"]}, risk_level="Low"),
        ScenarioResult(scenario_name="Worst Case", projected_outcomes={"score": h_data["worst"]}, risk_level="Medium"),
        ScenarioResult(scenario_name="Risk Scenario", projected_outcomes={"score": round(h_data["worst"] - abs(modifier), 1)}, risk_level="High", warnings=["High variance detected."]),
    ]

    key_metrics = {
        "baseline": h_data["baseline"],
        "projected": h_data["expected"],
        "delta": h_data["delta"],
    }

    return scenarios, horizon_impacts, key_metrics


def run_simulation(db: Session, user_id: UUID, request: SimulationRequest) -> SimulationResponse:
    dt_state = get_digital_twin_state(db, user_id)
    params = request.input_parameters or {}
    selected_horizon = str(params.get("time_horizon", "1_month")).lower()
    cat = request.decision_type.lower()

    if cat == "financial":
        scenarios, horizon_impacts, key_metrics = generate_financial_scenarios(dt_state, params, selected_horizon)
    elif cat == "forecasting":
        scenarios, horizon_impacts, key_metrics = generate_forecasting_scenarios(dt_state, params, selected_horizon)
    elif cat in ("academic", "study"):
        scenarios, horizon_impacts, key_metrics = generate_academic_scenarios(dt_state, params, selected_horizon)
    elif cat in ("lifestyle", "habits", "fitness"):
        scenarios, horizon_impacts, key_metrics = generate_lifestyle_scenarios(dt_state, params, selected_horizon)
    else:
        scenarios, horizon_impacts, key_metrics = generate_generic_scenarios(request.decision_type, dt_state, params, selected_horizon)

    predicted_outcome = {s.scenario_name: s.model_dump() for s in scenarios}

    simulation_result = {
        "status": "completed",
        "overall_health": dt_state.overall_state,
        "selected_horizon": selected_horizon,
        "horizon_impacts": horizon_impacts,
        "key_metrics": key_metrics,
    }

    horizon_label = HORIZON_LABELS.get(selected_horizon, "1 Month")
    sim_record = Simulation(
        user_id=user_id,
        decision_type=request.decision_type,
        scenario_name=f"{request.decision_type} Simulation ({horizon_label})",
        simulation_result=simulation_result,
        predicted_outcome=predicted_outcome,
        confidence_score=0.88,
        input_parameters=params,
    )
    db.add(sim_record)
    db.commit()
    db.refresh(sim_record)

    return SimulationResponse.model_validate(sim_record)


def get_user_simulations(db: Session, user_id: UUID, limit: int = 50) -> List[SimulationResponse]:
    sims = db.query(Simulation).filter(Simulation.user_id == user_id).order_by(Simulation.generated_at.desc()).limit(limit).all()
    return [SimulationResponse.model_validate(s) for s in sims]


def get_simulation_by_id(db: Session, sim_id: UUID, user_id: UUID) -> SimulationResponse:
    sim = db.query(Simulation).filter(Simulation.simulation_id == sim_id, Simulation.user_id == user_id).first()
    if not sim:
        return None
    return SimulationResponse.model_validate(sim)


def delete_simulation(db: Session, sim_id: UUID, user_id: UUID) -> bool:
    sim = db.query(Simulation).filter(Simulation.simulation_id == sim_id, Simulation.user_id == user_id).first()
    if not sim:
        return False
    db.delete(sim)
    db.commit()
    return True
