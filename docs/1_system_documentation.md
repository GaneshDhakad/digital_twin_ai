# System Documentation
**Digital Twin AI (TWIN.OS) — Personal Life Simulation & Decision Assistant**
*Version 2.0.0 | September 2026 | Source of truth: live codebase*

---

## 1. Product Overview

Digital Twin AI is a FastAPI + Streamlit web application that builds a continuously-updated **8-state Digital Twin** from a user's financial, academic, habit, fitness, and goal data, then uses machine learning and Gemini AI to forecast outcomes, simulate decisions, and generate personalized recommendations.

---

## 2. Technology Stack (Verified from codebase)

| Layer | Technology | Version |
|---|---|---|
| Backend API | FastAPI | 0.111.0 |
| ASGI Server | Uvicorn | 0.30.0 |
| Frontend UI | Streamlit | 1.36.0 |
| ORM | SQLAlchemy | 2.0.51 |
| Primary Database | PostgreSQL 15 (prod) / SQLite (dev fallback) | — |
| Data Validation | Pydantic | 2.7.0 |
| Auth | JWT via `python-jose` + bcrypt passlib | — |
| ML Framework | scikit-learn, XGBoost, Prophet, Statsmodels | — |
| AI LLM | Google Gemini (`google-genai >= 1.0.0`) | — |
| Cache | In-memory `PredictionCache` (SQLite/PG table) | — |
| Migrations | Alembic | 1.16.2 |

> **Note:** Redis, Celery, and `fastapi-cache2` are listed in `requirements.txt` but are **not yet integrated** into the running backend. Caching is currently handled via the `prediction_cache` database table.

---

## 3. Functional Modules (IMPLEMENTED & VERIFIED)

### 3.1 Authentication & User Management
- `POST /api/auth/register` — register with name, email, password, age, occupation
- `POST /api/auth/login` — OAuth2 form login → JWT token (24h expiry)
- `GET /api/auth/me` — get current user from token
- JWT encoded with email as `sub` claim
- Passwords hashed with bcrypt
- RBAC: `role IN ('user', 'admin')` enforced via `require_admin` dependency

### 3.2 Financial Domain
- `POST /api/financial/records` — log income or expense transaction
- `GET /api/financial/records` — paginated list with filtering
- `DELETE /api/financial/records/{id}` — delete own record
- `GET /api/financial/summary` — aggregate income, expenses, net savings, savings rate, category breakdown

### 3.3 Study (Academic) Domain
- `POST /api/study/activities` — log a study session
- `GET /api/study/activities` — list sessions
- `GET /api/study/summary` — avg focus, completion rate, peak hours, subject breakdown

### 3.4 Habit Tracking Domain
- `POST /api/habits` — log a habit entry
- `GET /api/habits` — list habits
- `GET /api/habits/analytics` — analytics including completion rate, streak, at-risk habits

### 3.5 Fitness Domain
- `POST /api/fitness/activities` — log workout
- `GET /api/fitness/activities` — list activities
- `GET /api/fitness/summary` — weekly count, total duration, calories, activity breakdown

### 3.6 Goals Domain
- `POST /api/goals` — create a goal with name, target, date
- `GET /api/goals` — list goals
- `GET /api/goals/summary` — total, completed, at-risk counts

### 3.7 Machine Learning Predictions
- `POST /api/ml/academic/predict` — predict exam score (GradientBoostingRegressor, R²=0.876)
- `POST /api/ml/lifestyle/predict` — classify sleep disorder risk (GradientBoostingClassifier, F1=0.977)
- `POST /api/ml/financial/predict` — predict disposable income (RandomForestRegressor)
- `POST /api/ml/forecasting/predict` — predict next-month spending (XGBRegressor, RMSE=1207)
- `GET /api/ml/models` — model availability status
- `GET /api/ml/digital-twin` — full Digital Twin state

### 3.8 Digital Twin Engine
- Aggregates live data from all 5 domain services
- Appends latest cached ML predictions
- Returns a `DigitalTwinState` with per-domain status: `healthy | stable | at-risk | declining | critical`

### 3.9 Decision Simulator
- `POST /api/simulations` — run 5-way scenario simulation
- `GET /api/simulations` — list user's simulations
- `GET /api/simulations/{id}` — get single simulation
- `DELETE /api/simulations/{id}` — delete simulation
- Supported decision types: `Financial`, `Forecasting`, `Academic`, `Lifestyle`, and generic types
- Produces: Current Path, Expected Case, Best Case, Worst Case, Risk Scenario
- Horizons: `7_days`, `1_month`, `3_months`, `1_year`, `2_years`

### 3.10 AI Intelligence (Gemini)
- `POST /api/ai/chat` — multi-turn conversation with Digital Twin context
- Uses `google-genai >= 1.0.0` SDK (not the deprecated `google-generativeai`)
- Full conversation memory stored in-memory per session
- context_builder enriches prompt with Digital Twin state
- response_parser extracts structured `AIInsight` objects from responses
- Graceful degradation: returns HTTP 503 if `GEMINI_API_KEY` not configured

### 3.11 Recommendations
- `GET /api/recommendations` — list recommendations for the authenticated user

### 3.12 Analytics
- `GET /api/analytics/logs` — user activity log

---

## 4. Non-Functional Requirements (Status)

| Requirement | Target | Status |
|---|---|---|
| API P95 response | < 300ms | ✅ Designed for (no load test run) |
| Simulation response | < 5 seconds | ✅ Verified in test suite |
| Test coverage | ≥ 90% | ⚠️ Tests run but coverage not yet measured |
| Security: bcrypt | ✅ | ✅ Implemented |
| Security: JWT | ✅ | ✅ Implemented |
| Security: RBAC | ✅ | ✅ Implemented |
| Usability SUS ≥ 85 | Target | 🔲 Not yet tested |
| Docker deployable | `docker compose up` | ⚠️ Docker config exists in `docker/` but not validated in this analysis |

---

## 5. Known Deprecation Warnings

The following Pydantic V1-style `class Config` patterns were found in 9 schema files and should be migrated to `model_config = ConfigDict(...)` before Pydantic V3 is released:

- `backend/app/schemas/user.py`
- `backend/app/schemas/financial.py`
- `backend/app/schemas/study.py`
- `backend/app/schemas/habits.py`
- `backend/app/schemas/fitness.py`
- `backend/app/schemas/goals.py`
- `backend/app/schemas/analytics.py`
- `backend/app/schemas/simulation.py`
- `backend/app/schemas/digital_twin.py`

Severity: **Low** — functional today, deprecated for Pydantic V3.

---

## 6. Out of Scope / Not Implemented

- Redis caching (listed in requirements, not integrated)
- Celery worker (listed, not integrated)
- Native mobile apps
- Bank feed / brokerage import (Plaid-style)
- Email/SMS delivery of summaries
- Multi-language (i18n) support
- Fitness ML prediction (model exists but deliberately excluded from API)
