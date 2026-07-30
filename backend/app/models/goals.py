from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from app.core.database import Base


class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    goal_name = Column(String, nullable=False)
    category = Column(String, nullable=False) # Financial, Academic, Fitness, Habit, Career
    target_value = Column(Float, nullable=False)
    current_progress = Column(Float, default=0.0, nullable=False)
    target_date = Column(DateTime, nullable=False)
    status = Column(String, default="On Track", nullable=False) # On Track, At Risk, Completed

    user = relationship("User", back_populates="goals")
