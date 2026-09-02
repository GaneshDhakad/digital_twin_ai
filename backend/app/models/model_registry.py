import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    domain = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    algorithm = Column(String(100), nullable=False)
    version = Column(String(20), nullable=False)
    metrics = Column(JSON, nullable=True)
    feature_importances = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
