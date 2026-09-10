"""Shared pytest fixtures: a FastAPI TestClient and cleanup of test data."""
import pytest
from fastapi.testclient import TestClient

from app.database.mongodb import (
    assessments_collection, athletes_collection, predictions_collection,
    shap_explanations_collection, users_collection,
)
from app.main import app


@pytest.fixture(scope="session")
def client():
    return TestClient(app)


@pytest.fixture(autouse=True, scope="session")
def cleanup_test_data():
    yield
    users_collection.delete_many({"username": {"$regex": "^pytest_"}})
    athletes_collection.delete_many({"athlete_id": {"$regex": "^PYTEST-"}})
    athletes_collection.delete_many({"name": "Auto ID Athlete"})
    assessments_collection.delete_many({"athlete_id": {"$regex": "^PYTEST-"}})
    predictions_collection.delete_many({"athlete_id": {"$regex": "^PYTEST-"}})
    shap_explanations_collection.delete_many({})


@pytest.fixture(scope="session")
def auth_token(client):
    username = "pytest_researcher"
    client.post("/api/auth/register", json={"username": username, "password": "pytestpass123", "role": "RESEARCHER"})
    res = client.post("/api/auth/login", data={"username": username, "password": "pytestpass123"})
    return res.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return {"Authorization": f"Bearer {auth_token}"}
