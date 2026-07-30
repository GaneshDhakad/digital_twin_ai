from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.orm import relationship

from app.core.database import Base


class Simulation(Base):
    __tablename__ = "simulations"

    simulation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    decision_type = Column(String, nullable=False)
    scenario_name = Column(String, nullable=False)
    simulation_result = Column(JSON, nullable=True)
    predicted_outcome = Column(String, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="simulations")
