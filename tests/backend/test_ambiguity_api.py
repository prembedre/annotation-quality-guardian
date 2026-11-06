"""
Tests for Ambiguity Insights API.
"""

import pytest
from app.models.annotation import Annotation
from app.models.annotator import Annotator
from app.models.item import Item
from app.models.project import Project


def test_ambiguity_classes_auth_required(client):
    res = client.get("/api/ambiguity/classes")
    assert res.status_code == 401


def test_ambiguity_classes_empty_project(client, db_session, admin_headers):
    project = Project(
        name="Empty Ambiguity Project",
        label_set=["Cat", "Dog"],
    )
    db_session.add(project)
    db_session.commit()

    res = client.get(
        f"/api/ambiguity/classes?project_id={project.id}",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == project.id
    assert "classes" in data
    assert "confusion_matrix" in data
    assert "recommendations" in data
    assert data["confusion_matrix"]["categories"] == ["Cat", "Dog"]


def test_ambiguity_classes_and_confusion_matrix_with_disagreements(client, db_session, admin_headers):
    project = Project(
        name="Disputed Project",
        label_set=["Positive", "Neutral", "Negative"],
    )
    db_session.add(project)
    db_session.flush()

    item1 = Item(project_id=project.id, external_id="amb-item-1", content={"text": "Review 1"})
    item2 = Item(project_id=project.id, external_id="amb-item-2", content={"text": "Review 2"})
    ann1 = Annotator(name="Alice")
    ann2 = Annotator(name="Bob")
    db_session.add_all([item1, item2, ann1, ann2])
    db_session.flush()

    # Disagreement on item1: Positive vs Neutral
    a1 = Annotation(item_id=item1.id, annotator_id=ann1.id, project_id=project.id, label="Positive")
    a2 = Annotation(item_id=item1.id, annotator_id=ann2.id, project_id=project.id, label="Neutral")

    # Disagreement on item2: Neutral vs Negative
    a3 = Annotation(item_id=item2.id, annotator_id=ann1.id, project_id=project.id, label="Neutral")
    a4 = Annotation(item_id=item2.id, annotator_id=ann2.id, project_id=project.id, label="Negative")

    db_session.add_all([a1, a2, a3, a4])
    db_session.commit()

    res = client.get(
        f"/api/ambiguity/classes?project_id={project.id}&disagreement_threshold=0.20&minimum_comparisons=1",
        headers=admin_headers,
    )
    assert res.status_code == 200
    data = res.json()

    assert data["project_id"] == project.id
    matrix_info = data["confusion_matrix"]
    assert "categories" in matrix_info
    assert matrix_info["total_pairs_evaluated"] == 2
    assert len(matrix_info["matrix"]) == 3
    assert len(data["recommendations"]) > 0

    # Test /api/ambiguity/confusion-matrix
    cm_res = client.get(
        f"/api/ambiguity/confusion-matrix?project_id={project.id}",
        headers=admin_headers,
    )
    assert cm_res.status_code == 200
    cm_data = cm_res.json()
    assert cm_data["total_pairs_evaluated"] == 2
    assert cm_data["categories"] == ["Positive", "Neutral", "Negative"]
