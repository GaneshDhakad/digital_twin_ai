import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_run_simulation():
    # Register and login a unique user
    test_email = "sim_test_user@example.com"
    test_password = "password123Secure"
    
    # Ignore if already exists
    client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Sim User",
        },
    )
    
    # Login
    login_res = client.post("/api/auth/login", data={"username": test_email, "password": test_password})
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Financial Simulation
    req = {
        "decision_type": "Financial",
        "input_parameters": {"impact": 500, "extra_expense": 500}
    }
    res = client.post("/api/simulations", json=req, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["decision_type"] == "Financial"
    assert "Current Path" in data["predicted_outcome"]
    assert "Best Case" in data["predicted_outcome"]
    assert "Expected Case" in data["predicted_outcome"]
    assert "Worst Case" in data["predicted_outcome"]
    assert "Risk Scenario" in data["predicted_outcome"]
    
    sim_id = data["simulation_id"]
    
    # Get simulations
    res = client.get("/api/simulations", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) > 0
    
    # Get specific
    res = client.get(f"/api/simulations/{sim_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["simulation_id"] == sim_id
    
    # Delete
    res = client.delete(f"/api/simulations/{sim_id}", headers=headers)
    assert res.status_code == 200
