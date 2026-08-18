"""
Unit & integration tests for Project Dataset Export (CSV & JSON formats).
"""

import pytest
from app.models import Project, Item, Annotator, Annotation, TrustScore


def test_export_project_json(client, db_session):
    project = Project(id=30, name="Export Test Project", label_set=["cat", "dog"])
    annotator = Annotator(id=1, name="Alice")
    item = Item(project_id=30, external_id="img_101", content={"url": "cat.jpg"}, is_gold=True, gold_label="cat")
    db_session.add_all([project, annotator, item])
    db_session.flush()

    annotation = Annotation(
        project_id=30,
        item_id=item.id,
        annotator_id=1,
        label="cat",
        confidence=0.99,
        duration_ms=500,
    )
    trust_score = TrustScore(
        item_id=item.id,
        score=0.98,
        breakdown={"gold_accuracy": 1.0, "agreement": 0.95},
        flagged=False,
    )
    db_session.add_all([annotation, trust_score])
    db_session.commit()

    # Request JSON export
    response = client.get("/api/projects/30/export?format=json")
    assert response.status_code == 200
    data = response.json()
    assert data["project_id"] == 30
    assert data["project_name"] == "Export Test Project"
    assert data["total_items"] == 1
    assert data["total_annotations"] == 1
    assert data["items"][0]["external_id"] == "img_101"
    assert data["items"][0]["gold_label"] == "cat"
    assert data["items"][0]["trust_score"] == 0.98
    assert len(data["items"][0]["annotations"]) == 1
    assert data["items"][0]["annotations"][0]["annotator_name"] == "Alice"


def test_export_project_csv(client, db_session):
    project = Project(id=31, name="CSV Export Project", label_set=["A", "B"])
    annotator = Annotator(id=2, name="Bob")
    item = Item(project_id=31, external_id="item_csv_1", content={"text": "sample"}, is_gold=False)
    db_session.add_all([project, annotator, item])
    db_session.flush()

    annotation = Annotation(
        project_id=31,
        item_id=item.id,
        annotator_id=2,
        label="A",
        confidence=0.85,
    )
    db_session.add(annotation)
    db_session.commit()

    # Request CSV export
    response = client.get("/api/projects/31/export?format=csv")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/csv")
    assert 'filename="project_31_export.csv"' in response.headers.get("content-disposition", "")
    
    csv_text = response.text
    assert "project_id,project_name,item_id,external_id" in csv_text
    assert "CSV Export Project" in csv_text
    assert "item_csv_1" in csv_text
    assert "Bob" in csv_text


def test_export_nonexistent_project(client):
    response = client.get("/api/projects/99999/export?format=json")
    assert response.status_code == 404


def test_export_invalid_format(client, db_session):
    project = Project(id=32, name="Format Test", label_set=["X"])
    db_session.add(project)
    db_session.commit()

    response = client.get("/api/projects/32/export?format=xml")
    assert response.status_code == 400
