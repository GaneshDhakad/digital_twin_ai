"""
tests/test_ml.py
Integration tests for all four ML prediction API endpoints.

Tests:
  - Academic: /api/ml/academic/predict
  - Lifestyle: /api/ml/lifestyle/predict
  - Financial: /api/ml/financial/predict
  - Forecasting: /api/ml/forecasting/predict
  - Model status: GET /api/ml/models

Covers:
  1. Model loading / availability
  2. Valid prediction (correct response schema)
  3. Unauthenticated request → 401/403
  4. Invalid input → 422
  5. Model status endpoint structure
"""
import pytest
import os

# ── Use isolated SQLite for tests ─────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_digital_twin.db")

import sys
from pathlib import Path

backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_TEST_EMAIL = "ml_test_user@example.com"
_TEST_PASSWORD = "SecurePass123"
_AUTH_HEADERS: dict = {}


def _get_auth_headers() -> dict:
    """Register (or re-use) a test user and return Bearer token headers."""
    if _AUTH_HEADERS:
        return _AUTH_HEADERS

    # Try register first
    client.post(
        "/api/auth/register",
        json={
            "email": _TEST_EMAIL,
            "password": _TEST_PASSWORD,
            "name": "ML Test User",
            "age": 25,
            "occupation": "Engineer",
        },
    )

    # Login
    resp = client.post(
        "/api/auth/login",
        data={"username": _TEST_EMAIL, "password": _TEST_PASSWORD},
    )
    assert resp.status_code == 200, f"Login failed: {resp.text}"
    token = resp.json()["access_token"]
    _AUTH_HEADERS["Authorization"] = f"Bearer {token}"
    return _AUTH_HEADERS


# ─────────────────────────────────────────────────────────────────────────────
# GET /api/ml/models — Model Status (no auth required)
# ─────────────────────────────────────────────────────────────────────────────

class TestModelStatus:
    def test_model_status_endpoint_reachable(self):
        resp = client.get("/api/ml/models")
        assert resp.status_code == 200

    def test_model_status_contains_four_domains(self):
        resp = client.get("/api/ml/models")
        data = resp.json()
        for domain in ["academic", "lifestyle", "financial", "forecasting"]:
            assert domain in data, f"Missing domain: {domain}"

    def test_model_status_fitness_not_available(self):
        resp = client.get("/api/ml/models")
        data = resp.json()
        assert "fitness" in data
        assert data["fitness"].get("available") is False

    def test_available_models_have_required_fields(self):
        resp = client.get("/api/ml/models")
        data = resp.json()
        for domain in ["academic", "lifestyle", "financial", "forecasting"]:
            info = data[domain]
            if info.get("available"):
                assert "model" in info
                assert "version" in info
                assert "target" in info


# ─────────────────────────────────────────────────────────────────────────────
# ACADEMIC
# ─────────────────────────────────────────────────────────────────────────────

_VALID_ACADEMIC_PAYLOAD = {
    "age": 22,
    "gender": "Male",
    "major": "Engineering",
    "study_hours_per_day": 5.0,
    "social_media_hours": 2.0,
    "netflix_hours": 1.5,
    "part_time_job": "No",
    "attendance_percentage": 88.0,
    "sleep_hours": 7.0,
    "diet_quality": "Good",
    "exercise_frequency": 3.0,
    "parental_education_level": "Bachelor",
    "internet_quality": "Good",
    "mental_health_rating": 7.0,
    "extracurricular_participation": "Yes",
    "previous_gpa": 3.2,
    "semester": 4.0,
    "stress_level": 5.0,
    "dropout_risk": "Low",
    "social_activity": 5.0,
    "screen_time": 4.0,
    "study_environment": "Library",
    "access_to_tutoring": "Yes",
    "family_income_range": "Medium",
    "parental_support_level": 7.0,
    "motivation_level": 8.0,
    "exam_anxiety_score": 5.0,
    "learning_style": "Visual",
    "time_management_score": 7.0,
    "study_efficiency": 6.5,
    "digital_distraction_hours": 2.0,
    "wellbeing_score": 7.0,
}


class TestAcademicPrediction:
    def test_unauthenticated_returns_401(self):
        resp = client.post("/api/ml/academic/predict", json=_VALID_ACADEMIC_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_valid_prediction_returns_200(self):
        resp = client.post(
            "/api/ml/academic/predict",
            json=_VALID_ACADEMIC_PAYLOAD,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    def test_valid_prediction_schema(self):
        resp = client.post(
            "/api/ml/academic/predict",
            json=_VALID_ACADEMIC_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert "prediction" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "target" in data
        assert "timestamp" in data

    def test_prediction_is_numeric(self):
        resp = client.post(
            "/api/ml/academic/predict",
            json=_VALID_ACADEMIC_PAYLOAD,
            headers=_get_auth_headers(),
        )
        val = resp.json()["prediction"]
        assert isinstance(val, (int, float))
        assert 0 <= val <= 100

    def test_correct_model_metadata(self):
        resp = client.post(
            "/api/ml/academic/predict",
            json=_VALID_ACADEMIC_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert data["target"] == "exam_score"
        assert data["model_version"] == "1.0"

    def test_invalid_input_returns_422(self):
        bad_payload = {**_VALID_ACADEMIC_PAYLOAD, "attendance_percentage": 150.0}
        resp = client.post(
            "/api/ml/academic/predict",
            json=bad_payload,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 422

    def test_missing_required_field_returns_422(self):
        bad_payload = {k: v for k, v in _VALID_ACADEMIC_PAYLOAD.items() if k != "age"}
        resp = client.post(
            "/api/ml/academic/predict",
            json=bad_payload,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# LIFESTYLE
# ─────────────────────────────────────────────────────────────────────────────

_VALID_LIFESTYLE_PAYLOAD = {
    "gender": "Female",
    "age": 30,
    "occupation": "Software Engineer",
    "sleep_hours": 6.5,
    "sleep_quality": 6.0,
    "physical_activity_level": 45.0,
    "stress_level": 7.0,
    "bmi_category": "Normal",
    "blood_pressure": "120/80",
    "heart_rate": 75.0,
    "daily_steps": 6000.0,
    "activity_sleep_balance": 55.0,
    "lifestyle_risk_score": 42.0,
}


class TestLifestylePrediction:
    def test_unauthenticated_returns_401(self):
        resp = client.post("/api/ml/lifestyle/predict", json=_VALID_LIFESTYLE_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_valid_prediction_returns_200(self):
        resp = client.post(
            "/api/ml/lifestyle/predict",
            json=_VALID_LIFESTYLE_PAYLOAD,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    def test_valid_prediction_schema(self):
        resp = client.post(
            "/api/ml/lifestyle/predict",
            json=_VALID_LIFESTYLE_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert "prediction" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "target" in data

    def test_prediction_is_string(self):
        resp = client.post(
            "/api/ml/lifestyle/predict",
            json=_VALID_LIFESTYLE_PAYLOAD,
            headers=_get_auth_headers(),
        )
        val = resp.json()["prediction"]
        assert isinstance(val, str)

    def test_correct_model_metadata(self):
        resp = client.post(
            "/api/ml/lifestyle/predict",
            json=_VALID_LIFESTYLE_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert data["target"] == "sleep_disorder"

    def test_missing_required_field_returns_422(self):
        bad = {k: v for k, v in _VALID_LIFESTYLE_PAYLOAD.items() if k != "gender"}
        resp = client.post(
            "/api/ml/lifestyle/predict",
            json=bad,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# FINANCIAL
# ─────────────────────────────────────────────────────────────────────────────

_VALID_FINANCIAL_PAYLOAD = {
    "income": 75000.0,
    "age": 35,
    "dependents": 2,
    "occupation": "Salaried",
    "city_tier": "Tier 1",
    "desired_savings_percentage": 20.0,
    "desired_savings": 15000.0,
}


class TestFinancialPrediction:
    def test_unauthenticated_returns_401(self):
        resp = client.post("/api/ml/financial/predict", json=_VALID_FINANCIAL_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_valid_prediction_returns_200(self):
        resp = client.post(
            "/api/ml/financial/predict",
            json=_VALID_FINANCIAL_PAYLOAD,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    def test_valid_prediction_schema(self):
        resp = client.post(
            "/api/ml/financial/predict",
            json=_VALID_FINANCIAL_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert "prediction" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "target" in data

    def test_prediction_is_numeric(self):
        resp = client.post(
            "/api/ml/financial/predict",
            json=_VALID_FINANCIAL_PAYLOAD,
            headers=_get_auth_headers(),
        )
        val = resp.json()["prediction"]
        assert isinstance(val, (int, float))

    def test_correct_model_metadata(self):
        resp = client.post(
            "/api/ml/financial/predict",
            json=_VALID_FINANCIAL_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert data["target"] == "disposable_income"

    def test_missing_required_field_returns_422(self):
        bad = {k: v for k, v in _VALID_FINANCIAL_PAYLOAD.items() if k != "income"}
        resp = client.post(
            "/api/ml/financial/predict",
            json=bad,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# FORECASTING
# ─────────────────────────────────────────────────────────────────────────────

_VALID_FORECASTING_PAYLOAD = {
    "month": "January",
    "total_signed_amount": 12500.0,
    "total_absolute_amount": 45000.0,
    "positive_amount": 28750.0,
    "negative_amount": 16250.0,
    "transaction_count": 85,
    "positive_transaction_count": 20,
    "negative_transaction_count": 65,
    "average_transaction_amount": 529.41,
    "unique_merchants": 32,
    "unique_cards": 3,
    "error_count": 2,
    "total_absolute_amount_lag_1": 43200.0,
    "total_absolute_amount_rolling_3m": 44100.0,
    "positive_amount_lag_1": 27500.0,
    "positive_amount_rolling_3m": 28100.0,
    "negative_amount_lag_1": 15700.0,
    "negative_amount_rolling_3m": 16000.0,
    "transaction_count_lag_1": 80,
    "transaction_count_rolling_3m": 82.0,
}


class TestForecastingPrediction:
    def test_unauthenticated_returns_401(self):
        resp = client.post("/api/ml/forecasting/predict", json=_VALID_FORECASTING_PAYLOAD)
        assert resp.status_code in (401, 403)

    def test_valid_prediction_returns_200(self):
        resp = client.post(
            "/api/ml/forecasting/predict",
            json=_VALID_FORECASTING_PAYLOAD,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 200, resp.text

    def test_valid_prediction_schema(self):
        resp = client.post(
            "/api/ml/forecasting/predict",
            json=_VALID_FORECASTING_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert "prediction" in data
        assert "model_name" in data
        assert "model_version" in data
        assert "target" in data

    def test_prediction_is_non_negative(self):
        resp = client.post(
            "/api/ml/forecasting/predict",
            json=_VALID_FORECASTING_PAYLOAD,
            headers=_get_auth_headers(),
        )
        val = resp.json()["prediction"]
        assert isinstance(val, (int, float))
        assert val >= 0

    def test_correct_model_metadata(self):
        resp = client.post(
            "/api/ml/forecasting/predict",
            json=_VALID_FORECASTING_PAYLOAD,
            headers=_get_auth_headers(),
        )
        data = resp.json()
        assert data["target"] == "next_month_spending"

    def test_missing_required_field_returns_422(self):
        bad = {k: v for k, v in _VALID_FORECASTING_PAYLOAD.items() if k != "month"}
        resp = client.post(
            "/api/ml/forecasting/predict",
            json=bad,
            headers=_get_auth_headers(),
        )
        assert resp.status_code == 422
