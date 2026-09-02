import uuid
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.reference import SimulationTemplate


class Simulation(Base):
    __tablename__ = "simulations"

    simulation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("simulation_templates.template_id", ondelete="SET NULL"), nullable=True)
    decision_type = Column(String(50), nullable=False)
    scenario_name = Column(String(150), nullable=False)
    simulation_result = Column(JSON, default=dict, nullable=False)
    predicted_outcome = Column(JSON, default=dict, nullable=False)
    confidence_score = Column(Float, nullable=True)
    input_parameters = Column(JSON, default=dict, nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="simulations")
    template = relationship("SimulationTemplate", lazy="joined")
