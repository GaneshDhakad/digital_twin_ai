import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def get_auth_headers(email: str = "fin_test_user@example.com"):
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123Secure",
            "name": "Finance Tester",
        },
    )
    res = client.post(
        "/api/auth/login",
        data={"username": email, "password": "password123Secure"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_financial_records_and_summary():
    headers = get_auth_headers()

    # Log Income Record
    inc_res = client.post(
        "/api/financial/records",
        headers=headers,
        json={
            "type": "income",
            "amount": 5000.0,
            "category": "Salary",
            "description": "Monthly Paycheck",
            "recurring_frequency": "Monthly",
        },
    )
    assert inc_res.status_code == 201
    assert inc_res.json()["income"] == 5000.0
    assert inc_res.json()["savings"] == 5000.0

    # Log Expense Record
    exp_res = client.post(
        "/api/financial/records",
        headers=headers,
        json={
            "type": "expense",
            "amount": 1200.0,
            "category": "Housing",
            "description": "Apartment Rent",
            "recurring_frequency": "Monthly",
        },
    )
    assert exp_res.status_code == 201
    assert exp_res.json()["expenses"] == 1200.0

    # Get Records List
    list_res = client.get("/api/financial/records", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 2

    # Get Summary
    sum_res = client.get("/api/financial/summary", headers=headers)
    assert sum_res.status_code == 200
    summary = sum_res.json()
    assert summary["total_income"] == 5000.0
    assert summary["total_expenses"] == 1200.0
    assert summary["net_savings"] == 3800.0
    assert summary["savings_rate"] == 76.0

    # Delete Record
    rec_id = exp_res.json()["record_id"]
    del_res = client.delete(f"/api/financial/records/{rec_id}", headers=headers)
    assert del_res.status_code == 200
