from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime, Text, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class UserSetting(Base):
    __tablename__ = "user_settings"

    setting_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), unique=True, nullable=False)
    theme = Column(String(20), nullable=False, default="light")
    notifications_enabled = Column(Boolean, nullable=False, default=True)
    email_alerts = Column(Boolean, nullable=False, default=True)
    ai_personality = Column(String(50), nullable=False, default="analytical")
    risk_tolerance = Column(String(20), nullable=False, default="moderate")
    custom_preferences = Column(JSON, default={})
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="settings")


class Notification(Base):
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    title = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, default="info")
    is_read = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="notifications")


class PredictionCache(Base):
    __tablename__ = "prediction_cache"

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    model_name = Column(String(100), nullable=False)
    prediction_data = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="prediction_caches")


class AIConversation(Base):
    __tablename__ = "ai_conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    prompt = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context_domain = Column(String(50), default="general")
    tokens_used = Column(Integer, default=0)
    feedback_score = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="ai_conversations")
