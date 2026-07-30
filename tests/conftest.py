import os
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_path = str(Path(__file__).resolve().parents[1] / "backend")
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Set isolated SQLite database URL for tests
os.environ["DATABASE_URL"] = "sqlite:///./test_digital_twin.db"

import pytest
from app.core.database import engine, Base

@pytest.fixture(autouse=True, scope="session")
def setup_test_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
