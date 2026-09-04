"""
app/services/ai — AI backend service package.

Provides:
    context_builder    — converts DigitalTwinState → structured AI context
    assistant_service  — Gemini LLM client + four-section prompt construction
                         (Steps 1–5: integration, context, memory, prompt quality,
                          recommendations, structured output instructions,
                          security/injection defence)
    conversation_memory — thread-safe, in-memory, per-user conversation store
    response_parser    — safe parser/validator for AI-generated structured insights
                         (Step 6: structured output, never crashes on malformed JSON)
    input_validator    — user input validation and safe log sanitization utilities
                         (Step 7: safety, hardening, PII-safe logging)
"""
