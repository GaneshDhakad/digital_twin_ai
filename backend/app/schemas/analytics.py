from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel


class AnalyticsLogResponse(BaseModel):
    log_id: int
    user_id: Optional[int] = None
    activity_type: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    response_time_ms: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
