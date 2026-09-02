from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.reference import Subject


class StudyActivity(Base):
    __tablename__ = "study_activities"

    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    subject_id = Column(UUID(as_uuid=True), ForeignKey("subjects.subject_id", ondelete="SET NULL"), nullable=True)
    study_hours = Column(Float, nullable=False)
    performance_score = Column(Float, nullable=True, default=80.0)
    task_completion_rate = Column(Float, nullable=False, default=100.0)
    notes = Column(String, nullable=True)
    activity_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="study_activities")
    subject_rel = relationship("Subject", lazy="joined")

    __table_args__ = (
        Index("idx_user_study_date", "user_id", "activity_date"),
    )

    def __init__(self, **kwargs):
        subj = kwargs.pop("subject", None)
        super().__init__(**kwargs)
        if subj is not None:
            self._temp_subject = subj

    @hybrid_property
    def subject(self) -> str:
        if self.subject_rel and self.subject_rel.name:
            return self.subject_rel.name
        return getattr(self, "_temp_subject", "General")

    @subject.setter
    def subject(self, val: str):
        self._temp_subject = val

    @subject.expression
    def subject(cls):
        return Subject.name
