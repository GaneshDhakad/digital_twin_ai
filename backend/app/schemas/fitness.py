from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field


from typing import Optional, Dict, Union

class FitnessActivityCreate(BaseModel):
    activity_type: str = Field(..., min_length=1, description="e.g. Running, Gym, Yoga, Cycling")
    duration: Optional[float] = Field(None, gt=0, description="Duration in minutes")
    duration_minutes: Optional[float] = Field(None, gt=0, description="Duration in minutes")
    calories_burned: Optional[float] = Field(0.0, ge=0)
    intensity_level: Optional[str] = Field("moderate", description="low, moderate, high, extreme")
    activity_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class FitnessActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    duration: Optional[float] = Field(None, gt=0)
    duration_minutes: Optional[float] = Field(None, gt=0)
    calories_burned: Optional[float] = Field(None, ge=0)
    intensity_level: Optional[str] = None
    activity_date: Optional[datetime] = None


class FitnessActivityResponse(BaseModel):
    fitness_id: Union[UUID, int, str]
    user_id: UUID
    activity_type: str
    duration: float
    duration_minutes: Optional[float] = None
    calories_burned: float
    intensity_level: Optional[str] = "moderate"
    activity_date: datetime

    class Config:
        from_attributes = True


class FitnessSummary(BaseModel):
    weekly_activity_count: int
    total_calories: float
    total_duration_minutes: float
    activity_breakdown: Dict[str, int]
