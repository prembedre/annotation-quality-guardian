"""
Unit and integration tests for CSV/JSON ingestion.
"""

import io
import json

from app.models import Project, Item, Annotation, Annotator


def create_project(db_session, project_id, name, labels):
    """Create a test project."""

    project = Project(
        id=project_id,
        name=name,
        label_set=labels,
    )

    db_session.add(project)
    db_session.commit()

    return project


def create_annotator(db_session, annotator_id, username):
    """Create a test annotator."""

    annotator = Annotator(
        id=annotator_id,
        username=username,
        email=f"{username}@example.com",
    )

    db_session.add(annotator)
    db_session.commit()

    return annotator


def test_upload_valid_csv(client, db_session):
    """Test successful CSV ingestion."""

    create_project(
        db_session,
        1,
        "Sentiment Project",
        ["positive", "negative", "neutral"],
    )

    create_annotator(db_session, 101, "alice")
    create_annotator(db_session, 102, "bob")

    csv_data = (
        "project_id,external_id,annotator_id,label,confidence,content\n"
        '1,item_1,101,positive,0.95,"{\\"text\\":\\"Great job\\"}"\n'
        '1,item_2,102,negative,0.88,"{\\"text\\":\\"Bad result\\"}"\n'
    )

    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    response = client.post(
        "/ingestion/upload",
        files={
            "file": (
                "annotations.csv",
                file_bytes,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["inserted_records"] == 2

    items = (
        db_session.query(Item)
        .filter(Item.project_id == 1)
        .all()
    )

    annotations = (
        db_session.query(Annotation)
        .filter(Annotation.project_id == 1)
        .all()
    )

    assert len(items) == 2
    assert len(annotations) == 2


def test_upload_valid_json(client, db_session):
    """Test successful JSON ingestion."""

    create_project(
        db_session,
        2,
        "Intent Project",
        ["greeting", "farewell"],
    )

    create_annotator(db_session, 201, "charlie")
    create_annotator(db_session, 202, "david")

    json_payload = [
        {
            "project_id": 2,
            "external_id": "item_10",
            "annotator_id": 201,
            "label": "greeting",
            "confidence": 0.99,
            "content": {
                "text": "Hello"
            },
        },
        {
            "project_id": 2,
            "external_id": "item_20",
            "annotator_id": 202,
            "label": "farewell",
            "confidence": 0.91,
            "content": {
                "text": "Goodbye"
            },
        },
    ]

    file_bytes = io.BytesIO(
        json.dumps(json_payload).encode("utf-8")
    )

    response = client.post(
        "/ingestion/upload",
        files={
            "file": (
                "dataset.json",
                file_bytes,
                "application/json",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["inserted_records"] == 2


def test_upload_with_project_id_form(client, db_session):
    """Test ingestion using project_id supplied as a form field."""

    create_project(
        db_session,
        3,
        "Form Project",
        ["yes", "no"],
    )

    create_annotator(db_session, 301, "eve")

    csv_data = (
        "external_id,annotator_id,label,confidence,content\n"
        'item_1,301,yes,0.95,"{\\"text\\":\\"Yes\\"}"\n'
    )

    file_bytes = io.BytesIO(csv_data.encode("utf-8"))

    response = client.post(
        "/ingestion/upload",
        data={
            "project_id": "3",
        },
        files={
            "file": (
                "form_project.csv",
                file_bytes,
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["success"] is True
    assert data["inserted_records"] == 1


def test_upload_empty_file(client):
    """Test rejection of an empty file."""

    file_bytes = io.BytesIO(b"")

    response = client.post(
        "/ingestion/upload",
        files={
            "file": (
                "empty.csv",
                file_bytes,
                "text/csv",
            )
        },
    )

    assert response.status_code == 400


def test_upload_unsupported_file_extension(client):
    """Test rejection of unsupported file types."""

    file_bytes = io.BytesIO(b"dummy data")

    response = client.post(
        "/ingestion/upload",
        files={
            "file": (
                "data.xyz",
                file_bytes,
                "application/octet-stream",
            )
        },
    )

    assert response.status_code == 400
