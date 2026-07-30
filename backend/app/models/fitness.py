from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class FitnessActivity(Base):
    __tablename__ = "fitness_activities"

    fitness_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    activity_type = Column(String, nullable=False) # Running, Gym, Yoga, Cycling, etc.
    duration = Column(Float, nullable=False) # minutes
    calories_burned = Column(Float, default=0.0, nullable=False)
    activity_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

    user = relationship("User", back_populates="fitness_activities")

__table_args__ = (
    Index("idx_user_fitness_date", FitnessActivity.user_id, FitnessActivity.activity_date),
)
