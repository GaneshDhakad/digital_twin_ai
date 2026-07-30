from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.orm import relationship

from app.core.database import Base


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    record_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    type = Column(String, nullable=False, default="expense") # 'income' or 'expense'
    income = Column(Float, default=0.0, nullable=False)
    expenses = Column(Float, default=0.0, nullable=False)
    savings = Column(Float, default=0.0, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    category = Column(String, nullable=False) # Housing, Food, Transport, Education, etc.
    description = Column(String, nullable=True)
    recurring_frequency = Column(String, default="None", nullable=False) # None, Daily, Weekly, Monthly, Annual

    user = relationship("User", back_populates="financial_records")

__table_args__ = (
    Index("idx_user_trans_date", FinancialRecord.user_id, FinancialRecord.transaction_date),
)
