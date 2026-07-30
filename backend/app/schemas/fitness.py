from datetime import datetime
from typing import Optional, Dict
from pydantic import BaseModel, Field


class FitnessActivityCreate(BaseModel):
    activity_type: str = Field(..., min_length=1, description="e.g. Running, Gym, Yoga, Cycling")
    duration: float = Field(..., gt=0, description="Duration in minutes")
    calories_burned: Optional[float] = Field(0.0, ge=0)
    activity_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class FitnessActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    duration: Optional[float] = Field(None, gt=0)
    calories_burned: Optional[float] = Field(None, ge=0)
    activity_date: Optional[datetime] = None


class FitnessActivityResponse(BaseModel):
    fitness_id: int
    user_id: int
    activity_type: str
    duration: float
    calories_burned: float
    activity_date: datetime

    class Config:
        from_attributes = True


class FitnessSummary(BaseModel):
    weekly_activity_count: int
    total_calories: float
    total_duration_minutes: float
    activity_breakdown: Dict[str, int]
