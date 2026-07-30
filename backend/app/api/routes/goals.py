from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.goals import (
    GoalCreate,
    GoalUpdate,
    GoalProgressUpdate,
    GoalResponse,
    GoalSummary,
)
from app.services.goal_service import (
    add_goal,
    get_goals,
    get_goal_by_id,
    update_goal,
    update_goal_progress,
    delete_goal,
    get_goal_summary,
)

router = APIRouter(
    prefix="/goals",
    tags=["Goals Management"],
)


@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def create_goal(
    data: GoalCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    created = add_goal(db, current_user.user_id, data)
    return GoalResponse(
        goal_id=created.goal_id,
        user_id=created.user_id,
        goal_name=created.goal_name,
        category=created.category,
        target_value=created.target_value,
        current_progress=created.current_progress,
        target_date=created.target_date,
        status=created.status,
        progress_percentage=0.0,
    )


@router.get("", response_model=List[GoalResponse])
def list_goals(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_goals(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/summary", response_model=GoalSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_goal_summary(db, current_user.user_id)


@router.put("/{goal_id}/progress", response_model=GoalResponse)
def update_progress(
    goal_id: int,
    data: GoalProgressUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_goal_progress(db, goal_id, current_user.user_id, data.current_progress)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return updated


@router.put("/{goal_id}", response_model=GoalResponse)
def update_goal_entry(
    goal_id: int,
    data: GoalUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_goal(db, goal_id, current_user.user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    pct = (updated.current_progress / updated.target_value * 100.0) if updated.target_value > 0 else 0.0
    return GoalResponse(
        goal_id=updated.goal_id,
        user_id=updated.user_id,
        goal_name=updated.goal_name,
        category=updated.category,
        target_value=updated.target_value,
        current_progress=updated.current_progress,
        target_date=updated.target_date,
        status=updated.status,
        progress_percentage=round(min(100.0, max(0.0, pct)), 1),
    )


@router.delete("/{goal_id}", status_code=status.HTTP_200_OK)
def delete_goal_entry(
    goal_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_goal(db, goal_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found",
        )
    return {"message": "Goal successfully deleted"}
