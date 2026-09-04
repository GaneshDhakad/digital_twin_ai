"""
schemas/ai.py — Pydantic schemas for the AI chat endpoint.

Step 3: Added conversation_id to request + response.
Step 6: Added AIInsight model and insights list to AIChatResponse.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ─────────────────────────────────────────────────────────────────────────────
# Step 6 — Structured Output Schema
# ─────────────────────────────────────────────────────────────────────────────

class AIInsight(BaseModel):
    """
    A single structured insight or recommendation from the AI assistant.

    Produced when the AI identifies a meaningful, data-grounded observation or
    recommendation from the user's Digital Twin context.

    All fields have safe defaults — the schema is designed to tolerate partial
    or missing AI-generated data without crashing.

    Note: This schema mirrors response_parser.AIInsight. Both are kept for
    separation of concerns: response_parser handles parse/validation logic;
    this schema is the API contract exposed to API consumers.
    """

    model_config = {"extra": "ignore"}

    area: str = Field(
        default="general",
        description=(
            "The Digital Twin domain this insight relates to. "
            "Examples: academic, financial, fitness, lifestyle, habits, goals, forecasting."
        ),
    )
    type: str = Field(
        default="recommendation",
        description=(
            "The type of insight. "
            "One of: recommendation, warning, observation, insight, tip."
        ),
    )
    title: str = Field(
        default="",
        description="Short title for the insight (for display in UI).",
    )
    description: str = Field(
        default="",
        description="Full description of the insight or recommendation.",
    )
    priority: Optional[str] = Field(
        default=None,
        description=(
            "Priority level if data justifies it: 'high', 'medium', or 'low'. "
            "Null if the data does not support assigning a specific priority."
        ),
    )
    reason: str = Field(
        default="",
        description="Why this insight is being surfaced (grounded in Digital Twin data).",
    )


# ─────────────────────────────────────────────────────────────────────────────
# Request / Response schemas
# ─────────────────────────────────────────────────────────────────────────────

class AIChatRequest(BaseModel):
    """Request body for POST /api/ai/chat."""

    message: str = Field(
        ...,
        description="The user's question or message for the Digital Twin assistant.",
        min_length=1,
        max_length=2000,
    )

    conversation_id: Optional[str] = Field(
        default=None,
        description=(
            "Optional conversation ID for multi-turn conversations. "
            "If omitted, a new conversation is created and its ID is returned. "
            "If provided, the previous conversation history is included in the AI context."
        ),
    )

    @field_validator("message")
    @classmethod
    def message_not_whitespace(cls, v: str) -> str:
        """Reject messages that are whitespace-only."""
        if not v.strip():
            raise ValueError(
                "Message must not be empty or consist of only whitespace."
            )
        return v


class AIChatResponse(BaseModel):
    """
    Response body for POST /api/ai/chat.

    Backward-compatible extension from Steps 1–4:
        - response, conversation_id, status — unchanged from Step 3
        - insights                          — new in Step 6, defaults to []
    """

    response: str = Field(
        ...,
        description="The AI assistant's prose response text.",
    )
    conversation_id: str = Field(
        ...,
        description=(
            "The conversation ID for this exchange. "
            "Pass this in subsequent requests to continue the conversation."
        ),
    )
    status: str = Field(
        default="success",
        description="Response status indicator.",
    )
    insights: List[AIInsight] = Field(
        default_factory=list,
        description=(
            "Optional list of structured insights or recommendations extracted from "
            "the AI response. Empty list if the AI produced no structured output or "
            "if the response was purely conversational."
        ),
    )
