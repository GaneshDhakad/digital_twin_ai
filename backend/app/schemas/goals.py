from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    goal_name: str = Field(..., min_length=1)
    category: str = Field(..., min_length=1, description="Financial, Academic, Fitness, Habit, Career")
    target_value: float = Field(..., gt=0)
    target_date: datetime


class GoalUpdate(BaseModel):
    goal_name: Optional[str] = None
    category: Optional[str] = None
    target_value: Optional[float] = Field(None, gt=0)
    target_date: Optional[datetime] = None
    status: Optional[str] = None


class GoalProgressUpdate(BaseModel):
    current_progress: float = Field(..., ge=0)


class GoalResponse(BaseModel):
    goal_id: int
    user_id: int
    goal_name: str
    category: str
    target_value: float
    current_progress: float
    target_date: datetime
    status: str
    progress_percentage: float = 0.0

    class Config:
        from_attributes = True


class GoalSummary(BaseModel):
    total_goals: int
    on_track_count: int
    at_risk_count: int
    completed_count: int
