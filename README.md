# Digital Twin AI (TWIN.OS) — Personal Life Simulation & Decision Assistant

[![Milestone 1](https://img.shields.io/badge/Milestone_1-Certified_Complete-10B981?style=for-the-badge)](docs/MILESTONE_1_REPORT.md)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PostgreSQL 15](https://img.shields.io/badge/PostgreSQL-15-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Streamlit 1.36](https://img.shields.io/badge/Streamlit-1.36-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)

**Digital Twin AI (TWIN.OS)** is a state-of-the-art personal life simulation and decision engineering platform. By unifying 8 life domains into a single normalized PostgreSQL 15 database and applying machine learning forecasting, anomaly detection, and 5-way Monte-Carlo decision simulations, TWIN.OS enables you to model life decisions with mathematical clarity.

---

## 🌟 Key Architectural Features (`architecture.py`)

- **8 Synchronized Life Domains**:
  - Financial Ledger & Net Worth Forecasting
  - Study & Academic Cognitive Intelligence
  - Habit Consistency Streaks & Anomaly Detection
  - Fitness & Caloric Modeling
  - Real-time Goal Milestone Trajectories
  - 6-Month Risk & Emergency Buffer
  - Behavioral Telemetry & Activity Timeline
  - 9-Category Decision Simulation Suite
- **Champion/Challenger Model Registry**:
  - Compares Prophet, ARIMA, XGBoost, and LightGBM for financial regression.
  - Compares Random Forest, XGBoost, and CatBoost for study and habit prediction.
  - Automatically audits Root Mean Square Error (RMSE), MAE, and R², elevating the best model to Champion status.
- **5-Way Monte-Carlo Decision Simulator**:
  - Computes Current Path, Best Case (95th percentile), Expected Path, Worst Case (5th percentile), and Risk Assessment across 9 decision categories.
- **Explainable Hybrid Recommendation Engine**:
  - Combines deterministic rule triggers with ML confidence scoring and LLM narration (OpenAI GPT-4o / Google Gemini).

---

## 🎨 Dual Presentation Layers

### 1. Apple/Stripe/Linear-Inspired Light-Themed Showcase Website (`website/`)
- A standalone, award-winning marketing and showcase website mounted at the root of the FastAPI backend (`http://localhost:8000/`).
- Features **all 10 requested sections**: Hero with interactive mockup, Architecture & 8 Domains, Animated Counters, Interactive Product Showcase Tabs, Operator Testimonials, SaaS Pricing Tiers, Accordion FAQ, Blog Preview, CTA Banner, and Multi-Column Footer.
- Styled with vanilla CSS (`styles.css`) and JavaScript (`script.js`) using `#FFFFFF` background, `#F8FAFC` surfaces, `#2563EB` accents, `#4F46E5 -> #3B82F6 -> #06B6D4` gradients, 16–24px rounded corners, and soft glassmorphic cards.

### 2. Streamlit 1.36 Multipage Application (`frontend/`)
- Interactive application interface powered by Streamlit 1.36's native `st.Page` and `st.navigation`.
- **Zero Sidebar Clutter on Entry**: Unauthenticated users see only a clean Login & Registration interface. Upon authentication, users are programmatically routed to the Executive Dashboard with categorized navigation (`Overview`, `Life Modules`, `AI Intelligence`).

---

## 🚀 Quick Start & Local Setup

### 1. Requirements & Virtual Environment
Ensure Python 3.11+ and PostgreSQL 15+ are installed.
```bash
# Create and activate virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Launch FastAPI Backend Server
Start the backend server (automatically mounts the showcase website at `/` and API at `/api`):
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Showcase Website**: [http://localhost:8000/](http://localhost:8000/)
- **Interactive API Swagger Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc Specification**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **System Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

### 3. Launch Streamlit Frontend Application
In a separate terminal, launch the Streamlit multipage application:
```bash
streamlit run frontend/app.py --server.port 8501
```
- **Streamlit Application**: [http://localhost:8501/](http://localhost:8501/)

---

## 📁 Project Structure

```
digital_twin_ai/
├── architecture.py                 # Full System Architecture Document (SAD v2.0)
├── srs.py                          # Software Requirements Specification (SRS v2.0)
├── website/                        # Apple/Stripe/Linear Light-Themed Showcase Website
│   ├── index.html                  # 10 semantic sections (Hero, Features, Showcase, FAQ, Pricing, etc.)
│   ├── styles.css                  # Light-themed design system, glassmorphism, 16-24px radii
│   └── script.js                   # Scroll animations, interactive tabs, counter animations, FAQ accordion
├── backend/                        # FastAPI Backend Engine
│   ├── main.py                     # App root, CORS, middleware, static mount (GET / -> website)
│   ├── app/
│   │   ├── api/routes/             # Auth, Users, Financial, Study, Habits, Fitness, Goals, Simulation, Recommendations, Analytics
│   │   ├── services/               # Domain business logic layer
│   │   ├── models/                 # SQLAlchemy ORM models (10 tables)
│   │   ├── schemas/                # Pydantic validation schemas
│   │   └── core/                   # Security (JWT/bcrypt), database engine, config
│   └── tests/                      # Pytest automated verification suite
├── frontend/                       # Streamlit 1.36 Multipage UI
│   ├── app.py                      # Multi-page router with st.Page & st.navigation
│   ├── views/                      # Dedicated view modules (login, profile, dashboard, financial, etc.)
│   ├── components/                 # Reusable UI components (header, KPI card, AI insight panel)
│   └── theme/                      # Light-themed design tokens (16-24px radii, glassmorphic cards)
├── docs/                           # Documentation & Milestone Reports
│   ├── MILESTONE_1_REPORT.md       # Certified Milestone 1 Completion Report
│   └── ARCHITECTURE.md             # Architecture reference summary
└── docker/                         # Docker & container orchestration configurations
```

---

## 🧪 Testing & Verification

Run the full automated test suite using `pytest`:
```bash
pytest backend/tests/ -v
```

All 39+ unit and integration tests pass cleanly across authentication, financial ledger, study intelligence, habit streaks, fitness modeling, simulation engine, and API health checks.

---

## 📜 Documentation & Reports
- **Milestone 1 Formal Completion Report**: See [`docs/MILESTONE_1_REPORT.md`](docs/MILESTONE_1_REPORT.md)
- **System Architecture Document**: See [`architecture.py`](architecture.py)
- **Software Requirements Specification**: See [`srs.py`](srs.py)

---

*Copyright © 2026 Digital Twin AI Team. Built with Python 3.11, FastAPI, PostgreSQL 15, and Streamlit.*