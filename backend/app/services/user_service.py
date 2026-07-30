from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.user import User
from app.models.financial import FinancialRecord
from app.models.goals import Goal
from app.models.habits import HabitTracking
from app.models.study import StudyActivity
from app.models.fitness import FitnessActivity
from app.schemas.user import UserCreate, UserUpdate, UserSummaryResponse
from app.core.security import hash_password


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.user_id == user_id, User.is_active == True).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user_data: UserCreate) -> User:
    hashed_pwd = hash_password(user_data.password)
    db_user = User(
        email=user_data.email,
        name=user_data.name,
        password_hash=hashed_pwd,
        age=user_data.age,
        occupation=user_data.occupation,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user_profile(db: Session, user: User, update_data: UserUpdate) -> User:
    if update_data.name is not None:
        user.name = update_data.name
    if update_data.age is not None:
        user.age = update_data.age
    if update_data.occupation is not None:
        user.occupation = update_data.occupation
    
    db.commit()
    db.refresh(user)
    return user


def soft_delete_user(db: Session, user: User) -> User:
    user.is_active = False
    db.commit()
    return user


def get_user_dashboard_summary(db: Session, user_id: int) -> UserSummaryResponse:
    total_fin = db.query(FinancialRecord).filter(FinancialRecord.user_id == user_id).count()
    active_goals = db.query(Goal).filter(Goal.user_id == user_id, Goal.status != "Completed").count()
    
    # Calculate streak from recent completed habits
    habits = db.query(HabitTracking).filter(
        HabitTracking.user_id == user_id,
        HabitTracking.status == "completed"
    ).count()
    
    total_study = db.query(func.sum(StudyActivity.study_hours)).filter(
        StudyActivity.user_id == user_id
    ).scalar() or 0.0
    
    weekly_fitness = db.query(FitnessActivity).filter(
        FitnessActivity.user_id == user_id
    ).count()
    
    return UserSummaryResponse(
        total_financial_records=total_fin,
        active_goals=active_goals,
        habit_streak=habits,
        total_study_hours=round(float(total_study), 2),
        weekly_workout_count=weekly_fitness
    )
