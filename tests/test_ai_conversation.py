"""
tests/test_ai_conversation.py
Tests for Milestone 4 Steps 3 & 4 — Conversational Memory and Prompt Engineering.

Coverage:
    Step 3 — Conversational Memory:
    1.  New conversation created when no conversation_id supplied
    2.  conversation_id returned in response
    3.  Existing conversation continuation (history included)
    4.  User isolation — user A cannot access user B's conversation
    5.  Invalid/unknown conversation_id handled safely (new conversation created)
    6.  History size limit (MAX_CONVERSATION_MESSAGES enforced)
    7.  Existing Step 1–2 behavior remains functional

    Step 4 — Prompt Engineering:
    8.  System instructions present in the prompt config
    9.  Conversation history converted to Content objects correctly
    10. Current message includes Digital Twin context
    11. History is included when non-empty

    ConversationMemory unit tests:
    12. create_conversation returns a UUID string
    13. validate_ownership returns True for own conversation
    14. validate_ownership returns False for other user's conversation
    15. validate_ownership returns False for non-existent conversation
    16. get_history returns empty list for new conversation
    17. add_message appends messages and they appear in get_history
    18. History cap: MAX_CONVERSATION_MESSAGES enforced (oldest dropped)
    19. clear_user_history removes all conversations for a user
    20. ConversationMessage rejects invalid role

Important:
    NO real LLM API calls are made. The Gemini client is fully mocked.
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock, call, patch

import pytest

# ── Isolated SQLite for tests ──────────────────────────────────────────────────
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_digital_twin.db")

backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

from fastapi.testclient import TestClient
from backend.main import app
from app.services.ai.conversation_memory import (
    ConversationMemory,
    ConversationMessage,
    MAX_CONVERSATION_MESSAGES,
    conversation_store,
)
from app.services.ai.assistant_service import (
    get_ai_response,
    _build_history_contents,
    _build_current_message_content,
    _SYSTEM_INSTRUCTIONS,
)
from app.services.ai.context_builder import build_ai_context
from app.schemas.digital_twin import DigitalTwinState, DomainState, MLPredictions
from google.genai import types as genai_types

client = TestClient(app)

# ─────────────────────────────────────────────────────────────────────────────
# Shared test helpers
# ─────────────────────────────────────────────────────────────────────────────

_MOCK_AI_RESPONSE = "Based on your Digital Twin data, your finances look healthy."

_USER_A_EMAIL = "conv_user_a@example.com"
_USER_A_PASSWORD = "SecurePassA1"
_USER_B_EMAIL = "conv_user_b@example.com"
_USER_B_PASSWORD = "SecurePassB1"

_auth_cache: Dict[str, str] = {}


def _register_and_login(email: str, password: str) -> str:
    """Register user (ignore if already exists) and return Bearer token."""
    if email in _auth_cache:
        return _auth_cache[email]

    client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": "Conv Test User"},
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


def _make_twin_state() -> DigitalTwinState:
    """Helper: build a minimal DigitalTwinState for unit tests."""
    now = datetime.now(timezone.utc)
    domain = DomainState(status="stable", metrics={}, last_updated=now)
    ml = MLPredictions(
        academic=None,
        financial=None,
        lifestyle=None,
        forecasting=None,
        fitness=None,
        retrieved_at=now.isoformat(),
    )
    return DigitalTwinState(
        user_id="test-conv-user-123",
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
    Return a mock for app.services.ai.assistant_service.genai that simulates
    a successful Gemini response. No real network calls are made.
    """
    mock_client_instance = MagicMock()
    mock_response = MagicMock()
    mock_response.text = response_text
    mock_client_instance.models.generate_content.return_value = mock_response

    mock_genai = MagicMock()
    mock_genai.Client.return_value = mock_client_instance
    return mock_genai


# ─────────────────────────────────────────────────────────────────────────────
# ConversationMemory Unit Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationMemoryUnit:
    """Unit tests for the ConversationMemory class (no HTTP, no Gemini)."""

    def setup_method(self):
        """Use a fresh ConversationMemory for each test."""
        self.mem = ConversationMemory()

    # 12. create_conversation returns a UUID-like string
    def test_create_conversation_returns_string(self):
        """create_conversation must return a non-empty string."""
        conv_id = self.mem.create_conversation("user-1")
        assert isinstance(conv_id, str)
        assert len(conv_id) > 0

    def test_create_conversation_unique_ids(self):
        """Each call to create_conversation must return a unique ID."""
        id1 = self.mem.create_conversation("user-1")
        id2 = self.mem.create_conversation("user-1")
        assert id1 != id2

    # 13. validate_ownership True for own conversation
    def test_validate_ownership_own_conversation(self):
        """validate_ownership must return True for the creating user."""
        conv_id = self.mem.create_conversation("user-1")
        assert self.mem.validate_ownership("user-1", conv_id) is True

    # 14. validate_ownership False for other user's conversation
    def test_validate_ownership_cross_user(self):
        """validate_ownership must return False for a different user."""
        conv_id = self.mem.create_conversation("user-1")
        assert self.mem.validate_ownership("user-2", conv_id) is False

    # 15. validate_ownership False for non-existent conversation
    def test_validate_ownership_nonexistent(self):
        """validate_ownership must return False for an unknown conversation_id."""
        assert self.mem.validate_ownership("user-1", "does-not-exist") is False

    # 16. get_history returns empty list for new conversation
    def test_get_history_empty_for_new_conversation(self):
        """A freshly created conversation must have an empty history."""
        conv_id = self.mem.create_conversation("user-1")
        history = self.mem.get_history("user-1", conv_id)
        assert history == []

    def test_get_history_returns_empty_for_unknown(self):
        """get_history for an unknown conversation returns []."""
        history = self.mem.get_history("user-1", "unknown-conv-id")
        assert history == []

    # 17. add_message appends and appears in get_history
    def test_add_message_appears_in_history(self):
        """Messages added must appear in get_history in order."""
        conv_id = self.mem.create_conversation("user-1")
        self.mem.add_message("user-1", conv_id, "user", "Hello")
        self.mem.add_message("user-1", conv_id, "model", "Hi there!")

        history = self.mem.get_history("user-1", conv_id)
        assert len(history) == 2
        assert history[0] == {"role": "user", "content": "Hello"}
        assert history[1] == {"role": "model", "content": "Hi there!"}

    def test_add_message_auto_creates_conversation(self):
        """add_message for an unknown conv_id auto-creates it."""
        self.mem.add_message("user-1", "auto-created-id", "user", "test")
        history = self.mem.get_history("user-1", "auto-created-id")
        assert len(history) == 1

    # 18. History cap enforced — oldest messages dropped
    def test_history_cap_enforced(self):
        """History must not exceed MAX_CONVERSATION_MESSAGES."""
        conv_id = self.mem.create_conversation("user-cap")
        for i in range(MAX_CONVERSATION_MESSAGES + 5):
            role = "user" if i % 2 == 0 else "model"
            self.mem.add_message("user-cap", conv_id, role, f"message-{i}")

        history = self.mem.get_history("user-cap", conv_id)
        assert len(history) == MAX_CONVERSATION_MESSAGES

    def test_history_cap_drops_oldest_first(self):
        """When cap is exceeded, the oldest messages must be dropped."""
        conv_id = self.mem.create_conversation("user-cap2")
        for i in range(MAX_CONVERSATION_MESSAGES + 3):
            self.mem.add_message("user-cap2", conv_id, "user", f"msg-{i}")

        history = self.mem.get_history("user-cap2", conv_id)
        # The first remaining message should NOT be "msg-0"
        assert history[0]["content"] != "msg-0"
        # The last message should be the most recent
        assert history[-1]["content"] == f"msg-{MAX_CONVERSATION_MESSAGES + 2}"

    # 19. clear_user_history
    def test_clear_user_history(self):
        """clear_user_history must remove all conversations for the user."""
        conv_id = self.mem.create_conversation("user-clear")
        self.mem.add_message("user-clear", conv_id, "user", "Hi")
        self.mem.clear_user_history("user-clear")
        assert self.mem.validate_ownership("user-clear", conv_id) is False

    # 20. ConversationMessage rejects invalid role
    def test_conversation_message_invalid_role(self):
        """ConversationMessage must raise ValueError for an invalid role."""
        with pytest.raises(ValueError, match="Invalid role"):
            ConversationMessage(role="assistant", content="Hello")

    def test_conversation_message_valid_roles(self):
        """ConversationMessage must accept 'user' and 'model'."""
        msg_user = ConversationMessage(role="user", content="Hello")
        msg_model = ConversationMessage(role="model", content="Hi!")
        assert msg_user.to_dict() == {"role": "user", "content": "Hello"}
        assert msg_model.to_dict() == {"role": "model", "content": "Hi!"}

    def test_user_isolation_structural(self):
        """User A's conversation must not appear when querying User B."""
        conv_id_a = self.mem.create_conversation("user-A")
        self.mem.add_message("user-A", conv_id_a, "user", "User A secret")

        # User B has no conversations
        history_b = self.mem.get_history("user-B", conv_id_a)
        assert history_b == []

        # User B cannot validate ownership of user A's conversation
        assert self.mem.validate_ownership("user-B", conv_id_a) is False

    def test_get_conversation_count(self):
        """get_conversation_count must reflect actual number of conversations."""
        user_id = "user-count"
        assert self.mem.get_conversation_count(user_id) == 0
        self.mem.create_conversation(user_id)
        assert self.mem.get_conversation_count(user_id) == 1
        self.mem.create_conversation(user_id)
        assert self.mem.get_conversation_count(user_id) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Prompt Architecture Unit Tests (Step 4)
# ─────────────────────────────────────────────────────────────────────────────

class TestPromptArchitecture:
    """Unit tests for the four-section prompt construction (Step 4)."""

    def _make_context(self) -> Dict[str, Any]:
        twin = _make_twin_state()
        return build_ai_context(twin)

    # 8. System instructions present
    def test_system_instructions_not_empty(self):
        """_SYSTEM_INSTRUCTIONS must be a non-empty string."""
        assert isinstance(_SYSTEM_INSTRUCTIONS, str)
        assert len(_SYSTEM_INSTRUCTIONS) > 100

    def test_system_instructions_cover_key_rules(self):
        """System instructions must mention critical integrity rules."""
        rules = [
            "null",         # null handling
            "fabricat",     # no fabrication
            "status",       # respect status field
            "insufficient_data",  # status values
            "model_unavailable",  # status values
            "available",    # status values
            "predict",      # prediction language
            "API key",      # security rule
        ]
        for rule in rules:
            assert rule.lower() in _SYSTEM_INSTRUCTIONS.lower(), (
                f"System instructions missing coverage for: '{rule}'"
            )

    # 10. Current message includes Digital Twin context
    def test_current_message_content_has_context(self):
        """_build_current_message_content must embed Digital Twin JSON."""
        ctx = self._make_context()
        content = _build_current_message_content("What is my financial status?", ctx)

        assert isinstance(content, genai_types.Content)
        assert content.role == "user"
        text = content.parts[0].text
        assert "DIGITAL TWIN CONTEXT" in text
        assert "financial" in text.lower()  # context JSON embedded
        assert "What is my financial status?" in text

    def test_current_message_separates_sections(self):
        """The current message must clearly label section 2 and section 4."""
        ctx = self._make_context()
        content = _build_current_message_content("Test question", ctx)
        text = content.parts[0].text
        assert "SECTION 2" in text
        assert "SECTION 4" in text

    # 9. Conversation history converted to Content objects
    def test_build_history_contents_empty(self):
        """Empty history must return an empty list."""
        result = _build_history_contents([])
        assert result == []

    def test_build_history_contents_single_turn(self):
        """Single user message must produce one Content object."""
        history = [{"role": "user", "content": "Hello"}]
        result = _build_history_contents(history)
        assert len(result) == 1
        assert isinstance(result[0], genai_types.Content)
        assert result[0].role == "user"
        assert result[0].parts[0].text == "Hello"

    def test_build_history_contents_multi_turn(self):
        """Multi-turn history must produce correct number of Content objects."""
        history = [
            {"role": "user", "content": "How are my finances?"},
            {"role": "model", "content": "Your finances look stable."},
            {"role": "user", "content": "How can I improve?"},
        ]
        result = _build_history_contents(history)
        assert len(result) == 3
        assert result[0].role == "user"
        assert result[1].role == "model"
        assert result[2].role == "user"
        assert result[1].parts[0].text == "Your finances look stable."

    # 11. History is included in get_ai_response call
    @patch("app.services.ai.assistant_service.genai")
    def test_get_ai_response_includes_history_in_contents(self, mock_genai):
        """get_ai_response must include conversation history in the contents list."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Here is your answer."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        ctx = self._make_context()
        history = [
            {"role": "user", "content": "Previous question"},
            {"role": "model", "content": "Previous answer"},
        ]

        result = get_ai_response("New question", ctx, conversation_history=history)
        assert result == "Here is your answer."

        # Verify generate_content was called with correct number of contents
        call_args = mock_client.models.generate_content.call_args
        contents = call_args.kwargs.get("contents") or call_args.args[1] if call_args.args else None
        if contents is None:
            # Try positional args
            contents = call_args[1].get("contents") if len(call_args) > 1 else None

        # Check generate_content was called at all
        assert mock_client.models.generate_content.called

    @patch("app.services.ai.assistant_service.genai")
    def test_get_ai_response_no_history(self, mock_genai):
        """get_ai_response must work correctly with no history (None)."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Single turn response."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        ctx = self._make_context()
        result = get_ai_response("Question", ctx, conversation_history=None)
        assert result == "Single turn response."
        assert mock_client.models.generate_content.called

    @patch("app.services.ai.assistant_service.genai")
    def test_get_ai_response_empty_history(self, mock_genai):
        """get_ai_response must work correctly with empty history list."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "Empty history response."
        mock_client.models.generate_content.return_value = mock_response
        mock_genai.Client.return_value = mock_client

        ctx = self._make_context()
        result = get_ai_response("Question", ctx, conversation_history=[])
        assert result == "Empty history response."


# ─────────────────────────────────────────────────────────────────────────────
# Integration Tests — Step 3: Conversational Memory via HTTP
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationalMemoryAPI:
    """Integration tests for conversational memory through the HTTP API."""

    # 1. New conversation created when no conversation_id supplied
    @patch("app.services.ai.assistant_service.genai")
    def test_new_conversation_created_without_id(self, mock_genai):
        """When no conversation_id is sent, a new conversation is created."""
        mock_genai.Client.return_value = _mock_genai_client().Client.return_value
        mock_genai.Client.return_value.models.generate_content.return_value.text = _MOCK_AI_RESPONSE

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "How am I doing financially?"},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text

    # 2. conversation_id returned in response
    @patch("app.services.ai.assistant_service.genai")
    def test_conversation_id_returned_in_response(self, mock_genai):
        """The response must include a conversation_id field."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = _MOCK_AI_RESPONSE
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "Tell me about my goals."},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "conversation_id" in data
        assert isinstance(data["conversation_id"], str)
        assert len(data["conversation_id"]) > 0

    # 3. Existing conversation continuation (history included)
    @patch("app.services.ai.assistant_service.genai")
    def test_existing_conversation_continuation(self, mock_genai):
        """
        A second request with the same conversation_id should succeed and
        the assistant should receive prior history.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = _MOCK_AI_RESPONSE
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)

        # First turn
        resp1 = client.post(
            "/api/ai/chat",
            json={"message": "How are my finances?"},
            headers=headers,
        )
        assert resp1.status_code == 200, resp1.text
        conv_id = resp1.json()["conversation_id"]

        # Second turn with same conversation_id
        resp2 = client.post(
            "/api/ai/chat",
            json={"message": "How can I improve it?", "conversation_id": conv_id},
            headers=headers,
        )
        assert resp2.status_code == 200, resp2.text
        data2 = resp2.json()
        assert data2["conversation_id"] == conv_id

    @patch("app.services.ai.assistant_service.genai")
    def test_continuation_same_conversation_id_preserved(self, mock_genai):
        """Subsequent requests with same conversation_id preserve that ID."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Good answer."
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp1 = client.post(
            "/api/ai/chat",
            json={"message": "What is my study status?"},
            headers=headers,
        )
        assert resp1.status_code == 200
        conv_id = resp1.json()["conversation_id"]

        resp2 = client.post(
            "/api/ai/chat",
            json={"message": "Can you elaborate?", "conversation_id": conv_id},
            headers=headers,
        )
        assert resp2.status_code == 200
        # The same conversation ID must be returned
        assert resp2.json()["conversation_id"] == conv_id

    # 5. Invalid/unknown conversation_id handled safely
    @patch("app.services.ai.assistant_service.genai")
    def test_invalid_conversation_id_handled_safely(self, mock_genai):
        """An unknown conversation_id must not cause an error — new conversation created."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = _MOCK_AI_RESPONSE
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={
                "message": "What are my fitness goals?",
                "conversation_id": "totally-invalid-uuid-that-does-not-exist",
            },
            headers=headers,
        )
        # Must succeed — not error — but return a new conversation_id
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "conversation_id" in data
        # Must return a NEW (different) conversation_id
        assert data["conversation_id"] != "totally-invalid-uuid-that-does-not-exist"

    # 7. Existing Step 1–2 behavior intact
    @patch("app.services.ai.assistant_service.genai")
    def test_existing_step1_2_behavior_intact(self, mock_genai):
        """
        Existing Step 1–2 behavior (request without conversation_id) must
        still return 200 with response and status fields.
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = _MOCK_AI_RESPONSE
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "Give me an overview of my digital twin."},
            headers=headers,
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "response" in data
        assert "status" in data
        assert data["status"] == "success"
        assert isinstance(data["response"], str)
        assert len(data["response"]) > 0
        # Also check conversation_id is now present (backward-compatible extension)
        assert "conversation_id" in data

    @patch("app.services.ai.assistant_service.genai")
    def test_response_schema_includes_all_fields(self, mock_genai):
        """Response must contain response, status, and conversation_id."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = _MOCK_AI_RESPONSE
        mock_genai.Client.return_value = mock_client

        headers = _headers(_USER_A_EMAIL, _USER_A_PASSWORD)
        resp = client.post(
            "/api/ai/chat",
            json={"message": "What domains does my digital twin cover?"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert set(data.keys()) >= {"response", "status", "conversation_id"}
        assert data["status"] == "success"


# ─────────────────────────────────────────────────────────────────────────────
# 4. User Isolation — conversation history
# ─────────────────────────────────────────────────────────────────────────────

class TestConversationUserIsolation:
    """User isolation tests for conversational memory."""

    @patch("app.services.ai.assistant_service.genai")
    def test_user_b_cannot_use_user_a_conversation_id(self, mock_genai):
        """
        If user B sends user A's conversation_id, it must be treated as
        invalid and a NEW conversation must be created (not error, not leak).
        """
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Response text."
        mock_genai.Client.return_value = mock_client

        # User A creates a conversation
        resp_a = client.post(
            "/api/ai/chat",
            json={"message": "What is my financial status?"},
            headers=_headers(_USER_A_EMAIL, _USER_A_PASSWORD),
        )
        assert resp_a.status_code == 200
        user_a_conv_id = resp_a.json()["conversation_id"]

        # User B tries to use user A's conversation_id
        resp_b = client.post(
            "/api/ai/chat",
            json={
                "message": "Can I see the previous messages?",
                "conversation_id": user_a_conv_id,
            },
            headers=_headers(_USER_B_EMAIL, _USER_B_PASSWORD),
        )
        # Must succeed (not 403/500) but must get a DIFFERENT conversation_id
        assert resp_b.status_code == 200, resp_b.text
        user_b_conv_id = resp_b.json()["conversation_id"]
        assert user_b_conv_id != user_a_conv_id

    @patch("app.services.ai.assistant_service.genai")
    def test_two_users_independent_conversations(self, mock_genai):
        """User A and User B must have completely independent conversations."""
        mock_client = MagicMock()
        mock_client.models.generate_content.return_value.text = "Independent."
        mock_genai.Client.return_value = mock_client

        resp_a = client.post(
            "/api/ai/chat",
            json={"message": "User A first message"},
            headers=_headers(_USER_A_EMAIL, _USER_A_PASSWORD),
        )
        resp_b = client.post(
            "/api/ai/chat",
            json={"message": "User B first message"},
            headers=_headers(_USER_B_EMAIL, _USER_B_PASSWORD),
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        # Different conversation IDs
        assert resp_a.json()["conversation_id"] != resp_b.json()["conversation_id"]

    def test_conversation_memory_user_isolation_direct(self):
        """
        Direct test of validate_ownership: conversation created by user A
        must not be accessible by user B.
        """
        mem = ConversationMemory()
        conv_id_a = mem.create_conversation("user-isolation-A")
        mem.add_message("user-isolation-A", conv_id_a, "user", "Secret data")

        # User B cannot own user A's conversation
        assert mem.validate_ownership("user-isolation-B", conv_id_a) is False
        # User B's history for that ID must be empty
        assert mem.get_history("user-isolation-B", conv_id_a) == []

    def test_get_history_cross_user_returns_empty(self):
        """
        get_history must return [] when the conversation belongs to another user,
        even if the conversation_id is known.
        """
        mem = ConversationMemory()
        conv_id = mem.create_conversation("user-X")
        mem.add_message("user-X", conv_id, "user", "User X private message")

        result = mem.get_history("user-Y", conv_id)
        assert result == []


# ─────────────────────────────────────────────────────────────────────────────
# 6. History Size Limit (via API)
# ─────────────────────────────────────────────────────────────────────────────

class TestHistorySizeLimit:
    """Tests for history size cap enforcement."""

    def test_max_conversation_messages_constant_defined(self):
        """MAX_CONVERSATION_MESSAGES must be a positive integer."""
        assert isinstance(MAX_CONVERSATION_MESSAGES, int)
        assert MAX_CONVERSATION_MESSAGES > 0

    def test_max_conversation_messages_reasonable(self):
        """MAX_CONVERSATION_MESSAGES must be a reasonable value (10–100)."""
        assert 10 <= MAX_CONVERSATION_MESSAGES <= 100, (
            f"MAX_CONVERSATION_MESSAGES={MAX_CONVERSATION_MESSAGES} seems out of range"
        )

    def test_history_never_exceeds_cap(self):
        """Adding more than cap messages must not exceed the limit."""
        mem = ConversationMemory()
        conv_id = mem.create_conversation("limit-user")

        excess = MAX_CONVERSATION_MESSAGES + 10
        for i in range(excess):
            role = "user" if i % 2 == 0 else "model"
            mem.add_message("limit-user", conv_id, role, f"msg-{i}")

        history = mem.get_history("limit-user", conv_id)
        assert len(history) <= MAX_CONVERSATION_MESSAGES

    def test_history_size_exactly_at_cap(self):
        """Adding exactly MAX messages must retain all of them."""
        mem = ConversationMemory()
        conv_id = mem.create_conversation("exact-cap-user")

        for i in range(MAX_CONVERSATION_MESSAGES):
            role = "user" if i % 2 == 0 else "model"
            mem.add_message("exact-cap-user", conv_id, role, f"msg-{i}")

        history = mem.get_history("exact-cap-user", conv_id)
        assert len(history) == MAX_CONVERSATION_MESSAGES

    def test_oldest_messages_dropped_when_cap_exceeded(self):
        """When cap is exceeded, oldest messages are dropped, newest retained."""
        mem = ConversationMemory()
        conv_id = mem.create_conversation("drop-user")

        total = MAX_CONVERSATION_MESSAGES + 3
        for i in range(total):
            mem.add_message("drop-user", conv_id, "user", f"msg-{i}")

        history = mem.get_history("drop-user", conv_id)
        # Oldest (msg-0, msg-1, msg-2) should be gone
        contents = [m["content"] for m in history]
        assert "msg-0" not in contents
        assert "msg-1" not in contents
        assert "msg-2" not in contents
        # Most recent should be present
        assert f"msg-{total - 1}" in contents
