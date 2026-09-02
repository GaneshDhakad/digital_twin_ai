import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, Boolean, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    recommendation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    recommendation_text = Column(String, nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), default="medium", nullable=False) # low, medium, high, critical
    confidence_score = Column(Float, default=0.85, nullable=False)
    action_plan = Column(JSON, nullable=True)
    is_actioned = Column(Boolean, default=False, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="recommendations")
