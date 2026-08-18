"""
Unit & integration tests for CSV/JSON ingestion service and upload endpoints.
"""

import io
import json
import os
import pytest
from app.models import Project, Item, Annotation, Annotator


def test_upload_valid_csv(client, db_session):
    # Setup project
    project = Project(id=1, name="Sentiment Project", label_set=["positive", "negative", "neutral"])
    db_session.add(project)
    db_session.commit()

    csv_data = (
        "project_id,item_id,annotator_id,label,confidence,duration_ms,content\n"
        '1,item_1,101,positive,0.95,1200,"{\\"text\\":\\"Great job\\"}"\n'
        '1,item_2,102,negative,0.88,1500,"{\\"text\\":\\"Bad result\\"}"\n'
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    response = client.post(
        "/api/annotations/upload",
        files={"file": ("annotations.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["inserted_records"] == 2
    assert data["duplicate_records"] == 0
    assert data["failed_records"] == 0

    # Verify records in DB
    items = db_session.query(Item).filter(Item.project_id == 1).all()
    assert len(items) == 2
    annotations = db_session.query(Annotation).filter(Annotation.project_id == 1).all()
    assert len(annotations) == 2


def test_upload_real_sample_annotations_csv(client, db_session):
    # Setup project 1
    project = Project(id=1, name="Project 1", label_set=["positive", "negative", "neutral"])
    db_session.add(project)
    db_session.commit()

    sample_csv_path = os.path.join("data", "sample_annotations.csv")
    if os.path.exists(sample_csv_path):
        with open(sample_csv_path, "rb") as f:
            response = client.post(
                "/api/annotations/upload",
                files={"file": ("sample_annotations.csv", f, "text/csv")},
                data={"project_id": 1},
            )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["inserted_records"] > 0


def test_upload_valid_json(client, db_session):
    # Setup project
    project = Project(id=2, name="Intent Project", label_set=["greeting", "farewell"])
    db_session.add(project)
    db_session.commit()

    json_payload = [
        {"project_id": 2, "item_id": "item_10", "annotator_id": 201, "label": "greeting", "confidence": 0.99},
        {"project_id": 2, "item_id": "item_20", "annotator_id": 202, "label": "farewell", "confidence": 0.91},
    ]
    file_bytes = io.BytesIO(json.dumps(json_payload).encode("utf-8"))

    response = client.post(
        "/api/annotations/upload",
        files={"file": ("dataset.json", file_bytes, "application/json")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["inserted_records"] == 2


def test_upload_invalid_label_for_project(client, db_session):
    project = Project(id=3, name="Restricted Project", label_set=["cat", "dog"])
    db_session.add(project)
    db_session.commit()

    csv_data = (
        "project_id,item_id,annotator_id,label,confidence\n"
        "3,item_1,101,bird,0.95\n"
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    response = client.post(
        "/api/annotations/upload",
        files={"file": ("invalid_label.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_records"] == 0
    assert data["failed_records"] == 1
    assert len(data["errors"]) > 0


def test_upload_duplicate_detection(client, db_session):
    project = Project(id=4, name="Dupe Project", label_set=["yes", "no"])
    db_session.add(project)
    db_session.commit()

    # CSV containing in-batch duplicates
    csv_data = (
        "project_id,item_id,annotator_id,label,confidence\n"
        "4,item_1,101,yes,0.9\n"
        "4,item_1,101,yes,0.9\n"  # Duplicate row
    )
    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    response = client.post(
        "/api/annotations/upload",
        files={"file": ("dupe.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_records"] == 1
    assert data["duplicate_records"] == 1


def test_upload_empty_file(client):
    file_bytes = io.BytesIO(b"")
    response = client.post(
        "/api/annotations/upload",
        files={"file": ("empty.csv", file_bytes, "text/csv")},
    )
    assert response.status_code == 400


def test_upload_unsupported_file_extension(client):
    file_bytes = io.BytesIO(b"dummy binary data")
    response = client.post(
        "/api/annotations/upload",
        files={"file": ("data.xyz", file_bytes, "application/octet-stream")},
    )
    assert response.status_code == 400
