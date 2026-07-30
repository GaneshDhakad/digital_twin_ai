from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.study import (
    StudyActivityCreate,
    StudyActivityUpdate,
    StudyActivityResponse,
    StudySummary,
)
from app.services.study_service import (
    add_study_activity,
    get_study_activities,
    get_study_activity_by_id,
    update_study_activity,
    delete_study_activity,
    get_study_summary,
)

router = APIRouter(
    prefix="/study",
    tags=["Study Activities"],
)


@router.post("/activities", response_model=StudyActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    data: StudyActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_study_activity(db, current_user.user_id, data)


@router.get("/activities", response_model=List[StudyActivityResponse])
def list_activities(
    subject: Optional[str] = Query(None, description="Filter by subject"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_study_activities(db, current_user.user_id, subject=subject, skip=skip, limit=limit)


@router.get("/summary", response_model=StudySummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_study_summary(db, current_user.user_id)


@router.put("/activities/{activity_id}", response_model=StudyActivityResponse)
def update_activity(
    activity_id: int,
    data: StudyActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_study_activity(db, activity_id, current_user.user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study activity record not found",
        )
    return updated


@router.delete("/activities/{activity_id}", status_code=status.HTTP_200_OK)
def delete_activity(
    activity_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_study_activity(db, activity_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Study activity record not found",
        )
    return {"message": "Study activity record successfully deleted"}
