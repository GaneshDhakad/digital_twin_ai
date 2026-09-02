from pathlib import Path
import time
from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import engine, Base, SessionLocal
from app.api.routes.auth import router as auth_router
from app.api.routes.users import router as users_router
from app.api.routes.financial import router as financial_router
from app.api.routes.study import router as study_router
from app.api.routes.habits import router as habits_router
from app.api.routes.fitness import router as fitness_router
from app.api.routes.goals import router as goals_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.simulation import router as simulation_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.ml import router as ml_router
from app.services.analytics_service import log_activity

# Automatically initialize database schema tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Digital Twin AI",
    version="2.0.0",
    description="Digital Twin AI - Personal Life Simulation & Decision Assistant Backend API",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def bg_log_activity(user_id: UUID | None, activity_type: str, endpoint: str, method: str, response_time_ms: float):
    db: Session = SessionLocal()
    try:
        log_activity(
            db=db,
            user_id=user_id,
            activity_type=activity_type,
            endpoint=endpoint,
            method=method,
            response_time_ms=response_time_ms,
        )
    except Exception:
        pass
    finally:
        db.close()


@app.middleware("http")
async def analytics_logging_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000.0

    # Auto-log non-static API calls
    path = request.url.path
    if path.startswith("/api"):
        method = request.method
        # Background logging task
        bg_log_activity(
            user_id=None,
            activity_type=f"API_REQUEST_{method}",
            endpoint=path,
            method=method,
            response_time_ms=round(duration_ms, 2),
        )

    return response


# Register API Routers under /api
api_prefix = "/api"
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(financial_router, prefix=api_prefix)
app.include_router(study_router, prefix=api_prefix)
app.include_router(habits_router, prefix=api_prefix)
app.include_router(fitness_router, prefix=api_prefix)
app.include_router(goals_router, prefix=api_prefix)
app.include_router(analytics_router, prefix=api_prefix)
app.include_router(simulation_router, prefix=api_prefix)
app.include_router(recommendations_router, prefix=api_prefix)
app.include_router(ml_router, prefix=api_prefix)


ROOT_DIR = Path(__file__).resolve().parent.parent
WEBSITE_DIR = ROOT_DIR / "website"


@app.get("/")
def root():
    index_file = WEBSITE_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "title": "Digital Twin AI API",
        "version": "2.0.0",
        "status": "online",
        "documentation": "/docs"
    }


@app.get("/styles.css")
def get_styles():
    css_file = WEBSITE_DIR / "styles.css"
    if css_file.exists():
        return FileResponse(css_file, media_type="text/css")
    return {"error": "not found"}


@app.get("/script.js")
def get_script():
    js_file = WEBSITE_DIR / "script.js"
    if js_file.exists():
        return FileResponse(js_file, media_type="application/javascript")
    return {"error": "not found"}


@app.get("/health")
def health():
    return {"status": "ok"}