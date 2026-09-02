"""
Unit tests for Phase 3 Database Schema, Models, Relationships, Constraints, and Migrations.
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
)


@pytest.fixture
def db_session():
    """Create an isolated SQLite database session for Phase 3 model tests."""
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


def test_create_project_threshold_and_defaults(db_session):
    """Test creating a project threshold configuration with default values."""
    project = Project(
        name="Threshold Test Project",
        description="Testing threshold settings",
        label_set=["pos", "neg"],
    )
    db_session.add(project)
    db_session.commit()

    threshold = ProjectThreshold(
        project_id=project.id,
        gold_threshold=0.90,
        kappa_threshold=0.70,
        behavioral_threshold=0.75,
        embedding_threshold=0.80,
        trust_threshold=0.60,
    )
    db_session.add(threshold)
    db_session.commit()
    db_session.refresh(threshold)

    assert threshold.id is not None
    assert threshold.project_id == project.id
    assert float(threshold.gold_threshold) == 0.90
    assert float(threshold.kappa_threshold) == 0.70
    assert float(threshold.behavioral_threshold) == 0.75
    assert float(threshold.embedding_threshold) == 0.80
    assert float(threshold.trust_threshold) == 0.60

    # Verify 1-to-1 relationship
    assert project.threshold == threshold
    assert threshold.project == project


def test_unique_project_threshold_constraint(db_session):
    """Test that a project can have only one threshold configuration."""
    project = Project(
        name="Unique Threshold Project",
        label_set=["label1", "label2"],
    )
    db_session.add(project)
    db_session.commit()

    threshold1 = ProjectThreshold(
        project_id=project.id,
        gold_threshold=0.85,
    )
    db_session.add(threshold1)
    db_session.commit()

    threshold2 = ProjectThreshold(
        project_id=project.id,
        gold_threshold=0.95,
    )
    db_session.add(threshold2)

    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()


def test_reviewer_decision_workflow_actions(db_session):
    """Test creating reviewer decision records for CONFIRM, CORRECT, and ESCALATE."""
    project = Project(
        name="Reviewer Workflow Project",
        label_set=["A", "B", "C"],
    )
    reviewer = Annotator(
        username="lead_reviewer",
        email="lead@example.com",
    )
    annotator = Annotator(
        username="worker_annotator",
        email="worker@example.com",
    )
    db_session.add_all([project, reviewer, annotator])
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="item-flagged-001",
        content={"text": "Ambiguous input data"},
    )
    db_session.add(item)
    db_session.commit()

    annotation = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="A",
    )
    db_session.add(annotation)
    db_session.commit()

    # 1. Action: CONFIRM
    decision_confirm = ReviewerDecision(
        project_id=project.id,
        item_id=item.id,
        annotation_id=annotation.id,
        review_status="CONFIRM",
        reviewed_by=reviewer.id,
        corrected_label="A",
        review_notes="Confirmed existing label A",
    )

    # 2. Action: CORRECT
    decision_correct = ReviewerDecision(
        project_id=project.id,
        item_id=item.id,
        annotation_id=annotation.id,
        review_status="CORRECT",
        reviewed_by=reviewer.id,
        corrected_label="B",
        review_notes="Overrode label to B based on guidelines",
    )

    # 3. Action: ESCALATE
    decision_escalate = ReviewerDecision(
        project_id=project.id,
        item_id=item.id,
        annotation_id=None,
        review_status="ESCALATE",
        reviewed_by=reviewer.id,
        review_notes="Escalated to domain expert",
    )

    db_session.add_all([decision_confirm, decision_correct, decision_escalate])
    db_session.commit()

    assert decision_confirm.id is not None
    assert decision_correct.id is not None
    assert decision_escalate.id is not None

    assert decision_confirm.review_status == "CONFIRM"
    assert decision_correct.review_status == "CORRECT"
    assert decision_escalate.review_status == "ESCALATE"

    # Verify relationships
    assert len(item.reviewer_decisions) == 3
    assert len(project.reviewer_decisions) == 3
    assert len(reviewer.reviewed_decisions) == 3
    assert annotation.reviewer_decisions[0].review_status in ["CONFIRM", "CORRECT"]


def test_cascade_deletions(db_session):
    """Test cascade deletion behavior for thresholds and reviewer decisions."""
    project = Project(
        name="Cascade Test Project",
        label_set=["yes", "no"],
    )
    reviewer = Annotator(username="cascade_reviewer", email="rev@example.com")
    db_session.add_all([project, reviewer])
    db_session.commit()

    threshold = ProjectThreshold(project_id=project.id, trust_threshold=0.65)
    item = Item(project_id=project.id, external_id="cascade-item", content={})
    db_session.add_all([threshold, item])
    db_session.commit()

    decision = ReviewerDecision(
        project_id=project.id,
        item_id=item.id,
        review_status="CONFIRM",
        reviewed_by=reviewer.id,
    )
    db_session.add(decision)
    db_session.commit()

    # Delete project and verify cascade delete on thresholds and decisions
    db_session.delete(project)
    db_session.commit()

    assert db_session.query(ProjectThreshold).filter_by(id=threshold.id).first() is None
    assert db_session.query(Item).filter_by(id=item.id).first() is None
    assert db_session.query(ReviewerDecision).filter_by(id=decision.id).first() is None


def test_phase1_phase2_backward_compatibility(db_session):
    """Verify Phase 1 and Phase 2 entities continue to work without regression."""
    project = Project(name="Compat Project", label_set=["cat", "dog"])
    annotator = Annotator(username="compat_user", email="user@example.com")
    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(project_id=project.id, external_id="compat-001", content={"img": "cat.jpg"})
    db_session.add(item)
    db_session.commit()

    annotation = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="cat",
        confidence=0.99,
    )
    trust_score = TrustScore(
        project_id=project.id,
        item_id=item.id,
        final_score=0.95,
        flagged=False,
    )
    behavioral_score = BehavioralScore(
        project_id=project.id,
        annotator_id=annotator.id,
        item_id=item.id,
        time_score=0.9,
    )
    embedding_result = EmbeddingResult(
        project_id=project.id,
        item_id=item.id,
        model_name="test_model",
        outlier_score=0.1,
    )
    db_session.add_all([annotation, trust_score, behavioral_score, embedding_result])
    db_session.commit()

    assert annotation.id is not None
    assert trust_score.id is not None
    assert behavioral_score.id is not None
    assert embedding_result.id is not None

    # Test backward compatible aliases
    assert annotator.name == "compat_user"
    assert trust_score.score == 0.95
