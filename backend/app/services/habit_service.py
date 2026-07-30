from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.habits import HabitTracking
from app.schemas.habits import HabitCreate, HabitUpdate, HabitAnalytics


def add_habit(db: Session, user_id: int, data: HabitCreate) -> HabitTracking:
    habit = HabitTracking(
        user_id=user_id,
        habit_name=data.habit_name,
        status=data.status.lower(),
        completion_rate=data.completion_rate or 100.0,
        impact_level=data.impact_level or "Medium",
        record_date=data.record_date,
    )
    db.add(habit)
    db.commit()
    db.refresh(habit)
    return habit


def get_habits(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[HabitTracking]:
    return (
        db.query(HabitTracking)
        .filter(HabitTracking.user_id == user_id)
        .order_by(HabitTracking.record_date.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_habit_by_id(db: Session, habit_id: int, user_id: int) -> Optional[HabitTracking]:
    return db.query(HabitTracking).filter(
        HabitTracking.habit_id == habit_id,
        HabitTracking.user_id == user_id
    ).first()


def update_habit(db: Session, habit_id: int, user_id: int, data: HabitUpdate) -> Optional[HabitTracking]:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return None

    if data.habit_name is not None:
        habit.habit_name = data.habit_name
    if data.status is not None:
        habit.status = data.status.lower()
    if data.completion_rate is not None:
        habit.completion_rate = data.completion_rate
    if data.impact_level is not None:
        habit.impact_level = data.impact_level
    if data.record_date is not None:
        habit.record_date = data.record_date

    db.commit()
    db.refresh(habit)
    return habit


def delete_habit(db: Session, habit_id: int, user_id: int) -> bool:
    habit = get_habit_by_id(db, habit_id, user_id)
    if not habit:
        return False
    db.delete(habit)
    db.commit()
    return True


def get_habit_analytics(db: Session, user_id: int) -> HabitAnalytics:
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
