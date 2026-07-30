from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.models.analytics import AnalyticsLog


def log_activity(
    db: Session,
    user_id: Optional[int],
    activity_type: str,
    endpoint: Optional[str] = None,
    method: Optional[str] = None,
    response_time_ms: Optional[float] = None,
    metadata_json: Optional[Dict[str, Any]] = None,
) -> AnalyticsLog:
    log_entry = AnalyticsLog(
        user_id=user_id,
        activity_type=activity_type,
        endpoint=endpoint,
        method=method,
        response_time_ms=response_time_ms,
        metadata_json=metadata_json,
    )
    db.add(log_entry)
    db.commit()
    db.refresh(log_entry)
    return log_entry


def get_user_analytics_logs(db: Session, user_id: int, limit: int = 50) -> List[AnalyticsLog]:
    return (
        db.query(AnalyticsLog)
        .filter(AnalyticsLog.user_id == user_id)
        .order_by(AnalyticsLog.timestamp.desc())
        .limit(limit)
        .all()
    )
