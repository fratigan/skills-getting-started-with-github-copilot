import pytest
from fastapi.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset participants to a known state before each test."""
    original = {name: list(data["participants"]) for name, data in activities.items()}
    yield
    for name, participants in original.items():
        activities[name]["participants"] = participants


@pytest.fixture
def client():
    return TestClient(app)


# --- GET /activities ---

def test_get_activities_returns_all(client):
    # Arrange: no setup needed, data is preloaded

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert len(response.json()) == 9


def test_get_activities_structure(client):
    # Arrange: no setup needed

    # Act
    response = client.get("/activities")

    # Assert
    activity = response.json()["Chess Club"]
    assert "description" in activity
    assert "schedule" in activity
    assert "max_participants" in activity
    assert "participants" in activity


# --- POST /activities/{activity_name}/signup ---

def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email in activities[activity_name]["participants"]


def test_signup_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "x@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_already_registered(client):
    # Arrange
    activity_name = "Chess Club"
    email = "dup@mergington.edu"
    client.post(f"/activities/{activity_name}/signup?email={email}")

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up"


def test_signup_activity_full(client):
    # Arrange: fill Art Club (max 18, starts with 1 participant)
    activity_name = "Art Club"
    for i in range(17):
        client.post(f"/activities/{activity_name}/signup?email=student{i}@mergington.edu")

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email=overflow@mergington.edu")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


# --- DELETE /activities/{activity_name}/unregister ---

def test_unregister_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 200
    assert email in response.json()["message"]
    assert email not in activities[activity_name]["participants"]


def test_unregister_unknown_activity(client):
    # Arrange
    activity_name = "Unknown Activity"
    email = "x@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_not_signed_up(client):
    # Arrange
    activity_name = "Chess Club"
    email = "nobody@mergington.edu"

    # Act
    response = client.delete(f"/activities/{activity_name}/unregister?email={email}")

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"
