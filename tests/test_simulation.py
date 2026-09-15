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

def test_multidomain_multihorizon_simulations():
    test_email = "domains_test_user@example.com"
    test_password = "password123Secure"
    client.post(
        "/api/auth/register",
        json={"email": test_email, "password": test_password, "name": "Domains Tester"},
    )
    login_res = client.post("/api/auth/login", data={"username": test_email, "password": test_password})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    domains = ["Financial", "Forecasting", "Academic", "Lifestyle"]
    horizons = ["7_days", "1_month", "3_months", "1_year", "2_years"]

    for domain in domains:
        for horizon in horizons:
            req = {
                "decision_type": domain,
                "input_parameters": {
                    "time_horizon": horizon,
                    "impact": 10,
                    "savings_delta": 300,
                    "spending_shift_pct": -10,
                    "study_hours_delta": 2.0,
                    "sleep_delta": 1.0,
                },
            }
            res = client.post("/api/simulations", json=req, headers=headers)
            assert res.status_code == 201, f"Failed for {domain} on {horizon}: {res.text}"
            data = res.json()
            assert data["decision_type"] == domain
            assert "Current Path" in data["predicted_outcome"]
            assert "Expected Case" in data["predicted_outcome"]
            
            sim_res = data.get("simulation_result")
            assert sim_res is not None
            assert sim_res.get("selected_horizon") == horizon
            assert "horizon_impacts" in sim_res
            for h in horizons:
                assert h in sim_res["horizon_impacts"]

