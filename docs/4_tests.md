# Testing Strategy & Results
**Digital Twin AI (TWIN.OS)**
*September 2026 | Verified against live test run*

---

## Test Results (Latest Run)

```
Platform: win32, Python 3.11.9
Pytest: 8.2.0
Test mode: asyncio=Mode.STRICT

134 passed, 9 warnings in 21.56s
```

**✅ All 134 tests pass.** 0 failures, 0 errors.

---

## Running the Tests

Tests require the project root to be in `PYTHONPATH` because test files import `from backend.main import app`.

```powershell
# Windows PowerShell — from project root:
$env:PYTHONPATH="." ; venv\Scripts\python.exe -m pytest tests/ -v

# Linux / macOS:
PYTHONPATH=. pytest tests/ -v
```

The `conftest.py` automatically:
1. Sets `DATABASE_URL=sqlite:///./test_digital_twin.db`
2. Drops and recreates all tables before the test session
3. Drops all tables after the test session

---

## Test Files Overview

| File | Tests | Covers |
|---|---|---|
| `tests/test_auth.py` | 3 | Registration, login, duplicate detection, JWT, protected routes, invalid credentials |
| `tests/test_users.py` | ~5 | Profile GET/PATCH, settings, data isolation |
| `tests/test_financial.py` | 3 | CRUD operations, summary calculations, savings rate |
| `tests/test_domain_apis.py` | ~10 | Study, habits, fitness, goals CRUD |
| `tests/test_simulation.py` | 2 | Single simulation, multi-domain × multi-horizon (4×5=20 combinations) |
| `tests/test_ml.py` | ~40 | Academic predict, lifestyle predict, financial predict, forecasting predict, model status, digital twin |
| `tests/test_ai.py` | ~25 | AI chat with/without API key, context building, empty message, malformed input |
| `tests/test_ai_conversation.py` | ~20 | Multi-turn conversation, conversation ownership, cross-user isolation |
| `tests/test_digital_twin.py` | ~5 | Digital Twin state for new/partial/full user |

---

## Test Coverage Areas

### Authentication ✅
- Valid registration and token return
- Duplicate email rejection (HTTP 400)
- Successful login → JWT
- Invalid credentials → HTTP 401
- Protected routes reject missing/invalid tokens → HTTP 401
- Inactive account → HTTP 403
- `/api/auth/me` returns correct user

### Data Domain CRUD ✅
- Financial: income/expense recording, summary (total income, total expenses, net savings, savings_rate)
- Study: session logging, completion rate calculation
- Habits: habit logging with `impact_level` validation
- Fitness: workout logging with `duration_minutes`
- Goals: goal creation and progress tracking

### Simulation Engine ✅
- All 4 decision types (Financial, Forecasting, Academic, Lifestyle)
- All 5 time horizons (7 days → 2 years)
- 5-scenario output (Current Path, Expected Case, Best Case, Worst Case, Risk Scenario)
- Full JSONB persistence and retrieval
- Per-user isolation

### ML Predictions ✅
- Academic model: valid inputs → predicted exam score (float)
- Lifestyle model: valid inputs → one of Normal / Insomnia / Sleep Apnea
- Financial model: valid inputs → predicted disposable income (float)
- Forecasting model: valid inputs → predicted next-month spending (float)
- Model status endpoint: all domains listed with availability
- Prediction caching: second call returns cached result
- Missing model → HTTP 503 (not 500)

### Digital Twin ✅
- Empty user → stable state returned (no NaN, no exceptions)
- Partial user → appropriate domain statuses
- Full user → domains correctly classified as healthy/at-risk/etc.

### AI Intelligence ✅
- Chat without API key → HTTP 503
- Empty message → HTTP 422 (Pydantic validation)
- Valid chat with mocked Gemini → success
- Conversation ownership: User A's conv_id returns 200 for User A, starts new conv for User B
- `insights` list returned alongside prose response

---

## Known Warnings in Test Output

9 warnings exist — all are **Pydantic V1-style `class Config` deprecation warnings**, not failures:

```
PydanticDeprecatedSince20: Support for class-based `config` is deprecated,
use ConfigDict instead.
```

These warnings do not affect test pass rate or functionality. They should be addressed before Pydantic V3.

---

## Test Environment Notes

- Tests use **SQLite** as the test database (not PostgreSQL)
- ML model tests load **actual trained model files** from `backend/app/ml_models/`
- AI tests **mock** the Gemini API to avoid API key dependency and external network calls
- Tests run in **strict asyncio** mode (ASGI test client)
- The `test_digital_twin.db` SQLite file is created and cleaned up automatically

---

## Adding New Tests

New tests should be added to the appropriate file in `tests/`. Always:
1. Use a unique test email (e.g., `"yourtest_xyz@example.com"`) to avoid cross-test contamination since the DB is shared across the session.
2. Register + login to get a token before calling protected endpoints.
3. Clean up any created records in the same test function if needed for isolation.
