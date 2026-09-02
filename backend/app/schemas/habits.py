from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


from typing import Optional, List, Union

class HabitCreate(BaseModel):
    habit_name: str = Field(..., min_length=1)
    status: str = Field("completed", description="'completed', 'missed', 'partial', 'skipped'")
    completion_rate: Optional[float] = Field(100.0, ge=0, le=100)
    impact_level: Optional[str] = Field("medium", description="'low', 'medium', 'high', 'critical'")
    record_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class HabitUpdate(BaseModel):
    habit_name: Optional[str] = None
    status: Optional[str] = None
    completion_rate: Optional[float] = Field(None, ge=0, le=100)
    impact_level: Optional[str] = None
    record_date: Optional[datetime] = None


class HabitResponse(BaseModel):
    habit_id: Union[UUID, int, str]
    user_id: UUID
    habit_type_id: Optional[UUID] = None
    habit_name: str
    status: str
    completion_rate: float
    streak_count: int = 0
    impact_level: str
    record_date: datetime

    class Config:
        from_attributes = True


class HabitAnalytics(BaseModel):
    total_habits_logged: int
    overall_completion_rate: float
    current_streak: int
    at_risk_habits: List[str]
