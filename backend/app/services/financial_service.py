from datetime import datetime
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import extract

from app.models.financial import FinancialRecord
from app.schemas.financial import (
    FinancialRecordCreate,
    FinancialRecordUpdate,
    FinancialSummary,
)


def add_financial_record(db: Session, user_id: int, data: FinancialRecordCreate) -> FinancialRecord:
    rec_type = data.type.lower()
    amount = data.amount
    
    if rec_type == "income":
        inc = amount
        exp = 0.0
        sav = amount
    else:
        inc = 0.0
        exp = amount
        sav = -amount

    record = FinancialRecord(
        user_id=user_id,
        type=rec_type,
        income=inc,
        expenses=exp,
        savings=sav,
        category=data.category.value,
        description=data.description,
        transaction_date=data.transaction_date or datetime.utcnow(),
        recurring_frequency=data.recurring_frequency.value,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_financial_records(
    db: Session,
    user_id: int,
    category: Optional[str] = None,
    month: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[FinancialRecord]:
    query = db.query(FinancialRecord).filter(FinancialRecord.user_id == user_id)
    
    if category:
        query = query.filter(FinancialRecord.category == category)
        
    if month:
        # Expected format YYYY-MM
        try:
            year, m = map(int, month.split("-"))
            query = query.filter(
                extract("year", FinancialRecord.transaction_date) == year,
                extract("month", FinancialRecord.transaction_date) == m
            )
        except Exception:
            pass

    return query.order_by(FinancialRecord.transaction_date.desc()).offset(skip).limit(limit).all()


def get_financial_record_by_id(db: Session, record_id: int, user_id: int) -> Optional[FinancialRecord]:
    return db.query(FinancialRecord).filter(
        FinancialRecord.record_id == record_id,
        FinancialRecord.user_id == user_id
    ).first()


def update_financial_record(
    db: Session,
    record_id: int,
    user_id: int,
    data: FinancialRecordUpdate,
) -> Optional[FinancialRecord]:
    record = get_financial_record_by_id(db, record_id, user_id)
    if not record:
        return None

    if data.type is not None:
        record.type = data.type.lower()
    
    if data.amount is not None:
        if record.type == "income":
            record.income = data.amount
            record.expenses = 0.0
            record.savings = data.amount
        else:
            record.income = 0.0
            record.expenses = data.amount
            record.savings = -data.amount
            
    if data.category is not None:
        record.category = data.category.value
    if data.description is not None:
        record.description = data.description
    if data.transaction_date is not None:
        record.transaction_date = data.transaction_date
    if data.recurring_frequency is not None:
        record.recurring_frequency = data.recurring_frequency.value

    db.commit()
    db.refresh(record)
    return record


def delete_financial_record(db: Session, record_id: int, user_id: int) -> bool:
    record = get_financial_record_by_id(db, record_id, user_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_financial_summary(db: Session, user_id: int) -> FinancialSummary:
    records = db.query(FinancialRecord).filter(FinancialRecord.user_id == user_id).all()

    total_inc = sum(r.income for r in records)
    total_exp = sum(r.expenses for r in records)
    net_sav = total_inc - total_exp
    sav_rate = (net_sav / total_inc * 100) if total_inc > 0 else 0.0

    cat_breakdown: Dict[str, float] = {}
    for r in records:
        if r.type == "expense":
            cat_breakdown[r.category] = cat_breakdown.get(r.category, 0.0) + r.expenses

    # Monthly trend calculation
    monthly_data: Dict[str, Dict[str, float]] = {}
    for r in records:
        month_key = r.transaction_date.strftime("%Y-%m")
        if month_key not in monthly_data:
            monthly_data[month_key] = {"income": 0.0, "expenses": 0.0, "savings": 0.0}
        monthly_data[month_key]["income"] += r.income
        monthly_data[month_key]["expenses"] += r.expenses
        monthly_data[month_key]["savings"] += (r.income - r.expenses)

    monthly_trend = [
        {"month": k, "income": v["income"], "expenses": v["expenses"], "savings": v["savings"]}
        for k, v in sorted(monthly_data.items())
    ]

    return FinancialSummary(
        total_income=round(total_inc, 2),
        total_expenses=round(total_exp, 2),
        net_savings=round(net_sav, 2),
        savings_rate=round(sav_rate, 1),
        category_breakdown={k: round(v, 2) for k, v in cat_breakdown.items()},
        monthly_trend=monthly_trend,
    )
