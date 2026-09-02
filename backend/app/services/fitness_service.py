from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session

from app.models.fitness import FitnessActivity
from app.schemas.fitness import FitnessActivityCreate, FitnessActivityUpdate, FitnessSummary


def normalize_intensity(val: Optional[str]) -> str:
    if not val:
        return "moderate"
    cleaned = val.strip().lower()
    if cleaned in {"low", "moderate", "high", "extreme"}:
        return cleaned
    if "low" in cleaned:
        return "low"
    if "high" in cleaned:
        return "high"
    if "ext" in cleaned:
        return "extreme"
    return "moderate"


def add_fitness_activity(db: Session, user_id: UUID, data: FitnessActivityCreate) -> FitnessActivity:
    dur = data.duration_minutes if data.duration_minutes is not None else (data.duration if data.duration is not None else 30.0)
    dur = max(0.0, float(dur))
    cal = max(0.0, float(data.calories_burned or 0.0))
    intensity = normalize_intensity(data.intensity_level)

    activity = FitnessActivity(
        user_id=user_id,
        activity_type=data.activity_type,
        duration_minutes=dur,
        calories_burned=cal,
        intensity_level=intensity,
        activity_date=data.activity_date or datetime.utcnow(),
    )
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity


def get_fitness_activities(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[FitnessActivity]:
    return (
        db.query(FitnessActivity)
        .filter(FitnessActivity.user_id == user_id)
        .order_by(FitnessActivity.activity_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_fitness_activity_by_id(db: Session, fitness_id: Any, user_id: UUID) -> Optional[FitnessActivity]:
    parsed_id = fitness_id
    if isinstance(fitness_id, str):
        try:
            parsed_id = UUID(fitness_id)
        except Exception:
            try:
                parsed_id = int(fitness_id)
            except Exception:
                pass
    return db.query(FitnessActivity).filter(
        FitnessActivity.fitness_id == parsed_id,
        FitnessActivity.user_id == user_id
    ).first()


def update_fitness_activity(
    db: Session,
    fitness_id: Any,
    user_id: UUID,
    data: FitnessActivityUpdate,
) -> Optional[FitnessActivity]:
    activity = get_fitness_activity_by_id(db, fitness_id, user_id)
    if not activity:
        return None

    if data.activity_type is not None:
        activity.activity_type = data.activity_type
    if data.duration_minutes is not None:
        activity.duration_minutes = max(0.0, float(data.duration_minutes))
    elif data.duration is not None:
        activity.duration_minutes = max(0.0, float(data.duration))
    if data.calories_burned is not None:
        activity.calories_burned = max(0.0, float(data.calories_burned))
    if data.intensity_level is not None:
        activity.intensity_level = normalize_intensity(data.intensity_level)
    if data.activity_date is not None:
        activity.activity_date = data.activity_date

    db.commit()
    db.refresh(activity)
    return activity


def delete_fitness_activity(db: Session, fitness_id: Any, user_id: UUID) -> bool:
    activity = get_fitness_activity_by_id(db, fitness_id, user_id)
    if not activity:
        return False
    db.delete(activity)
    db.commit()
    return True


def get_fitness_summary(db: Session, user_id: UUID) -> FitnessSummary:
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
