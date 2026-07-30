from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from app.models.fitness import FitnessActivity
from app.schemas.fitness import FitnessActivityCreate, FitnessActivityUpdate, FitnessSummary


def add_fitness_activity(db: Session, user_id: int, data: FitnessActivityCreate) -> FitnessActivity:
    activity = FitnessActivity(
        user_id=user_id,
        activity_type=data.activity_type,
        duration=data.duration,
        calories_burned=data.calories_burned or 0.0,
        activity_date=data.activity_date,
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_fitness_activities(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[FitnessActivity]:
    return (
        db.query(FitnessActivity)
        .filter(FitnessActivity.user_id == user_id)
        .order_by(FitnessActivity.activity_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_fitness_activity_by_id(db: Session, fitness_id: int, user_id: int) -> Optional[FitnessActivity]:
    return db.query(FitnessActivity).filter(
        FitnessActivity.fitness_id == fitness_id,
        FitnessActivity.user_id == user_id
    ).first()


def update_fitness_activity(
    db: Session,
    fitness_id: int,
    user_id: int,
    data: FitnessActivityUpdate,
) -> Optional[FitnessActivity]:
    activity = get_fitness_activity_by_id(db, fitness_id, user_id)
    if not activity:
        return None

    if data.activity_type is not None:
        activity.activity_type = data.activity_type
    if data.duration is not None:
        activity.duration = data.duration
    if data.calories_burned is not None:
        activity.calories_burned = data.calories_burned
    if data.activity_date is not None:
        activity.activity_date = data.activity_date

    db.commit()
    db.refresh(activity)
    return activity


def delete_fitness_activity(db: Session, fitness_id: int, user_id: int) -> bool:
    activity = get_fitness_activity_by_id(db, fitness_id, user_id)
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


def get_fitness_summary(db: Session, user_id: int) -> FitnessSummary:
    activities = db.query(FitnessActivity).filter(FitnessActivity.user_id == user_id).all()
    if not activities:
        return FitnessSummary(
            weekly_activity_count=0,
            total_calories=0.0,
            total_duration_minutes=0.0,
            activity_breakdown={},
        )

    tot_cal = sum(a.calories_burned for a in activities)
    tot_dur = sum(a.duration for a in activities)
    
    breakdown: Dict[str, int] = {}
    for a in activities:
        breakdown[a.activity_type] = breakdown.get(a.activity_type, 0) + 1

    return FitnessSummary(
        weekly_activity_count=len(activities),
        total_calories=round(tot_cal, 1),
        total_duration_minutes=round(tot_dur, 1),
        activity_breakdown=breakdown,
    )
