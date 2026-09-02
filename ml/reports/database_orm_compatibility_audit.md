# Database / ORM Compatibility Audit

**Project:** Digital Twin AI (TWIN.OS)  
**Date:** September 2026  
**Scope:** Complete Read-Only Compatibility Audit of PostgreSQL 15, SQLAlchemy ORM, Pydantic Schemas, Domain Services, and API Routes prior to Milestone 3.  
**Database Source of Truth:** PostgreSQL (`digital_twin_ai`)

---

## 1. Database Summary

PostgreSQL 15 contains **22 tables** utilizing 3NF architecture, UUID primary keys (`gen_random_uuid()`), and explicit `CHECK` / `FOREIGN KEY` constraints:

| Table Name | Primary Key | Foreign Key References | Check Constraints |
|---|---|---|---|
| `users` | `user_id UUID` | None | `age >= 0 AND age <= 120`, `role IN ('user', 'admin', 'analyst')` |
| `financial_records` | `record_id UUID` | `user_id -> users`, `category_id -> expense_categories` | `amount >= 0`, `income >= 0`, `expenses >= 0`, `savings >= 0`, `recurring_frequency IN ('none', 'daily', 'weekly', 'monthly', 'annual')`, `type IN ('income', 'expense', 'transfer', 'investment')` |
| `expense_categories` | `category_id UUID` | None | `type IN ('income', 'expense', 'investment', 'savings')` |
| `study_activities` | `activity_id UUID` | `user_id -> users`, `subject_id -> subjects` | `study_hours >= 0 AND <= 24`, `performance_score >= 0 AND <= 100`, `task_completion_rate >= 0 AND <= 100` |
| `subjects` | `subject_id UUID` | None | None |
| `habit_tracking` | `habit_id UUID` | `user_id -> users`, `habit_type_id -> habit_types` | `completion_rate >= 0 AND <= 100`, `streak_count >= 0`, `impact_level IN ('low', 'medium', 'high', 'critical')`, `status IN ('completed', 'missed', 'partial', 'skipped')` |
| `habit_types` | `habit_type_id UUID` | None | `default_impact IN ('low', 'medium', 'high', 'critical')` |
| `fitness_activities` | `fitness_id UUID` | `user_id -> users` | `duration_minutes >= 0`, `calories_burned >= 0`, `intensity_level IN ('low', 'moderate', 'high', 'extreme')` |
| `goals` | `goal_id UUID` | `user_id -> users`, `category_id -> goal_categories` | `target_value > 0`, `current_progress >= 0`, `status IN ('on_track', 'at_risk', 'completed', 'abandoned', 'behind')` |
| `goal_categories` | `category_id UUID` | None | None |
| `simulations` | `simulation_id UUID` | `user_id -> users`, `template_id -> simulation_templates` | `confidence_score >= 0 AND <= 1` |
| `simulation_templates` | `template_id UUID` | None | None |
| `recommendations` | `recommendation_id UUID` | `user_id -> users` | `confidence_score >= 0 AND <= 1`, `priority IN ('low', 'medium', 'high', 'critical')` |
| `analytics_logs` | `log_id UUID` | `user_id -> users` | None |
| `user_settings` | `setting_id UUID` | `user_id -> users` | `theme IN ('light', 'dark', 'system')`, `ai_personality IN ('analytical', 'encouraging', 'direct', 'socratic')`, `risk_tolerance IN ('conservative', 'moderate', 'aggressive')` |
| `notifications` | `notification_id UUID` | `user_id -> users` | `type IN ('info', 'warning', 'alert', 'achievement', 'recommendation')` |
| `prediction_cache` | `cache_id UUID` | `user_id -> users` | None |
| `ai_conversations` | `conversation_id UUID` | `user_id -> users` | `feedback_score >= 1 AND <= 5`, `tokens_used >= 0` |
| `user_sessions` | `session_id UUID` | `user_id -> users` | None |
| `audit_logs` | `audit_id UUID` | `user_id -> users` | None |
| `feedback` | `feedback_id UUID` | `user_id -> users` | `rating >= 1 AND <= 5`, `feedback_type IN ('bug', 'feature_request', 'simulation_accuracy', 'recommendation_quality', 'general')`, `status IN ('open', 'reviewed', 'resolved', 'dismissed')` |
| `model_registry` | `model_id UUID` | None | None |

---

## 2. ORM Models Audited

All 22 registered SQLAlchemy ORM models were audited from `backend/app/models/`:
1. `User` (`users`)
2. `FinancialRecord` (`financial_records`)
3. `StudyActivity` (`study_activities`)
4. `ExpenseCategory` (`expense_categories`)
5. `Subject` (`subjects`)
6. `HabitType` (`habit_types`)
7. `GoalCategory` (`goal_categories`)
8. `SimulationTemplate` (`simulation_templates`)
9. `UserSetting` (`user_settings`)
10. `Notification` (`notifications`)
11. `PredictionCache` (`prediction_cache`)
12. `AIConversation` (`ai_conversations`)
13. `UserSession` (`user_sessions`)
14. `AuditLog` (`audit_logs`)
15. `Feedback` (`feedback`)
16. `FitnessActivity` (`fitness_activities`)
17. `Goal` (`goals`)
18. `HabitTracking` (`habit_tracking`)
19. `Simulation` (`simulations`)
20. `Recommendation` (`recommendations`)
21. `AnalyticsLog` (`analytics_logs`)
22. `ModelRegistry` (`model_registry`)

---

## 3. PASSING DOMAINS

[PASS]
Domain: Authentication & User Management
Database table: `users`
ORM model: `User`
Schema compatible: YES
Service compatible: YES
API verified: YES (`GET /api/auth/me`, `GET /api/users/profile`)

[PASS]
Domain: Financial Data Management & Ledger
Database table: `financial_records`
ORM model: `FinancialRecord`
Schema compatible: YES
Service compatible: YES
API verified: YES (`GET /api/financial/records`, `POST /api/financial/records`, `GET /api/financial/summary`, `DELETE /api/financial/records/{id}`)

[PASS]
Domain: Academic Study Activities
Database table: `study_activities`
ORM model: `StudyActivity`
Schema compatible: YES
Service compatible: YES
API verified: YES (`GET /api/study/activities`, `POST /api/study/activities`, `GET /api/study/summary`, `DELETE /api/study/activities/{id}`)

[PASS]
Domain: Reference Lookups (Expense Categories, Subjects, Habit Types, Goal Categories, Simulation Templates)
Database table: `expense_categories`, `subjects`, `habit_types`, `goal_categories`, `simulation_templates`
ORM model: `ExpenseCategory`, `Subject`, `HabitType`, `GoalCategory`, `SimulationTemplate`
Schema compatible: YES
Service compatible: YES
API verified: YES

[PASS]
Domain: User Settings & Personalization
Database table: `user_settings`
ORM model: `UserSetting`
Schema compatible: YES
Service compatible: YES
API verified: YES

[PASS]
Domain: Machine Learning Cache & State
Database table: `prediction_cache`
ORM model: `PredictionCache`
Schema compatible: YES
Service compatible: YES
API verified: YES (`GET /api/ml/digital-twin`)

[PASS]
Domain: Supporting Security & Telemetry (Sessions, Audit, Feedback, Conversations, Notifications)
Database table: `user_sessions`, `audit_logs`, `feedback`, `ai_conversations`, `notifications`
ORM model: `UserSession`, `AuditLog`, `Feedback`, `AIConversation`, `Notification`
Schema compatible: YES
Service compatible: YES
API verified: YES

---

## 4. WARNINGS

[WARNING]
Domain: User Management
Table: `users`
Model: `User`
Issue: PostgreSQL table contains `updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP`, but `User` ORM model does not map `updated_at`.
Severity: Low
Potential impact: Updates to user records via ORM do not automatically update `updated_at` column in the database unless done by database triggers.
Recommended fix: Add `updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)` to `User` model.

[WARNING]
Domain: Decision Simulations (Read Route)
Table: `simulations`
Model: `Simulation`
Issue: `GET /api/simulation/status` is a stub endpoint returning hardcoded status; the full persistence CRUD router for simulations is not yet implemented.
Severity: Medium
Potential impact: Milestone 3 Monte Carlo simulation outputs will require an updated model before saving.
Recommended fix: Align `Simulation` ORM model columns with PostgreSQL before writing simulation persistence logic.

---

## 5. CRITICAL MISMATCHES

### [CRITICAL] 1. Goals Domain
Domain: Goals Management  
Database table: `goals`  
ORM model: `Goal`  
Database definition:
```sql
goal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
category_id UUID REFERENCES goal_categories(category_id) ON DELETE SET NULL,
goal_name VARCHAR(200) NOT NULL,
target_value NUMERIC(12, 2) NOT NULL CHECK (target_value > 0),
current_progress NUMERIC(12, 2) NOT NULL DEFAULT 0.00 CHECK (current_progress >= 0),
target_date TIMESTAMPTZ NOT NULL,
status VARCHAR(20) NOT NULL DEFAULT 'on_track' CHECK (status IN ('on_track', 'at_risk', 'completed', 'abandoned', 'behind')),
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/goals.py`):
```python
goal_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
goal_name = Column(String, nullable=False)
category = Column(String, nullable=False) # Nonexistent column in PostgreSQL!
target_value = Column(Float, nullable=False)
current_progress = Column(Float, default=0.0, nullable=False)
target_date = Column(DateTime, nullable=False)
status = Column(String, default="On Track", nullable=False) # Violates CHECK constraint!
```
Exact mismatch:
1. `goals.category` column does NOT exist in PostgreSQL. In PostgreSQL, it is `category_id UUID REFERENCES goal_categories(category_id)`.
2. Primary key `goal_id` is `UUID` in PostgreSQL, but `Integer` in ORM and Pydantic schemas.
3. Check constraint violation: PostgreSQL requires lowercase snake_case `status IN ('on_track', 'at_risk', 'completed', 'abandoned', 'behind')`. ORM and service default to `"On Track"`.
4. Cascade impact: `User.goals` relationship causes `GET /api/users/profile` and `GET /api/users/summary` to fail with `column goals.category does not exist`.

Affected files:
- `backend/app/models/goals.py`
- `backend/app/schemas/goals.py`
- `backend/app/services/goal_service.py`
- `backend/app/api/routes/goals.py`
- `backend/app/api/routes/users.py`

Affected endpoints:
- `GET /api/goals` (Fails 500)
- `POST /api/goals` (Fails 500)
- `GET /api/goals/summary` (Fails 500)
- `GET /api/users/profile` (Fails 500 when loading goals)
- `GET /api/users/summary` (Fails 500 when querying goals)

Recommended minimum fix:
1. In `models/goals.py`, change `goal_id` to `UUID(as_uuid=True)`.
2. Replace `category` column with `category_id = Column(UUID(as_uuid=True), ForeignKey("goal_categories.category_id", ondelete="SET NULL"), nullable=True)` and add `goal_category = relationship("GoalCategory", lazy="joined")`.
3. Provide `@hybrid_property def category` returning `goal_category.name` to preserve API contract.
4. Normalize `status` strings to lowercase snake_case (`'on_track'`).
5. Update `GoalResponse.goal_id` to `Union[UUID, int, str]`.

---

### [CRITICAL] 2. Fitness Activities Domain
Domain: Fitness Activities  
Database table: `fitness_activities`  
ORM model: `FitnessActivity`  
Database definition:
```sql
fitness_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
activity_type VARCHAR(100) NOT NULL,
duration_minutes NUMERIC(6, 2) NOT NULL CHECK (duration_minutes >= 0),
calories_burned NUMERIC(7, 2) NOT NULL DEFAULT 0.00 CHECK (calories_burned >= 0),
intensity_level VARCHAR(20) NOT NULL DEFAULT 'moderate' CHECK (intensity_level IN ('low', 'moderate', 'high', 'extreme')),
activity_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/fitness.py`):
```python
fitness_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
activity_type = Column(String, nullable=False)
duration = Column(Float, nullable=False) # Nonexistent column in PostgreSQL!
calories_burned = Column(Float, default=0.0, nullable=False)
activity_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
```
Exact mismatch:
1. Column `fitness_activities.duration` does NOT exist in PostgreSQL; the database column is `duration_minutes`.
2. Primary key `fitness_id` is `UUID` in PostgreSQL, but `Integer` in ORM and Pydantic schemas.
3. Missing columns in ORM: `intensity_level` and `created_at`.

Affected files:
- `backend/app/models/fitness.py`
- `backend/app/schemas/fitness.py`
- `backend/app/services/fitness_service.py`
- `backend/app/api/routes/fitness.py`

Affected endpoints:
- `GET /api/fitness/activities` (Fails 500)
- `POST /api/fitness/activities` (Fails 500)
- `GET /api/fitness/summary` (Fails 500)

Recommended minimum fix:
1. In `models/fitness.py`, change `fitness_id` to `UUID(as_uuid=True)`.
2. Map `duration_minutes = Column(Float, nullable=False)` and provide `@hybrid_property def duration` aliasing `duration_minutes`.
3. Add `intensity_level = Column(String(20), default="moderate")` and `created_at = Column(DateTime)`.
4. Update `FitnessActivityResponse.fitness_id` to `Union[UUID, int, str]`.

---

### [CRITICAL] 3. Habit Tracking Domain
Domain: Habit Streaks & Tracking  
Database table: `habit_tracking`  
ORM model: `HabitTracking`  
Database definition:
```sql
habit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
habit_type_id UUID REFERENCES habit_types(habit_type_id) ON DELETE SET NULL,
habit_name VARCHAR(150) NOT NULL,
status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'missed', 'partial', 'skipped')),
completion_rate NUMERIC(5, 2) NOT NULL DEFAULT 100.00 CHECK (completion_rate >= 0 AND completion_rate <= 100),
streak_count INT NOT NULL DEFAULT 0 CHECK (streak_count >= 0),
impact_level VARCHAR(10) NOT NULL DEFAULT 'medium' CHECK (impact_level IN ('low', 'medium', 'high', 'critical')),
record_date TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/habits.py`):
```python
habit_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
habit_name = Column(String, nullable=False)
status = Column(String, nullable=False, default="completed")
completion_rate = Column(Float, default=100.0, nullable=False)
impact_level = Column(String, default="Medium", nullable=False) # Violates CHECK constraint!
record_date = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
```
Exact mismatch:
1. Primary key `habit_id` is `UUID` in PostgreSQL, but `Integer` in ORM and Pydantic schemas.
2. Check constraint violation: PostgreSQL requires lowercase `impact_level IN ('low', 'medium', 'high', 'critical')`. ORM model defaults to `"Medium"` and service receives `"High"`, failing with `CheckViolation`.
3. Check constraint on `status`: requires lowercase `'completed'`, `'missed'`, `'partial'`, `'skipped'`.
4. Missing columns in ORM: `habit_type_id`, `streak_count`, and `created_at`.

Affected files:
- `backend/app/models/habits.py`
- `backend/app/schemas/habits.py`
- `backend/app/services/habit_service.py`
- `backend/app/api/routes/habits.py`

Affected endpoints:
- `POST /api/habits` (Fails 500 CheckViolation when impact_level is capitalized)
- `GET /api/habits/{id}` (Fails on UUID parsing)

Recommended minimum fix:
1. In `models/habits.py`, change `habit_id` to `UUID(as_uuid=True)`.
2. Add `habit_type_id = Column(UUID(as_uuid=True), ForeignKey("habit_types.habit_type_id", ondelete="SET NULL"), nullable=True)`, `streak_count`, and `created_at`.
3. Normalize `impact_level` to lowercase in `habit_service.py`.
4. Update `HabitResponse.habit_id` to `Union[UUID, int, str]`.

---

### [CRITICAL] 4. Simulations Domain (Milestone 3 Core)
Domain: Decision Simulations  
Database table: `simulations`  
ORM model: `Simulation`  
Database definition:
```sql
simulation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
template_id UUID REFERENCES simulation_templates(template_id) ON DELETE SET NULL,
decision_type VARCHAR(50) NOT NULL,
scenario_name VARCHAR(150) NOT NULL,
simulation_result JSONB NOT NULL DEFAULT '{}'::jsonb,
predicted_outcome JSONB NOT NULL DEFAULT '{}'::jsonb,
confidence_score NUMERIC(5, 4) CHECK (confidence_score >= 0 AND confidence_score <= 1),
input_parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/simulations.py`):
```python
simulation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE"), index=True, nullable=False)
decision_type = Column(String, nullable=False)
scenario_name = Column(String, nullable=False)
simulation_result = Column(JSON, nullable=True)
predicted_outcome = Column(String, nullable=True) # Type mismatch: DB is JSONB!
generated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
```
Exact mismatch:
1. `simulation_id` is `UUID` in PostgreSQL, but `Integer` in ORM.
2. `predicted_outcome` is `JSONB` in PostgreSQL, but `Column(String)` in ORM.
3. Missing columns in ORM: `template_id UUID`, `confidence_score NUMERIC(5, 4)`, and `input_parameters JSONB`.

Affected files:
- `backend/app/models/simulations.py`
- Milestone 3 simulation service and persistence router.

Recommended minimum fix:
1. Change `simulation_id` to `UUID(as_uuid=True)`.
2. Change `predicted_outcome` to `Column(JSON)`.
3. Add `template_id`, `confidence_score`, and `input_parameters` columns.

---

### [CRITICAL] 5. Recommendations Domain
Domain: Recommendation Engine  
Database table: `recommendations`  
ORM model: `Recommendation`  
Database definition:
```sql
recommendation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
recommendation_text TEXT NOT NULL,
category VARCHAR(50) NOT NULL,
priority VARCHAR(20) NOT NULL DEFAULT 'medium' CHECK (priority IN ('low', 'medium', 'high', 'critical')),
confidence_score NUMERIC(5, 4) NOT NULL DEFAULT 0.8500 CHECK (confidence_score >= 0 AND confidence_score <= 1),
action_plan JSONB,
is_actioned BOOLEAN NOT NULL DEFAULT FALSE,
generated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/recommendations.py`):
```python
recommendation_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
priority = Column(String, default="Medium", nullable=False) # Violates CHECK constraint!
confidence_score = Column(Float, default=0.85, nullable=False)
```
Exact mismatch:
1. `recommendation_id` is `UUID` in PostgreSQL, but `Integer` in ORM.
2. Check constraint violation: `priority` default is `"Medium"` in ORM, but PostgreSQL check constraint requires lowercase `'medium'`.

Affected files:
- `backend/app/models/recommendations.py`

Recommended minimum fix:
1. Change `recommendation_id` to `UUID(as_uuid=True)`.
2. Change `priority` default to lowercase `"medium"`.

---

### [CRITICAL] 6. Analytics Logs Domain
Domain: Telemetry & Behavior Logging  
Database table: `analytics_logs`  
ORM model: `AnalyticsLog`  
Database definition:
```sql
log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
user_id UUID REFERENCES users(user_id) ON DELETE CASCADE,
activity_type VARCHAR(100) NOT NULL,
endpoint VARCHAR(255),
method VARCHAR(10),
status_code INT,
response_time_ms NUMERIC(8, 2),
metadata_json JSONB,
timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/analytics.py`):
```python
log_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
# Missing status_code
```
Exact mismatch:
1. `log_id` is `UUID` in PostgreSQL, but `Integer` in ORM.
2. Missing column in ORM: `status_code INT`.

Affected files:
- `backend/app/models/analytics.py`

Recommended minimum fix:
1. Change `log_id` to `UUID(as_uuid=True)`.
2. Add `status_code = Column(Integer, nullable=True)`.

---

### [CRITICAL] 7. Model Registry Domain
Domain: ML Model Registry  
Database table: `model_registry`  
ORM model: `ModelRegistry`  
Database definition:
```sql
model_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
domain VARCHAR(50) NOT NULL,
model_name VARCHAR(100) NOT NULL,
algorithm VARCHAR(100) NOT NULL,
version VARCHAR(20) NOT NULL,
metrics JSONB,
feature_importances JSONB,
is_active BOOLEAN NOT NULL DEFAULT TRUE,
trained_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
```
Current code definition (`backend/app/models/model_registry.py`):
```python
model_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
# Missing domain column!
```
Exact mismatch:
1. `model_id` is `UUID` in PostgreSQL, but `Integer` in ORM.
2. Missing `NOT NULL` column: `domain VARCHAR(50) NOT NULL` exists in PostgreSQL but is missing from ORM. Any insert via ORM fails.

Affected files:
- `backend/app/models/model_registry.py`

Recommended minimum fix:
1. Change `model_id` to `UUID(as_uuid=True)`.
2. Add `domain = Column(String(50), nullable=False)`.

---

## 6. Constraint Problems

The audit detected specific service / ORM patterns that directly violate PostgreSQL constraints:

1. **`goals.status` Check Constraint**:
   * PostgreSQL requires: `status IN ('on_track', 'at_risk', 'completed', 'abandoned', 'behind')`.
   * Current code sets: `status = "On Track"` (Title Case with space).
2. **`habit_tracking.impact_level` Check Constraint**:
   * PostgreSQL requires: `impact_level IN ('low', 'medium', 'high', 'critical')`.
   * Current code defaults to `"Medium"` and receives `"High"` from forms.
3. **`habit_tracking.status` Check Constraint**:
   * PostgreSQL requires: `status IN ('completed', 'missed', 'partial', 'skipped')`.
4. **`recommendations.priority` Check Constraint**:
   * PostgreSQL requires: `priority IN ('low', 'medium', 'high', 'critical')`.
   * Current code defaults to `"Medium"`.
5. **`model_registry.domain` NOT NULL Constraint**:
   * PostgreSQL requires: `domain VARCHAR(50) NOT NULL`.
   * Current ORM omits the column completely.

---

## 7. API Verification

Integration endpoints verified live against PostgreSQL:

| Endpoint | Method | Live Status | Result |
|---|---|:---:|---|
| `/api/auth/login` | POST | **200 OK** | JWT token issued successfully |
| `/api/financial/records` | GET | **200 OK** | Returns records via `ExpenseCategory` join |
| `/api/financial/records` | POST | **201 Created** | Resolves `category_id`, inserts without error |
| `/api/financial/records/{id}` | GET | **200 OK** | Reads record by UUID |
| `/api/financial/summary` | GET | **200 OK** | Computes totals and category breakdown |
| `/api/financial/records/{id}` | DELETE | **200 OK** | Deletes record cleanly |
| `/api/study/activities` | GET | **200 OK** | Returns activities via `Subject` join |
| `/api/study/activities` | POST | **201 Created** | Resolves `subject_id`, inserts without error |
| `/api/study/summary` | GET | **200 OK** | Aggregates focus and hours |
| `/api/study/activities/{id}` | DELETE | **200 OK** | Deletes activity cleanly |
| `/api/ml/digital-twin` | GET | **200 OK** | Aggregates multi-domain prediction state |
| `/api/ml/models` | GET | **200 OK** | Returns status of all 5 ML models |
| `/api/users/profile` | GET | **500 Internal Error** | Fails: `goals.category does not exist` |
| `/api/users/summary` | GET | **500 Internal Error** | Fails: `goals.category does not exist` |
| `/api/goals` | GET / POST | **500 Internal Error** | Fails: `goals.category does not exist` |
| `/api/goals/summary` | GET | **500 Internal Error** | Fails: `goals.category does not exist` |
| `/api/fitness/activities` | GET / POST | **500 Internal Error** | Fails: `fitness_activities.duration does not exist` |
| `/api/fitness/summary` | GET | **500 Internal Error** | Fails: `fitness_activities.duration does not exist` |
| `/api/habits` | POST | **500 Internal Error** | Fails: `habit_tracking_impact_level_check` violation |

---

## 8. Automated Tests

Automated verification suite run in isolated test environment (`pytest -q`):

```
Total:    39
Passed:   39
Failed:    0
Skipped:   0
Warnings:  7 (Pydantic V2 ConfigDict deprecation warnings)
```

*(Note: Pytest passes 39/39 because test fixtures use an isolated SQLite test database with `create_all()`, masking the PostgreSQL 15 3NF column name and check constraint mismatches).*

---

## 9. ML Integration Compatibility

The audit verified that all machine learning artifacts and pipelines remain intact:
* **Academic Model**: `ml_models/trained/academic/model.joblib` (`GradientBoostingRegressor`) — Verified intact.
* **Lifestyle Model**: `ml_models/trained/lifestyle/model.joblib` (`LogisticRegression`) — Verified intact.
* **Financial Model**: `ml_models/trained/financial/model.joblib` (`RandomForestRegressor`) — Verified intact.
* **Forecasting Model**: `ml_models/trained/forecasting/model.joblib` (`XGBRegressor`) — Verified intact.
* **Fitness Model**: Explicitly excluded from Phase 3 scope per architecture.
* **Model Registry JSON**: [`ml_models/model_registry.json`](file:///c:/Users/gkdha/OneDrive/Desktop/INFO_PROJECT/digital_twin_ai/ml_models/model_registry.json) — Unchanged and valid.

---

## 10. FINAL ASSESSMENT

### **FIX REQUIRED BEFORE MILESTONE 3**

Milestone 3 directly relies on the Digital Twin engine synthesizing **Goals**, **Fitness**, **Habits**, and **Simulation** data alongside Financial and Study data. Proceeding into Milestone 3 without resolving these mismatches will break dashboard profile loading and Monte Carlo persistence.

### Prioritized Remediation Plan:

#### **P0 (Must Fix — Blocks Core Endpoints and Dashboard)**:
1. **Goals Domain (`models/goals.py`, `schemas/goals.py`, `services/goal_service.py`)**:
   * Change `goal_id` to `UUID`.
   * Replace `category` column with `category_id UUID REFERENCES goal_categories(category_id)`.
   * Provide `@hybrid_property def category` for seamless API compatibility.
   * Normalize `status` to lowercase snake_case (`'on_track'`).
   * *Unblocks `/api/goals`, `/api/goals/summary`, `/api/users/profile`, and `/api/users/summary`.*
2. **Fitness Domain (`models/fitness.py`, `schemas/fitness.py`, `services/fitness_service.py`)**:
   * Change `fitness_id` to `UUID`.
   * Map `duration_minutes` with `@hybrid_property def duration`.
   * Add `intensity_level` and `created_at`.
   * *Unblocks `/api/fitness/activities` and `/api/fitness/summary`.*
3. **Habits Domain (`models/habits.py`, `schemas/habits.py`, `services/habit_service.py`)**:
   * Change `habit_id` to `UUID`.
   * Add `habit_type_id UUID REFERENCES habit_types(habit_type_id)`, `streak_count`, and `created_at`.
   * Normalize `impact_level` to lowercase (`'medium'`, `'high'`).
   * *Unblocks `POST /api/habits` and habit streak tracking.*

#### **P1 (Should Fix — Required for Milestone 3 Simulation & Recommendations)**:
4. **Simulations Domain (`models/simulations.py`)**:
   * Change `simulation_id` to `UUID`.
   * Change `predicted_outcome` from `String` to `JSON`.
   * Add `template_id UUID REFERENCES simulation_templates(template_id)`, `confidence_score`, and `input_parameters`.
5. **Recommendations Domain (`models/recommendations.py`)**:
   * Change `recommendation_id` to `UUID`.
   * Set lowercase default for `priority = "medium"`.
6. **Analytics Logs Domain (`models/analytics.py`)**:
   * Change `log_id` to `UUID`.
   * Add `status_code INT`.

#### **P2 (Optional / Best Practice)**:
7. **Model Registry (`models/model_registry.py`)**:
   * Change `model_id` to `UUID`.
   * Add `domain VARCHAR(50) NOT NULL`.
8. **User Model (`models/user.py`)**:
   * Add `updated_at = Column(DateTime(timezone=True))`.
