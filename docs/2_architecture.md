# Architecture Reference (SAD)
**Digital Twin AI (TWIN.OS) — System Architecture Document**
*Version 2.0.0 | September 2026 | Source of truth: live codebase inspection*

---

## 1. Architectural Style

**Layered N-Tier architecture** with a service-oriented internal structure and a strict **Repository-Service** pattern. The system is deployed as a single FastAPI application rather than microservices, because all 5 life domains share the same PostgreSQL schema and a single Digital Twin state object.

```
Presentation (Streamlit)
    ↓ HTTP/JSON
API (FastAPI Routers + Pydantic Validation)
    ↓
Service Layer (domain logic, orchestration)
    ↓
Repository / ORM (SQLAlchemy 2.0 models)
    ↓
Database (PostgreSQL 15 in production, SQLite fallback in dev/test)
```

ML and AI layers are called from the Service layer, not from routers.

---

## 2. Project Directory Map

```
digital_twin_ai/
├── backend/
│   ├── main.py                        # FastAPI app, CORS, middleware, router registration
│   └── app/
│       ├── api/routes/                # 12 FastAPI routers
│       │   ├── auth.py                # POST /register, POST /login, GET /me
│       │   ├── users.py               # GET /profile, PATCH /profile
│       │   ├── financial.py           # CRUD + summary
│       │   ├── study.py               # CRUD + summary
│       │   ├── habits.py              # CRUD + analytics
│       │   ├── fitness.py             # CRUD + summary
│       │   ├── goals.py               # CRUD + summary
│       │   ├── simulation.py          # CRUD + run
│       │   ├── ml.py                  # predict endpoints + digital-twin GET
│       │   ├── ai.py                  # POST /chat (Gemini)
│       │   ├── analytics.py           # GET /logs
│       │   └── recommendations.py    # GET /recommendations
│       ├── core/
│       │   ├── config.py              # pydantic-settings (env vars)
│       │   ├── database.py            # Engine + SQLite fallback logic
│       │   ├── security.py            # JWT encode/decode, bcrypt
│       │   └── dependencies.py        # get_db, get_current_user, require_admin
│       ├── models/                    # 22 SQLAlchemy ORM models
│       ├── schemas/                   # 13 Pydantic schema modules
│       ├── services/                  # Domain service modules
│       │   ├── financial_service.py
│       │   ├── study_service.py
│       │   ├── habit_service.py
│       │   ├── fitness_service.py
│       │   ├── goal_service.py
│       │   ├── simulation_service.py
│       │   ├── user_service.py
│       │   ├── analytics_service.py
│       │   ├── digital_twin_service.py
│       │   ├── ml/                    # ML prediction services (per domain)
│       │   │   ├── model_loader.py
│       │   │   ├── academic_service.py
│       │   │   ├── financial_service.py
│       │   │   ├── forecasting_service.py
│       │   │   └── lifestyle_service.py
│       │   └── ai/                    # AI / Gemini integration
│       │       ├── assistant_service.py
│       │       ├── context_builder.py
│       │       ├── conversation_memory.py
│       │       ├── input_validator.py
│       │       └── response_parser.py
│       └── ml_models/                 # Trained model artifacts (deployed)
│           ├── academic/              # model.joblib, metadata.json, feature_info.json
│           ├── lifestyle/             # model.joblib, metadata.json, feature_info.json
│           ├── financial/             # model.joblib, metadata.json, feature_info.json
│           ├── forecasting/           # model.joblib, metadata.json, feature_info.json
│           ├── fitness/               # model.joblib (deliberately NOT exposed via API)
│           └── model_registry.json    # JSON registry of all deployed models
├── frontend/
│   ├── app.py                         # Streamlit entry point, navigation routing
│   └── views/
│       ├── login.py                   # Auth, register
│       ├── dashboard.py               # KPI overview
│       ├── profile.py                 # User profile
│       ├── financial.py               # Financial CRUD + charts
│       ├── study.py                   # Study CRUD + analytics
│       ├── habits.py                  # Habits + fitness CRUD
│       ├── forecasting.py             # ML prediction forms
│       ├── ai_intelligence.py         # Gemini chat UI
│       └── simulation.py             # Decision simulator UI
├── ml/
│   ├── reports/                       # Training reports, CSV metrics, ORM audit
│   └── training/                      # Training scripts
├── tests/                             # 12 pytest modules, 134 tests
├── docs/                              # This documentation
└── requirements.txt                   # All dependencies
```

---

## 3. Database Design (22 ORM Models, PostgreSQL 15)

PostgreSQL primary keys are **UUID** (`gen_random_uuid()`). All tables have `CASCADE` delete from `users`.

### Core User Tables
| Table | ORM Class | Notes |
|---|---|---|
| `users` | `User` | Hub table; all others FK → `user_id` |
| `user_settings` | `UserSetting` | One-to-one with User |
| `user_sessions` | `UserSession` | Session tracking |
| `audit_logs` | `AuditLog` | Action auditing |

### Domain Data Tables
| Table | ORM Class | Key Fields |
|---|---|---|
| `financial_records` | `FinancialRecord` | income, expenses, savings, category, type |
| `study_activities` | `StudyActivity` | study_hours, performance_score, task_completion_rate |
| `habit_tracking` | `HabitTracking` | status, completion_rate, streak_count, impact_level |
| `fitness_activities` | `FitnessActivity` | duration_minutes (`@hybrid_property duration`), calories_burned, intensity_level |
| `goals` | `Goal` | category_id FK → goal_categories, target_value, status |

### Intelligence Tables
| Table | ORM Class | Key Fields |
|---|---|---|
| `simulations` | `Simulation` | decision_type, simulation_result (JSONB), predicted_outcome (JSONB), confidence_score |
| `recommendations` | `Recommendation` | priority (lowercase: low/medium/high/critical), confidence_score, action_plan (JSONB) |
| `prediction_cache` | `PredictionCache` | cache_key SHA256, model_name, expires_at |
| `analytics_logs` | `AnalyticsLog` | activity_type, endpoint, method, response_time_ms |
| `ai_conversations` | `AIConversation` | conversation history |
| `notifications` | `Notification` | type, is_read |
| `feedback` | `Feedback` | rating, feedback_type, status |
| `model_registry` | `ModelRegistry` | algorithm, metrics, is_active |

### Reference Tables (Lookup / Enum Values)
| Table | ORM Class |
|---|---|
| `expense_categories` | `ExpenseCategory` |
| `subjects` | `Subject` |
| `habit_types` | `HabitType` |
| `goal_categories` | `GoalCategory` |
| `simulation_templates` | `SimulationTemplate` |

---

## 4. Authentication Flow

```
POST /api/auth/register
    → Pydantic validation
    → check duplicate email
    → bcrypt hash password
    → INSERT user
    → create_access_token(sub=email)
    → return Token

POST /api/auth/login
    → OAuth2PasswordRequestForm (username=email)
    → get_user_by_email
    → verify_password (bcrypt)
    → create_access_token(sub=email)
    → return Token

Protected routes → get_current_user (Depends)
    → extract Bearer token
    → decode JWT → get email (sub)
    → query User by email
    → check is_active
    → return User object
```

---

## 5. ML Architecture

### Model Loading
All models live in `backend/app/ml_models/<domain>/` with 3 files:
- `model.joblib` — trained sklearn pipeline
- `metadata.json` — model name, version, metrics, training date
- `feature_info.json` — feature names, types, preprocessing spec

`model_loader.py` caches all models in-memory after first load (process-level).

### Digital Twin Integration
When `GET /api/ml/digital-twin` is called:
1. `get_digital_twin_state(db, user_id)` is called
2. Each domain service (financial, study, habit, fitness, goals) is queried
3. `get_current_predictions()` reads the latest unexpired `PredictionCache` entries
4. Returns `DigitalTwinState` with per-domain status + ML prediction snapshots

---

## 6. AI (Gemini) Integration

```
POST /api/ai/chat
    → authenticate user
    → validate/create conversation_id (in-memory ConversationStore)
    → get_digital_twin_state(db, user_id)   ← real user data
    → build_ai_context(twin_state)           ← structured context string
    → get_ai_response(message, context, history)  ← calls Gemini API
    → parse_insights_from_response()         ← extracts AIInsight objects
    → store turns in conversation memory
    → return AIChatResponse
```

Model: `gemini-3.6-flash` (configurable via `GEMINI_MODEL` env var)
SDK: `google-genai >= 1.0.0` (NOT the deprecated `google-generativeai`)

Error codes:
- `503` — `GEMINI_API_KEY` not configured
- `502` — Provider returned empty/malformed response
- `503` — Provider unavailable (rate limit, auth, etc.)

---

## 7. Decision Simulator

Supported decision types:
- `Financial` — savings delta and expense impact projections
- `Forecasting` — next-month spending shift simulation (uses ML forecast as baseline)
- `Academic` / `Study` — exam score projection based on study hours delta
- `Lifestyle` / `Habits` / `Fitness` — vitality index simulation
- Any other string → generic simulation engine

Each simulation returns **5 scenarios**: Current Path, Expected Case, Best Case, Worst Case, Risk Scenario across **5 time horizons**: 7 days, 1 month, 3 months, 1 year, 2 years.

Results are persisted to `simulations` table with full JSONB output.

---

## 8. Security Model

| Control | Implementation |
|---|---|
| Password storage | bcrypt via passlib |
| Auth tokens | JWT HS256, 24h expiry, `sub=email` |
| Data isolation | All queries filter by `user_id` from JWT (never from request body) |
| Admin RBAC | `require_admin` dependency checks `user.role == 'admin'` |
| SQL injection | Parameterized SQLAlchemy queries only |
| AI context | User ID from JWT, not from chat message body |
| Logging | Message content NOT logged in full; token never logged |
| CORS | Currently `allow_origins=["*"]` — should be restricted in production |

> **Security Note:** `CORS allow_origins=["*"]` is set in `main.py`. This should be replaced with an explicit allowlist before any production deployment.

---

## 9. Deployment

**Development (SQLite)**
```bash
# Backend
$env:DATABASE_URL="sqlite:///./digital_twin.db"
uvicorn backend.main:app --reload

# Frontend
streamlit run frontend/app.py
```

**Production (PostgreSQL)**
```bash
# Set in .env
DATABASE_URL=postgresql://user:pass@host:5432/digital_twin_ai
GEMINI_API_KEY=<key>
SECRET_KEY=<strong-secret>
```

Docker Compose config exists in `docker/` but was **not validated** during this analysis.
