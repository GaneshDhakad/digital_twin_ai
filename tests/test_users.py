import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def get_authenticated_headers(email: str = "user_profile_test@example.com"):
    # Register user
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123Secure",
            "name": "Profile Tester",
            "age": 24,
            "occupation": "Engineer",
        },
    )
    # Login
    res = client.post(
        "/api/auth/login",
        data={"username": email, "password": "password123Secure"},
    )
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_user_profile_crud():
    headers = get_authenticated_headers()

    # Get Profile
    p_res = client.get("/api/users/profile", headers=headers)
    assert p_res.status_code == 200
    assert p_res.json()["name"] == "Profile Tester"

    # Update Profile
    u_res = client.put(
        "/api/users/profile",
        headers=headers,
        json={"name": "Updated Profile Tester", "age": 26, "occupation": "Senior Engineer"},
    )
    assert u_res.status_code == 200
    assert u_res.json()["name"] == "Updated Profile Tester"
    assert u_res.json()["age"] == 26

    # Summary
    s_res = client.get("/api/users/summary", headers=headers)
    assert s_res.status_code == 200
    assert "active_goals" in s_res.json()

    # Soft Delete Profile
    d_res = client.delete("/api/users/profile", headers=headers)
    assert d_res.status_code == 200

    # Unauthorized access after soft delete
    me_res = client.get("/api/users/profile", headers=headers)
    assert me_res.status_code in [401, 403]
