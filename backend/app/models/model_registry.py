from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON

from app.core.database import Base


class ModelRegistry(Base):
    __tablename__ = "model_registry"

    model_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_name = Column(String, nullable=False)
    algorithm = Column(String, nullable=False)
    version = Column(String, nullable=False)
    metrics = Column(JSON, nullable=True)
    feature_importances = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    trained_at = Column(DateTime, default=datetime.utcnow, nullable=False)
