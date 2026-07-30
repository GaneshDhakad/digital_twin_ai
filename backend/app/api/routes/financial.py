from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.financial import (
    FinancialRecordCreate,
    FinancialRecordUpdate,
    FinancialRecordResponse,
    FinancialSummary,
)
from app.services.financial_service import (
    add_financial_record,
    get_financial_records,
    get_financial_record_by_id,
    update_financial_record,
    delete_financial_record,
    get_financial_summary,
)

router = APIRouter(
    prefix="/financial",
    tags=["Financial"],
)


@router.post("/records", response_model=FinancialRecordResponse, status_code=status.HTTP_201_CREATED)
def create_record(
    data: FinancialRecordCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return add_financial_record(db, current_user.user_id, data)


@router.get("/records", response_model=List[FinancialRecordResponse])
def list_records(
    category: Optional[str] = Query(None, description="Filter by category"),
    month: Optional[str] = Query(None, description="Filter by month (YYYY-MM)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_financial_records(db, current_user.user_id, category=category, month=month, skip=skip, limit=limit)


@router.get("/summary", response_model=FinancialSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_financial_summary(db, current_user.user_id)


@router.get("/records/{record_id}", response_model=FinancialRecordResponse)
def get_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    record = get_financial_record_by_id(db, record_id, current_user.user_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found",
        )
    return record


@router.put("/records/{record_id}", response_model=FinancialRecordResponse)
def update_record(
    record_id: int,
    data: FinancialRecordUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    updated = update_financial_record(db, record_id, current_user.user_id, data)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found",
        )
    return updated


@router.delete("/records/{record_id}", status_code=status.HTTP_200_OK)
def delete_record(
    record_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    success = delete_financial_record(db, record_id, current_user.user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Financial record not found",
        )
    return {"message": "Financial record successfully deleted"}
