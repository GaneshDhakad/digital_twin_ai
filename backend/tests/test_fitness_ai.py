import pytest
from unittest.mock import patch, MagicMock
from uuid import uuid4
from datetime import datetime, timezone

from fastapi.testclient import TestClient
from main import app
from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.services.digital_twin_service import get_digital_twin_state

mock_user_id = uuid4()
def override_get_current_user():
    return User(user_id=mock_user_id, email="fitness_test@example.com")

def override_get_db():
    return MagicMock()

@pytest.fixture(autouse=True)
def setup_overrides():
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()

def test_fitness_model_unavailable_in_registry():
    client = TestClient(app)
    response = client.get("/api/ml/models")
    assert response.status_code == 200
    data = response.json()
    assert "fitness" in data
    assert data["fitness"]["available"] is False

def test_fitness_model_unavailable_in_digital_twin():
    db = MagicMock()
    with patch("app.services.digital_twin_service.get_fitness_summary") as mock_fitness:
        summary_obj = MagicMock()
        summary_obj.weekly_activity_count = 4
        summary_obj.total_duration_minutes = 180.0
        summary_obj.total_calories = 1500.0
        summary_obj.activity_breakdown = {"Running": 1, "Cycling": 3}
        mock_fitness.return_value = summary_obj
        
        state = get_digital_twin_state(db, mock_user_id)
        
        # Test that recorded fitness data is accessible in the domain state
        assert state.fitness.metrics["total_workouts"] == 4
        assert state.fitness.metrics["calories"] == 1500.0
        
        # Test that the ML prediction for fitness explicitly reports unavailable
        fitness_ml = state.ml_predictions.model_dump().get("fitness", {})
        assert fitness_ml["status"] == "model_unavailable"
        assert fitness_ml["prediction"] is None
