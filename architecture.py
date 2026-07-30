# -*- coding: utf-8 -*-
"""Content for the Digital Twin AI System Architecture Document."""

DOC_TITLE = "Digital Twin AI \u2013 Personal Life Simulation & Decision Assistant"
DOC_SUB = "System Architecture Document (SAD)"
DOC_META = "Version 2.0  |  July 2026  |  Reference: Project Brief & Software Requirements Specification v2.0"

INTRO = (
    "This document describes the software architecture of Digital Twin AI: its layers, components, "
    "design patterns, data model, machine-learning strategy, security posture, performance approach and "
    "deployment topology. It answers <i>how</i> the system is built. Companion document <b>Software "
    "Requirements Specification (SRS) v2.0</b> answers <i>what</i> the system must do; every architectural "
    "decision in this document exists to satisfy one or more requirements defined there."
)

SCOPE = (
    "This architecture covers the full application: the Streamlit-based presentation layer, the FastAPI "
    "backend (API, service, repository and cross-cutting layers), the machine-learning subsystem "
    "(forecasting, prediction, clustering, model registry), the Digital Twin and Simulation engines, the "
    "hybrid Recommendation Engine, the Conversational AI Assistant, the PostgreSQL data layer, and the "
    "Docker-based infrastructure. It is written for the development team, technical reviewers, and anyone "
    "evaluating the system for a demonstration or a technical interview."
)

GOALS = [
    "<b>Separation of Concerns</b> \u2014 presentation, business rules, machine learning, and data access must "
    "never be entangled in the same module.",
    "<b>Testability</b> \u2014 every layer must be unit-testable in isolation via dependency injection, "
    "without requiring a live database or a live LLM API call.",
    "<b>Scalability</b> \u2014 the API and simulation layers must scale horizontally behind a load balancer "
    "without code changes, using stateless services and an external cache (Redis).",
    "<b>Security by Design</b> \u2014 authentication, authorization and input validation are enforced at the "
    "framework level (dependencies, middleware), not left to individual endpoint authors to remember.",
    "<b>Extensibility</b> \u2014 new domains (e.g. a future sleep tracker) or new ML algorithms must be "
    "addable without modifying existing, tested code (Open/Closed Principle).",
    "<b>Explainability</b> \u2014 every prediction, forecast and recommendation must be traceable to the "
    "model, data and rule that produced it (Model Registry, SHAP, LLM narration).",
]

CONSTRAINTS = [
    "Backend implemented in Python 3.11 with FastAPI; frontend implemented in Streamlit \u2014 both mandated "
    "by the project brief.",
    "PostgreSQL 15 is the system of record; no other persistent datastore is introduced except Redis, "
    "which is a cache/rate-limit layer only and holds no data of record.",
    "At least one of OpenAI GPT-4o or Google Gemini must be integrated for the Conversational AI Assistant "
    "and for LLM-generated recommendation explanations.",
    "The system must be fully reproducible via a single `docker compose up` command on any Docker-capable host.",
    "Delivered as an academic/portfolio-grade project by a small team acting across architecture, backend, "
    "ML, frontend and DevOps roles \u2014 architecture must stay comprehensible to a student developer, not "
    "just theoretically correct.",
]

STYLE_RATIONALE = (
    "Digital Twin AI uses a <b>layered (N-tier) architecture</b> with an internal <b>service-oriented</b> "
    "structure and a strict <b>Repository Pattern</b> for data access. A layered style was chosen over a "
    "microservices split because the system's domains (financial, study, habit, fitness, goals) share a "
    "single relational schema and a single Digital Twin state object \u2014 splitting them into separate "
    "services would force distributed transactions across a tightly-coupled data model for no scaling "
    "benefit at this project's scale. Instead, scaling is achieved horizontally within one deployable "
    "backend (stateless FastAPI workers behind Redis-backed caching), which is simpler to build, test and "
    "reason about while still satisfying the performance and scalability requirements in the SRS."
)

LAYERS = [
    ("Layer", "Purpose", "Key Components", "Depends On"),
    ("Presentation", "What the user sees and interacts with.",
     "Streamlit pages; design-system components (KPI Card, AI Insight Panel, Recommendation Panel, "
     "Activity Timeline, Search/Filter bar); AgGrid tables; Plotly charts.",
     "API layer only, via a centralized api_client."),
    ("API", "Stable HTTP contract into the system; the only layer exposed to the network.",
     "FastAPI routers; Pydantic request/response schemas; JWT auth dependency; rate-limiting middleware.",
     "Business Logic layer."),
    ("Business Logic (Service)", "Orchestrates use cases; the only layer that knows business rules.",
     "financial_service, study_service, habit_service, fitness_service, goal_service, simulation_service, "
     "recommendation_service, analytics_service, ai_service.",
     "Repository layer, and the ML / Digital Twin / Simulation / Recommendation layers where relevant."),
    ("Machine Learning", "Produces forecasts, predictions and pattern detection.",
     "financial_forecasting.py (Prophet/ARIMA/XGBoost/LightGBM), study_prediction.py (RF/XGBoost/CatBoost), "
     "habit_analysis.py (Isolation Forest/KMeans/DBSCAN), model_registry.py.",
     "Repository layer (feature data) and the Model Registry."),
    ("Digital Twin", "The living, 8-state model of one user.",
     "digital_twin.py \u2192 DigitalTwin class; TwinUpdateEvent background-task pipeline.",
     "Every other layer's output; consumed by the Simulation layer as the baseline state."),
    ("Simulation", "Answers \u2018what if\u2019 questions across 9 decision types.",
     "9 simulator classes (Financial, Study, Career, Fitness, Lifestyle, Investment, Loan, Emergency, "
     "Custom); ScenarioComparer (5-way); RiskAssessor.",
     "Digital Twin (baseline state) and the ML layer (predictive components)."),
    ("Recommendation Engine", "Turns analysis into a specific, prioritized next action.",
     "Rule engine; recommendation_ranker.py (ML confidence scoring); ai_service.py (LLM explanation "
     "and action-plan narration).",
     "Digital Twin, Simulation output, and the external LLM service."),
    ("Database", "Single source of truth.",
     "PostgreSQL 15; 10 tables; SQLAlchemy 2.0 models; Alembic migrations.",
     "Nothing \u2014 the lowest layer."),
    ("Infrastructure", "Cross-cutting reliability, performance and delivery concerns.",
     "Redis (cache + rate limiting); Docker Compose; GitHub Actions CI; structured logging middleware; "
     "Celery (Monte-Carlo offload).",
     "Cross-cuts every layer above."),
]

DESIGN_PATTERNS = [
    ("Pattern / Principle", "Where It Lives", "Why It Is Used"),
    ("Repository Pattern", "repositories/base_repository.py + one subclass per model",
     "Isolates SQL/ORM detail behind a typed interface so services never see a raw Session object; "
     "makes swapping or mocking the data layer trivial in unit tests."),
    ("Service Layer", "services/*.py",
     "Holds business rules (e.g. \u2018savings rate below 20% triggers a recommendation\u2019) in one place, "
     "independent of both HTTP and SQL, so the same logic is reusable from the API, a background job, or a test."),
    ("Dependency Injection", "FastAPI Depends() chains: Router \u2192 Service \u2192 Repository \u2192 DB Session",
     "Each layer knows only about the layer directly beneath it (Dependency Inversion); enables unit "
     "testing by injecting fakes at any seam."),
    ("Global Exception Handling", "exceptions/custom_exceptions.py + handlers registered in main.py",
     "Every error, anywhere in the stack, resolves to one consistent JSON error envelope instead of "
     "ad hoc try/except blocks scattered across 40+ endpoints."),
    ("Single Responsibility", "One file per model; one service per domain",
     "financial_service.py never touches study logic; a change to habit rules cannot break financial forecasting."),
    ("Open/Closed Principle", "BaseRepository[T] generic class; ScenarioComparer normalization",
     "New domains extend BaseRepository without modifying it; new simulation types plug into "
     "ScenarioComparer without changing its ranking logic."),
    ("Strategy Pattern", "model_selector.py (champion/challenger selection)",
     "Each forecasting/prediction task treats its candidate algorithms (e.g. Prophet vs. XGBoost vs. "
     "LightGBM) as interchangeable strategies scored by an identical metric, so adding a fifth algorithm "
     "requires no change to the selection logic."),
    ("Don\u2019t Repeat Yourself", "utils/pagination.py, validators/common_validators.py, frontend/components/",
     "Pagination, filtering, positive-amount validation and UI cards are written once and reused "
     "everywhere instead of being re-implemented per page or per endpoint."),
]

FOLDER_STRUCTURE = """digital_twin_ai/
|-- backend/
|   |-- main.py
|   |-- app/
|   |   |-- api/routers/          <- FastAPI routers (auth, users, financial, study,
|   |   |                             habits, fitness, goals, simulation,
|   |   |                             recommendations, analytics, assistant, admin)
|   |   |-- services/             <- business logic (one file per domain)
|   |   |-- repositories/         <- BaseRepository[T] + one repository per model
|   |   |-- schemas/              <- Pydantic request/response models
|   |   |-- models/               <- SQLAlchemy ORM models
|   |   |-- core/                 <- config.py, security.py, database.py
|   |   |-- middleware/           <- logging, timing, request-id middleware
|   |   |-- utils/                <- pagination.py and other shared helpers
|   |   |-- validators/           <- reusable Pydantic validators
|   |   |-- exceptions/           <- custom exception classes + handlers
|   |   `-- ml/
|   |       |-- financial_forecasting.py
|   |       |-- study_prediction.py
|   |       |-- habit_analysis.py
|   |       |-- model_registry.py
|   |       |-- model_selector.py
|   |       |-- digital_twin.py
|   |       |-- simulation_engine.py
|   |       |-- scenario_comparison.py
|   |       |-- risk_assessment.py
|   |       |-- recommendation_engine.py
|   |       `-- recommendation_ranker.py
|   |-- migrations/               <- Alembic migrations
|   `-- tests/
|-- frontend/
|   |-- app.py                    <- Streamlit entry point
|   |-- pages/                    <- Profile, Financial, Study, Habits & Fitness,
|   |                                Forecasting, Simulation, Dashboard, Model Insights
|   |-- components/               <- header, kpi_card, ai_insight_panel,
|   |                                recommendation_panel, activity_timeline,
|   |                                search_filter_bar, empty_state
|   |-- theme/                    <- design tokens + light/dark theme manager
|   `-- utils/                    <- centralized api_client
|-- ml_models/trained/             <- serialized .pkl / .joblib model files
|-- docker/                        <- Dockerfile.backend, Dockerfile.frontend,
|                                      docker-compose.yml
|-- docs/                          <- ARCHITECTURE.md, SRS, diagrams/, model_cards/
|-- tests/                         <- integration + load tests
|-- .env.example
|-- requirements.txt
`-- README.md"""

COMPONENT_TABLE = [
    ("Component", "Layer", "Responsibility"),
    ("BaseRepository[T]", "Database", "Generic get / get_multi (paginated) / create / update / delete / exists."),
    ("UserService, FinancialService, StudyService, HabitService, FitnessService, GoalService",
     "Business Logic", "CRUD orchestration, validation, and domain summaries per data type."),
    ("AnalyticsService", "Business Logic", "Aggregates all ML outputs into one consolidated report per user."),
    ("ModelRegistry", "Machine Learning", "Persists and serves accuracy/RMSE/MAE/precision/recall/feature "
     "importance per trained model version; marks the active (auto-selected) model."),
    ("ModelSelector", "Machine Learning", "Champion/challenger comparison across candidate algorithms; "
     "selects and persists the best performer per task."),
    ("DigitalTwin", "Digital Twin", "Aggregates the user's 8 state domains; projects state forward for "
     "simulations; updates on every user write via background events."),
    ("9 Simulator classes", "Simulation", "One class per decision category, each returning a 5-way "
     "scenario comparison (Current / Best / Expected / Worst / Risk)."),
    ("ScenarioComparer", "Simulation", "Normalizes and ranks multiple scenarios on a common metric for "
     "side-by-side comparison."),
    ("RiskAssessor", "Simulation", "Monte-Carlo percentile risk scoring; emergency-fund and goal-deadline checks."),
    ("RecommendationEngine + Ranker", "Recommendation", "Rule triggers -> ML confidence scoring -> ranked, "
     "deduplicated recommendation list."),
    ("AIRecommendationEnhancer / DigitalTwinAssistant", "Recommendation / Presentation-facing",
     "LLM-generated explanations, action-plan narration, conversational Q&A, and chart/simulation "
     "explanation on demand."),
]

DATA_MODEL_INTRO = (
    "The data layer is a single normalized PostgreSQL 15 database. <b>Users</b> is the hub table; every "
    "other table holds a <code>user_id</code> foreign key back to it, giving a strict one-to-many, "
    "user-centric schema (see the Entity Relationship diagram below). JSONB columns "
    "(<code>Simulations.simulation_result</code>, <code>Recommendations.action_plan</code>, "
    "<code>Analytics_Logs.metadata</code>, <code>Model_Registry.metrics</code>) are used deliberately, and "
    "only, where the payload shape is inherently variable (a simulation's result structure differs by "
    "decision type) \u2014 every other column is a typed, indexed relational column."
)

DB_TABLES = [
    ("Table", "Key Fields", "Purpose"),
    ("Users", "user_id (PK), name, email, age, occupation, password_hash, role, is_active, created_at",
     "Identity, profile and authorization root."),
    ("Financial_Records", "record_id (PK), user_id (FK), income, expenses, savings, transaction_date, "
     "category, recurring_frequency",
     "Income/expense ledger; primary input to the forecasting engine."),
    ("Study_Activities", "activity_id (PK), user_id (FK), study_hours, subject, performance_score, "
     "task_completion_rate, activity_date",
     "Study-session log; input to the study prediction models."),
    ("Habit_Tracking", "habit_id (PK), user_id (FK), habit_name, status, completion_rate, impact_level, record_date",
     "Daily habit completion log; input to clustering/anomaly detection."),
    ("Fitness_Activities", "fitness_id (PK), user_id (FK), activity_type, duration, calories_burned, activity_date",
     "Workout log; input to fitness goal forecasting."),
    ("Goals", "goal_id (PK), user_id (FK), goal_name, category, target_value, target_date, current_progress, status",
     "User-defined targets tracked across all domains."),
    ("Simulations", "simulation_id (PK), user_id (FK), decision_type, scenario_name, simulation_result "
     "(JSONB), predicted_outcome, generated_at",
     "Persisted history of every simulation run, across all 9 decision types."),
    ("Recommendations", "recommendation_id (PK), user_id (FK), category, priority, confidence_score, "
     "action_plan (JSONB), is_actioned, generated_at",
     "Generated advice, its ML confidence score, and completion tracking."),
    ("Analytics_Logs", "log_id (PK), user_id (FK), activity_type, metadata (JSONB), timestamp",
     "Every significant user action, powering the Activity Timeline and the Digital Twin's behavioral state."),
    ("Model_Registry", "model_id (PK), model_name, algorithm, version, metrics (JSONB), "
     "feature_importances (JSONB), is_active, trained_at",
     "Tracks every trained model version and which one is currently active, for transparency and audit."),
]

INDEX_STRATEGY = [
    "A composite index on (user_id, transaction_date) on Financial_Records and (user_id, activity_date) "
    "on Study_Activities / Fitness_Activities supports the most common query pattern: \u2018this user\u2019s "
    "records in a date range\u2019.",
    "A single-column index on user_id exists on every table, since every query in the system is scoped "
    "to one authenticated user.",
    "N+1 query patterns are eliminated via SQLAlchemy's joinedload()/selectinload() rather than indexes alone.",
    "Foreign-key constraints (ON DELETE CASCADE from Users) guarantee referential integrity and make a "
    "user-initiated account deletion a single, safe cascading operation.",
    "JSONB columns (Simulations.simulation_result, Model_Registry.metrics) use PostgreSQL's native GIN "
    "indexing only where ad hoc querying inside the JSON is required for the admin Model Insights view.",
]

ML_STRATEGY_INTRO = (
    "Rather than shipping a single model per prediction task, the architecture treats model choice as a "
    "<b>Strategy pattern</b>: several candidate algorithms are trained on identical data splits, evaluated "
    "on identical metrics, and the best performer is promoted to \u2018active\u2019 in the Model Registry. "
    "This is re-evaluated whenever the model is retrained, so the active model can change as real usage "
    "data accumulates and supersedes the initial synthetic training set."
)

ML_COMPARISON = [
    ("Domain", "Candidate Algorithms", "Selection Metric", "Rationale Summary"),
    ("Financial Forecasting", "Prophet, ARIMA, XGBoost, LightGBM", "MAPE (lower wins); RMSE as tie-break",
     "Prophet decomposes trend + seasonality interpretably; ARIMA is a classical univariate cash-flow "
     "baseline; XGBoost captures non-linear category interactions; LightGBM's leaf-wise growth wins as "
     "history grows."),
    ("Study Performance Prediction", "Random Forest, XGBoost, CatBoost", "R\u00b2 (higher wins); MAE as tie-break",
     "Random Forest is a low-variance baseline; XGBoost raises the accuracy ceiling via boosting; "
     "CatBoost handles categorical features (subject, day-of-week) natively."),
    ("Habit Pattern Clustering", "KMeans vs. DBSCAN (compared); Isolation Forest (separate anomaly task)",
     "Silhouette score (KMeans vs. DBSCAN)",
     "KMeans is fast when the cluster count is roughly known; DBSCAN finds arbitrary-shaped groups without "
     "specifying k and naturally flags noise; Isolation Forest solves a different problem (anomalous weeks) "
     "and is not compared against the clustering pair."),
]

PERFORMANCE_TARGETS = [
    ("Metric", "Target", "Mechanism"),
    ("Simple CRUD API response (P95)", "< 300 ms", "Connection pooling, async SQLAlchemy, composite indexes."),
    ("Dashboard full load", "< 2 seconds", "Redis-cached full analytics report; concurrent asyncio.gather() ML calls."),
    ("Forecast endpoint (ML-backed)", "< 2 seconds", "Singleton in-process model loading; 1-hour Redis result cache."),
    ("Simulation (any of 9 types)", "< 5 seconds, including at 10 concurrent users", "Celery/async offload for "
     "Monte-Carlo runs; 15-minute result cache for identical parameters."),
    ("Test coverage (backend)", "\u2265 90%", "Enforced at each milestone gate via pytest-cov."),
]

SECURITY_CONTROLS = [
    "<b>Authentication:</b> stateless JWT bearer tokens (HS256, 24-hour expiry); no server-side session state.",
    "<b>Password storage:</b> bcrypt hashing with per-password salt; plaintext passwords are never logged or persisted.",
    "<b>Authorization:</b> role-based access control (Standard User / Administrator) enforced by a "
    "require_admin FastAPI dependency; ownership checks ensure a user can only read or write their own records.",
    "<b>Input validation:</b> Pydantic schemas plus a shared validators/ library reject malformed or "
    "out-of-range input before it reaches the service layer.",
    "<b>Injection protection:</b> all database access goes through parameterized SQLAlchemy queries via the "
    "Repository layer \u2014 no raw string-built SQL exists anywhere in the codebase.",
    "<b>XSS protection:</b> all user-supplied text is treated as data, not markup, by both the API layer "
    "and the Streamlit renderer; Content-Security-Policy headers are set on all responses.",
    "<b>CORS:</b> an explicit allow-list of origins is configured via CORSMiddleware; wildcard origins are "
    "never used in a production-like configuration.",
    "<b>CSRF:</b> because authentication is a JWT bearer token in an Authorization header (not a cookie), "
    "classic browser CSRF does not apply to this API. This is a deliberate architectural choice, documented "
    "so it is not mistaken for an oversight; if a cookie-based session is ever added, SameSite=Strict plus "
    "a double-submit CSRF token is the specified defense-in-depth.",
    "<b>Rate limiting:</b> a global limit (100 requests/minute/IP) plus a stricter limit on the "
    "Conversational AI endpoint (30 messages/user/hour) protect both infrastructure and third-party LLM cost.",
    "<b>Secrets management:</b> all credentials and API keys are loaded from environment variables via "
    "pydantic-settings; none are hardcoded or committed to source control.",
]

DEPLOYMENT_DESC = [
    "The system is packaged as a Docker Compose stack of five services: <b>frontend</b> (Streamlit), "
    "<b>backend</b> (FastAPI/uvicorn), <b>postgres</b> (PostgreSQL 15 with a named volume for persistence), "
    "<b>redis</b> (cache and rate-limit store), and <b>celery-worker</b> (offloads Monte-Carlo-heavy "
    "simulation requests so the API layer stays responsive).",
    "Each service defines a healthcheck; the backend waits for PostgreSQL to report healthy before "
    "accepting traffic, avoiding startup race conditions.",
    "Configuration is injected exclusively through environment variables (an .env file locally; secrets "
    "in a managed secret store in any cloud deployment), so the same image is promotable across environments "
    "without rebuilding.",
    "A GitHub Actions pipeline runs the full pytest suite and a bandit security scan on every push to "
    "main, and builds both Docker images; a failing pipeline blocks merge.",
    "The stack is horizontally scalable at the backend/celery-worker tier (stateless workers behind a load "
    "balancer) without any code change, because session state lives in the JWT token and shared state lives "
    "in PostgreSQL/Redis, not in process memory.",
]

RISKS = [
    ("Risk", "Impact", "Mitigation"),
    ("Third-party LLM API latency, cost, or outage", "Conversational AI and LLM-enhanced recommendations degrade",
     "Rule-based recommendation text as an automatic fallback; per-user/per-hour rate limits; response streaming "
     "to reduce perceived latency."),
    ("Model drift as real user data replaces synthetic training data", "Forecast/prediction accuracy could decay silently",
     "Model Registry tracks metrics per version; champion/challenger re-evaluation is designed to be re-run "
     "as new data accumulates, not only once at launch."),
    ("Monte-Carlo simulations exceeding the 5-second target under load", "Milestone 4 performance criterion at risk",
     "Async/Celery offload; iteration-count tuning; 15-minute result caching for repeated identical requests."),
    ("A single PostgreSQL instance as a scaling bottleneck", "Read-heavy analytics could contend with writes at scale",
     "Connection pooling now; the Repository abstraction makes introducing a read replica a contained, "
     "single-layer change later."),
    ("Sensitive financial/personal data exposure", "Privacy and trust risk",
     "Ownership-scoped queries at the repository layer, JWT-only access, no data shared with the LLM "
     "provider beyond the minimum context needed to answer the specific query in flight."),
]

FUTURE_EVOLUTION = (
    "The layered/Repository design is deliberately positioned so that, if usage outgrows a single-host "
    "deployment, the Machine Learning, Simulation and Recommendation layers could each be extracted into "
    "independently deployable services behind the existing Service-layer interfaces without touching the "
    "Presentation or API layers \u2014 the Repository Pattern and Dependency Injection boundaries defined in "
    "this document are exactly the seams such a split would use."
)