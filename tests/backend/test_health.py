"""
Sanity check tests for health endpoint and DB connectivity.
"""

from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert "service" in data
    assert data["service"] == "Annotation Quality Guardian"


def test_health_check_endpoint(client: TestClient):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ok"
    assert data["database"] == "connected"
