from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class FinancialCategoryEnum(str, Enum):
    Housing = "Housing"
    Food = "Food"
    Transport = "Transport"
    Education = "Education"
    Entertainment = "Entertainment"
    Healthcare = "Healthcare"
    Investment = "Investment"
    Salary = "Salary"
    Freelance = "Freelance"
    Other = "Other"


class RecurringFrequencyEnum(str, Enum):
    None_Freq = "None"
    Daily = "Daily"
    Weekly = "Weekly"
    Monthly = "Monthly"
    Annual = "Annual"


class FinancialRecordCreate(BaseModel):
    type: str = Field("expense", description="Type of record: 'income' or 'expense'")
    amount: float = Field(..., gt=0, description="Transaction amount")
    category: FinancialCategoryEnum
    description: Optional[str] = None
    transaction_date: Optional[datetime] = Field(default_factory=datetime.utcnow)
    recurring_frequency: RecurringFrequencyEnum = RecurringFrequencyEnum.None_Freq


class FinancialRecordUpdate(BaseModel):
    type: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    category: Optional[FinancialCategoryEnum] = None
    description: Optional[str] = None
    transaction_date: Optional[datetime] = None
    recurring_frequency: Optional[RecurringFrequencyEnum] = None


class FinancialRecordResponse(BaseModel):
    record_id: int
    user_id: int
    type: str
    income: float
    expenses: float
    savings: float
    category: str
    description: Optional[str] = None
    recurring_frequency: str
    transaction_date: datetime

    class Config:
        from_attributes = True


class FinancialSummary(BaseModel):
    total_income: float
    total_expenses: float
    net_savings: float
    savings_rate: float
    category_breakdown: Dict[str, float]
    monthly_trend: List[Dict[str, Any]]
