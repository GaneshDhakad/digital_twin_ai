from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.analytics import AnalyticsLogResponse
from app.services.analytics_service import get_user_analytics_logs

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics Logs"],
)


@router.get("/activity-log", response_model=List[AnalyticsLogResponse])
def get_activity_log(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_user_analytics_logs(db, current_user.user_id, limit=limit)
