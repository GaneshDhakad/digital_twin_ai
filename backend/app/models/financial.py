from datetime import datetime
import uuid
from typing import Optional
from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property

from app.core.database import Base
from app.models.reference import ExpenseCategory


class FinancialRecord(Base):
    __tablename__ = "financial_records"

    record_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
    category_id = Column(UUID(as_uuid=True), ForeignKey("expense_categories.category_id", ondelete="SET NULL"), nullable=True)
    type = Column(String(20), nullable=False, default="expense")  # 'income' or 'expense'
    amount = Column(Float, default=0.0, nullable=False)
    income = Column(Float, default=0.0, nullable=False)
    expenses = Column(Float, default=0.0, nullable=False)
    savings = Column(Float, default=0.0, nullable=False)
    transaction_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    description = Column(String, nullable=True)
    recurring_frequency = Column(String(20), default="none", nullable=False)  # none, daily, weekly, monthly, annual
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="financial_records")
    expense_category = relationship("ExpenseCategory", lazy="joined")

    __table_args__ = (
        Index("idx_user_trans_date", "user_id", "transaction_date"),
    )

    def __init__(self, **kwargs):
        category_name = kwargs.pop("category", None)
        super().__init__(**kwargs)
        if category_name is not None:
            self._temp_category = category_name

    @hybrid_property
    def category(self) -> str:
        if self.expense_category and self.expense_category.name:
            return self.expense_category.name
        return getattr(self, "_temp_category", "Other")

    @category.setter
    def category(self, val: str):
        self._temp_category = val

    @category.expression
    def category(cls):
        return ExpenseCategory.name

