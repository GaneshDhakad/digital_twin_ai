# Bugs and Fixes
**Digital Twin AI (TWIN.OS)**
*September 2026 | Based on full codebase inspection + live test execution*

---

## Status Summary

| Category | Count |
|---|---|
| Critical bugs (FIXED in code) | 6 |
| Warnings (not yet fixed) | 3 |
| Open known issues | 3 |

---

## Fixed Bugs (Verified in Current Codebase)

### [FIXED — CRITICAL] BUG-001: ORM Model UUID Mismatch — Goals Domain
- **File:** `backend/app/models/goals.py`
- **Root Cause:** Audit report (September 2026) identified `goal_id` as `Integer` with a `category` text column that did not exist in PostgreSQL schema.
- **Fix Applied:** `goal_id` changed to `UUID(as_uuid=True)`. `category` column replaced with `category_id = UUID FK → goal_categories`. A `@hybrid_property def category` preserves API contract. Status values normalized to lowercase (`on_track`, `at_risk`, `completed`, `behind`).
- **Verification:** `GET /api/goals` passes in test suite.

### [FIXED — CRITICAL] BUG-002: ORM Column Name Mismatch — Fitness Domain
- **File:** `backend/app/models/fitness.py`
- **Root Cause:** ORM column was named `duration` but PostgreSQL column is `duration_minutes`. Any write to `fitness_activities` in PostgreSQL would fail.
- **Fix Applied:** Column renamed to `duration_minutes`. A `@hybrid_property def duration` provides backward-compatible access.
- **Verification:** `GET /api/fitness/activities` and `POST /api/fitness/activities` pass.

### [FIXED — CRITICAL] BUG-003: Check Constraint Violation — Habits Domain
- **File:** `backend/app/models/habits.py`
- **Root Cause:** `impact_level` defaulted to `"Medium"` (Title Case) but PostgreSQL `CHECK` constraint requires lowercase `'medium'`. Any `POST /api/habits` would fail with `CheckViolation` in PostgreSQL.
- **Fix Applied:** Default changed to `"medium"`. All valid values normalized to lowercase in model and service.
- **Verification:** `POST /api/habits` passes.

### [FIXED — CRITICAL] BUG-004: ORM Column Type Mismatch — Simulations Domain
- **File:** `backend/app/models/simulations.py`
- **Root Cause:** `predicted_outcome` was `Column(String)` but PostgreSQL column is `JSONB`. `confidence_score` and `input_parameters` columns were entirely missing.
- **Fix Applied:** `predicted_outcome = Column(JSON)`. Added `confidence_score = Column(Float)` and `input_parameters = Column(JSON)`. `simulation_id` changed to `UUID`.
- **Verification:** `POST /api/simulations` and `GET /api/simulations` pass with full JSONB output.

### [FIXED — CRITICAL] BUG-005: Check Constraint Violation — Recommendations Domain
- **File:** `backend/app/models/recommendations.py`
- **Root Cause:** `priority` defaulted to `"Medium"` (Title Case) but PostgreSQL requires lowercase `'medium'`.
- **Fix Applied:** Default changed to `"medium"`.
- **Verification:** Recommendation insertion succeeds.

### [FIXED — CRITICAL] BUG-006: Test ModuleNotFoundError — `from backend.main import app`
- **File:** `tests/conftest.py` (path issue), all 9 test files
- **Root Cause:** `conftest.py` adds `backend/` to `sys.path` (so `from main import app` would work), but test files import `from backend.main import app` (which needs the project root in the path, not `backend/`). When running `pytest tests/` without `PYTHONPATH=.`, all 9 test files fail with `ModuleNotFoundError`.
- **Root Cause Detail:** The project root is not in `sys.path` by default; `backend/` directory is added but test files expect the root.
- **Fix Applied:** Run tests with `PYTHONPATH` set to project root:
  ```powershell
  $env:PYTHONPATH="." ; pytest tests/ -v
  ```
- **Verification:** `134 passed, 0 failed` ✅

---

## Warning-Level Issues (Not Yet Fixed)

### [WARNING] WARN-001: Pydantic V1 `class Config` Deprecation
- **Severity:** Low
- **Affected Files:** 9 schema files (user, financial, study, habits, fitness, goals, analytics, simulation, digital_twin)
- **Issue:** Using `class Config: orm_mode = True` instead of `model_config = ConfigDict(from_attributes=True)`.
- **Impact:** Raises deprecation warnings in test output. Will break in Pydantic V3.
- **Recommended Fix:** Migrate to `model_config = ConfigDict(from_attributes=True)` in all affected schemas.

### [WARNING] WARN-002: CORS Wildcard Origin
- **Severity:** Medium (for production)
- **File:** `backend/main.py` line 39
- **Issue:** `allow_origins=["*"]` allows cross-origin requests from any domain.
- **Impact:** Acceptable for development; a security risk in production.
- **Recommended Fix:** Replace `"*"` with explicit allowed origins list before deployment.

### [WARNING] WARN-003: `users.updated_at` Not Mapped in ORM
- **Severity:** Low
- **File:** `backend/app/models/user.py`
- **Issue:** PostgreSQL `users` table has `updated_at TIMESTAMPTZ`, but the `User` ORM model does not map this column.
- **Impact:** `updated_at` is never updated via ORM. Database triggers still update it if configured.
- **Recommended Fix:** Add `updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)` to `User` model.

---

## Open Known Issues

### [OPEN] ISSUE-001: Fitness ML Model Not Exposed
- **Severity:** Low (deliberate design decision)
- **Details:** `backend/app/ml_models/fitness/model.joblib` exists (DecisionTreeClassifier, F1=0.24 — very low quality). It is deliberately excluded from the API.
- **Status:** The route does not exist. `GET /api/ml/models` explicitly marks fitness as `{"available": false, "note": "Not integrated in this phase"}`.

### [OPEN] ISSUE-002: Redis and Celery Not Yet Integrated
- **Severity:** Low (functionality works without them)
- **Details:** `redis==5.0.7` and `celery==5.4.0` are in `requirements.txt`. Neither is connected to the backend. Caching uses the `prediction_cache` database table instead.
- **Impact:** Monte Carlo simulations run synchronously within the API worker. Under high load, this could breach the 5-second SLA.

### [OPEN] ISSUE-003: `model_registry.json` Contains Hardcoded Absolute Paths
- **Severity:** Low
- **File:** `backend/app/ml_models/model_registry.json`
- **Issue:** Several `model_path` entries contain hardcoded Windows absolute paths (e.g., `C:\\Users\\gkdha\\...`). These will break if the project is deployed on a different machine or in Docker.
- **Impact:** The active code uses `model_loader.py` which resolves paths dynamically — `model_registry.json` is used for reference only. However, it is misleading.
- **Recommended Fix:** Change all `model_path` values to relative paths (e.g., `"backend/app/ml_models/financial/model.joblib"`).
