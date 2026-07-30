from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.fitness import (
    FitnessActivityCreate,
    FitnessActivityUpdate,
    FitnessActivityResponse,
    FitnessSummary,
)
from app.services.fitness_service import (
    add_fitness_activity,
    get_fitness_activities,
    get_fitness_activity_by_id,
    update_fitness_activity,
    delete_fitness_activity,
    get_fitness_summary,
)

router = APIRouter(
    prefix="/fitness",
    tags=["Fitness Activities"],
)


@router.post("/activities", response_model=FitnessActivityResponse, status_code=status.HTTP_201_CREATED)
def create_activity(
    data: FitnessActivityCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_fitness_activity(db, current_user.user_id, data)


@router.get("/activities", response_model=List[FitnessActivityResponse])
def list_activities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_fitness_activities(db, current_user.user_id, skip=skip, limit=limit)


@router.get("/summary", response_model=FitnessSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_fitness_summary(db, current_user.user_id)


@router.put("/activities/{fitness_id}", response_model=FitnessActivityResponse)
def update_activity(
    fitness_id: int,
    data: FitnessActivityUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_fitness_activity(db, fitness_id, current_user.user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness activity record not found",
        )
    return updated


@router.delete("/activities/{fitness_id}", status_code=status.HTTP_200_OK)
def delete_activity(
    fitness_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_fitness_activity(db, fitness_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Fitness activity record not found",
        )
    return {"message": "Fitness activity record successfully deleted"}
