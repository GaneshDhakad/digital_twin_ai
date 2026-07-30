from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.habits import (
    HabitCreate,
    HabitUpdate,
    HabitResponse,
    HabitAnalytics,
)
from app.services.habit_service import (
    add_habit,
    get_habits,
    get_habit_by_id,
    update_habit,
    delete_habit,
    get_habit_analytics,
)

router = APIRouter(
    prefix="/habits",
    tags=["Habit Tracking"],
)


@router.post("", response_model=HabitResponse, status_code=status.HTTP_201_CREATED)
def create_habit(
    data: HabitCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_habit(db, current_user.user_id, data)


@router.get("", response_model=List[HabitResponse])
def list_habits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_habits(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/analytics", response_model=HabitAnalytics)
def get_analytics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_habit_analytics(db, current_user.user_id)


@router.put("/{habit_id}", response_model=HabitResponse)
def update_habit_entry(
    habit_id: int,
    data: HabitUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_habit(db, habit_id, current_user.user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit entry not found",
        )
    return updated


@router.delete("/{habit_id}", status_code=status.HTTP_200_OK)
def delete_habit_entry(
    habit_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_habit(db, habit_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Habit entry not found",
        )
    return {"message": "Habit entry successfully deleted"}
