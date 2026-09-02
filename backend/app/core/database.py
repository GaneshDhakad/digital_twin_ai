import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.core.config import settings

logger = logging.getLogger("uvicorn.error")

def create_db_engine():
    db_url = settings.DATABASE_URL
    
    # SQLite configuration handling
    if "sqlite" in db_url:
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False
        )
    
    # Try creating postgresql engine
    try:
        engine = create_engine(db_url, pool_pre_ping=True, echo=False)
        # Test connection
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        logger.warning(f"Could not connect to PostgreSQL ({e}). Falling back to local SQLite database.")
        sqlite_fallback = "sqlite:///./digital_twin_fallback.db"
        return create_engine(
            sqlite_fallback,
            connect_args={"check_same_thread": False},
            echo=False
        )

engine = create_db_engine()

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()