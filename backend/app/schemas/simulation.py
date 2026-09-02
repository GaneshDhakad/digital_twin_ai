from typing import Dict, Any, Optional, List
from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

class ScenarioResult(BaseModel):
    scenario_name: str  # Current Path, Best Case, Expected Case, Worst Case, Risk Scenario
    projected_outcomes: Dict[str, Any]
    risk_level: str  # Low, Medium, High
    warnings: List[str] = []

class SimulationRequest(BaseModel):
    decision_type: str  # e.g., 'financial', 'study', 'career', 'fitness', 'lifestyle', 'investment', 'loan', 'emergency', 'custom'
    input_parameters: Dict[str, Any]

class SimulationResponse(BaseModel):
    simulation_id: UUID
    decision_type: str
    scenario_name: str
    simulation_result: Any
    predicted_outcome: Any
    confidence_score: Optional[float] = None
    input_parameters: Any
    generated_at: datetime
    
    @field_validator('simulation_result', 'predicted_outcome', 'input_parameters', mode='before')
    @classmethod
    def parse_json_string(cls, v):
        import json
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                pass
        return v
    
    class Config:
        from_attributes = True
