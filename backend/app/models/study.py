from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class StudyActivity(Base):
    __tablename__ = "study_activities"

    activity_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    study_hours = Column(Float, nullable=False)
    subject = Column(String, nullable=False)
    performance_score = Column(Float, nullable=True, default=80.0)
    task_completion_rate = Column(Float, nullable=False, default=100.0)
    activity_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="study_activities")

__table_args__ = (
    Index("idx_user_study_date", StudyActivity.user_id, StudyActivity.activity_date),
)
