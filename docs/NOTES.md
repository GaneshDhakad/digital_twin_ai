# Digital Twin AI - System Notes & Architecture Reference (Milestone 1)

## Architecture Overview
The system follows an N-Tier layered architecture:
- **Presentation Layer**: Streamlit web client with Stitch-inspired *Synthetic Intelligence* glassmorphic HUD theme.
- **API Layer**: FastAPI application exposing versioned REST endpoints under `/api`.
- **Business Logic Layer**: Domain services (`user_service`, `financial_service`, `study_service`, `habit_service`, `fitness_service`, `goal_service`, `analytics_service`).
- **Data Layer**: SQLAlchemy ORM with PostgreSQL 15 / SQLite fallback support.

## Endpoints (35+ Endpoints Operational)

### Authentication (`/api/auth`)
- `POST /api/auth/register` - Register a new user profile with password hashing.
- `POST /api/auth/login` - Authenticate user credentials and return 24-hour JWT token.
- `GET /api/auth/me` - Retrieve current user account.

### Profile Management (`/api/users`)
- `GET /api/users/profile` - Full profile detail & stats.
- `PUT /api/users/profile` - Update profile parameters.
- `DELETE /api/users/profile` - Soft-delete account (`is_active=False`).
- `GET /api/users/summary` - Aggregated user counts & streak statistics.

### Financial Records (`/api/financial`)
- `POST /api/financial/records` - Log income/expense with net savings calculation.
- `GET /api/financial/records` - Paginated & filtered list by category and month.
- `GET /api/financial/records/{record_id}` - Single record detail.
- `PUT /api/financial/records/{record_id}` - Update record.
- `DELETE /api/financial/records/{record_id}` - Delete record.
- `GET /api/financial/summary` - Monthly income, expenses, savings rate, and category breakdown.

### Study Activities (`/api/study`)
- `POST /api/study/activities` - Log study session.
- `GET /api/study/activities` - List study entries with subject filtering.
- `GET /api/study/summary` - Avg focus score, completion rate, peak hours.
- `PUT /api/study/activities/{activity_id}` - Update study session.
- `DELETE /api/study/activities/{activity_id}` - Delete study session.

### Habit Tracking (`/api/habits`)
- `POST /api/habits` - Create/log habit status.
- `GET /api/habits` - List habits with streak calculation.
- `GET /api/habits/analytics` - Completion rate, streak, at-risk habit flags.
- `PUT /api/habits/{habit_id}` - Update habit record.
- `DELETE /api/habits/{habit_id}` - Delete habit record.

### Fitness Activities (`/api/fitness`)
- `POST /api/fitness/activities` - Log workout session.
- `GET /api/fitness/activities` - List fitness activities.
- `GET /api/fitness/summary` - Weekly workout count, total duration, calorie trend.
- `PUT /api/fitness/activities/{fitness_id}` - Update workout entry.
- `DELETE /api/fitness/activities/{fitness_id}` - Delete workout entry.

### Goals Management (`/api/goals`)
- `POST /api/goals` - Create user goal.
- `GET /api/goals` - List goals with progress percentage.
- `PUT /api/goals/{goal_id}/progress` - Update current progress.
- `GET /api/goals/summary` - Breakdown of goals by status.
- `DELETE /api/goals/{goal_id}` - Delete goal.

### Analytics & Audit (`/api/analytics`)
- `GET /api/analytics/activity-log` - Access user action and API response history.
