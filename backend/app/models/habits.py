import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.reference import HabitType


class HabitTracking(Base):
    __tablename__ = "habit_tracking"

    habit_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    habit_type_id = Column(UUID(as_uuid=True), ForeignKey("habit_types.habit_type_id", ondelete="SET NULL"), nullable=True)
    habit_name = Column(String(150), nullable=False)
    status = Column(String(20), nullable=False, default="completed") # completed, missed, partial, skipped
    completion_rate = Column(Float, default=100.0, nullable=False)
    streak_count = Column(Integer, default=0, nullable=False)
    impact_level = Column(String(10), default="medium", nullable=False) # low, medium, high, critical
    record_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="habit_trackings")
    habit_type = relationship("HabitType", lazy="joined")

    __table_args__ = (
        Index("idx_user_habit_date", "user_id", "record_date"),
    )
