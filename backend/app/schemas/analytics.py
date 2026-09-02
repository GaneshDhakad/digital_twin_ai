from datetime import datetime
from typing import Optional, Any, Dict
from uuid import UUID
from pydantic import BaseModel


from typing import Optional, Any, Dict, Union

class AnalyticsLogResponse(BaseModel):
    log_id: Union[UUID, int, str]
    user_id: Optional[UUID] = None
    activity_type: str
    endpoint: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    metadata_json: Optional[Dict[str, Any]] = None
    timestamp: datetime

    class Config:
        from_attributes = True
