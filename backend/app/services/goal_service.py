from datetime import datetime
from typing import Optional, List, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.goals import Goal
from app.models.reference import GoalCategory
from app.schemas.goals import GoalCreate, GoalUpdate, GoalSummary, GoalResponse


def _resolve_goal_category(db: Session, cat_name: str) -> Optional[GoalCategory]:
    if not cat_name:
        return None
    # 1. Exact match
    cat = db.query(GoalCategory).filter(GoalCategory.name == cat_name).first()
    if cat:
        return cat
    # 2. Case-insensitive or substring match
    cat = db.query(GoalCategory).filter(
        or_(
            GoalCategory.name.ilike(f"{cat_name}%"),
            GoalCategory.name.ilike(f"%{cat_name}%"),
        )
    ).first()
    if cat:
        return cat
    # 3. Create category if not exists
    try:
        new_cat = GoalCategory(name=cat_name, description=f"{cat_name} Goals")
        db.add(new_cat)
        db.flush()
        return new_cat
    except Exception:
        db.rollback()
        return db.query(GoalCategory).first()


def normalize_goal_status(status_str: Optional[str]) -> str:
    if not status_str:
        return "on_track"
    cleaned = status_str.strip().lower().replace(" ", "_")
    valid_statuses = {"on_track", "at_risk", "completed", "abandoned", "behind"}
    if cleaned in valid_statuses:
        return cleaned
    if "track" in cleaned:
        return "on_track"
    if "risk" in cleaned:
        return "at_risk"
    if "complete" in cleaned:
        return "completed"
    if "abandon" in cleaned:
        return "abandoned"
    if "behind" in cleaned:
        return "behind"
    return "on_track"


def add_goal(db: Session, user_id: UUID, data: GoalCreate) -> Goal:
    cat_obj = _resolve_goal_category(db, data.category)
    status_val = normalize_goal_status(getattr(data, "status", None) or "on_track")

    goal = Goal(
        user_id=user_id,
        category_id=cat_obj.category_id if cat_obj else None,
        goal_name=data.goal_name,
        target_value=data.target_value,
        current_progress=0.0,
        target_date=data.target_date,
        status=status_val,
    )
    if cat_obj:
        goal.goal_category = cat_obj
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return goal


def get_goals(db: Session, user_id: UUID, skip: int = 0, limit: int = 100) -> List[GoalResponse]:
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
            category_id=g.category_id,
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


def get_goal_by_id(db: Session, goal_id: Any, user_id: UUID) -> Optional[Goal]:
    parsed_id = goal_id
    if isinstance(goal_id, str):
        try:
            parsed_id = UUID(goal_id)
        except Exception:
            try:
                parsed_id = int(goal_id)
            except Exception:
                pass
    return db.query(Goal).filter(
        Goal.goal_id == parsed_id,
        Goal.user_id == user_id
    ).first()


def update_goal(db: Session, goal_id: Any, user_id: UUID, data: GoalUpdate) -> Optional[Goal]:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return None

    if data.goal_name is not None:
        goal.goal_name = data.goal_name
    if data.category is not None:
        cat_obj = _resolve_goal_category(db, data.category)
        if cat_obj:
            goal.category_id = cat_obj.category_id
            goal.goal_category = cat_obj
    if data.target_value is not None:
        goal.target_value = data.target_value
    if data.target_date is not None:
        goal.target_date = data.target_date
    if data.status is not None:
        goal.status = normalize_goal_status(data.status)

    db.commit()
    db.refresh(goal)
    return goal


def update_goal_progress(db: Session, goal_id: Any, user_id: UUID, progress: float) -> Optional[GoalResponse]:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return None

    goal.current_progress = progress
    if goal.current_progress >= goal.target_value:
        goal.status = "completed"
    elif goal.target_date < datetime.utcnow() and goal.current_progress < goal.target_value:
        goal.status = "at_risk"

    db.commit()
    db.refresh(goal)

    pct = (goal.current_progress / goal.target_value * 100.0) if goal.target_value > 0 else 0.0
    pct = min(100.0, max(0.0, pct))
    return GoalResponse(
        goal_id=goal.goal_id,
        user_id=goal.user_id,
        category_id=goal.category_id,
        goal_name=goal.goal_name,
        category=goal.category,
        target_value=goal.target_value,
        current_progress=goal.current_progress,
        target_date=goal.target_date,
        status=goal.status,
        progress_percentage=round(pct, 1)
    )


def delete_goal(db: Session, goal_id: Any, user_id: UUID) -> bool:
    goal = get_goal_by_id(db, goal_id, user_id)
    if not goal:
        return False
    db.delete(goal)
    db.commit()
    return True


def get_goal_summary(db: Session, user_id: UUID) -> GoalSummary:
    goals = db.query(Goal).filter(Goal.user_id == user_id).all()
    
    on_track = sum(1 for g in goals if g.status in ("on_track", "On Track"))
    at_risk = sum(1 for g in goals if g.status in ("at_risk", "At Risk"))
    completed = sum(1 for g in goals if g.status in ("completed", "Completed"))

    return GoalSummary(
        total_goals=len(goals),
        on_track_count=on_track,
        at_risk_count=at_risk,
        completed_count=completed,
    )
