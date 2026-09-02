import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.reference import GoalCategory


class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("goal_categories.category_id", ondelete="SET NULL"), nullable=True)
    goal_name = Column(String(200), nullable=False)
    target_value = Column(Float, nullable=False)
    current_progress = Column(Float, default=0.0, nullable=False)
    target_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="on_track", nullable=False) # on_track, at_risk, completed, abandoned, behind
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="goals")
    goal_category = relationship("GoalCategory", lazy="joined")

    @hybrid_property
    def category(self) -> str:
        if self.goal_category:
            return self.goal_category.name
        return "General"

    @category.setter
    def category(self, value: str):
        pass

    @category.expression
    def category(cls):
        return GoalCategory.name
