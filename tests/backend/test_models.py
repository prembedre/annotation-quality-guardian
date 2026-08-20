"""
Unit tests verifying SQLAlchemy models and relationships.
"""

from fastapi.testclient import TestClient


def test_create_project(client: TestClient):
    """
    Verify that a project can be created successfully.
    """

    response = client.post(
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

    assert response.status_code == 201

    data = response.json()

    assert data["id"] is not None
    assert data["name"] == "Sentiment Analysis"
    assert data["description"] == "Test sentiment project"
    assert data["label_set"] == [
        "positive",
        "negative",
        "neutral",
    ]


def test_get_project(client: TestClient):
    """
    Verify that a created project can be retrieved.
    """

    create_response = client.post(
        "/projects/",
        json={
            "name": "Named Entity Recognition",
            "description": "Test NER project",
            "label_set": [
                "PER",
                "ORG",
                "LOC",
                "MISC",
            ],
        },
    )

    assert create_response.status_code == 201

    project = create_response.json()
    project_id = project["id"]

    response = client.get(f"/projects/{project_id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == project_id
    assert data["name"] == "Named Entity Recognition"


def test_list_projects(client: TestClient):
    """
    Verify that projects can be listed.
    """

    response = client.post(
        "/projects/",
        json={
            "name": "Test Project",
            "description": "Project for testing",
            "label_set": ["positive", "negative"],
        },
    )

    assert response.status_code == 201

    response = client.get("/projects/")

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)
    assert len(data) >= 1


def test_duplicate_project_name(client: TestClient):
    """
    Verify that duplicate project names are rejected.
    """

    payload = {
        "name": "Duplicate Project",
        "description": "Duplicate test",
        "label_set": ["yes", "no"],
    }

    first_response = client.post(
        "/projects/",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/projects/",
        json=payload,
    )

    assert second_response.status_code == 409


def test_health_after_database_operations(client: TestClient):
    """
    Verify that the PostgreSQL test database remains connected.
    """

    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database"] == "connected"
