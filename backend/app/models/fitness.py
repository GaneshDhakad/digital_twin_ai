import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.database import Base


class FitnessActivity(Base):
    __tablename__ = "fitness_activities"

    fitness_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    activity_type = Column(String(100), nullable=False) # Running, Gym, Yoga, Cycling, etc.
    duration_minutes = Column(Float, nullable=False) # minutes
    calories_burned = Column(Float, default=0.0, nullable=False)
    intensity_level = Column(String(20), default="moderate", nullable=False) # low, moderate, high, extreme
    activity_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="fitness_activities")

    @hybrid_property
    def duration(self) -> float:
        return float(self.duration_minutes) if self.duration_minutes is not None else 0.0

    @duration.setter
    def duration(self, value: float):
        self.duration_minutes = value

    @duration.expression
    def duration(cls):
        return cls.duration_minutes

    __table_args__ = (
        Index("idx_user_fitness_date", "user_id", "activity_date"),
    )
