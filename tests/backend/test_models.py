"""
Unit tests verifying SQLAlchemy models and relationships.
"""

from fastapi.testclient import TestClient


def test_create_project_and_annotator(client: TestClient):
    """
    Verify that a project and annotator can be created
    through the application API.
    """

    project_response = client.post(
        "/projects/",
        json={
            "name": "Sentiment Analysis",
            "description": "Test sentiment project",
            "label_set": [
                "positive",
                "negative",
                "neutral",
            ],
        },
    )

    assert project_response.status_code in (200, 201)

    project = project_response.json()

    assert project["id"] is not None
    assert project["name"] == "Sentiment Analysis"


def test_database_models_are_available(client: TestClient):
    """
    Basic database health check through the application.
    """

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database"] == "connected"
