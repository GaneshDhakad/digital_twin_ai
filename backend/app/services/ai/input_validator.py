"""
input_validator.py
User input safety and sanitization utilities for the AI assistant layer.

Responsibilities:
    - Validate and clean user-supplied messages before they reach the prompt
    - Provide safe log sanitization to avoid logging PII or sensitive content
    - Enforce consistent length limits across the service layer

Security:
    - Full message text is NEVER logged — only length and a truncated prefix
    - JWT tokens, API keys, and passwords must never be passed here
    - sanitize_for_log() is the ONLY function that should produce log strings
      from user content

Step 7 (Safety & Hardening):
    This module is part of the Step 7 input-hardening layer.
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Maximum characters allowed in a single user message.
# This is enforced at the Pydantic schema level (max_length=2000) AND here
# as a defence-in-depth check inside the service layer.
MAX_MESSAGE_LENGTH: int = 2000

# Prefix length preserved in sanitized log output (avoids logging full messages)
_LOG_PREVIEW_CHARS: int = 80


def validate_message(message: str) -> str:
    """
    Validate and normalise a user-supplied chat message.

    Performs:
        1. Strip leading/trailing whitespace
        2. Reject empty or whitespace-only messages
        3. Enforce MAX_MESSAGE_LENGTH

    Args:
        message: Raw message string from the request body.

    Returns:
        Stripped, validated message string.

    Raises:
        ValueError: If the message is empty, whitespace-only, or too long.
    """
    stripped = message.strip()

    if not stripped:
        raise ValueError(
            "Message must not be empty or consist only of whitespace."
        )

    if len(stripped) > MAX_MESSAGE_LENGTH:
        raise ValueError(
            f"Message exceeds the maximum allowed length of {MAX_MESSAGE_LENGTH} characters. "
            f"Received {len(stripped)} characters."
        )

    return stripped


def sanitize_for_log(text: str, max_chars: int = _LOG_PREVIEW_CHARS) -> str:
    """
    Produce a safe, truncated representation of text for server-side logging.

    This function must be used whenever user message content needs to be
    included in a log line. It prevents:
        - Logging of full user messages that may contain PII
        - Log injection attacks via newlines/special characters in messages
        - Accidentally logging secrets the user might paste into the chat

    Args:
        text:      The raw text to sanitize.
        max_chars: Maximum number of characters to include in the log output.
                   Defaults to 80.

    Returns:
        A safe string of at most max_chars printable characters, with a
        trailing indicator if the original was truncated.
    """
    if not text:
        return "<empty>"

    # Replace control characters and newlines with spaces to prevent log injection
    safe = "".join(ch if ch.isprintable() and ch != "\n" else " " for ch in text)

    if len(safe) <= max_chars:
        return safe

    return safe[:max_chars] + f"…[+{len(safe) - max_chars} chars]"
