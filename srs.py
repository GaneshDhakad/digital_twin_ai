# -*- coding: utf-8 -*-
"""Content for the Digital Twin AI Software Requirements Specification (IEEE-830-style)."""

DOC_TITLE = "Digital Twin AI \u2013 Personal Life Simulation & Decision Assistant"
DOC_SUB = "Software Requirements Specification (SRS)"
DOC_META = "Version 2.0  |  July 2026  |  Prepared per an IEEE-830 / Wiegers-style SRS template  |  " \
           "Companion document: System Architecture Document (SAD) v2.0"

PURPOSE = (
    "This Software Requirements Specification (SRS) defines the functional and non-functional requirements "
    "for <b>Digital Twin AI \u2014 Personal Life Simulation & Decision Assistant</b>, an AI-driven "
    "decision-support platform that builds a continuously-updated digital twin of a user's financial, "
    "academic, habitual and fitness life, and uses it to forecast outcomes, simulate decisions, and "
    "generate personalized, explainable recommendations. This document is intended to be the single "
    "source of truth for <i>what</i> the system must do; <i>how</i> it is built is defined separately in "
    "the System Architecture Document (SAD)."
)

CONVENTIONS = (
    "Each functional requirement is uniquely numbered <b>FR-<i>group</i>.<i>item</i></b> and each "
    "non-functional requirement <b>NFR-<i>n</i></b>. The keyword <b>shall</b> denotes a mandatory "
    "requirement; <b>should</b> denotes a strong recommendation that may be deferred without invalidating "
    "the release. Requirement priority is stated as High, Medium, or Low against each feature group in "
    "Section 3."
)

AUDIENCE = (
    "This document is written for: the development team (backend, frontend, ML and DevOps engineers) "
    "implementing the system; the project evaluator or reviewing panel assessing it as a final-year "
    "project, portfolio piece, or production-readiness review; and any future maintainer extending the "
    "system. Section 3 (System Features) is the primary reference for developers; Sections 5\u20136 "
    "(interfaces and non-functional requirements) are the primary reference for QA and DevOps; Section 2 "
    "gives reviewers the fastest orientation to the product as a whole."
)

SCOPE = (
    "Digital Twin AI shall allow a user to record financial, study, habit, fitness and goal data; shall "
    "maintain a personalized, continuously-updated 8-state Digital Twin from that data; shall forecast "
    "financial and academic outcomes using multiple, automatically-compared machine-learning models; shall "
    "simulate at least nine categories of personal decisions and compare each across five scenarios "
    "(Current Path, Best, Expected, Worst, Risk); shall generate personalized, confidence-scored "
    "recommendations combining rule-based logic, machine learning and a Large Language Model; shall expose "
    "a conversational AI assistant able to answer questions, explain charts and simulations, and generate "
    "periodic summaries; and shall present all of the above through an interactive, themeable dashboard "
    "with exportable reports. Payment processing, direct bank-account integration, and mobile native apps "
    "are explicitly out of scope for this version."
)

REFERENCES = [
    "Project Brief: \u201cDigital Twin AI \u2013 Personal Life Simulation & Decision Assistant\u201d (source requirements document).",
    "System Architecture Document (SAD) v2.0 \u2014 companion document describing the technical design that "
    "satisfies this specification.",
    "IEEE Std 830-1998, Recommended Practice for Software Requirements Specifications (structural template reference).",
    "System Usability Scale (SUS), Brooke, J. (1996) \u2014 referenced for the usability acceptance target in Section 6.4.",
]

PRODUCT_PERSPECTIVE = (
    "Digital Twin AI is a new, self-contained web application; it is not a modification of an existing "
    "system. It consists of a Streamlit-based client, a FastAPI backend exposing a versioned REST API, a "
    "PostgreSQL data store, a Redis cache, and outbound integrations to one Large Language Model provider "
    "(OpenAI GPT-4o or Google Gemini). All processing \u2014 forecasting, simulation, and recommendation "
    "generation \u2014 happens server-side; the client is a thin, stateless presentation layer that renders "
    "whatever the API returns."
)

PRODUCT_FUNCTIONS = [
    "Personal data collection and profile management across finances, study, habits, fitness and goals.",
    "A personalized, 8-state Digital Twin that updates as new data arrives.",
    "Multi-algorithm financial forecasting with automatic best-model selection.",
    "Academic performance prediction and optimal study-plan generation.",
    "Habit pattern analysis, anomaly detection, and a composite Productivity Index.",
    "A 9-type decision simulation engine with 5-way scenario comparison and Monte-Carlo risk assessment.",
    "A hybrid (rule-based + ML + LLM) recommendation engine with confidence scores and action plans.",
    "A conversational AI assistant that reads live user data, explains results, and answers questions.",
    "An interactive analytics dashboard with exportable PDF reports.",
    "A transparent Model Registry exposing accuracy, error and explainability metrics for every model in use.",
]

USER_CLASSES = [
    ("Standard User", "The primary user of the system: an individual tracking their own financial, "
     "academic, habit and fitness life. Assumed to have no technical background; interacts exclusively "
     "through the Streamlit dashboard."),
    ("Administrator", "A privileged internal user (e.g. the development/evaluation team) who can view "
     "aggregate, de-identified model-performance metrics via the Model Insights view. Administrators do "
     "not have elevated access to any individual user's personal data beyond what a Standard User of their "
     "own account would see."),
    ("Developer / Maintainer", "Extends or maintains the system; consumes the API directly via Swagger/"
     "ReDoc documentation and the System Architecture Document, not the SRS."),
]

OPERATING_ENV = [
    "Server: Linux container (Docker), Python 3.11 runtime, PostgreSQL 15, Redis 7.",
    "Client: any modern desktop or tablet web browser (Chrome, Firefox, Safari, Edge) with JavaScript enabled.",
    "Network: HTTPS between client and backend; outbound HTTPS from the backend to the configured LLM provider.",
    "No native mobile application is provided in this version; the web client is usable on mobile browsers "
    "but is not optimized for small viewports.",
]

DESIGN_CONSTRAINTS = [
    "The backend must be implemented in Python 3.11 using FastAPI; the frontend must be implemented in Streamlit.",
    "PostgreSQL is the mandated system of record; no other persistent database technology may be substituted.",
    "The system must integrate at least one of OpenAI GPT-4o or Google Gemini for all LLM-dependent features.",
    "The complete system must be deployable via a single Docker Compose command, with no manual "
    "post-deployment configuration steps beyond supplying environment variables.",
    "Automated backend test coverage must reach at least 90% before a milestone is considered complete.",
]

ASSUMPTIONS = [
    "Valid API credentials for the chosen LLM provider are available to the deployment environment.",
    "Users have a modern browser and a reasonably reliable internet connection; the system does not need "
    "to function fully offline.",
    "At initial launch, insufficient real user history exists to train ML models; synthetic data generated "
    "to mirror realistic financial, study and habit patterns is an acceptable and expected basis for the "
    "first trained model versions, to be superseded as real usage accumulates.",
    "Users are adults capable of managing their own financial and personal data; the system does not "
    "provide licensed financial or medical advice and states this within the product.",
]

APPORTIONING = (
    "All requirements in Sections 3\u20136 are in scope for Version 2.0 of the system (this specification). "
    "A small number of explicitly-flagged items are Should, not Shall, and may be deferred to a future "
    "version without invalidating this release: multi-language localization, native mobile clients, and "
    "direct bank-feed import are not required for Version 2.0 and are noted as future scope in Appendix D."
)

# ---------------------------------------------------------------------------
# FUNCTIONAL REQUIREMENT GROUPS
# Each: (group_no, title, priority, description, [(id, text), ...])
# ---------------------------------------------------------------------------
FEATURES = [
    (1, "User Registration, Authentication & Profile Management", "High",
     "Allows an individual to create an account, securely authenticate, and manage their own profile; "
     "underlies every other feature since all data is scoped to an authenticated user.",
     [
      ("FR-1.1", "The system shall allow a new user to register with name, email, password, age, and occupation."),
      ("FR-1.2", "The system shall reject a registration attempt using an email address already on file."),
      ("FR-1.3", "The system shall hash and salt every password using bcrypt before storage; the system "
                  "shall never persist or log a plaintext password."),
      ("FR-1.4", "The system shall authenticate a registered user by email and password and, on success, "
                  "issue a JWT access token valid for 24 hours."),
      ("FR-1.5", "The system shall allow an authenticated user to view and update their own profile "
                  "(name, age, occupation)."),
      ("FR-1.6", "The system shall allow a user to deactivate (soft-delete) their own account."),
      ("FR-1.7", "The system shall restrict every user's data access to records they own, with the sole "
                  "exception of the aggregate metrics available to the Administrator role."),
      ("FR-1.8", "The system shall support two roles \u2014 Standard User and Administrator \u2014 and shall "
                  "enforce role-based access control on every protected endpoint."),
     ]),
    (2, "Financial Data Management", "High",
     "Captures the income, expense and savings data that is the primary input to the forecasting engine.",
     [
      ("FR-2.1", "The system shall allow a user to record a financial transaction with amount, category, "
                  "description, date, type (income or expense), and recurring frequency."),
      ("FR-2.2", "The system shall support at least the following categories: Housing, Food, Transport, "
                  "Education, Entertainment, Healthcare, Investment, Salary, Freelance, Other."),
      ("FR-2.3", "The system shall allow a user to view, edit, and delete their own financial records."),
      ("FR-2.4", "The system shall allow a user to filter and search financial records by category, date "
                  "range, and free-text description."),
      ("FR-2.5", "The system shall paginate financial record listings."),
      ("FR-2.6", "The system shall compute and expose a financial summary \u2014 total income, total "
                  "expenses, net savings, and savings rate \u2014 for any user-selected period."),
     ]),
    (3, "Study Activity Management", "High",
     "Captures study sessions and academic performance data used by the study-prediction models.",
     [
      ("FR-3.1", "The system shall allow a user to log a study session with subject, hours studied, focus "
                  "score, and completion percentage."),
      ("FR-3.2", "The system shall allow a user to view, edit, and delete their own study records."),
      ("FR-3.3", "The system shall compute a study summary: average focus score, task completion rate, "
                  "and peak study hours."),
     ]),
    (4, "Habit Tracking", "High",
     "Captures recurring habit data used by the pattern-detection and productivity models.",
     [
      ("FR-4.1", "The system shall allow a user to define a habit and log its daily completion status."),
      ("FR-4.2", "The system shall calculate and display the current completion streak for each habit."),
      ("FR-4.3", "The system shall compute a habit completion rate and flag any habit below a 60% "
                  "completion threshold as \u201cat risk.\u201d"),
     ]),
    (5, "Fitness Activity Management", "Medium",
     "Captures workout data used by fitness goal forecasting and the Productivity Index.",
     [
      ("FR-5.1", "The system shall allow a user to log a fitness activity with type, duration, and calories burned."),
      ("FR-5.2", "The system shall compute a weekly fitness summary, including activity count and calorie trend."),
     ]),
    (6, "Goal Management", "High",
     "Tracks user-defined targets across every domain and their projected achievement.",
     [
      ("FR-6.1", "The system shall allow a user to create a goal with a name, category, target value, and target date."),
      ("FR-6.2", "The system shall track and display current progress toward each goal as a percentage."),
      ("FR-6.3", "The system shall classify each goal as On Track, At Risk, or Completed based on its "
                  "projected trajectory relative to its target date."),
     ]),
    (7, "Financial Forecasting Engine", "High",
     "Produces forward-looking financial projections; the system's core AI-powered outcome.",
     [
      ("FR-7.1", "The system shall generate a savings projection for 6-month, 1-year, and 3-year horizons "
                  "from historical financial data."),
      ("FR-7.2", "The system shall generate a category-level expense forecast for a user-specified number of months."),
      ("FR-7.3", "The system shall train and compare at least four forecasting algorithms and automatically "
                  "select the best-performing model for each forecasting task."),
      ("FR-7.4", "The system shall achieve a Mean Absolute Percentage Error of 15% or lower (i.e. at least "
                  "85% forecasting accuracy) on held-out financial data."),
      ("FR-7.5", "The system shall allow a user to simulate the effect of a hypothetical change in savings "
                  "rate on projected future savings."),
     ]),
    (8, "Study Performance Prediction", "Medium",
     "Forecasts academic outcomes and recommends a study plan to reach a target score.",
     [
      ("FR-8.1", "The system shall predict a user's expected academic performance score from historical study data."),
      ("FR-8.2", "The system shall train and compare at least three algorithms for study performance "
                  "prediction, automatically selecting the best-performing model, targeting an R\u00b2 of "
                  "0.75 or higher."),
      ("FR-8.3", "The system shall generate an optimal study plan given a target score and an exam date."),
     ]),
    (9, "Habit Analysis & Productivity Intelligence", "Medium",
     "Detects behavioral patterns and expresses overall discipline as a single composite score.",
     [
      ("FR-9.1", "The system shall detect behavioral patterns and anomalies in habit data using at least "
                  "two distinct clustering or anomaly-detection algorithms."),
      ("FR-9.2", "The system shall compute a composite Productivity Index, on a 0\u2013100 scale, from study, "
                  "habit, fitness, and financial-discipline data."),
      ("FR-9.3", "The system shall forecast the user's Productivity Index for the next 4 weeks."),
     ]),
    (10, "Digital Twin Engine", "High",
     "Maintains the continuously-updated behavioral model of the user that the Simulation Engine projects forward.",
     [
      ("FR-10.1", "The system shall maintain a per-user Digital Twin comprising eight state domains: "
                   "Financial, Study, Habit, Fitness, Goal, Productivity, Behavioral, and Risk."),
      ("FR-10.2", "The system shall update the relevant Digital Twin state domain within the same "
                   "processing cycle whenever a user adds, edits, or deletes a financial, study, habit, "
                   "fitness, or goal record."),
      ("FR-10.3", "The system shall persist versioned snapshots of the Digital Twin state, each with a "
                   "timestamp and the event that triggered it."),
      ("FR-10.4", "The system shall allow the current Digital Twin state and its history to be retrieved via the API."),
     ]),
    (11, "Simulation Engine", "High",
     "Answers \u2018what if\u2019 questions across nine categories of personal decisions.",
     [
      ("FR-11.1", "The system shall support at least nine categories of decision simulation: Financial, "
                   "Study, Career, Fitness, Lifestyle, Investment, Loan, Emergency Scenario, and Custom Scenario."),
      ("FR-11.2", "The system shall project each simulation across five comparison scenarios: Current Path, "
                   "Best Case, Expected Case, Worst Case, and Risk Scenario."),
      ("FR-11.3", "The system shall complete any single simulation request in 5 seconds or less."),
      ("FR-11.4", "The system shall allow a user to compare up to four simulation scenarios side by side."),
      ("FR-11.5", "The system shall calculate a risk score and risk level (Low/Medium/High) for each "
                   "simulated scenario, including a check for emergency-fund adequacy."),
      ("FR-11.6", "The system shall retain a history of a user's previous simulations for later retrieval."),
     ]),
    (12, "Recommendation Engine", "High",
     "Converts analysis into specific, prioritized, and explained next actions.",
     [
      ("FR-12.1", "The system shall generate personalized recommendations across financial, study, habit, "
                   "and fitness domains, triggered by rules evaluated against the user's Digital Twin state."),
      ("FR-12.2", "The system shall assign each recommendation a Confidence Score, computed by a "
                   "machine-learning model trained on historical recommendation-acceptance data."),
      ("FR-12.3", "The system shall assign each recommendation a Priority, an Estimated Time to complete, "
                   "a Difficulty level, and a multi-step Action Plan."),
      ("FR-12.4", "The system shall generate a natural-language Explanation for each recommendation using "
                   "a Large Language Model, referencing the user's specific data."),
      ("FR-12.5", "The system shall not present the same recommendation to a user more than once within a "
                   "7-day period."),
      ("FR-12.6", "The system shall allow a user to mark a recommendation as actioned or dismissed."),
     ]),
    (13, "Conversational AI Assistant", "High",
     "Provides a natural-language interface over all of the user's data and the system's analytical outputs.",
     [
      ("FR-13.1", "The system shall provide a natural-language chat interface allowing users to ask "
                   "questions about their financial, study, habit, and fitness data."),
      ("FR-13.2", "The assistant shall retrieve live data from the forecasting, simulation, analytics, and "
                   "recommendation services when answering a query, rather than relying solely on static "
                   "context."),
      ("FR-13.3", "The assistant shall retain conversational context for at least the previous 10 exchanges "
                   "within a session."),
      ("FR-13.4", "The system shall allow a user to request a plain-language explanation of any displayed "
                   "chart or simulation result."),
      ("FR-13.5", "The system shall generate a periodic (weekly or monthly) natural-language summary of "
                   "the user's overall progress."),
      ("FR-13.6", "The assistant shall decline to provide advice that facilitates a financially or "
                   "physically harmful decision and shall redirect the user appropriately."),
     ]),
    (14, "Dashboard & Visualization", "High",
     "The primary interactive surface consolidating every other feature into one view.",
     [
      ("FR-14.1", "The system shall present an interactive dashboard displaying key performance "
                   "indicators, forecast charts, productivity trends, and recommendations in one consolidated view."),
      ("FR-14.2", "The system shall allow a user to switch the analysis period (1 month/3 months/1 year/3 "
                   "years) and have all dashboard charts update accordingly."),
      ("FR-14.3", "The system shall allow a user to export a report \u2014 financial projections, goal "
                   "forecasts, study trends, and recommendations \u2014 as a PDF document."),
      ("FR-14.4", "The system shall provide search and filter controls on every data-listing view."),
     ]),
    (15, "Model Registry & Explainability", "Medium",
     "Makes model performance and reasoning transparent and auditable.",
     [
      ("FR-15.1", "The system shall record accuracy, RMSE, MAE, and \u2014 where the underlying task is "
                   "classification-shaped \u2014 precision and recall, for every trained model version."),
      ("FR-15.2", "The system shall compute and expose feature-importance data for every gradient-boosted model."),
      ("FR-15.3", "The system shall make current model performance metrics available to Administrator "
                   "users through a dedicated view."),
     ]),
    (16, "Activity Logging", "Low",
     "Provides an auditable history of user actions across the system.",
     [
      ("FR-16.1", "The system shall log every significant user action \u2014 create, update, and delete "
                   "operations across all domains, and chat interactions \u2014 with a timestamp, for "
                   "display in an Activity Timeline."),
     ]),
]

# ---------------------------------------------------------------------------
# EXTERNAL INTERFACES
# ---------------------------------------------------------------------------
UI_REQS = [
    "The user interface shall be delivered as a themeable (light/dark) responsive web application built "
    "with Streamlit, readable on desktop and tablet screen widths.",
    "Every primary page shall include, at minimum: a header, key-performance-indicator cards, one or more "
    "charts, an AI Insight panel, a Recommendation panel (where applicable), a filter/search control, and "
    "an activity timeline entry point.",
    "Data-heavy listings (financial records, study sessions, simulation history) shall be rendered in a "
    "sortable, filterable grid supporting inline edit and delete.",
    "All destructive actions (delete) shall require an explicit confirmation step.",
]

HARDWARE_REQS = [
    "No dedicated client hardware is required beyond a device capable of running a modern web browser.",
    "Server-side, the Machine Learning layer shall run on standard CPU compute; no GPU is required for "
    "the model sizes specified in this document.",
]

SOFTWARE_INTERFACES = [
    ("OpenAI API or Google Gemini API", "HTTPS/JSON", "Powers the Conversational AI Assistant and "
     "LLM-generated recommendation explanations. The system shall function with rule-based fallbacks if "
     "this interface is unavailable."),
    ("PostgreSQL 15", "SQL over TCP (via SQLAlchemy)", "System of record for all persisted data."),
    ("Redis 7", "RESP protocol", "Caches analytics/forecast results and backs API rate limiting."),
    ("SMTP / Email provider (optional, future)", "SMTP", "Reserved for future periodic-summary email "
     "delivery; not required for Version 2.0."),
]

COMM_REQS = [
    "All client-server communication shall use HTTPS.",
    "The API shall exchange data exclusively in JSON, following the request/response schemas documented "
    "in the OpenAPI (Swagger) specification generated directly from the codebase.",
    "The Conversational AI response shall support token-level streaming to the client for perceived "
    "responsiveness.",
]

# ---------------------------------------------------------------------------
# NON-FUNCTIONAL REQUIREMENTS
# ---------------------------------------------------------------------------
NFR_PERFORMANCE = [
    ("NFR-1", "The 95th-percentile response time for a simple CRUD API request shall not exceed 300 milliseconds."),
    ("NFR-2", "The dashboard shall fully load within 2 seconds under normal load."),
    ("NFR-3", "Any machine-learning-backed forecast endpoint shall respond within 2 seconds."),
    ("NFR-4", "Any simulation request shall complete within 5 seconds, including under a load of 10 "
               "concurrent simulation requests."),
]
NFR_SECURITY = [
    ("NFR-5", "All API endpoints except registration and login shall require a valid JWT bearer token."),
    ("NFR-6", "All passwords shall be hashed using bcrypt with an appropriate work factor; plaintext "
               "passwords shall never be stored or logged."),
    ("NFR-7", "The system shall enforce role-based access control distinguishing Standard User and "
               "Administrator privileges."),
    ("NFR-8", "The system shall validate and sanitize all user input to prevent SQL injection and "
               "cross-site scripting."),
    ("NFR-9", "The system shall restrict cross-origin requests to an explicitly configured allow-list of "
               "origins."),
    ("NFR-10", "The system shall document its Cross-Site Request Forgery exposure and mitigations given "
                "its token-based (non-cookie) authentication model."),
    ("NFR-11", "The system shall never return a user's password hash, or any other credential, in any API response."),
]
NFR_RELIABILITY = [
    ("NFR-12", "The system shall return a consistent, structured error response for any unhandled "
                "exception, without exposing internal stack traces to the client."),
    ("NFR-13", "The system shall gracefully degrade to rule-based recommendation text if the third-party "
                "LLM provider is unavailable."),
    ("NFR-14", "The system shall maintain data integrity through foreign-key constraints and transactional writes."),
]
NFR_USABILITY = [
    ("NFR-15", "A first-time user shall be able to complete registration and log their first financial "
                "record without external guidance."),
    ("NFR-16", "The system shall achieve a System Usability Scale (SUS) score of 85 or higher during "
                "user-acceptance testing."),
    ("NFR-17", "The system shall support both a light and a dark visual theme."),
]
NFR_MAINTAIN = [
    ("NFR-18", "The backend codebase shall maintain automated test coverage of 90% or higher."),
    ("NFR-19", "The system shall be fully deployable via a single Docker Compose command on any "
                "Docker-compatible host."),
    ("NFR-20", "The codebase shall follow a layered architecture with documented separation of concerns, "
                "to support independent modification of each layer."),
]
NFR_SCALABILITY = [
    ("NFR-21", "The system shall support at least 10 concurrent simulation requests without breaching the "
                "performance targets in NFR-1 through NFR-4."),
    ("NFR-22", "The database connection layer shall use connection pooling to support horizontal scaling "
                "of the API layer."),
]

OTHER_LEGAL = (
    "Financial and personal data handled by this system is sensitive. The system shall store such data "
    "securely (encrypted at rest at the infrastructure level and in transit via HTTPS), shall allow a user "
    "to request deletion of their account and associated data, and shall not share user data with any "
    "third party beyond the minimum context sent to the configured LLM provider to answer a specific, "
    "in-flight query. The system does not constitute licensed financial or medical advice, and this "
    "limitation shall be disclosed to the user within the product."
)
OTHER_QA = (
    "Unit, integration, API, load, and user-acceptance testing shall be performed at each project "
    "milestone. Automated tests shall cover authentication, data isolation between users, CRUD "
    "correctness, ML prediction ranges, simulation performance, and recommendation personalization, as "
    "detailed in the project's Testing Guide."
)

GLOSSARY = [
    ("Digital Twin", "A continuously-updated, per-user data structure comprising eight state domains "
     "(Financial, Study, Habit, Fitness, Goal, Productivity, Behavioral, Risk) that mirrors the user's "
     "real-life situation and serves as the baseline for every simulation."),
    ("Scenario Comparison", "The side-by-side projection of a decision across five outcomes: Current "
     "Path, Best Case, Expected Case, Worst Case, and Risk Scenario."),
    ("Confidence Score", "A 0\u2013100% machine-learning-predicted likelihood that a specific user will act "
     "on a specific recommendation, distinct from the recommendation's Priority or Impact."),
    ("Champion/Challenger Selection", "The process of training multiple candidate algorithms on identical "
     "data and automatically promoting the best-scoring one to production use."),
    ("MAPE", "Mean Absolute Percentage Error \u2014 the accuracy metric used for financial forecasting; a "
     "MAPE of 15% or lower is treated as \u226585% accuracy."),
    ("SUS", "System Usability Scale \u2014 a standardized 10-question usability questionnaire producing a "
     "0\u2013100 score."),
    ("RBAC", "Role-Based Access Control \u2014 restricting system functionality based on a user's assigned role."),
    ("JWT", "JSON Web Token \u2014 a signed, stateless token used to authenticate API requests."),
    ("LLM", "Large Language Model \u2014 e.g. OpenAI GPT-4o or Google Gemini, used for natural-language "
     "explanation and conversation."),
]

USE_CASES = [
    ("UC-1", "Register and build a profile", "Standard User", "A new user creates an account and enters "
     "initial profile information.", "FR-1.1\u20131.5"),
    ("UC-2", "Log daily data", "Standard User", "A user records financial transactions, study sessions, "
     "habit completions, and fitness activities.", "FR-2, FR-3, FR-4, FR-5"),
    ("UC-3", "View financial forecast", "Standard User", "A user views a 6-month/1-year/3-year savings "
     "projection generated by the auto-selected forecasting model.", "FR-7"),
    ("UC-4", "Run a decision simulation", "Standard User", "A user selects a decision (e.g. increase "
     "savings rate) and receives a 5-way scenario comparison within 5 seconds.", "FR-11"),
    ("UC-5", "Receive and act on a recommendation", "Standard User", "The system surfaces a "
     "confidence-scored, explained recommendation; the user marks it actioned.", "FR-12"),
    ("UC-6", "Ask the AI assistant a question", "Standard User", "A user asks a natural-language question "
     "and receives a data-grounded, explained answer.", "FR-13"),
    ("UC-7", "Export a report", "Standard User", "A user exports their current forecasts and "
     "recommendations as a PDF.", "FR-14.3"),
    ("UC-8", "Review model performance", "Administrator", "An administrator reviews accuracy, error and "
     "feature-importance metrics for every active model.", "FR-15"),
]

TBD = [
    "Multi-language (i18n) support for the user interface.",
    "Native iOS/Android client applications.",
    "Direct bank-feed / brokerage account import (Plaid-style integration).",
    "Email/SMS delivery of periodic summaries (the summary content itself is in scope; the delivery "
    "channel is future scope).",
]