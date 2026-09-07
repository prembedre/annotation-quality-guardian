"""
Unit tests for Phase 4 Database Schema, Models, Relationships, Constraints, and Migrations.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.core.db import Base
from app.models import (
    Project,
    Item,
    Annotator,
    Annotation,
    TrustScore,
    BehavioralScore,
    EmbeddingResult,
    ProjectThreshold,
    ReviewerDecision,
    ExternalDBConnector,
    RerouteHistory,
    ABTestExperiment,
)


@pytest.fixture
def db_session():
    """Create an isolated SQLite database session for Phase 4 model tests."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    SessionLocal = sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
    )

    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_external_db_connector_and_constraints(db_session):
    """Test creating an external DB connector and verifying constraints."""
    connector = ExternalDBConnector(
        connection_name="prod_label_studio_replica",
        database_type="postgresql",
        host="10.0.0.12",
        port=5432,
        database_name="label_studio_db",
        username="readonly_aqg",
        password_encrypted="ZW5jcnlwdGVkX3B3",
        status="active",
        read_only=True,
        query_config={"table_name": "task_completion", "column_mapping": {"external_id": "task_id"}},
    )
    db_session.add(connector)
    db_session.commit()
    db_session.refresh(connector)

    assert connector.id is not None
    assert connector.connection_name == "prod_label_studio_replica"
    assert connector.database_type == "postgresql"
    assert connector.read_only is True
    assert connector.query_config["table_name"] == "task_completion"
    assert connector.created_at is not None

    # Test unique connection_name constraint
    dup_connector = ExternalDBConnector(
        connection_name="prod_label_studio_replica",
        database_type="postgresql",
        database_name="other_db",
    )
    db_session.add(dup_connector)
    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()


def test_create_reroute_history_and_relationships(db_session):
    """Test creating RerouteHistory records and checking ForeignKeys and relationships."""
    project = Project(name="Reroute Test Project", label_set=["cat", "dog"])
    orig_annotator = Annotator(username="junior_annotator", email="junior@example.com")
    new_annotator = Annotator(username="senior_expert", email="senior@example.com")
    db_session.add_all([project, orig_annotator, new_annotator])
    db_session.commit()

    item = Item(project_id=project.id, external_id="item-reroute-01", content={"img": "dog.jpg"})
    db_session.add(item)
    db_session.commit()

    reroute = RerouteHistory(
        item_id=item.id,
        project_id=project.id,
        original_annotator_id=orig_annotator.id,
        reassigned_annotator_id=new_annotator.id,
        reason="Low trust score (0.32) on high-priority dataset",
        trust_score_snapshot=0.32,
        reroute_status="ASSIGNED",
    )
    db_session.add(reroute)
    db_session.commit()
    db_session.refresh(reroute)

    assert reroute.id is not None
    assert reroute.item_id == item.id
    assert reroute.project_id == project.id
    assert reroute.original_annotator_id == orig_annotator.id
    assert reroute.reassigned_annotator_id == new_annotator.id
    assert reroute.reroute_status == "ASSIGNED"
    assert float(reroute.trust_score_snapshot) == 0.32

    # Verify relationships
    assert reroute.item == item
    assert reroute.project == project
    assert reroute.original_annotator == orig_annotator
    assert reroute.reassigned_annotator == new_annotator

    assert len(item.reroute_histories) == 1
    assert len(project.reroute_histories) == 1
    assert len(orig_annotator.rerouted_from_tasks) == 1
    assert len(new_annotator.rerouted_to_tasks) == 1


def test_create_ab_test_experiment_and_relationships(db_session):
    """Test creating ABTestExperiment model and verifying relationships."""
    project = Project(name="AB Test Project", label_set=["A", "B", "C"])
    db_session.add(project)
    db_session.commit()

    exp = ABTestExperiment(
        experiment_name="3-class vs 5-class labeling experiment",
        project_id=project.id,
        schema_version_a={"version": "1.0", "classes": ["A", "B", "C"]},
        schema_version_b={"version": "2.0", "classes": ["A1", "A2", "B", "C1", "C2"]},
        annotator_group={"group_a": [1, 2], "group_b": [3, 4]},
        assigned_version="SPLIT_50_50",
        status="active",
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)

    assert exp.id is not None
    assert exp.experiment_name == "3-class vs 5-class labeling experiment"
    assert exp.project_id == project.id
    assert exp.schema_version_a["version"] == "1.0"
    assert exp.schema_version_b["version"] == "2.0"
    assert exp.status == "active"
    assert exp.created_at is not None

    # Verify relationship
    assert exp.project == project
    assert len(project.ab_test_experiments) == 1


def test_phase4_cascade_deletions(db_session):
    """Test that deleting a project cascades properly to reroute history and A/B experiments."""
    project = Project(name="Cascade Phase 4 Project", label_set=["label1"])
    annotator = Annotator(username="cascade_user")
    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(project_id=project.id, external_id="cascade-p4-item", content={})
    db_session.add(item)
    db_session.commit()

    reroute = RerouteHistory(
        item_id=item.id,
        project_id=project.id,
        original_annotator_id=annotator.id,
        reroute_status="PENDING",
    )
    exp = ABTestExperiment(
        experiment_name="Cascade Exp",
        project_id=project.id,
        schema_version_a={"v": 1},
        schema_version_b={"v": 2},
    )
    db_session.add_all([reroute, exp])
    db_session.commit()

    reroute_id = reroute.id
    exp_id = exp.id

    # Delete project
    db_session.delete(project)
    db_session.commit()

    assert db_session.query(RerouteHistory).filter_by(id=reroute_id).first() is None
    assert db_session.query(ABTestExperiment).filter_by(id=exp_id).first() is None


def test_phase4_backward_compatibility_with_phases1_to_3(db_session):
    """Verify all models from Phases 1, 2, 3, and 4 work harmoniously together."""
    project = Project(name="All Phases Project", label_set=["pos", "neg"])
    annotator = Annotator(username="unified_user", email="u@example.com")
    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(project_id=project.id, external_id="unified-001", content={"text": "All phases"})
    db_session.add(item)
    db_session.commit()

    annotation = Annotation(project_id=project.id, item_id=item.id, annotator_id=annotator.id, label="pos", confidence=0.9)
    trust_score = TrustScore(project_id=project.id, item_id=item.id, final_score=0.92, flagged=False)
    behavioral = BehavioralScore(project_id=project.id, annotator_id=annotator.id, item_id=item.id, time_score=0.88)
    embedding = EmbeddingResult(project_id=project.id, item_id=item.id, model_name="all-mini", outlier_score=0.05)
    threshold = ProjectThreshold(project_id=project.id, gold_threshold=0.95)
    decision = ReviewerDecision(project_id=project.id, item_id=item.id, review_status="CONFIRM", reviewed_by=annotator.id)
    connector = ExternalDBConnector(connection_name="all_phases_conn", database_name="ext_db")
    reroute = RerouteHistory(item_id=item.id, project_id=project.id, original_annotator_id=annotator.id, reroute_status="COMPLETED")
    exp = ABTestExperiment(experiment_name="Unified Exp", project_id=project.id, schema_version_a={}, schema_version_b={})

    db_session.add_all([annotation, trust_score, behavioral, embedding, threshold, decision, connector, reroute, exp])
    db_session.commit()

    assert annotation.id is not None
    assert trust_score.id is not None
    assert behavioral.id is not None
    assert embedding.id is not None
    assert threshold.id is not None
    assert decision.id is not None
    assert connector.id is not None
    assert reroute.id is not None
    assert exp.id is not None
