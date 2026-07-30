# Implementation Plan - Days 1 to 9: Data Collection & User Profiling (Backend & Stitch-Inspired Frontend)

This plan outlines the complete implementation of **Milestone 1 (Days 1–9)** for the **Digital Twin AI** application. It fulfills all requirements specified in `architecture.py`, `srs.py`, the daily roadmap PDF, and incorporates design guidance from **Stitch MCP** (*Synthetic Intelligence* theme).

---

## User Review Required

> [!IMPORTANT]
> **Stitch MCP Design System Integration**: The Streamlit frontend will use custom CSS styling derived from Stitch's *Synthetic Intelligence* design system:
> - **Color Palette**: Deep Dark Navy background (`#0A0E1A` / `#0F131F`), Slate glassmorphic cards (`#1B1F2C` / `#1E293B` at 60-80% opacity), Vibrant Cyan (`#00F2FF`) and Electric Violet (`#8A2BE2`) glowing accents.
> - **Typography**: Google Fonts **Sora** for headings/labels and **Inter** for dense body and metric numbers.
> - **Interactive Elements**: Glassmorphic cards, neon pips, progress bars, and responsive metric widgets.

> [!NOTE]
> **Database Resilience**: Database configuration (`core/database.py`) will default to PostgreSQL, with an automatic fallback to SQLite for local development and test execution.

---

## Proposed Changes

### Backend Core & Infrastructure (Days 1 - 2)

#### [MODIFY] [config.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/core/config.py)
- Load all environment variables via `pydantic-settings`.

#### [MODIFY] [database.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/core/database.py)
- SQLAlchemy Engine & Session factory with automatic connection retry / SQLite fallback.

#### [NEW] ORM Models in [models/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/models/)
- `models/user.py`: `User` model (PK `user_id`, `name`, `email`, `age`, `occupation`, `password_hash`, `role`, `is_active`, `created_at`).
- `models/financial.py`: `FinancialRecord` model (`record_id`, `user_id`, `income`, `expenses`, `savings`, `transaction_date`, `category`, `description`, `recurring_frequency`).
- `models/study.py`: `StudyActivity` model (`activity_id`, `user_id`, `study_hours`, `subject`, `performance_score`, `activity_date`, `task_completion_rate`).
- `models/goals.py`: `Goal` model (`goal_id`, `user_id`, `goal_name`, `target_value`, `target_date`, `current_progress`, `category`, `status`).
- `models/habits.py`: `HabitTracking` model (`habit_id`, `user_id`, `habit_name`, `status`, `completion_rate`, `record_date`, `impact_level`).
- `models/fitness.py`: `FitnessActivity` model (`fitness_id`, `user_id`, `activity_type`, `duration`, `calories_burned`, `activity_date`).
- `models/simulations.py`: `Simulation` model (`simulation_id`, `user_id`, `decision_type`, `scenario_name`, `simulation_result`, `predicted_outcome`, `generated_at`).
- `models/recommendations.py`: `Recommendation` model (`recommendation_id`, `user_id`, `recommendation_text`, `category`, `priority`, `confidence_score`, `action_plan`, `is_actioned`, `generated_at`).
- `models/analytics.py`: `AnalyticsLog` model (`log_id`, `user_id`, `activity_type`, `endpoint`, `method`, `response_time_ms`, `metadata`, `timestamp`).
- `models/model_registry.py`: `ModelRegistry` model (`model_id`, `model_name`, `algorithm`, `version`, `metrics`, `feature_importances`, `is_active`, `trained_at`).

---

### Authentication & Security (Day 3)

#### [MODIFY] [security.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/core/security.py)
- Password hashing using `bcrypt` and JWT token creation/verification.

#### [MODIFY] [dependencies.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/core/dependencies.py)
- FastAPI `get_current_user` dependency validating JWT tokens from HTTP Authorization Bearer headers.

---

### Pydantic Schemas & Services (Days 3 - 6)

#### [NEW] Schemas in [schemas/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/schemas/)
- `schemas/user.py`, `schemas/financial.py`, `schemas/study.py`, `schemas/habits.py`, `schemas/fitness.py`, `schemas/goals.py`, `schemas/analytics.py`.

#### [NEW] Services in [services/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/services/)
- Business logic for Users, Financial Records, Study Sessions, Habits, Fitness, Goals, and Analytics calculations.

---

### Backend API Routers & Middleware (Days 3 - 7)

#### [NEW] Routers in [routes/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/app/api/routes/)
- `routes/auth.py`: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/auth/me`.
- `routes/users.py`: `GET /api/users/profile`, `PUT /api/users/profile`, `DELETE /api/users/profile`, `GET /api/users/summary`.
- `routes/financial.py`: `POST /api/financial/records`, `GET /api/financial/records`, `GET /api/financial/records/{record_id}`, `PUT /api/financial/records/{record_id}`, `DELETE /api/financial/records/{record_id}`, `GET /api/financial/summary`.
- `routes/study.py`: `POST /api/study/activities`, `GET /api/study/activities`, `GET /api/study/summary`, `PUT /api/study/activities/{activity_id}`, `DELETE /api/study/activities/{activity_id}`.
- `routes/habits.py`: `POST /api/habits`, `GET /api/habits`, `GET /api/habits/analytics`, `PUT /api/habits/{habit_id}`, `DELETE /api/habits/{habit_id}`.
- `routes/fitness.py`: `POST /api/fitness/activities`, `GET /api/fitness/activities`, `GET /api/fitness/summary`, `PUT /api/fitness/activities/{fitness_id}`, `DELETE /api/fitness/activities/{fitness_id}`.
- `routes/goals.py`: `POST /api/goals`, `GET /api/goals`, `PUT /api/goals/{goal_id}/progress`, `GET /api/goals/summary`, `DELETE /api/goals/{goal_id}`.
- `routes/analytics.py`: `GET /api/analytics/activity-log`.

#### [MODIFY] [main.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/backend/main.py)
- Attach analytics logging middleware to measure response times and auto-log requests to `Analytics_Logs`.
- Mount all routers under `/api`.

---

### Streamlit Frontend (Stitch 'Synthetic Intelligence' HUD Theme) (Days 8 - 9)

#### [NEW] [frontend/theme/styles.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/frontend/theme/styles.py)
- Custom CSS injector injecting Google Fonts (Sora, Inter), dark navy backdrop (`#0A0E1A`), glassmorphic containers with cyan glowing borders, styled inputs, and neon pips.

#### [NEW] Components in [frontend/components/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/frontend/components/)
- `sidebar.py`: Navigation sidebar with user avatar, status pips, active goal badges, and logout option.
- `metrics_card.py`: Futuristic KPI metric cards with change indicators and cyan top accent borders.
- `alerts.py`: Styled notification banners for success/error/warning alerts.

#### [NEW] [frontend/utils/api_client.py](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/frontend/utils/api_client.py)
- Centralized HTTP client wrapping `requests` with automatic JWT token injection.

#### [NEW] Entry Point & Pages in [frontend/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/frontend/)
- `frontend/app.py`: Main landing, login, and registration interface.
- `frontend/pages/1_Profile.py`: Interactive user profile view and edit page with goal progress and behavioral stats.
- `frontend/pages/2_Financial.py`, `3_Study.py`, `4_Habits_Fitness.py`, `5_Forecasting.py`, `6_Simulation.py`, `7_Dashboard.py`: Multi-page layout for data entry and analytics visualization.

---

### Documentation & Verification (Days 1 - 9)

#### [NEW] [docs/NOTES.md](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/docs/NOTES.md)
- Architecture notes and API reference documentation.

#### [NEW] Automated Pytest Suite in [tests/](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/tests/)
- Unit tests covering authentication, user profiles, financial CRUD, study sessions, habits, fitness, and goals.

---

## Verification Plan

### Automated Tests
```bash
pytest backend/tests/ -v
```

### Manual Verification
1. Start FastAPI backend with `python -m uvicorn backend.main:app --port 8000`.
2. Access `http://localhost:8000/docs` to verify OpenAPI docs.
3. Run Streamlit frontend with `streamlit run frontend/app.py` and test user registration, login, profile editing, and tab navigation.
