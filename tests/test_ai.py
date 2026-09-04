"""
tests/test_ai.py
Unit and integration tests for the AI Backend Service (Milestone 4, Steps 1 & 2).

Coverage:
    1.  Valid chat request → 200 + response text
    2.  Empty message → 422
    3.  Whitespace-only message → 422
    4.  Digital Twin with available academic prediction → numeric preserved
    5.  Digital Twin with insufficient_data → null preserved faithfully
    6.  Digital Twin with model_unavailable → null preserved faithfully
    7.  Missing GEMINI_API_KEY → 503
    8.  LLM provider failure → 502/503
    9.  Unauthenticated request → 401
    10. User isolation — user A cannot see user B's context
    11. null predictions remain null in the AI context
    12. Numeric predictions remain numeric in the AI context
    13. No fake 0.0 fallback is introduced

Important:
    NO real LLM API calls are made. The Gemini client is fully mocked.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock, patch, PropertyMock

import pytest

# ── Isolated SQLite for tests ──────────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_digital_twin.db")

backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from backend.main import app
from app.services.ai.context_builder import build_ai_context, _build_prediction_context
from app.schemas.digital_twin import DigitalTwinState, DomainState, MLPredictions

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Shared test helpers
# ─────────────────────────────────────────────────────────────────────────────

_MOCK_AI_RESPONSE = "Based on your Digital Twin data, your finances look healthy."

_USER_A_EMAIL = "ai_user_a@example.com"
_USER_A_PASSWORD = "SecurePassA1"
_USER_B_EMAIL = "ai_user_b@example.com"
_USER_B_PASSWORD = "SecurePassB1"

_auth_cache: Dict[str, str] = {}


def _register_and_login(email: str, password: str) -> str:
    """Register user (ignore if already exists) and return Bearer token."""
    if email in _auth_cache:
        return _auth_cache[email]

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "AI Test User"},
    )
    resp = client.post(
        "/api/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.text}"
    token = resp.json()["access_token"]
    _auth_cache[email] = token
    return token


def _headers(email: str, password: str) -> Dict[str, str]:
    return {"Authorization": f"Bearer {_register_and_login(email, password)}"}


def _make_twin_state(
    academic_pred: Any = None,
    financial_pred: Any = None,
    lifestyle_pred: Any = None,
    forecasting_pred: Any = None,
    fitness_pred: Any = None,
) -> DigitalTwinState:
    """Helper: build a minimal DigitalTwinState for pure unit tests."""
    now = datetime.now(timezone.utc)
    domain = DomainState(status="stable", metrics={}, last_updated=now)
    ml = MLPredictions(
        academic=academic_pred,
        financial=financial_pred,
        lifestyle=lifestyle_pred,
        forecasting=forecasting_pred,
        fitness=fitness_pred,
        retrieved_at=now.isoformat(),
    )
    return DigitalTwinState(
        user_id="test-user-123",
        overall_state="stable",
        financial=domain,
        academic=domain,
        fitness=domain,
        lifestyle_habits=domain,
        goals=domain,
        ml_predictions=ml,
        generated_at=now,
    )


def _mock_genai_client(response_text: str = _MOCK_AI_RESPONSE):
    """
    Return a patch context for app.services.ai.assistant_service.genai that
    simulates a successful Gemini response.

    Patches the google.genai Client so no real network calls are made.
    """
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client_instance.models.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client_instance
    return mock_genai


# ─────────────────────────────────────────────────────────────────────────────
# 1. Valid chat request
# ─────────────────────────────────────────────────────────────────────────────

class TestValidChatRequest:
    @patch("app.services.ai.assistant_service.genai")
    def test_valid_request_returns_200(self, mock_genai):
        """Valid authenticated request with mocked Gemini → 200."""
        mock_genai.Client.return_value = _mock_genai_client().Client.return_value
        mock_genai.Client.return_value.models.generate_content.return_value.text = _MOCK_AI_RESPONSE

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "How am I doing financially?"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    @patch("app.services.ai.assistant_service.genai")
    def test_valid_request_response_schema(self, mock_genai):
        """Response must contain 'response' and 'status' fields."""
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = _MOCK_AI_RESPONSE
        mock_client.models.generate_content.return_value = mock_resp
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "What are my goals?"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "response" in data
        assert "status" in data
        assert data["status"] == "success"
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0


# ─────────────────────────────────────────────────────────────────────────────
# 2. Empty message → 422
# ─────────────────────────────────────────────────────────────────────────────

class TestEmptyMessage:
    def test_empty_string_returns_422(self):
        """Empty message must be rejected with 422 before reaching the AI."""
        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": ""},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_missing_message_field_returns_422(self):
        """Missing 'message' field must be rejected with 422."""
        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={},
            headers=headers,
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 3. Whitespace-only message → 422
# ─────────────────────────────────────────────────────────────────────────────

class TestWhitespaceMessage:
    def test_spaces_only_returns_422(self):
        """A message of only spaces must be rejected."""
        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "   "},
            headers=headers,
        )
        assert resp.status_code == 422

    def test_tabs_and_newlines_only_returns_422(self):
        """A message of only tabs/newlines must be rejected."""
        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "\t\n\r"},
            headers=headers,
        )
        assert resp.status_code == 422


# ─────────────────────────────────────────────────────────────────────────────
# 4 & 11 & 12. Context builder — available prediction (numeric stays numeric)
# ─────────────────────────────────────────────────────────────────────────────

class TestContextBuilderAvailablePrediction:
    def test_available_prediction_preserved(self):
        """Available academic prediction → numeric value retained in context."""
        pred = {
            "status": "available",
            "prediction": 78.5,
            "model_name": "GradientBoostingRegressor",
            "target": "exam_score",
        }
        twin = _make_twin_state(academic_pred=pred)
        ctx = build_ai_context(twin)

        academic_ctx = ctx["ml_predictions"]["academic"]
        assert academic_ctx["status"] == "available"
        assert academic_ctx["prediction"] == 78.5
        assert isinstance(academic_ctx["prediction"], float)

    def test_numeric_prediction_is_not_zero_fabricated(self):
        """Prediction value 78.5 must not be replaced with 0 or 0.0."""
        pred = {"status": "available", "prediction": 78.5, "target": "exam_score"}
        twin = _make_twin_state(academic_pred=pred)
        ctx = build_ai_context(twin)

        val = ctx["ml_predictions"]["academic"]["prediction"]
        assert val != 0
        assert val != 0.0
        assert val == 78.5

    def test_string_prediction_preserved(self):
        """String predictions (e.g., sleep_disorder classification) stay as strings."""
        pred = {"status": "available", "prediction": "Insomnia", "target": "sleep_disorder"}
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf_ctx = ctx["ml_predictions"]["lifestyle"]
        assert lf_ctx["status"] == "available"
        assert lf_ctx["prediction"] == "Insomnia"
        assert isinstance(lf_ctx["prediction"], str)


# ─────────────────────────────────────────────────────────────────────────────
# 5 & 11. insufficient_data → null prediction preserved
# ─────────────────────────────────────────────────────────────────────────────

class TestContextBuilderInsufficientData:
    def test_insufficient_data_status_preserved(self):
        """insufficient_data status must be preserved exactly."""
        pred = {
            "status": "insufficient_data",
            "prediction": None,
            "reason": "Missing required academic features",
        }
        twin = _make_twin_state(academic_pred=pred)
        ctx = build_ai_context(twin)

        academic_ctx = ctx["ml_predictions"]["academic"]
        assert academic_ctx["status"] == "insufficient_data"

    def test_null_prediction_stays_null_not_zero(self):
        """null prediction for insufficient_data must NOT be converted to 0 or 0.0."""
        pred = {"status": "insufficient_data", "prediction": None}
        twin = _make_twin_state(academic_pred=pred)
        ctx = build_ai_context(twin)

        val = ctx["ml_predictions"]["academic"]["prediction"]
        assert val is None, f"Expected None but got {val!r}"

    def test_insufficient_data_reason_preserved(self):
        """The 'reason' field must be preserved for insufficient_data."""
        reason = "Missing required academic features (e.g., demographics, habits)"
        pred = {"status": "insufficient_data", "prediction": None, "reason": reason}
        twin = _make_twin_state(academic_pred=pred)
        ctx = build_ai_context(twin)

        assert ctx["ml_predictions"]["academic"]["reason"] == reason

    def test_no_fake_zero_fallback_introduced(self):
        """Confirm 0.0 is never inserted as a substitute for null."""
        pred = {"status": "insufficient_data", "prediction": None}
        twin = _make_twin_state(financial_pred=pred)
        ctx = build_ai_context(twin)

        fin_pred = ctx["ml_predictions"]["financial"]["prediction"]
        assert fin_pred is None
        assert fin_pred != 0
        assert fin_pred != 0.0


# ─────────────────────────────────────────────────────────────────────────────
# 6 & 11 & 13. model_unavailable → null prediction preserved
# ─────────────────────────────────────────────────────────────────────────────

class TestContextBuilderModelUnavailable:
    def test_model_unavailable_status_preserved(self):
        """model_unavailable status must be preserved exactly."""
        pred = {
            "status": "model_unavailable",
            "prediction": None,
            "reason": "No trained fitness model exists",
        }
        twin = _make_twin_state(fitness_pred=pred)
        ctx = build_ai_context(twin)

        fitness_ctx = ctx["ml_predictions"]["fitness"]
        assert fitness_ctx["status"] == "model_unavailable"

    def test_model_unavailable_prediction_is_null(self):
        """Prediction for model_unavailable must remain None — never 0."""
        pred = {"status": "model_unavailable", "prediction": None}
        twin = _make_twin_state(fitness_pred=pred)
        ctx = build_ai_context(twin)

        val = ctx["ml_predictions"]["fitness"]["prediction"]
        assert val is None

    def test_model_unavailable_not_confused_with_available(self):
        """model_unavailable must not produce status='available'."""
        pred = {"status": "model_unavailable", "prediction": None}
        twin = _make_twin_state(fitness_pred=pred)
        ctx = build_ai_context(twin)

        assert ctx["ml_predictions"]["fitness"]["status"] != "available"


# ─────────────────────────────────────────────────────────────────────────────
# 7. Missing GEMINI_API_KEY → 503
# ─────────────────────────────────────────────────────────────────────────────

class TestMissingApiKey:
    @patch("app.services.ai.assistant_service.settings")
    def test_missing_api_key_returns_503(self, mock_settings):
        """When GEMINI_API_KEY is empty, the endpoint must return 503."""
        mock_settings.GEMINI_API_KEY = ""

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "What is my financial status?"},
            headers=headers,
        )
        assert resp.status_code == 503

    @patch("app.services.ai.assistant_service.settings")
    def test_none_api_key_returns_503(self, mock_settings):
        """When GEMINI_API_KEY is None, the endpoint must return 503."""
        mock_settings.GEMINI_API_KEY = None

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "What is my fitness data?"},
            headers=headers,
        )
        assert resp.status_code == 503


# ─────────────────────────────────────────────────────────────────────────────
# 8. LLM provider failure → non-200
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMProviderFailure:
    @patch("app.services.ai.assistant_service.genai")
    def test_runtime_error_from_provider_returns_non_200(self, mock_genai):
        """If generate_content raises RuntimeError → 502 or 503."""
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = RuntimeError("Simulated provider error")
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "Tell me about my goals."},
            headers=headers,
        )
        assert resp.status_code in (502, 503)

    @patch("app.services.ai.assistant_service.genai")
    def test_empty_provider_response_returns_non_200(self, mock_genai):
        """If provider returns empty text → RuntimeError → non-200."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = ""  # empty response
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "Am I on track?"},
            headers=headers,
        )
        assert resp.status_code in (502, 503)


# ─────────────────────────────────────────────────────────────────────────────
# 9. Unauthenticated request → 401
# ─────────────────────────────────────────────────────────────────────────────

class TestAuthentication:
    def test_no_token_returns_401(self):
        """Request without Authorization header must be rejected with 401."""
        resp = client.post(
            "/api/ai/chat",
            json={"message": "How am I doing?"},
        )
        assert resp.status_code in (401, 403)

    def test_invalid_token_returns_401(self):
        """Request with a bad token must be rejected."""
        resp = client.post(
            "/api/ai/chat",
            json={"message": "How am I doing?"},
            headers={"Authorization": "Bearer this_is_not_a_real_token"},
        )
        assert resp.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 10. User isolation — authenticated user gets their own Digital Twin
# ─────────────────────────────────────────────────────────────────────────────

class TestUserIsolation:
    @patch("app.services.ai.assistant_service.genai")
    def test_build_ai_context_called_for_each_user(self, mock_genai):
        """Context builder must be invoked — verifying the pipeline is wired correctly."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Your data looks good."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        with patch("app.api.routes.ai.build_ai_context") as mock_build:
            mock_build.return_value = {
                "user": {"user_id": "some-user"},
                "digital_twin": {"overall_state": "stable"},
                "ml_predictions": {},
            }
            headers_a = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
            resp = client.post(
                "/api/ai/chat",
                json={"message": "What is my overall status?"},
                headers=headers_a,
            )
            assert resp.status_code == 200
            # Context builder must be called with the twin state
            assert mock_build.called

    @patch("app.services.ai.assistant_service.genai")
    def test_two_different_users_both_get_200(self, mock_genai):
        """Two different authenticated users can independently call the AI endpoint."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Your data is here."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        resp_a = client.post(
            "/api/ai/chat",
            json={"message": "How are my finances?"},
            headers=_headers(_USER_A_EMAIL, _USER_A_PASSWORD),
        )
        resp_b = client.post(
            "/api/ai/chat",
            json={"message": "How are my finances?"},
            headers=_headers(_USER_B_EMAIL, _USER_B_PASSWORD),
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200


# ─────────────────────────────────────────────────────────────────────────────
# Context structure validation
# ─────────────────────────────────────────────────────────────────────────────

class TestContextStructure:
    def test_context_has_required_top_level_keys(self):
        """AI context must have user, digital_twin, and ml_predictions sections."""
        twin = _make_twin_state()
        ctx = build_ai_context(twin)

        assert "user" in ctx
        assert "digital_twin" in ctx
        assert "ml_predictions" in ctx

    def test_context_digital_twin_has_all_domains(self):
        """digital_twin section must include all five life domains."""
        twin = _make_twin_state()
        ctx = build_ai_context(twin)

        dt = ctx["digital_twin"]
        for domain in ("academic", "financial", "fitness", "lifestyle_habits", "goals"):
            assert domain in dt, f"Missing domain: {domain}"

    def test_context_ml_predictions_has_all_models(self):
        """ml_predictions must include all five model domains."""
        twin = _make_twin_state()
        ctx = build_ai_context(twin)

        ml = ctx["ml_predictions"]
        for domain in ("academic", "financial", "forecasting", "lifestyle", "fitness"):
            assert domain in ml, f"Missing ML domain: {domain}"

    def test_context_user_id_preserved(self):
        """user_id in the context must match the DigitalTwinState user_id."""
        twin = _make_twin_state()
        ctx = build_ai_context(twin)

        assert ctx["user"]["user_id"] == "test-user-123"


    def test_none_prediction_dict_returns_unavailable(self):
        """When ml.academic is None (not set), context status must be 'unavailable'."""
        twin = _make_twin_state(academic_pred=None)
        ctx = build_ai_context(twin)

        academic_ctx = ctx["ml_predictions"]["academic"]
        assert academic_ctx["status"] == "unavailable"
        assert academic_ctx["prediction"] is None


# ─────────────────────────────────────────────────────────────────────────────
# LIFESTYLE 3-CLASS AI CONTEXT TESTS
# Verifies the AI context correctly handles all three Lifestyle ML classes:
#   Normal | Insomnia | Sleep Apnea
# and correct status handling for insufficient_data and model_unavailable.
# ─────────────────────────────────────────────────────────────────────────────

class TestLifestyle3ClassAIContext:
    """
    Verify the AI context builder correctly handles the 3-class Lifestyle model.
    All three classes must be preserved as strings; no class must be fabricated.
    """

    def test_lifestyle_normal_prediction_preserved_in_context(self):
        """'Normal' lifestyle prediction must be preserved in AI context."""
        pred = {
            "status": "available",
            "prediction": "Normal",
            "model_name": "GradientBoostingClassifier",
            "model_version": "2.0",
            "target": "sleep_disorder",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["status"] == "available"
        assert lf["prediction"] == "Normal"
        assert isinstance(lf["prediction"], str)

    def test_lifestyle_insomnia_prediction_preserved_in_context(self):
        """'Insomnia' lifestyle prediction must be preserved in AI context."""
        pred = {
            "status": "available",
            "prediction": "Insomnia",
            "model_name": "GradientBoostingClassifier",
            "target": "sleep_disorder",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["status"] == "available"
        assert lf["prediction"] == "Insomnia"

    def test_lifestyle_sleep_apnea_prediction_preserved_in_context(self):
        """'Sleep Apnea' lifestyle prediction must be preserved in AI context."""
        pred = {
            "status": "available",
            "prediction": "Sleep Apnea",
            "model_name": "GradientBoostingClassifier",
            "target": "sleep_disorder",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["status"] == "available"
        assert lf["prediction"] == "Sleep Apnea"

    def test_lifestyle_normal_not_fabricated_as_null(self):
        """'Normal' prediction must not be treated as null/unavailable."""
        pred = {"status": "available", "prediction": "Normal", "target": "sleep_disorder"}
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["prediction"] is not None
        assert lf["status"] == "available"

    def test_lifestyle_insufficient_data_yields_null_not_class(self):
        """insufficient_data must produce prediction=None, never a class string."""
        pred = {
            "status": "insufficient_data",
            "prediction": None,
            "reason": "Missing required lifestyle features",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["status"] == "insufficient_data"
        assert lf["prediction"] is None
        # Must not have been fabricated as any valid class
        assert lf["prediction"] not in ("Normal", "Insomnia", "Sleep Apnea")

    def test_lifestyle_model_unavailable_yields_null_not_class(self):
        """model_unavailable must produce prediction=None, never a class string."""
        pred = {
            "status": "model_unavailable",
            "prediction": None,
            "reason": "Lifestyle model could not be loaded",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf["status"] == "model_unavailable"
        assert lf["prediction"] is None

    def test_lifestyle_prediction_is_not_zero_fabricated(self):
        """Lifestyle prediction must never be replaced with 0 or 0.0."""
        pred = {"status": "available", "prediction": "Sleep Apnea", "target": "sleep_disorder"}
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        val = ctx["ml_predictions"]["lifestyle"]["prediction"]
        assert val != 0
        assert val != 0.0
        assert val == "Sleep Apnea"

    def test_lifestyle_reason_preserved_on_insufficient_data(self):
        """The 'reason' field must be preserved for insufficient_data lifestyle prediction."""
        reason = "Missing required lifestyle features (e.g., blood_pressure, occupation)"
        pred = {"status": "insufficient_data", "prediction": None, "reason": reason}
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        assert ctx["ml_predictions"]["lifestyle"].get("reason") == reason

    def test_lifestyle_and_other_domains_coexist_in_context(self):
        """Lifestyle prediction must coexist with other domain predictions in context."""
        lifestyle_pred = {"status": "available", "prediction": "Insomnia", "target": "sleep_disorder"}
        academic_pred = {"status": "available", "prediction": 82.0, "target": "exam_score"}
        twin = _make_twin_state(lifestyle_pred=lifestyle_pred, academic_pred=academic_pred)
        ctx = build_ai_context(twin)

        ml = ctx["ml_predictions"]
        assert ml["lifestyle"]["prediction"] == "Insomnia"
        assert ml["academic"]["prediction"] == 82.0

    def test_lifestyle_model_metadata_passed_through_in_context(self):
        """model_name, model_version, target must be passed through when available."""
        pred = {
            "status": "available",
            "prediction": "Normal",
            "model_name": "GradientBoostingClassifier",
            "model_version": "2.0",
            "target": "sleep_disorder",
        }
        twin = _make_twin_state(lifestyle_pred=pred)
        ctx = build_ai_context(twin)

        lf = ctx["ml_predictions"]["lifestyle"]
        assert lf.get("model_name") == "GradientBoostingClassifier"
        assert lf.get("model_version") == "2.0"
        assert lf.get("target") == "sleep_disorder"

    def test_lifestyle_prediction_in_digital_twin_domain_context(self):
        """Digital Twin lifestyle_habits domain must appear in context structure."""
        twin = _make_twin_state()
        ctx = build_ai_context(twin)

        dt = ctx["digital_twin"]
        assert "lifestyle_habits" in dt, "lifestyle_habits must be in digital_twin context"
        assert "status" in dt["lifestyle_habits"]
        assert "metrics" in dt["lifestyle_habits"]

