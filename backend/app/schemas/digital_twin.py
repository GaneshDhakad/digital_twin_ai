from typing import Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime

class DomainState(BaseModel):
    status: str  # healthy, stable, improving, declining, at-risk, critical
    metrics: Dict[str, Any]
    last_updated: datetime

class MLPredictions(BaseModel):
    academic: Optional[Dict[str, Any]] = None
    lifestyle: Optional[Dict[str, Any]] = None
    financial: Optional[Dict[str, Any]] = None
    forecasting: Optional[Dict[str, Any]] = None
    fitness: Optional[Dict[str, Any]] = None
    retrieved_at: str

class DigitalTwinState(BaseModel):
    user_id: str
    overall_state: str  # healthy, stable, at-risk, etc.
    financial: DomainState
    academic: DomainState
    fitness: DomainState
    lifestyle_habits: DomainState
    goals: DomainState
    ml_predictions: MLPredictions
    generated_at: datetime

    class Config:
        from_attributes = True
