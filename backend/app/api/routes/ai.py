"""
routes/ai.py — AI chat endpoint for the Personal Digital Twin assistant.

Endpoint:
    POST /api/ai/chat

Pipeline:
    Authenticated user
        → ConversationMemory (get or create conversation)             [Step 3]
        → DigitalTwinService (source of truth)                        [Step 2]
        → ContextBuilder                                              [Step 2]
        → AssistantService (Gemini) with conversation history         [Steps 3–5]
        → ResponseParser (extract + validate structured insights)     [Step 6]
        → Store user + model turn in ConversationMemory               [Step 3]
        → AIChatResponse (response, conversation_id, status, insights)[Steps 3+6]

Security (Step 7):
    - Requires valid JWT (get_current_user)
    - User ID is taken from the authenticated token — never from request body
    - conversation_id ownership is validated — users cannot access other users' histories
    - Invalid conversation_id → new conversation silently (no information disclosure)
    - API key errors return 503, not 500
    - No secrets, stack traces, or API keys exposed in error messages
    - User message content not logged in full (only length)
    - JWT tokens never logged
"""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, get_db
from app.models.user import User
from app.schemas.ai import AIChatRequest, AIChatResponse, AIInsight
from app.services.digital_twin_service import get_digital_twin_state
from app.services.ai.context_builder import build_ai_context
from app.services.ai.assistant_service import get_ai_response
from app.services.ai.conversation_memory import conversation_store
from app.services.ai.response_parser import parse_insights_from_response
from app.services.ai.input_validator import sanitize_for_log

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/ai",
    tags=["AI Assistant"],
)


@router.post(
    "/chat",
    response_model=AIChatResponse,
    summary="Chat with your Personal Digital Twin AI assistant",
    status_code=status.HTTP_200_OK,
)
def ai_chat(
    request: AIChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AIChatResponse:
    """
    Send a question to the AI assistant grounded in your Digital Twin context.

    Supports multi-turn conversations via `conversation_id`. If you omit
    `conversation_id`, a new conversation is started and its ID is returned.
    Pass the returned ID in subsequent requests to maintain conversation context.

    When the AI identifies data-grounded insights or recommendations, they are
    returned as structured objects in the `insights` list alongside the prose
    response. If no structured insights are produced, `insights` is an empty list.

    The assistant has access only to your own Digital Twin data — it cannot
    access another user's data. The authenticated user's ID is used exclusively
    to retrieve their Digital Twin and conversation history; no user_id is
    accepted from the request body.

    Returns:
        AIChatResponse with: response, conversation_id, status, insights.

    Error codes:
        400 — invalid/empty message (handled by Pydantic validation → 422)
        401 — unauthenticated
        403 — inactive account
        500 — unexpected internal error
        502 — AI provider returned unexpected/empty response
        503 — Gemini API key not configured or provider unavailable
    """
    user_id = str(current_user.user_id)

    # Step 7 — Log request metadata safely (no full message content, no tokens)
    logger.info(
        "AI chat request: user_id=%s msg_chars=%d has_conv_id=%s",
        user_id,
        len(request.message),
        bool(request.conversation_id),
    )

    # ── Step 1: Resolve conversation ID ────────────────────────────────────────
    # If a conversation_id is provided, validate that it belongs to this user.
    # If validation fails (unknown ID, or another user's ID), silently create a
    # new conversation — we do NOT reveal whether the ID belongs to another user
    # (Step 7: no information disclosure).
    conversation_id: str
    requested_conv_id = request.conversation_id

    if requested_conv_id:
        if conversation_store.validate_ownership(user_id, requested_conv_id):
            conversation_id = requested_conv_id
            logger.debug(
                "Resuming conversation conv_id=%s user_id=%s",
                conversation_id,
                user_id,
            )
        else:
            # Unknown or cross-user ID — start fresh, do not reveal the reason
            # Step 7: warning logged server-side but NOT surfaced to client
            logger.warning(
                "Invalid or cross-user conversation_id requested by user_id=%s. "
                "Starting a new conversation.",
                user_id,
            )
            conversation_id = conversation_store.create_conversation(user_id)
    else:
        conversation_id = conversation_store.create_conversation(user_id)
        logger.debug(
            "Created new conversation conv_id=%s user_id=%s",
            conversation_id,
            user_id,
        )

    # ── Step 2: Retrieve conversation history ──────────────────────────────────
    history = conversation_store.get_history(user_id, conversation_id)

    # ── Step 3: Retrieve the authenticated user's Digital Twin ─────────────────
    try:
        twin_state = get_digital_twin_state(db, user_id)
    except Exception as exc:
        logger.exception(
            "Failed to retrieve Digital Twin for user_id=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to retrieve your Digital Twin data. "
                "Please ensure your data is set up and try again."
            ),
        )

    # ── Step 4: Build AI context from the Digital Twin ─────────────────────────
    try:
        ai_context = build_ai_context(twin_state)
    except Exception as exc:
        logger.exception(
            "Failed to build AI context for user_id=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to prepare your Digital Twin context for the AI assistant.",
        )

    # ── Step 5: Send context + history + message to Gemini ─────────────────────
    clean_message = request.message.strip()

    try:
        raw_ai_text = get_ai_response(
            message=clean_message,
            ai_context=ai_context,
            conversation_history=history,
        )
    except ValueError as exc:
        # GEMINI_API_KEY not configured (Step 7)
        logger.error(
            "AI service configuration error for user_id=%s: %s", user_id, exc
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The AI assistant service is not available at this time. "
                "Please contact the administrator."
            ),
        )
    except RuntimeError as exc:
        # Provider returned empty/unexpected response (Step 7)
        logger.error("AI runtime error for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The AI provider returned an unexpected response. Please try again.",
        )
    except Exception as exc:
        # Google API errors (rate limit, auth, etc.) and any other unexpected error
        # Step 7: log exc server-side but return generic message (no stack trace)
        logger.exception("Unexpected AI error for user_id=%s: %s", user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "The AI assistant is temporarily unavailable. "
                "Please try again in a moment."
            ),
        )

    # ── Step 6: Parse and validate structured insights ─────────────────────────
    # parse_insights_from_response never raises — returns (clean_text, [insights])
    # on any error. The insights block (if any) is stripped from the user-visible text.
    response_text, insights = parse_insights_from_response(raw_ai_text)

    # Ensure response_text is never empty after stripping the insights block
    if not response_text or not response_text.strip():
        response_text = raw_ai_text.strip()

    logger.debug(
        "AI response parsed: user_id=%s text_chars=%d num_insights=%d",
        user_id,
        len(response_text),
        len(insights),
    )

    # ── Step 7: Persist turns to conversation memory ───────────────────────────
    # Store the clean user message and the clean AI prose text.
    # Store clean_message (not raw_ai_text, not context, not system prompt).
    # NEVER store: API keys, JWT tokens, passwords, raw system prompt, context JSON.
    # Store prose text in history (not the raw AI text with insight blocks) so that
    # multi-turn context is human-readable and compact.
    conversation_store.add_message(
        user_id=user_id,
        conversation_id=conversation_id,
        role="user",
        content=clean_message,
    )
    conversation_store.add_message(
        user_id=user_id,
        conversation_id=conversation_id,
        role="model",
        content=response_text,
    )

    # Convert parser AIInsight objects → schema AIInsight objects
    # (both have identical fields; this ensures the route always returns
    #  schema-validated objects regardless of parser internals)
    schema_insights = [
        AIInsight(
            area=insight.area,
            type=insight.type,
            title=insight.title,
            description=insight.description,
            priority=insight.priority,
            reason=insight.reason,
        )
        for insight in insights
    ]

    return AIChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        status="success",
        insights=schema_insights,
    )
