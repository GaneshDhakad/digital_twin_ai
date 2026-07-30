from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    recommendation_text = Column(String, nullable=False)
    category = Column(String, nullable=False)
    priority = Column(String, default="Medium", nullable=False) # High, Medium, Low
    confidence_score = Column(Float, default=0.85, nullable=False)
    action_plan = Column(JSON, nullable=True)
    is_actioned = Column(Boolean, default=False, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="recommendations")
