# Digital Twin AI (TWIN.OS)
**Personal Life Simulation & Decision Assistant**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.36-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io/)
[![Tests](https://img.shields.io/badge/Tests-134%20passed-10B981?style=for-the-badge)](docs/4_tests.md)

**Digital Twin AI (TWIN.OS)** is a full-stack AI-powered personal life simulation platform. It builds a living **Digital Twin** of your financial, academic, habit, fitness, and goal life, and uses machine learning and Google Gemini to forecast outcomes, simulate decisions, and deliver personalized AI-grounded advice.

---

## 🌟 Core Features

| Feature | Description | Status |
|---|---|---|
| Digital Twin Engine | Aggregates 5 domain states + ML predictions into a live user model | ✅ Implemented |
| Financial Analysis | Income/expense tracking, savings rate, category breakdown | ✅ Implemented |
| Study Tracking | Focus hours, completion rate, subject analytics | ✅ Implemented |
| Habit Tracking | Completion streaks, at-risk habit detection | ✅ Implemented |
| Fitness Tracking | Workout logging, calorie tracking, intensity levels | ✅ Implemented |
| Goal Management | Target tracking, on-track / at-risk status | ✅ Implemented |
| Academic ML | GradientBoostingRegressor, R²=0.876, exam score prediction | ✅ Active |
| Lifestyle ML | GradientBoostingClassifier, F1=0.977, sleep disorder risk | ✅ Active |
| Financial ML | RandomForestRegressor, disposable income prediction | ✅ Active |
| Forecasting ML | XGBRegressor, RMSE=1207, next-month spending forecast | ✅ Active |
| Decision Simulator | 5-scenario, 5-horizon Monte Carlo simulations | ✅ Implemented |
| AI Chat (Gemini) | Multi-turn conversation grounded in your Digital Twin data | ✅ Implemented |

---

## 🚀 Quick Start

**Requirements:** Python 3.11+, PostgreSQL 15+ (or SQLite for dev)

### 1. Install Dependencies
```bash
python -m venv venv
venv\Scripts\activate         # Windows
# source venv/bin/activate    # macOS/Linux

pip install -r requirements.txt
```

### 2. Configure Environment
Copy `.env.example` → `.env` and fill in:
```
DATABASE_URL=sqlite:///./digital_twin.db   # dev (SQLite)
# DATABASE_URL=postgresql://user:pass@host:5432/digital_twin_ai  # production
SECRET_KEY=your-strong-secret-key
GEMINI_API_KEY=your-gemini-api-key         # required for AI chat
```

### 3. Launch Backend
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```
- API: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health: [http://localhost:8000/health](http://localhost:8000/health)

### 4. Launch Frontend
```bash
streamlit run frontend/app.py
```
- Dashboard: [http://localhost:8501](http://localhost:8501)

---

## 🧪 Running Tests

```powershell
# Windows
$env:PYTHONPATH="." ; venv\Scripts\python.exe -m pytest tests/ -v

# macOS/Linux
PYTHONPATH=. pytest tests/ -v
```

**Latest result: 134 passed, 0 failed ✅**

---

## 📁 Project Structure

```
digital_twin_ai/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   └── app/
│       ├── api/routes/            # 12 API routers
│       ├── services/              # Domain logic + ML services + AI
│       ├── models/                # 22 SQLAlchemy ORM models
│       ├── schemas/               # Pydantic schemas
│       ├── core/                  # Config, security, database, dependencies
│       └── ml_models/             # Deployed model artifacts (.joblib)
├── frontend/
│   ├── app.py                     # Streamlit entry + navigation
│   └── views/                     # 9 page modules
├── ml/
│   └── reports/                   # Training reports and ORM audit
├── tests/                         # 12 test modules, 134 tests
└── docs/
    ├── 1_system_documentation.md  # Full SRS and API reference
    ├── 2_architecture.md          # Architecture and DB design
    ├── 3_bugs_and_fixes.md        # Bug tracking and resolutions
    ├── 4_tests.md                 # Testing strategy and results
    └── 5_accuracy.md              # ML model metrics and evaluation
```

---

## 📖 Documentation

| Document | Contents |
|---|---|
| [System Documentation](docs/1_system_documentation.md) | API endpoints, modules, NFRs, known limitations |
| [Architecture](docs/2_architecture.md) | Layers, DB schema, auth flow, ML/AI integration, security |
| [Bugs & Fixes](docs/3_bugs_and_fixes.md) | ORM issues found & fixed, open warnings |
| [Tests](docs/4_tests.md) | Test results (134 passed), coverage areas, run instructions |
| [Accuracy](docs/5_accuracy.md) | Real ML metrics from deployed models |

---

## 🔒 Security

- Passwords hashed with **bcrypt**
- Auth via **JWT HS256** (24h expiry), `sub=email`
- All data queries scoped by **user_id from JWT** (never from request body)
- RBAC: `user` vs `admin` roles enforced via FastAPI `Depends`
- No secrets, API keys, or stack traces exposed in API responses

> ⚠️ **CORS is currently `allow_origins=["*"]`** — must be restricted before any production deployment.

---

*Copyright © 2026 Digital Twin AI Team. Python 3.11 · FastAPI · PostgreSQL 15 · Streamlit · Google Gemini*