import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def get_headers(email: str = "domain_test_user@example.com"):
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "password123Secure",
            "name": "Domain Tester",
        },
    )
    res = client.post(
        "/api/auth/login",
        data={"username": email, "password": "password123Secure"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_study_api():
    headers = get_headers("study_test@example.com")

    # Post Study Session
    s_res = client.post(
        "/api/study/activities",
        headers=headers,
        json={
            "subject": "Deep Learning",
            "study_hours": 3.5,
            "performance_score": 90.0,
            "task_completion_rate": 95.0,
        },
    )
    assert s_res.status_code == 201
    assert s_res.json()["subject"] == "Deep Learning"

    # Get Summary
    sum_res = client.get("/api/study/summary", headers=headers)
    assert sum_res.status_code == 200
    assert sum_res.json()["total_hours"] == 3.5


def test_habits_api():
    headers = get_headers("habits_test@example.com")

    # Log Habit
    h_res = client.post(
        "/api/habits",
        headers=headers,
        json={
            "habit_name": "Morning Yoga",
            "status": "completed",
            "impact_level": "High",
        },
    )
    assert h_res.status_code == 201

    # Analytics
    a_res = client.get("/api/habits/analytics", headers=headers)
    assert a_res.status_code == 200
    assert a_res.json()["current_streak"] == 1


def test_fitness_api():
    headers = get_headers("fitness_test@example.com")

    # Log Workout
    f_res = client.post(
        "/api/fitness/activities",
        headers=headers,
        json={
            "activity_type": "Running",
            "duration": 45.0,
            "calories_burned": 420.0,
        },
    )
    assert f_res.status_code == 201

    # Summary
    s_res = client.get("/api/fitness/summary", headers=headers)
    assert s_res.status_code == 200
    assert s_res.json()["weekly_activity_count"] == 1


def test_goals_api():
    headers = get_headers("goals_test@example.com")

    # Create Goal
    g_res = client.post(
        "/api/goals",
        headers=headers,
        json={
            "goal_name": "Emergency Fund",
            "category": "Financial",
            "target_value": 10000.0,
            "target_date": "2026-12-31T00:00:00",
        },
    )
    assert g_res.status_code == 201
    goal_id = g_res.json()["goal_id"]

    # Update Progress
    p_res = client.put(
        f"/api/goals/{goal_id}/progress",
        headers=headers,
        json={"current_progress": 7500.0},
    )
    assert p_res.status_code == 200
    assert p_res.json()["progress_percentage"] == 75.0

    # Goals Summary
    s_res = client.get("/api/goals/summary", headers=headers)
    assert s_res.status_code == 200
    assert s_res.json()["on_track_count"] == 1


def test_analytics_log_api():
    headers = get_headers("analytics_test@example.com")
    a_res = client.get("/api/analytics/activity-log", headers=headers)
    assert a_res.status_code == 200
