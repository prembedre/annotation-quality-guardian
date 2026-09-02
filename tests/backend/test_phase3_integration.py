"""
Integration tests for Phase 3: Webhook live ingestion, Dashboard backend APIs,
Project settings, Reviewer workflow enhancements, and Trust Score recalculation.
"""

import json
import pytest
from app.models import Project, Item, Annotator, Annotation, TrustScore


@pytest.fixture
def sample_project_and_annotators(db_session):
    """Fixture providing a project and annotators for integration testing."""
    proj = Project(
        id=1,
        name="Phase3_Classification_Project",
        description="Integration testing project",
        label_set=["Dog", "Cat", "Bird"],
    )
    db_session.add(proj)

    ann1 = Annotator(id=10, username="annotator_alice")
    ann2 = Annotator(id=20, username="annotator_bob")
    db_session.add_all([ann1, ann2])
    db_session.commit()
    return proj


# ==============================================================================
# TASK 1 & TASK 2 & TASK 8: WEBHOOK RECEIVER & INGESTION
# ==============================================================================

def test_webhook_receives_valid_payload_and_computes_trust_score(client, sample_project_and_annotators, db_session):
    """Test webhook receives valid payload, persists records, and computes trust score."""
    payload = {
        "project_id": 1,
        "item_id": "IMG_001",
        "annotator_id": 10,
        "label": "Dog",
        "confidence": 0.95,
        "duration_ms": 1200,
        "timestamp": "2026-08-20T12:30:00Z",
        "metadata": {"device": "mobile"},
    }

    response = client.post("/api/webhook/annotations", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["project_id"] == 1
    assert data["external_id"] == "IMG_001"
    assert data["annotation_id"] is not None
    assert data["trust_score"] is not None
    assert "flagged" in data

    # Verify DB persistence
    saved_item = db_session.query(Item).filter(Item.external_id == "IMG_001").first()
    assert saved_item is not None
    assert saved_item.project_id == 1

    saved_ann = db_session.query(Annotation).filter(Annotation.item_id == saved_item.id).first()
    assert saved_ann is not None
    assert saved_ann.label == "Dog"
    assert saved_ann.confidence == 0.95


def test_webhook_rejects_missing_fields(client, sample_project_and_annotators):
    """Test webhook rejects payloads missing required fields."""
    # Missing item_id and label
    payload = {
        "project_id": 1,
        "annotator_id": 10,
    }
    response = client.post("/api/webhook/annotations", json=payload)
    assert response.status_code == 422


def test_webhook_rejects_invalid_project(client, sample_project_and_annotators):
    """Test webhook returns 404 when project does not exist."""
    payload = {
        "project_id": 9999,
        "item_id": "IMG_999",
        "annotator_id": 10,
        "label": "Dog",
    }
    response = client.post("/api/webhook/annotations", json=payload)
    assert response.status_code == 404
    assert "Project with ID 9999 not found" in response.json()["detail"]


def test_webhook_rejects_invalid_label_for_project(client, sample_project_and_annotators):
    """Test webhook rejects label that is not in the project's label_set."""
    payload = {
        "project_id": 1,
        "item_id": "IMG_002",
        "annotator_id": 10,
        "label": "Elephant",  # Not in ["Dog", "Cat", "Bird"]
    }
    response = client.post("/api/webhook/annotations", json=payload)
    assert response.status_code == 400
    assert "not in project's allowed label_set" in response.json()["detail"]


def test_webhook_rejects_invalid_confidence(client, sample_project_and_annotators):
    """Test webhook rejects confidence score out of bounds."""
    payload = {
        "project_id": 1,
        "item_id": "IMG_003",
        "annotator_id": 10,
        "label": "Dog",
        "confidence": 1.5,  # Invalid: > 1.0
    }
    response = client.post("/api/webhook/annotations", json=payload)
    assert response.status_code == 422


def test_webhook_rejects_duplicate_payload(client, sample_project_and_annotators):
    """Test webhook rejects duplicate annotation for same item and annotator."""
    payload = {
        "project_id": 1,
        "item_id": "IMG_DUP_1",
        "annotator_id": 10,
        "label": "Dog",
    }

    # First attempt: success
    res1 = client.post("/api/webhook/annotations", json=payload)
    assert res1.status_code == 201

    # Second attempt: duplicate conflict (409)
    res2 = client.post("/api/webhook/annotations", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


# ==============================================================================
# TASK 3: DASHBOARD BACKEND APIS (LEADERBOARD & AGREEMENT HEATMAP)
# ==============================================================================

def test_dashboard_leaderboard_empty_and_populated(client, sample_project_and_annotators, db_session):
    """Test leaderboard returns ranked list of annotators."""
    # Initially with no annotations for project 1
    res_empty = client.get("/api/dashboard/leaderboard?project_id=1")
    assert res_empty.status_code == 200
    assert res_empty.json()["total_annotators"] == 0

    # Ingest annotations for two annotators
    client.post("/api/webhook/annotations", json={
        "project_id": 1,
        "item_id": "ITEM_A",
        "annotator_id": 10,
        "label": "Dog",
        "confidence": 0.95,
        "duration_ms": 1000,
    })
    client.post("/api/webhook/annotations", json={
        "project_id": 1,
        "item_id": "ITEM_A",
        "annotator_id": 20,
        "label": "Dog",
        "confidence": 0.85,
        "duration_ms": 2000,
    })

    res = client.get("/api/dashboard/leaderboard?project_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["total_annotators"] == 2
    assert len(data["leaderboard"]) == 2
    top = data["leaderboard"][0]
    assert top["rank"] == 1
    assert "annotator_name" in top
    assert top["total_annotations"] >= 1


def test_dashboard_agreement_heatmap(client, sample_project_and_annotators):
    """Test agreement heatmap matrix computation."""
    # Ingest overlapping annotations
    client.post("/api/webhook/annotations", json={
        "project_id": 1,
        "item_id": "ITEM_HEAT_1",
        "annotator_id": 10,
        "label": "Dog",
    })
    client.post("/api/webhook/annotations", json={
        "project_id": 1,
        "item_id": "ITEM_HEAT_1",
        "annotator_id": 20,
        "label": "Dog",
    })

    res = client.get("/api/dashboard/agreement-heatmap?project_id=1")
    assert res.status_code == 200
    data = res.json()
    assert data["project_id"] == 1
    assert len(data["annotators"]) == 2
    assert len(data["matrix"]) == 2
    # Self-agreement should be 1.0
    assert data["matrix"][0][0] == 1.0
    assert data["matrix"][1][1] == 1.0
    # Cross agreement on 1 shared matching item should be 1.0
    assert data["matrix"][0][1] == 1.0
    assert len(data["cells"]) == 4


# ==============================================================================
# TASK 4: PROJECT SCORING SETTINGS API
# ==============================================================================

def test_project_settings_get_and_put(client, sample_project_and_annotators):
    """Test retrieving and updating project scoring thresholds."""
    # GET settings (default thresholds)
    get_res = client.get("/api/projects/1/settings")
    assert get_res.status_code == 200
    settings_data = get_res.json()
    assert settings_data["gold_threshold"] == 90.0
    assert settings_data["kappa_threshold"] == 0.7
    assert settings_data["behavior_threshold"] == 75.0
    assert settings_data["embedding_threshold"] == 80.0

    # PUT settings update
    update_payload = {
        "gold_threshold": 95.0,
        "kappa_threshold": 0.8,
    }
    put_res = client.put("/api/projects/1/settings", json=update_payload)
    assert put_res.status_code == 200
    updated_data = put_res.json()
    assert updated_data["gold_threshold"] == 95.0
    assert updated_data["kappa_threshold"] == 0.8
    assert updated_data["behavior_threshold"] == 75.0  # untouched

    # Verify subsequent GET returns updated thresholds
    get_res2 = client.get("/api/projects/1/settings")
    assert get_res2.status_code == 200
    assert get_res2.json()["gold_threshold"] == 95.0


def test_project_settings_nonexistent_project(client):
    """Test project settings return 404 for nonexistent project."""
    res = client.get("/api/projects/999/settings")
    assert res.status_code == 404


# ==============================================================================
# TASK 5 & TASK 6: REVIEWER RESOLVE WORKFLOW & TRUST SCORE RECALCULATION
# ==============================================================================

def test_reviewer_resolve_correct_action(client, sample_project_and_annotators, db_session):
    """Test reviewer resolves item with 'correct' action and triggers trust score recalculation."""
    # Create item with annotations
    item = Item(project_id=1, external_id="REVIEW_ITEM_1", content={"text": "A furry animal"})
    db_session.add(item)
    db_session.commit()

    ann = Annotation(project_id=1, item_id=item.id, annotator_id=10, label="Dog", confidence=0.7)
    db_session.add(ann)
    db_session.commit()

    # Initial trust score calculation
    ts = TrustScore(project_id=1, item_id=item.id, final_score=0.4, flagged=True)
    db_session.add(ts)
    db_session.commit()

    # Reviewer resolves with 'correct'
    payload = {
        "action": "correct",
        "correct_label": "Cat",
        "notes": "Originally misidentified as Dog",
    }
    res = client.post(f"/api/review/{item.id}/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["item_id"] == item.id
    assert data["status"] == "resolved"
    assert data["gold_label"] == "Cat"
    assert data["action"] == "correct"
    assert data["trust_score"] is not None

    # Verify item is updated in DB
    db_session.refresh(item)
    assert item.is_gold is True
    assert item.gold_label == "Cat"


def test_reviewer_resolve_confirm_action(client, sample_project_and_annotators, db_session):
    """Test reviewer resolves item with 'confirm' action."""
    item = Item(project_id=1, external_id="REVIEW_ITEM_2", content={"text": "Barking pet"})
    db_session.add(item)
    db_session.commit()

    ann = Annotation(project_id=1, item_id=item.id, annotator_id=10, label="Dog", confidence=0.99)
    db_session.add(ann)
    db_session.commit()

    payload = {
        "action": "confirm",
        "notes": "Verified correct by senior reviewer",
    }
    res = client.post(f"/api/review/{item.id}/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["gold_label"] == "Dog"
    assert data["status"] == "resolved"


def test_reviewer_resolve_escalate_action(client, sample_project_and_annotators, db_session):
    """Test reviewer resolves item with 'escalate' action."""
    item = Item(project_id=1, external_id="REVIEW_ITEM_3", content={"text": "Ambiguous image"})
    db_session.add(item)
    db_session.commit()

    ann = Annotation(project_id=1, item_id=item.id, annotator_id=10, label="Dog", confidence=0.5)
    db_session.add(ann)
    db_session.commit()

    payload = {
        "action": "escalate",
        "notes": "Requires domain expert review",
    }
    res = client.post(f"/api/review/{item.id}/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["status"] == "escalated"
    assert data["flagged"] is True


def test_reviewer_resolve_backward_compatibility(client, sample_project_and_annotators, db_session):
    """Test that legacy Phase 1 payload format (ground_truth_label) still works seamlessly."""
    item = Item(project_id=1, external_id="REVIEW_ITEM_LEGACY", content={"text": "Legacy test"})
    db_session.add(item)
    db_session.commit()

    ann = Annotation(project_id=1, item_id=item.id, annotator_id=10, label="Bird", confidence=0.8)
    db_session.add(ann)
    db_session.commit()

    # Legacy payload format
    payload = {
        "ground_truth_label": "Bird",
        "notes": "Phase 1 style resolution",
    }
    res = client.post(f"/api/review/{item.id}/resolve", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["gold_label"] == "Bird"


# ==============================================================================
# TASK 7: COMPATIBILITY WITH EXISTING APIS
# ==============================================================================

def test_existing_endpoints_compatibility(client, sample_project_and_annotators):
    """Verify health, review queue, export, scores, and annotations endpoints are accessible."""
    # 1. Health
    res_health = client.get("/health")
    assert res_health.status_code == 200

    # 2. Review queue
    res_queue = client.get("/api/review/queue")
    assert res_queue.status_code == 200

    # 3. Export
    res_export = client.get("/api/projects/1/export?format=json")
    assert res_export.status_code == 200

    # 4. Scores
    res_scores = client.get("/api/scores?project_id=1")
    assert res_scores.status_code == 200

    # 5. Annotations upload / ingestion
    res_ann = client.get("/api/annotations")
    assert res_ann.status_code == 200

