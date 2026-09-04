import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from main import app
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.digital_twin import DigitalTwinState, DomainState, MLPredictions
from app.services.digital_twin_service import get_digital_twin_state
from app.services.ai.context_builder import build_ai_context

# Mock user for overriding dependencies
mock_user_id = uuid4()
def override_get_current_user():
    return User(user_id=mock_user_id, email="financial_ai@example.com")

def override_get_db():
    # Provide a magic mock for db if needed, or we can mock the functions
    db = MagicMock()
    return db

@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

def test_financial_records_to_metrics():
    # Test that digital_twin_service correctly aggregates actual financial data
    db = MagicMock()
    with patch("app.services.digital_twin_service.get_financial_summary") as mock_summary:
        summary_obj = MagicMock()
        summary_obj.total_income = 5000.0
        summary_obj.total_expenses = 3000.0
        summary_obj.net_savings = 2000.0
        mock_summary.return_value = summary_obj
        
        with patch("app.services.digital_twin_service.get_study_summary"), \
             patch("app.services.digital_twin_service.get_fitness_summary"), \
             patch("app.services.digital_twin_service.get_habit_analytics"), \
             patch("app.services.digital_twin_service.get_goal_summary"), \
             patch("app.services.digital_twin_service.get_current_predictions") as mock_preds:
             
             mock_preds.return_value = {
                 "academic": None, "financial": None, "lifestyle": None, "forecasting": None, "fitness": None, "retrieved_at": datetime.now(timezone.utc).isoformat()
             }
             
             state = get_digital_twin_state(db, mock_user_id)
             
             # The metrics should be populated and not empty
             assert state.financial.metrics["total_income"] == 5000.0
             assert state.financial.metrics["total_expenses"] == 3000.0
             assert state.financial.metrics["net_savings"] == 2000.0
def test_financial_metrics_to_ai_context():
    # Test that context_builder correctly maps metrics to context
    dt_state = DigitalTwinState(
        user_id=str(mock_user_id),
        overall_state="healthy",
        financial=DomainState(status="healthy", metrics={"total_income": 1000.0, "total_expenses": 500.0, "total_savings": 500.0}, last_updated=datetime.now(timezone.utc)),
        academic=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        fitness=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        lifestyle_habits=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        goals=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        ml_predictions=MLPredictions(retrieved_at=datetime.now(timezone.utc).isoformat()),
        generated_at=datetime.now(timezone.utc)
    )
    
    context = build_ai_context(dt_state)
    assert context["digital_twin"]["financial"]["metrics"]["total_income"] == 1000.0
    assert context["digital_twin"]["financial"]["metrics"]["total_savings"] == 500.0

def test_missing_financial_data_produces_insufficient_data():
    # If ML prediction for financial is missing/empty, status is insufficient_data or unavailable
    dt_state = DigitalTwinState(
        user_id=str(mock_user_id),
        overall_state="healthy",
        financial=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        academic=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        fitness=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        lifestyle_habits=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        goals=DomainState(status="stable", metrics={}, last_updated=datetime.now(timezone.utc)),
        ml_predictions=MLPredictions(financial={"status": "insufficient_data"}, retrieved_at=datetime.now(timezone.utc).isoformat()),
        generated_at=datetime.now(timezone.utc)
    )
    
    context = build_ai_context(dt_state)
    assert context["ml_predictions"]["financial"]["status"] == "insufficient_data"
    assert context["ml_predictions"]["financial"]["prediction"] is None
