from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from app.models.goals import Goal
from app.schemas.goals import GoalCreate, GoalUpdate, GoalSummary, GoalResponse


def add_goal(db: Session, user_id: int, data: GoalCreate) -> Goal:
    goal = Goal(
        user_id=user_id,
        goal_name=data.goal_name,
        category=data.category,
        target_value=data.target_value,
        current_progress=0.0,
        target_date=data.target_date,
        status="On Track",
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goals(db: Session, user_id: int, skip: int = 0, limit: int = 100) -> List[GoalResponse]:
    goals = (
        db.query(Goal)
        .filter(Goal.user_id == user_id)
        .order_by(Goal.target_date.asc())
        .offset(skip)
        .limit(limit)
        .all()
    )
    
    result = []
    for g in goals:
        pct = (g.current_progress / g.target_value * 100.0) if g.target_value > 0 else 0.0
        pct = min(100.0, max(0.0, pct))
        resp = GoalResponse(
            goal_id=g.goal_id,
            user_id=g.user_id,
            goal_name=g.goal_name,
            category=g.category,
            target_value=g.target_value,
            current_progress=g.current_progress,
            target_date=g.target_date,
            status=g.status,
            progress_percentage=round(pct, 1)
        )
        result.append(resp)
    return result


def get_goal_by_id(db: Session, goal_id: int, user_id: int) -> Optional[Goal]:
    return db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.user_id == user_id
    ).first()


def update_goal(db: Session, goal_id: int, user_id: int, data: GoalUpdate) -> Optional[Goal]:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return None

    if data.goal_name is not None:
        goal.goal_name = data.goal_name
    if data.category is not None:
        goal.category = data.category
    if data.target_value is not None:
        goal.target_value = data.target_value
    if data.target_date is not None:
        goal.target_date = data.target_date
    if data.status is not None:
        goal.status = data.status

    db.commit()
    db.refresh(goal)
    return goal


def update_goal_progress(db: Session, goal_id: int, user_id: int, progress: float) -> Optional[GoalResponse]:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return None

    goal.current_progress = progress
    if goal.current_progress >= goal.target_value:
        goal.status = "Completed"
    elif goal.target_date < datetime.utcnow() and goal.current_progress < goal.target_value:
        goal.status = "At Risk"

    db.commit()
    db.refresh(goal)

    pct = (goal.current_progress / goal.target_value * 100.0) if goal.target_value > 0 else 0.0
    pct = min(100.0, max(0.0, pct))
    return GoalResponse(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        goal_name=goal.goal_name,
        category=goal.category,
        target_value=goal.target_value,
        current_progress=goal.current_progress,
        target_date=goal.target_date,
        status=goal.status,
        progress_percentage=round(pct, 1)
    )


def delete_goal(db: Session, goal_id: int, user_id: int) -> bool:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return False
    db.delete(goal)
    db.commit()
    return True


def get_goal_summary(db: Session, user_id: int) -> GoalSummary:
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    
    on_track = sum(1 for g in goals if g.status == "On Track")
    at_risk = sum(1 for g in goals if g.status == "At Risk")
    completed = sum(1 for g in goals if g.status == "Completed")

    return GoalSummary(
        total_goals=len(goals),
        on_track_count=on_track,
        at_risk_count=at_risk,
        completed_count=completed,
    )
