from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class HabitTracking(Base):
    __tablename__ = "habit_tracking"

    habit_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    habit_name = Column(String, nullable=False)
    status = Column(String, nullable=False, default="completed") # completed, missed
    completion_rate = Column(Float, default=100.0, nullable=False)
    impact_level = Column(String, default="Medium", nullable=False) # Low, Medium, High
    record_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="habit_trackings")

__table_args__ = (
    Index("idx_user_habit_date", HabitTracking.user_id, HabitTracking.record_date),
)
