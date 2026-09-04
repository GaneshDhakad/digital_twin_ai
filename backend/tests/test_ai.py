import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from google.genai.errors import APIError

from main import app
from app.services.ai.assistant_service import get_ai_response
from app.core.config import settings
from app.models.user import User

client = TestClient(app)

# Dummy dependencies
def override_get_current_user():
    return User(user_id="123e4567-e89b-12d3-a456-426614174000", email="test@example.com")

app.dependency_overrides[app.dependency_overrides.get("get_current_user", "get_current_user")] = override_get_current_user

# Currently we just patch get_current_user by patching the dependency in the router.
# Let's import the actual dependency and override it properly.
from app.core.dependencies import get_current_user
app.dependency_overrides[get_current_user] = override_get_current_user

@pytest.fixture
def mock_get_digital_twin_state():
    with patch("app.api.routes.ai.get_digital_twin_state") as mock:
        # Mock the state returned by digital_twin_service
        state = MagicMock()
        state.user_id = "123e4567-e89b-12d3-a456-426614174000"
        state.overall_state = "good"
        mock.return_value = state
        yield mock

@pytest.fixture
def mock_build_ai_context():
    with patch("app.api.routes.ai.build_ai_context") as mock:
        mock.return_value = {"user": {"user_id": "123e4567-e89b-12d3-a456-426614174000"}}
        yield mock

@pytest.fixture
def mock_get_ai_response():
    with patch("app.api.routes.ai.get_ai_response") as mock:
        mock.return_value = "This is a successful AI response."
        yield mock

def test_ai_chat_success(mock_get_digital_twin_state, mock_build_ai_context, mock_get_ai_response):
    response = client.post("/api/ai/chat", json={"message": "Hello"})
    assert response.status_code == 200
    assert response.json()["response"] == "This is a successful AI response."
    assert "conversation_id" in response.json()
    assert response.json()["status"] == "success"

def test_ai_chat_missing_api_key(mock_get_digital_twin_state, mock_build_ai_context):
    with patch("app.api.routes.ai.get_ai_response", side_effect=ValueError("GEMINI_API_KEY is not configured")):
        response = client.post("/api/ai/chat", json={"message": "Hello"})
        assert response.status_code == 503
        assert "not available" in response.json()["detail"]

def test_ai_chat_provider_error(mock_get_digital_twin_state, mock_build_ai_context):
    with patch("app.api.routes.ai.get_ai_response", side_effect=RuntimeError("unexpected response format")):
        response = client.post("/api/ai/chat", json={"message": "Hello"})
        assert response.status_code == 502
        assert "unexpected response" in response.json()["detail"]

def test_ai_chat_general_exception(mock_get_digital_twin_state, mock_build_ai_context):
    with patch("app.api.routes.ai.get_ai_response", side_effect=Exception("Unknown error")):
        response = client.post("/api/ai/chat", json={"message": "Hello"})
        assert response.status_code == 503
        assert "temporarily unavailable" in response.json()["detail"]

def test_ai_chat_unauthenticated():
    # Remove the override to test unauthenticated access
    app.dependency_overrides.pop(get_current_user, None)
    response = client.post("/api/ai/chat", json={"message": "Hello"})
    assert response.status_code == 401
    # Restore the override for other tests if needed (pytest runs in order or isolates, but let's be safe)
    app.dependency_overrides[get_current_user] = override_get_current_user
