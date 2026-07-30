from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.user import UserUpdate, UserProfileResponse, UserSummaryResponse
from app.services.user_service import (
    update_user_profile,
    soft_delete_user,
    get_user_dashboard_summary,
)

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get("/profile", response_model=UserProfileResponse)
def get_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    summary = get_user_dashboard_summary(db, current_user.user_id)
    return UserProfileResponse(
        user_id=current_user.user_id,
        name=current_user.name,
        email=current_user.email,
        age=current_user.age,
        occupation=current_user.occupation,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        active_goals_count=summary.active_goals,
        habit_streak=summary.habit_streak,
    )


@router.put("/profile", response_model=UserProfileResponse)
def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_user_profile(db, current_user, update_data)
    summary = get_user_dashboard_summary(db, updated.user_id)
    return UserProfileResponse(
        user_id=updated.user_id,
        name=updated.name,
        email=updated.email,
        age=updated.age,
        occupation=updated.occupation,
        role=updated.role,
        is_active=updated.is_active,
        created_at=updated.created_at,
        active_goals_count=summary.active_goals,
        habit_streak=summary.habit_streak,
    )


@router.delete("/profile", status_code=status.HTTP_200_OK)
def delete_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    soft_delete_user(db, current_user)
    return {"message": "User account successfully deactivated"}


@router.get("/summary", response_model=UserSummaryResponse)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_dashboard_summary(db, current_user.user_id)
