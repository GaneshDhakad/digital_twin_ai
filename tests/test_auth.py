import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_user_registration_and_login():
    test_email = "test_user_day1_9@example.com"
    test_password = "password123Secure"

    # Register
    reg_response = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Test User",
            "age": 25,
            "occupation": "Developer",
        },
    )
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert "access_token" in reg_data
    assert reg_data["user"]["email"] == test_email

    # Duplicate registration should fail
    dup_response = client.post(
        "/api/auth/register",
        json={
            "email": test_email,
            "password": test_password,
            "name": "Test User Dup",
        },
    )
    assert dup_response.status_code == 400

    # Login via OAuth2 Form
    login_response = client.post(
        "/api/auth/login",
        data={
            "username": test_email,
            "password": test_password,
        },
    )
    assert login_response.status_code == 200
    token_data = login_response.json()
    assert "access_token" in token_data

    # Access protected route /api/auth/me
    token = token_data["access_token"]
    me_response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200
    assert me_response.json()["email"] == test_email


def test_invalid_login():
    response = client.post(
        "/api/auth/login",
        data={
            "username": "nonexistent@example.com",
            "password": "wrongpassword",
        },
    )
    assert response.status_code == 401
