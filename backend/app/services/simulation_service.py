import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.simulations import Simulation
from app.schemas.simulation import SimulationRequest, SimulationResponse, ScenarioResult
from app.services.digital_twin_service import get_digital_twin_state

logger = logging.getLogger(__name__)

def generate_financial_scenarios(dt_state: Any, params: Dict[str, Any]) -> List[ScenarioResult]:
    # Base params
    income = dt_state.financial.metrics.get("total_income", 5000)
    expenses = dt_state.financial.metrics.get("total_expenses", 3000)
    monthly_savings = income - expenses
    
    extra_expense = params.get("extra_expense", 0)
    new_monthly_savings = monthly_savings - extra_expense
    
    scenarios = []
    
    # 1. Current Path
    scenarios.append(ScenarioResult(
        scenario_name="Current Path",
        projected_outcomes={"12_month_savings": monthly_savings * 12},
        risk_level="Low" if monthly_savings > 0 else "High"
    ))
    
    # 2. Expected Case
    scenarios.append(ScenarioResult(
        scenario_name="Expected Case",
        projected_outcomes={"12_month_savings": new_monthly_savings * 12},
        risk_level="Medium" if new_monthly_savings < income * 0.1 else "Low"
    ))
    
    # 3. Best Case (Monte Carlo +15% variance)
    best_savings = new_monthly_savings * 1.15
    scenarios.append(ScenarioResult(
        scenario_name="Best Case",
        projected_outcomes={"12_month_savings": best_savings * 12},
        risk_level="Low"
    ))
    
    # 4. Worst Case (Monte Carlo -20% variance)
    worst_savings = new_monthly_savings * 0.80
    scenarios.append(ScenarioResult(
        scenario_name="Worst Case",
        projected_outcomes={"12_month_savings": worst_savings * 12},
        risk_level="High" if worst_savings <= 0 else "Medium"
    ))
    
    # 5. Risk Scenario (Emergency event: e.g. job loss for 3 months)
    risk_savings = (new_monthly_savings * 9) - (expenses * 3)
    scenarios.append(ScenarioResult(
        scenario_name="Risk Scenario",
        projected_outcomes={"12_month_savings": risk_savings},
        risk_level="Critical" if risk_savings < 0 else "High",
        warnings=["Emergency Fund Guardrail: Savings depleted if 3 month job loss occurs."] if risk_savings < 0 else []
    ))
    
    return scenarios

def generate_generic_scenarios(decision_type: str, dt_state: Any, params: Dict[str, Any]) -> List[ScenarioResult]:
    # A generic fallback for other categories
    # Study, Career, Fitness, Lifestyle, Investment, Loan, Emergency Scenario, Custom Scenario
    base_val = 100
    if decision_type == "Study":
        base_val = dt_state.academic.metrics.get("average_performance", 75)
    
    modifier = params.get("impact", 5)
    
    return [
        ScenarioResult(scenario_name="Current Path", projected_outcomes={"score": base_val}, risk_level="Low"),
        ScenarioResult(scenario_name="Expected Case", projected_outcomes={"score": base_val + modifier}, risk_level="Low"),
        ScenarioResult(scenario_name="Best Case", projected_outcomes={"score": base_val + modifier * 1.5}, risk_level="Low"),
        ScenarioResult(scenario_name="Worst Case", projected_outcomes={"score": base_val - abs(modifier)}, risk_level="Medium"),
        ScenarioResult(scenario_name="Risk Scenario", projected_outcomes={"score": base_val - abs(modifier)*2}, risk_level="High", warnings=["High variance detected."])
    ]

def run_simulation(db: Session, user_id: UUID, request: SimulationRequest) -> SimulationResponse:
    dt_state = get_digital_twin_state(db, user_id)
    
    # Route to specific simulator based on category
    cat = request.decision_type.lower()
    if cat == "financial":
        scenarios = generate_financial_scenarios(dt_state, request.input_parameters)
    else:
        # Generic for Study, Career, Fitness, Lifestyle, Investment, Loan, Emergency, Custom
        scenarios = generate_generic_scenarios(cat, dt_state, request.input_parameters)
        
    # Format into predicted_outcome
    predicted_outcome = {s.scenario_name: s.model_dump() for s in scenarios}
    
    # Persist
    sim_record = Simulation(
        user_id=user_id,
        decision_type=request.decision_type,
        scenario_name=f"{request.decision_type} Simulation",
        simulation_result={"status": "completed", "overall_health": dt_state.overall_state},
        predicted_outcome=predicted_outcome,
        confidence_score=0.85,
        input_parameters=request.input_parameters
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
