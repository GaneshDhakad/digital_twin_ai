from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters long")
    name: str = Field(..., min_length=1)
    age: Optional[int] = Field(None, ge=13, le=120)
    occupation: Optional[str] = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = Field(None, ge=13, le=120)
    occupation: Optional[str] = None


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    age: Optional[int] = None
    occupation: Optional[str] = None
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserProfileResponse(UserResponse):
    active_goals_count: int = 0
    habit_streak: int = 0


class UserSummaryResponse(BaseModel):
    total_financial_records: int = 0
    active_goals: int = 0
    habit_streak: int = 0
    total_study_hours: float = 0.0
    weekly_workout_count: int = 0


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse