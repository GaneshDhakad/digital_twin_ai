from datetime import datetime
from typing import Optional, List, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.habits import HabitTracking
from app.models.reference import HabitType
from app.schemas.habits import HabitCreate, HabitUpdate, HabitAnalytics


def _resolve_habit_type(db: Session, habit_name: str) -> Optional[HabitType]:
    if not habit_name:
        return None
    ht = db.query(HabitType).filter(HabitType.name == habit_name).first()
    if ht:
        return ht
    ht = db.query(HabitType).filter(
        or_(
            HabitType.name.ilike(f"{habit_name}%"),
            HabitType.name.ilike(f"%{habit_name}%"),
        )
    ).first()
    if ht:
        return ht
    try:
        new_ht = HabitType(name=habit_name, category="Personal", default_impact="medium")
        db.add(new_ht)
        db.flush()
        return new_ht
    except Exception:
        db.rollback()
        return db.query(HabitType).first()


def normalize_impact_level(val: Optional[str]) -> str:
    if not val:
        return "medium"
    cleaned = val.strip().lower()
    if cleaned in {"low", "medium", "high", "critical"}:
        return cleaned
    if "low" in cleaned:
        return "low"
    if "high" in cleaned:
        return "high"
    if "crit" in cleaned:
        return "critical"
    return "medium"


def normalize_habit_status(val: Optional[str]) -> str:
    if not val:
        return "completed"
    cleaned = val.strip().lower()
    if cleaned in {"completed", "missed", "partial", "skipped"}:
        return cleaned
    if "comp" in cleaned:
        return "completed"
    if "miss" in cleaned:
        return "missed"
    if "part" in cleaned:
        return "partial"
    if "skip" in cleaned:
        return "skipped"
    return "completed"


def add_habit(db: Session, user_id: UUID, data: HabitCreate) -> HabitTracking:
    ht_obj = _resolve_habit_type(db, data.habit_name)
    stat = normalize_habit_status(data.status)
    impact = normalize_impact_level(data.impact_level)
    comp_rate = max(0.0, min(100.0, float(data.completion_rate if data.completion_rate is not None else 100.0)))

    # Calculate streak from recent completed habits
    streak = 1 if stat == "completed" else 0
    recent = db.query(HabitTracking).filter(
        HabitTracking.user_id == user_id,
        HabitTracking.habit_name == data.habit_name
    ).order_by(HabitTracking.record_date.desc()).first()
    if recent and stat == "completed":
        streak = (recent.streak_count or 0) + 1

    habit = HabitTracking(
        user_id=user_id,
        habit_type_id=ht_obj.habit_type_id if ht_obj else None,
        habit_name=data.habit_name,
        status=stat,
        completion_rate=comp_rate,
        streak_count=streak,
        impact_level=impact,
        record_date=data.record_date or datetime.utcnow(),
    )
    if ht_obj:
        habit.habit_type = ht_obj
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def get_habits(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[HabitTracking]:
    return (
        db.query(HabitTracking)
        .filter(HabitTracking.user_id == user_id)
        .order_by(HabitTracking.record_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_habit_by_id(db: Session, habit_id: Any, user_id: UUID) -> Optional[HabitTracking]:
    parsed_id = habit_id
    if isinstance(habit_id, str):
        try:
            parsed_id = UUID(habit_id)
        except Exception:
            try:
                parsed_id = int(habit_id)
            except Exception:
                pass
    return db.query(HabitTracking).filter(
        HabitTracking.habit_id == parsed_id,
        HabitTracking.user_id == user_id
    ).first()


def update_habit(db: Session, habit_id: Any, user_id: UUID, data: HabitUpdate) -> Optional[HabitTracking]:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return None

    if data.habit_name is not None:
        habit.habit_name = data.habit_name
        ht_obj = _resolve_habit_type(db, data.habit_name)
        if ht_obj:
            habit.habit_type_id = ht_obj.habit_type_id
            habit.habit_type = ht_obj
    if data.status is not None:
        habit.status = normalize_habit_status(data.status)
    if data.completion_rate is not None:
        habit.completion_rate = max(0.0, min(100.0, float(data.completion_rate)))
    if data.impact_level is not None:
        habit.impact_level = normalize_impact_level(data.impact_level)
    if data.record_date is not None:
        habit.record_date = data.record_date

    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, habit_id: Any, user_id: UUID) -> bool:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return False
    db.delete(habit)
    db.commit()
    return True


def get_habit_analytics(db: Session, user_id: UUID) -> HabitAnalytics:
    habits = db.query(HabitTracking).filter(HabitTracking.user_id == user_id).all()
    if not habits:
        return HabitAnalytics(
            total_habits_logged=0,
            overall_completion_rate=0.0,
            current_streak=0,
            at_risk_habits=[],
        )

    completed = sum(1 for h in habits if h.status == "completed")
    overall_rate = (completed / len(habits)) * 100.0

    # Calculate streak (consecutive completed entries)
    sorted_habits = sorted(habits, key=lambda x: x.record_date, reverse=True)
    streak = 0
    for h in sorted_habits:
        if h.status == "completed":
            streak += 1
        else:
            break

    # Calculate per-habit completion rate to find at-risk (< 60%)
    habit_counts = {}
    habit_completed = {}
    for h in habits:
        name = h.habit_name
        habit_counts[name] = habit_counts.get(name, 0) + 1
        if h.status == "completed":
            habit_completed[name] = habit_completed.get(name, 0) + 1

    at_risk = []
    for name, count in habit_counts.items():
        comp_count = habit_completed.get(name, 0)
        rate = (comp_count / count) * 100.0
        if rate < 60.0:
            at_risk.append(name)

    return HabitAnalytics(
        total_habits_logged=len(habits),
        overall_completion_rate=round(overall_rate, 1),
        current_streak=streak,
        at_risk_habits=at_risk,
    )
