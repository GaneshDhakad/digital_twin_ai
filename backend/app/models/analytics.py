from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class AnalyticsLog(Base):
    __tablename__ = "analytics_logs"

    log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=True)
    activity_type = Column(String, nullable=False)
    endpoint = Column(String, nullable=True)
    method = Column(String, nullable=True)
    response_time_ms = Column(Float, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="analytics_logs")
