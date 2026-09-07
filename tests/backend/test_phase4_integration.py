"""
Integration tests for Phase 4: External DB Connectors (Read-Only),
Automatic Task Rerouting, A/B Testing database support, and end-to-end integration.
"""

import os
import sqlite3
import pytest
from app.models import Project, Item, Annotator, Annotation, TrustScore, ExternalDBConnector, RerouteHistory, ABTestExperiment


@pytest.fixture
def sample_project_and_annotators(db_session):
    """Fixture providing a project and annotators for Phase 4 testing."""
    proj = Project(
        id=1,
        name="Phase4_Integration_Project",
        description="Phase 4 testing project",
        label_set=["Positive", "Negative", "Neutral"],
    )
    db_session.add(proj)

    ann1 = Annotator(id=1, username="annotator_alice")
    ann2 = Annotator(id=2, username="annotator_bob")
    ann3 = Annotator(id=3, username="annotator_charlie")
    db_session.add_all([ann1, ann2, ann3])
    db_session.commit()
    return proj


@pytest.fixture
def external_sqlite_db(tmp_path):
    """Create a temporary external database simulating a 3rd-party labeling platform DB."""
    db_file = tmp_path / "external_platform.db"
    conn = sqlite3.connect(str(db_file))
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE label_studio_tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_external_id TEXT NOT NULL,
            annotator_id INTEGER NOT NULL,
            result_label TEXT NOT NULL,
            confidence REAL,
            duration_ms INTEGER,
            data_content TEXT
        )
    """)

    cursor.executemany("""
        INSERT INTO label_studio_tasks (task_external_id, annotator_id, result_label, confidence, duration_ms, data_content)
        VALUES (?, ?, ?, ?, ?, ?)
    """, [
        ("EXT-TASK-101", 1, "Positive", 0.96, 1500, '{"text": "Superb product quality!"}'),
        ("EXT-TASK-102", 2, "Negative", 0.89, 2100, '{"text": "Broke on the second day."}'),
        ("EXT-TASK-103", 3, "Neutral", 0.75, 3400, '{"text": "Average performance."}'),
    ])

    conn.commit()
    conn.close()
    return str(db_file)


# ==============================================================================
# 1. EXTERNAL DB CONNECTOR TESTS (CRUD, TESTING, & SECURITY)
# ==============================================================================

def test_external_connector_lifecycle(client, sample_project_and_annotators):
    """Test creating, listing, and deleting read-only external DB connectors."""
    # 1. Create connector
    create_payload = {
        "connection_name": "test_label_studio_pg",
        "database_type": "postgresql",
        "host": "localhost",
        "port": 5432,
        "database_name": "label_studio_replica",
        "username": "readonly_user",
        "password": "super_secret_password_123",
        "status": "active",
        "query_config": {
            "table_name": "task_completion",
            "column_mapping": {"external_id": "task_id", "label": "result_label"},
        },
    }

    res_create = client.post("/api/integrations/connectors", json=create_payload)
    assert res_create.status_code == 201
    data = res_create.json()
    assert data["id"] is not None
    assert data["connection_name"] == "test_label_studio_pg"
    assert data["read_only"] is True
    # Verify password is NOT in response
    assert "password" not in data
    assert "password_encrypted" not in data
    connector_id = data["id"]

    # 2. List connectors
    res_list = client.get("/api/integrations/connectors")
    assert res_list.status_code == 200
    connectors = res_list.json()
    assert len(connectors) >= 1
    found = next((c for c in connectors if c["id"] == connector_id), None)
    assert found is not None
    assert "password" not in found

    # 3. Delete connector
    res_del = client.delete(f"/api/integrations/connectors/{connector_id}")
    assert res_del.status_code == 200
    assert res_del.json()["success"] is True

    # 4. Verify deletion
    res_list2 = client.get("/api/integrations/connectors")
    assert not any(c["id"] == connector_id for c in res_list2.json())


def test_external_connector_test_and_sync(client, sample_project_and_annotators, external_sqlite_db, db_session):
    """Test connecting to a real external DB (SQLite), testing connectivity, and syncing data."""
    # 1. Register connector pointing to temp SQLite DB
    create_payload = {
        "connection_name": "local_sqlite_replica",
        "database_type": "sqlite",
        "database_name": external_sqlite_db,
        "status": "active",
        "query_config": {
            "table_name": "label_studio_tasks",
            "column_mapping": {
                "external_id": "task_external_id",
                "annotator_id": "annotator_id",
                "label": "result_label",
                "confidence": "confidence",
                "duration_ms": "duration_ms",
                "content": "data_content",
            },
        },
    }

    res_create = client.post("/api/integrations/connectors", json=create_payload)
    assert res_create.status_code == 201
    connector_id = res_create.json()["id"]

    # 2. Test Connection
    res_test = client.post(f"/api/integrations/connectors/{connector_id}/test")
    assert res_test.status_code == 200
    test_data = res_test.json()
    assert test_data["success"] is True
    assert test_data["read_only_verified"] is True
    assert test_data["latency_ms"] is not None

    # 3. Sync annotations into Project 1
    sync_payload = {
        "project_id": 1,
        "table_name": "label_studio_tasks",
    }
    res_sync = client.post(f"/api/integrations/connectors/{connector_id}/sync", json=sync_payload)
    assert res_sync.status_code == 200
    sync_data = res_sync.json()
    assert sync_data["success"] is True
    assert sync_data["total_fetched"] == 3
    assert sync_data["inserted_records"] == 3
    assert sync_data["duplicate_records"] == 0

    # 4. Verify items and annotations in AQG DB
    item1 = db_session.query(Item).filter(Item.external_id == "EXT-TASK-101").first()
    assert item1 is not None
    assert item1.project_id == 1
    ann1 = db_session.query(Annotation).filter(Annotation.item_id == item1.id).first()
    assert ann1 is not None
    assert ann1.label == "Positive"
    assert ann1.confidence == 0.96

    # 5. Verify re-sync handles duplicate skipping
    res_sync_dup = client.post(f"/api/integrations/connectors/{connector_id}/sync", json=sync_payload)
    assert res_sync_dup.status_code == 200
    assert res_sync_dup.json()["inserted_records"] == 0
    assert res_sync_dup.json()["duplicate_records"] == 3


def test_read_only_security_rejects_mutation_queries(client, sample_project_and_annotators, external_sqlite_db):
    """Test that any attempt to execute mutation queries is strictly rejected."""
    # Register connector
    res_create = client.post("/api/integrations/connectors", json={
        "connection_name": "mutation_test_conn",
        "database_type": "sqlite",
        "database_name": external_sqlite_db,
    })
    connector_id = res_create.json()["id"]

    # Attempt forbidden queries
    forbidden_queries = [
        "DELETE FROM label_studio_tasks WHERE id = 1",
        "DROP TABLE label_studio_tasks",
        "UPDATE label_studio_tasks SET result_label = 'Hacked'",
        "INSERT INTO label_studio_tasks VALUES (999, 'HACK', 1, 'Bad', 1.0, 100, '{}')",
    ]

    for fq in forbidden_queries:
        res = client.post(f"/api/integrations/connectors/{connector_id}/sync", json={
            "project_id": 1,
            "custom_query": fq,
        })
        assert res.status_code == 400
        assert "Only SELECT queries are permitted" in res.json()["detail"] or "Forbidden mutation" in res.json()["detail"]


# ==============================================================================
# 2. AUTOMATIC TASK REROUTING TESTS
# ==============================================================================

def test_task_rerouting_flow(client, sample_project_and_annotators, db_session):
    """Test retrieving pending reroute tasks and assigning them to new annotators."""
    # 1. Create a flagged item with low trust score
    item = Item(project_id=1, external_id="REROUTE_ITEM_01", content={"text": "Unclear text"})
    db_session.add(item)
    db_session.commit()

    ann = Annotation(project_id=1, item_id=item.id, annotator_id=2, label="Negative", confidence=0.4)
    ts = TrustScore(project_id=1, item_id=item.id, final_score=0.35, flagged=True)
    db_session.add_all([ann, ts])
    db_session.commit()

    # Create an explicit pending reroute record
    reroute = RerouteHistory(
        item_id=item.id,
        project_id=1,
        original_annotator_id=2,
        reason="Low trust score 0.35 detected by guardian",
        trust_score_snapshot=0.35,
        reroute_status="PENDING",
    )
    db_session.add(reroute)
    db_session.commit()

    # 2. GET pending reroutes
    res_pending = client.get("/api/rerouting/pending?project_id=1")
    assert res_pending.status_code == 200
    data = res_pending.json()
    assert data["total"] >= 1
    pending_item = next((i for i in data["items"] if i["item_id"] == item.id), None)
    assert pending_item is not None
    assert pending_item["reroute_status"] == "PENDING"
    assert pending_item["original_annotator_id"] == 2

    # 3. POST assign to Alice (Annotator 1)
    assign_payload = {
        "reassigned_annotator_id": 1,
        "reason": "Reassigned to senior annotator Alice for second pass",
    }
    res_assign = client.post(f"/api/rerouting/{item.id}/assign", json=assign_payload)
    assert res_assign.status_code == 200
    assign_data = res_assign.json()
    assert assign_data["success"] is True
    assert assign_data["reroute_status"] == "ASSIGNED"
    assert assign_data["reassigned_annotator_id"] == 1
    assert "Alice" in assign_data["message"] or "annotator_alice" in assign_data["message"]

    # 4. Verify DB status
    db_session.refresh(reroute)
    assert reroute.reroute_status == "ASSIGNED"
    assert reroute.reassigned_annotator_id == 1


# ==============================================================================
# 3. A/B TESTING DATABASE SUPPORT TESTS
# ==============================================================================

def test_ab_testing_database_model(db_session, sample_project_and_annotators):
    """Test creating and querying A/B testing experiment configurations."""
    exp = ABTestExperiment(
        experiment_name="Phase 4 Label Hierarchy Experiment",
        project_id=1,
        schema_version_a={"version": "1.0", "labels": ["Positive", "Negative", "Neutral"]},
        schema_version_b={"version": "2.0", "labels": ["Strongly Positive", "Positive", "Neutral", "Negative", "Strongly Negative"]},
        annotator_group={"cohort_a": [1], "cohort_b": [2, 3]},
        assigned_version="SPLIT_50_50",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    assert exp.id is not None
    assert exp.experiment_name == "Phase 4 Label Hierarchy Experiment"
    assert exp.schema_version_a["labels"] == ["Positive", "Negative", "Neutral"]
    assert exp.annotator_group["cohort_a"] == [1]


# ==============================================================================
# 4. BACKWARD COMPATIBILITY WITH ALL PRIOR PHASES
# ==============================================================================

def test_phase1_to_3_apis_continue_working_seamlessly(client, sample_project_and_annotators, db_session):
    """Verify all prior phase APIs remain 100% operational."""
    # 1. Health
    assert client.get("/health").status_code == 200

    # 2. Review queue
    assert client.get("/api/review/queue").status_code == 200

    # 3. Project settings GET & PUT
    assert client.get("/api/projects/1/settings").status_code == 200
    put_res = client.put("/api/projects/1/settings", json={"gold_threshold": 92.0})
    assert put_res.status_code == 200
    assert put_res.json()["gold_threshold"] == 92.0

    # 4. Webhook live ingestion
    webhook_res = client.post("/api/webhook/annotations", json={
        "project_id": 1,
        "item_id": "P4_WEBHOOK_ITEM",
        "annotator_id": 1,
        "label": "Positive",
        "confidence": 0.99,
    })
    assert webhook_res.status_code == 201

    # 5. Dashboard Leaderboard & Heatmap
    assert client.get("/api/dashboard/leaderboard?project_id=1").status_code == 200
    assert client.get("/api/dashboard/agreement-heatmap?project_id=1").status_code == 200

    # 6. Export
    assert client.get("/api/projects/1/export?format=json").status_code == 200
