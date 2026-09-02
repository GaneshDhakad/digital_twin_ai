from datetime import datetime
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field


class StudyActivityCreate(BaseModel):
    subject: str = Field(..., min_length=1)
    study_hours: float = Field(..., gt=0)
    performance_score: Optional[float] = Field(80.0, ge=0, le=100)
    task_completion_rate: Optional[float] = Field(100.0, ge=0, le=100)
    activity_date: Optional[datetime] = Field(default_factory=datetime.utcnow)


class StudyActivityUpdate(BaseModel):
    subject: Optional[str] = None
    study_hours: Optional[float] = Field(None, gt=0)
    performance_score: Optional[float] = Field(None, ge=0, le=100)
    task_completion_rate: Optional[float] = Field(None, ge=0, le=100)
    activity_date: Optional[datetime] = None


from typing import Optional, Dict, Union

class StudyActivityResponse(BaseModel):
    activity_id: Union[UUID, int, str]
    user_id: UUID
    subject_id: Optional[UUID] = None
    subject: str
    study_hours: float
    performance_score: Optional[float] = 80.0
    task_completion_rate: float
    activity_date: datetime

    class Config:
        from_attributes = True


class StudySummary(BaseModel):
    avg_focus_score: float
    task_completion_rate: float
    total_hours: float
    peak_hours: str
    subject_breakdown: Dict[str, float]
