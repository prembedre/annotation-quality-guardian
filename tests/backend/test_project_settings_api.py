"""
Tests for Project Settings API including negative input validation.
"""

import pytest
from app.models.project import Project


def test_project_settings_auth_required(client):
    res = client.get("/api/projects/1/settings")
    assert res.status_code == 401


def test_project_settings_valid_update(client, db_session, admin_headers):
    project = Project(name="Settings Test Project", label_set=["A", "B"])
    db_session.add(project)
    db_session.commit()

    # Valid get
    get_res = client.get(
        f"/api/projects/{project.id}/settings",
        headers=admin_headers,
    )
    assert get_res.status_code == 200
    data = get_res.json()
    assert data["project_id"] == project.id

    # Valid update
    update_res = client.put(
        f"/api/projects/{project.id}/settings",
        json={
            "gold_threshold": 95.0,
            "kappa_threshold": 0.85,
            "behavior_threshold": 80.0,
            "embedding_threshold": 85.0,
            "automation_enabled": True,
        },
        headers=admin_headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["gold_threshold"] == 95.0
    assert updated["kappa_threshold"] == 0.85
    assert updated["automation_enabled"] is True


def test_project_settings_negative_input_validation(client, db_session, admin_headers):
    project = Project(name="Negative Input Project", label_set=["A", "B"])
    db_session.add(project)
    db_session.commit()

    # 1. Gold threshold below 0
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"gold_threshold": -5.0},
        headers=admin_headers,
    )
    assert res.status_code == 422

    # 2. Gold threshold above 100
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"gold_threshold": 105.0},
        headers=admin_headers,
    )
    assert res.status_code == 422

    # 3. Kappa threshold above 1.0
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"kappa_threshold": 1.5},
        headers=admin_headers,
    )
    assert res.status_code == 422

    # 4. Kappa threshold below -1.0
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"kappa_threshold": -1.5},
        headers=admin_headers,
    )
    assert res.status_code == 422

    # 5. Behavior threshold negative
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"behavior_threshold": -1.0},
        headers=admin_headers,
    )
    assert res.status_code == 422

    # 6. Embedding threshold > 100
    res = client.put(
        f"/api/projects/{project.id}/settings",
        json={"embedding_threshold": 100.1},
        headers=admin_headers,
    )
    assert res.status_code == 422


def test_project_settings_nonexistent_project(client, admin_headers):
    res = client.get("/api/projects/99999/settings", headers=admin_headers)
    assert res.status_code == 404
