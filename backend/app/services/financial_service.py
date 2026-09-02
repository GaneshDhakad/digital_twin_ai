from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import extract, or_

from app.models.financial import FinancialRecord
from app.models.reference import ExpenseCategory
from app.schemas.financial import (
    FinancialRecordCreate,
    FinancialRecordUpdate,
    FinancialSummary,
)


def _resolve_expense_category(db: Session, cat_name: str, rec_type: str = "expense") -> Optional[ExpenseCategory]:
    if not cat_name:
        return None
    # 1. Exact match
    exp_cat = db.query(ExpenseCategory).filter(ExpenseCategory.name == cat_name).first()
    if exp_cat:
        return exp_cat
    # 2. Prefix / Contains match (e.g. 'Salary' -> 'Salary & Wages', 'Housing' -> 'Housing & Rent')
    exp_cat = db.query(ExpenseCategory).filter(
        or_(
            ExpenseCategory.name.ilike(f"{cat_name}%"),
            ExpenseCategory.name.ilike(f"%{cat_name}%")
        )
    ).first()
    if exp_cat:
        return exp_cat
    # 3. If not found in database, insert it so reference integrity is satisfied
    try:
        new_cat = ExpenseCategory(name=cat_name, type=rec_type, is_essential=True)
        db.add(new_cat)
        db.flush()
        return new_cat
    except Exception:
        db.rollback()
        return db.query(ExpenseCategory).first()


def add_financial_record(db: Session, user_id: UUID, data: FinancialRecordCreate) -> FinancialRecord:
    rec_type = data.type.lower()
    amount = data.amount
    
    if rec_type == "income":
        inc = amount
        exp = 0.0
        sav = amount
    else:
        inc = 0.0
        exp = amount
        sav = 0.0

    cat_str = data.category.value if hasattr(data.category, "value") else str(data.category)
    exp_cat = _resolve_expense_category(db, cat_str, rec_type)

    freq_str = (data.recurring_frequency.value if hasattr(data.recurring_frequency, "value") else str(data.recurring_frequency)).lower()

    record = FinancialRecord(
        user_id=user_id,
        category_id=exp_cat.category_id if exp_cat else None,
        type=rec_type,
        amount=amount,
        income=inc,
        expenses=exp,
        savings=sav,
        description=data.description,
        transaction_date=data.transaction_date or datetime.utcnow(),
        recurring_frequency=freq_str,
    )
    if exp_cat:
        record.expense_category = exp_cat

    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def get_financial_records(
    db: Session,
    user_id: UUID,
    category: Optional[str] = None,
    month: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[FinancialRecord]:
    query = db.query(FinancialRecord).filter(FinancialRecord.user_id == user_id)
    
    if category:
        query = query.outerjoin(FinancialRecord.expense_category).filter(
            or_(
                ExpenseCategory.name == category,
                ExpenseCategory.name.ilike(f"{category}%"),
                ExpenseCategory.name.ilike(f"%{category}%"),
            )
        )
        
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


def get_financial_record_by_id(db: Session, record_id: Any, user_id: UUID) -> Optional[FinancialRecord]:
    parsed_id = record_id
    if isinstance(record_id, str):
        try:
            parsed_id = UUID(record_id)
        except Exception:
            try:
                parsed_id = int(record_id)
            except Exception:
                pass
    return db.query(FinancialRecord).filter(
        FinancialRecord.record_id == parsed_id,
        FinancialRecord.user_id == user_id
    ).first()


def update_financial_record(
    db: Session,
    record_id: Any,
    user_id: UUID,
    data: FinancialRecordUpdate,
) -> Optional[FinancialRecord]:
    record = get_financial_record_by_id(db, record_id, user_id)
    if not record:
        return None

    if data.type is not None:
        record.type = data.type.lower()
    
    if data.amount is not None:
        record.amount = data.amount
        if record.type == "income":
            record.income = data.amount
            record.expenses = 0.0
            record.savings = data.amount
        else:
            record.income = 0.0
            record.expenses = data.amount
            record.savings = 0.0
            
    if data.category is not None:
        cat_str = data.category.value if hasattr(data.category, "value") else str(data.category)
        exp_cat = _resolve_expense_category(db, cat_str, record.type)
        if exp_cat:
            record.category_id = exp_cat.category_id
            record.expense_category = exp_cat
    if data.description is not None:
        record.description = data.description
    if data.transaction_date is not None:
        record.transaction_date = data.transaction_date
    if data.recurring_frequency is not None:
        record.recurring_frequency = (data.recurring_frequency.value if hasattr(data.recurring_frequency, "value") else str(data.recurring_frequency)).lower()

    db.commit()
    db.refresh(record)
    return record


def delete_financial_record(db: Session, record_id: Any, user_id: UUID) -> bool:
    record = get_financial_record_by_id(db, record_id, user_id)
    if not record:
        return False
    db.delete(record)
    db.commit()
    return True


def get_financial_summary(db: Session, user_id: UUID) -> FinancialSummary:
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
