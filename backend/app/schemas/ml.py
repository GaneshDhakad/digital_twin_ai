"""
ml.py — Pydantic schemas for ML prediction endpoints.

All request field names are derived directly from feature_info.json files.
No field names are invented or guessed.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ─────────────────────────────────────────────────────────────────────────────
# ACADEMIC MODEL
# Source: ml_models/trained/academic/feature_info.json
# Target: exam_score
# ─────────────────────────────────────────────────────────────────────────────

class AcademicPredictionRequest(BaseModel):
    # Numerical features
    age: float = Field(..., ge=13, le=35, description="Student age")
    study_hours_per_day: float = Field(..., ge=0.0, le=24.0)
    social_media_hours: float = Field(..., ge=0.0, le=24.0)
    netflix_hours: float = Field(..., ge=0.0, le=24.0)
    attendance_percentage: float = Field(..., ge=0.0, le=100.0)
    sleep_hours: float = Field(..., ge=0.0, le=24.0)
    exercise_frequency: float = Field(..., ge=0.0, le=7.0, description="Days per week")
    mental_health_rating: float = Field(..., ge=1.0, le=10.0)
    previous_gpa: float = Field(..., ge=0.0, le=4.0)
    semester: float = Field(..., ge=1.0, le=10.0)
    stress_level: float = Field(..., ge=1.0, le=10.0)
    social_activity: float = Field(..., ge=0.0, le=10.0)
    screen_time: float = Field(..., ge=0.0, le=24.0)
    parental_support_level: float = Field(..., ge=1.0, le=10.0)
    motivation_level: float = Field(..., ge=1.0, le=10.0)
    exam_anxiety_score: float = Field(..., ge=1.0, le=10.0)
    time_management_score: float = Field(..., ge=1.0, le=10.0)
    study_efficiency: float = Field(..., ge=0.0, le=10.0)
    digital_distraction_hours: float = Field(..., ge=0.0, le=24.0)
    wellbeing_score: float = Field(..., ge=0.0, le=10.0)

    # Categorical features
    gender: str = Field(..., description="Male or Female")
    major: str = Field(..., description="Field of study e.g. Engineering, Arts")
    part_time_job: str = Field(..., description="Yes or No")
    diet_quality: str = Field(..., description="Poor, Average, Good")
    parental_education_level: str = Field(..., description="High School, Bachelor, Master, PhD")
    internet_quality: str = Field(..., description="Poor, Average, Good, Excellent")
    extracurricular_participation: str = Field(..., description="Yes or No")
    dropout_risk: str = Field(..., description="Low, Medium, High")
    study_environment: str = Field(..., description="Home, Library, Cafe, Dorm")
    access_to_tutoring: str = Field(..., description="Yes or No")
    family_income_range: str = Field(..., description="Low, Medium, High")
    learning_style: str = Field(..., description="Visual, Auditory, Reading, Kinesthetic")


class AcademicPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction: float
    model_name: str
    model_version: str
    target: str
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# LIFESTYLE MODEL
# Source: ml_models/trained/lifestyle/feature_info.json
# Target: sleep_disorder
# ─────────────────────────────────────────────────────────────────────────────

class LifestylePredictionRequest(BaseModel):
    # Categorical features
    gender: str = Field(..., description="Male or Female")
    occupation: str = Field(..., description="e.g. Engineer, Doctor, Teacher, Student")
    bmi_category: str = Field(..., description="Underweight, Normal, Overweight, Obese")
    blood_pressure: str = Field(..., description="e.g. 120/80, 135/90")

    # Numerical features
    age: float = Field(..., ge=18, le=100)
    sleep_hours: float = Field(..., ge=0.0, le=24.0, description="Hours of sleep per night")
    sleep_quality: float = Field(..., ge=1.0, le=10.0, description="Self-rated sleep quality 1-10")
    physical_activity_level: float = Field(..., ge=0.0, le=100.0, description="Activity level 0-100")
    stress_level: float = Field(..., ge=1.0, le=10.0, description="Stress level 1-10")
    heart_rate: float = Field(..., ge=40.0, le=200.0, description="Resting heart rate BPM")
    daily_steps: float = Field(..., ge=0.0, le=50000.0, description="Steps per day")
    activity_sleep_balance: float = Field(..., ge=0.0, le=100.0, description="Balance score")
    lifestyle_risk_score: float = Field(..., ge=0.0, le=100.0, description="Composite risk 0-100")


class LifestylePredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction: str          # Classification: e.g. "Insomnia", "Sleep Apnea", "None"
    model_name: str
    model_version: str
    target: str
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL MODEL
# Source: ml_models/trained/financial/feature_info.json
# Target: disposable_income
# ─────────────────────────────────────────────────────────────────────────────

class FinancialPredictionRequest(BaseModel):
    # Numerical features
    income: float = Field(..., ge=0.0, description="Monthly gross income")
    age: float = Field(..., ge=18, le=100)
    dependents: float = Field(..., ge=0, le=20, description="Number of dependents")
    desired_savings_percentage: float = Field(..., ge=0.0, le=100.0, description="Target savings %")
    desired_savings: float = Field(..., ge=0.0, description="Desired savings amount")

    # Categorical features
    occupation: str = Field(..., description="e.g. Salaried, Self-Employed, Business")
    city_tier: str = Field(..., description="Tier 1, Tier 2, or Tier 3")


class FinancialPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction: float
    model_name: str
    model_version: str
    target: str
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# FORECASTING MODEL
# Source: ml_models/trained/forecasting/feature_info.json
# Target: next_month_spending
# NOTE: next_month_spending itself is NOT an input feature (it's the target)
# NOTE: next_month_transaction_count is excluded (future target info)
# ─────────────────────────────────────────────────────────────────────────────

class ForecastingPredictionRequest(BaseModel):
    # Categorical features
    month: str = Field(..., description="Month name e.g. January, February")

    # Numerical features — current month aggregates
    total_signed_amount: float = Field(..., description="Net signed transaction amount (income - expenses)")
    total_absolute_amount: float = Field(..., ge=0.0, description="Sum of absolute transaction values")
    positive_amount: float = Field(..., ge=0.0, description="Total positive (income) transactions")
    negative_amount: float = Field(..., ge=0.0, description="Total negative (expense) transactions")
    transaction_count: float = Field(..., ge=0, description="Total number of transactions this month")
    positive_transaction_count: float = Field(..., ge=0, description="Number of income transactions")
    negative_transaction_count: float = Field(..., ge=0, description="Number of expense transactions")
    average_transaction_amount: float = Field(..., description="Average transaction value")
    unique_merchants: float = Field(..., ge=0, description="Unique merchant count")
    unique_cards: float = Field(..., ge=0, description="Unique cards used")
    error_count: float = Field(..., ge=0, description="Number of erroneous transactions")

    # Lag and rolling features (from prior months)
    total_absolute_amount_lag_1: float = Field(..., ge=0.0, description="Prior month total absolute amount")
    total_absolute_amount_rolling_3m: float = Field(..., ge=0.0, description="3-month rolling avg absolute amount")
    positive_amount_lag_1: float = Field(..., ge=0.0, description="Prior month positive amount")
    positive_amount_rolling_3m: float = Field(..., ge=0.0, description="3-month rolling avg positive amount")
    negative_amount_lag_1: float = Field(..., ge=0.0, description="Prior month negative amount")
    negative_amount_rolling_3m: float = Field(..., ge=0.0, description="3-month rolling avg negative amount")
    transaction_count_lag_1: float = Field(..., ge=0, description="Prior month transaction count")
    transaction_count_rolling_3m: float = Field(..., ge=0, description="3-month rolling avg transaction count")


class ForecastingPredictionResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    prediction: float
    model_name: str
    model_version: str
    target: str
    timestamp: datetime


# ─────────────────────────────────────────────────────────────────────────────
# MODEL STATUS RESPONSE
# ─────────────────────────────────────────────────────────────────────────────

class ModelStatusResponse(BaseModel):
    academic: dict
    lifestyle: dict
    financial: dict
    forecasting: dict
    fitness: dict
