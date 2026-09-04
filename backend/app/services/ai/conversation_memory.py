"""
conversation_memory.py
Thread-safe, in-memory conversation history store for the AI assistant.

Design:
    - Data is stored in a nested dict: {user_id: {conversation_id: [messages]}}
    - Access is protected by a threading.Lock for thread safety.
    - Conversations are indexed first by user_id so cross-user access is
      structurally impossible (not just checked — impossible by design).
    - A module-level singleton (conversation_store) is used so that the entire
      application shares one store within a single process.

Security:
    - Messages stored here must NEVER contain secrets, API keys, JWT tokens,
      passwords, or raw system prompts. The caller is responsible for filtering.
    - History is bounded by MAX_CONVERSATION_MESSAGES to prevent unlimited growth.

Limitations:
    - In-memory only: conversations are lost on server restart.
    - Single-process only: will not share state across multiple uvicorn workers.
      For a production multi-process deployment, replace with Redis or a DB store.
"""
from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional
from uuid import uuid4

logger = logging.getLogger(__name__)

# Maximum number of individual messages (user + model turns combined) to keep
# per conversation. Older messages are dropped from the front when exceeded.
MAX_CONVERSATION_MESSAGES: int = 20


class ConversationMessage:
    """A single message in a conversation turn."""

    __slots__ = ("role", "content")

    def __init__(self, role: str, content: str) -> None:
        # role must be "user" or "model" (Gemini convention)
        if role not in ("user", "model"):
            raise ValueError(f"Invalid role '{role}'. Must be 'user' or 'model'.")
        self.role = role
        self.content = content

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


class ConversationMemory:
    """
    Thread-safe, per-user conversation memory store.

    Storage layout::

        _store = {
            "<user_id>": {
                "<conversation_id>": [
                    ConversationMessage(role="user", content="..."),
                    ConversationMessage(role="model", content="..."),
                    ...
                ]
            }
        }

    The user_id index provides structural user isolation — you cannot reach
    another user's conversation without knowing their user_id, which is always
    sourced from the authenticated JWT, never from request body data.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Dict[str, List[ConversationMessage]]] = {}
        self._lock = threading.Lock()

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    def create_conversation(self, user_id: str) -> str:
        """
        Create a new conversation for a user.

        Args:
            user_id: The authenticated user's ID (from JWT, not request body).

        Returns:
            A newly generated conversation_id (UUID4 string).
        """
        conversation_id = str(uuid4())
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = {}
            self._store[user_id][conversation_id] = []
        logger.debug(
            "Created new conversation %s for user %s", conversation_id, user_id
        )
        return conversation_id

    def validate_ownership(self, user_id: str, conversation_id: str) -> bool:
        """
        Return True if conversation_id exists and belongs to user_id.

        This is a security check that prevents one user from accessing another
        user's conversation by guessing or brute-forcing conversation IDs.

        Args:
            user_id:         Authenticated user's ID.
            conversation_id: The conversation ID to validate.

        Returns:
            True if the conversation exists and belongs to this user, else False.
        """
        with self._lock:
            user_convs = self._store.get(user_id)
            if user_convs is None:
                return False
            return conversation_id in user_convs

    def get_history(
        self, user_id: str, conversation_id: str
    ) -> List[Dict[str, str]]:
        """
        Retrieve the conversation history for a given user + conversation.

        If the conversation does not exist or belongs to a different user,
        an empty list is returned rather than raising an exception.

        Args:
            user_id:         Authenticated user's ID.
            conversation_id: The conversation ID to retrieve.

        Returns:
            List of dicts: [{"role": "user"|"model", "content": "..."}]
            Returns [] if conversation is empty or not found.
        """
        with self._lock:
            user_convs = self._store.get(user_id, {})
            messages = user_convs.get(conversation_id, [])
            return [msg.to_dict() for msg in messages]

    def add_message(
        self,
        user_id: str,
        conversation_id: str,
        role: str,
        content: str,
    ) -> None:
        """
        Append a message to the conversation history.

        If the conversation does not yet exist (e.g. was created inline by the
        caller), it is created automatically. If the history reaches
        MAX_CONVERSATION_MESSAGES, the oldest message is dropped.

        IMPORTANT — callers must NEVER pass secrets, API keys, JWT tokens, or
        internal system prompt text as content here. Only user messages and AI
        response text should be stored.

        Args:
            user_id:         Authenticated user's ID.
            conversation_id: The target conversation.
            role:            "user" or "model".
            content:         Message content (clean user/AI text only).
        """
        msg = ConversationMessage(role=role, content=content)
        with self._lock:
            if user_id not in self._store:
                self._store[user_id] = {}
            if conversation_id not in self._store[user_id]:
                self._store[user_id][conversation_id] = []

            history = self._store[user_id][conversation_id]
            history.append(msg)

            # Enforce the size cap — drop oldest messages from the front
            while len(history) > MAX_CONVERSATION_MESSAGES:
                dropped = history.pop(0)
                logger.debug(
                    "Conversation %s for user %s exceeded MAX_CONVERSATION_MESSAGES=%d. "
                    "Dropped oldest message (role=%s).",
                    conversation_id,
                    user_id,
                    MAX_CONVERSATION_MESSAGES,
                    dropped.role,
                )

    def get_conversation_count(self, user_id: str) -> int:
        """Return the number of active conversations for a user (for diagnostics)."""
        with self._lock:
            return len(self._store.get(user_id, {}))

    def clear_user_history(self, user_id: str) -> None:
        """Remove all conversations for a user (for testing / cleanup)."""
        with self._lock:
            self._store.pop(user_id, None)
        logger.debug("Cleared all conversation history for user %s", user_id)


# ─────────────────────────────────────────────────────────────────────────────
# Module-level singleton — shared across the entire process
# ─────────────────────────────────────────────────────────────────────────────

conversation_store = ConversationMemory()
