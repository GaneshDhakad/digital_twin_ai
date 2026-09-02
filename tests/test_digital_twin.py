import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_get_digital_twin_state():
    # Register and login a unique user
    test_email = "dt_test_user@example.com"
    test_password = "password123Secure"
    
    # Ignore if already exists
    client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "DT User",
        },
    )
    
    # Login
    login_res = client.post("/api/auth/login", data={"username": test_email, "password": test_password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get digital twin
    dt_res = client.get("/api/ml/digital-twin", headers=headers)
    assert dt_res.status_code == 200
    dt = dt_res.json()
    assert "user_id" in dt
    assert dt["overall_state"] in ["healthy", "stable", "improving", "declining", "at-risk", "critical"]
    assert "financial" in dt
    assert "academic" in dt
    assert "fitness" in dt
    assert "lifestyle_habits" in dt
    assert "goals" in dt
    assert "ml_predictions" in dt
