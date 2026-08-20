"""
Unit tests verifying SQLAlchemy models and relationships.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models import (
    Project,
    Item,
    Annotator,
    Annotation,
    TrustScore,
    BehavioralScore,
    EmbeddingResult,
)


@pytest.fixture
def db_session():
    """Create an isolated SQLite database for model tests."""
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


def test_create_project_and_item(db_session):
    """Test creating a project and an item belonging to it."""

    project = Project(
        name="Sentiment Analysis",
        description="Test sentiment project",
        label_set=["positive", "negative", "neutral"],
    )

    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    item = Item(
        project_id=project.id,
        external_id="item-001",
        content={"text": "Excellent product!"},
        is_gold=True,
        gold_label="positive",
    )

    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)

    assert project.id is not None
    assert item.id is not None
    assert item.project_id == project.id
    assert item.external_id == "item-001"
    assert item.is_gold is True
    assert item.gold_label == "positive"


def test_create_annotator(db_session):
    """Test creating an annotator."""

    annotator = Annotator(
        username="alex",
        email="alex@example.com",
    )

    db_session.add(annotator)
    db_session.commit()
    db_session.refresh(annotator)

    assert annotator.id is not None
    assert annotator.username == "alex"
    assert annotator.email == "alex@example.com"


def test_create_annotation_and_trust_score(db_session):
    """Test annotation and Phase 2 trust score relationships."""

    project = Project(
        name="Quality Test",
        label_set=["positive", "negative", "neutral"],
    )

    annotator = Annotator(
        username="sam",
        email="sam@example.com",
    )

    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="item-001",
        content={"text": "What is AQG?"},
    )

    db_session.add(item)
    db_session.commit()

    annotation = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="positive",
        confidence=0.98,
        duration_ms=1500,
        metadata={"source": "test"},
    )

    trust_score = TrustScore(
        project_id=project.id,
        item_id=item.id,
        gold_score=1.0,
        agreement_score=0.88,
        behavioral_score=0.90,
        embedding_score=0.85,
        final_score=0.92,
        breakdown={
            "gold": 1.0,
            "agreement": 0.88,
            "behavioral": 0.90,
            "embedding": 0.85,
        },
        flagged=False,
    )

    db_session.add_all([annotation, trust_score])
    db_session.commit()

    db_session.refresh(annotation)
    db_session.refresh(trust_score)

    assert annotation.id is not None
    assert trust_score.id is not None

    assert annotation.project_id == project.id
    assert annotation.item_id == item.id
    assert annotation.annotator_id == annotator.id
    assert annotation.label == "positive"
    assert annotation.confidence == 0.98

    assert trust_score.project_id == project.id
    assert trust_score.item_id == item.id
    assert float(trust_score.final_score) == 0.92
    assert trust_score.flagged is False

    assert len(item.annotations) == 1
    assert len(item.trust_scores) == 1
    assert item.annotations[0].label == "positive"
    assert item.annotations[0].annotator.username == "sam"
    assert item.annotations[0].project.name == "Quality Test"

    assert item.project.name == "Quality Test"
    assert len(project.items) == 1
    assert len(project.annotations) == 1
    assert len(annotator.annotations) == 1


def test_create_behavioral_score(db_session):
    """Test creating a behavioral scoring result."""

    project = Project(
        name="Behavioral Test",
        label_set=["yes", "no"],
    )

    annotator = Annotator(
        username="behavior_user",
        email="behavior@example.com",
    )

    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="behavior-item",
        content={"text": "Behavior test"},
    )

    db_session.add(item)
    db_session.commit()

    behavioral_score = BehavioralScore(
        project_id=project.id,
        annotator_id=annotator.id,
        item_id=item.id,
        time_score=0.90,
        streak_score=0.85,
        anomaly_score=0.10,
        details={
            "reason": "Normal annotation behavior",
        },
    )

    db_session.add(behavioral_score)
    db_session.commit()
    db_session.refresh(behavioral_score)

    assert behavioral_score.id is not None
    assert behavioral_score.project_id == project.id
    assert behavioral_score.annotator_id == annotator.id
    assert behavioral_score.item_id == item.id
    assert float(behavioral_score.time_score) == 0.90
    assert float(behavioral_score.streak_score) == 0.85
    assert float(behavioral_score.anomaly_score) == 0.10


def test_create_embedding_result(db_session):
    """Test creating an embedding result."""

    project = Project(
        name="Embedding Test",
        label_set=["positive", "negative"],
    )

    db_session.add(project)
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="embedding-item",
        content={"text": "Embedding test"},
    )

    nearest_item = Item(
        project_id=project.id,
        external_id="nearest-item",
        content={"text": "Nearest item"},
    )

    db_session.add_all([item, nearest_item])
    db_session.commit()

    embedding_result = EmbeddingResult(
        project_id=project.id,
        item_id=item.id,
        model_name="sentence-transformers",
        embedding=[0.12, 0.45, 0.78],
        outlier_score=0.18,
        is_outlier=False,
        nearest_item_id=nearest_item.id,
        details={
            "method": "cosine_similarity",
        },
    )

    db_session.add(embedding_result)
    db_session.commit()
    db_session.refresh(embedding_result)

    assert embedding_result.id is not None
    assert embedding_result.project_id == project.id
    assert embedding_result.item_id == item.id
    assert embedding_result.model_name == "sentence-transformers"
    assert float(embedding_result.outlier_score) == 0.18
    assert embedding_result.is_outlier is False
    assert embedding_result.nearest_item_id == nearest_item.id


def test_annotation_unique_per_item_and_annotator(db_session):
    """Test that one annotator cannot annotate the same item twice."""

    project = Project(
        name="Unique Test",
        label_set=["yes", "no"],
    )

    annotator = Annotator(
        username="unique_user",
        email="unique@example.com",
    )

    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="unique-item",
        content={"text": "Test"},
    )

    db_session.add(item)
    db_session.commit()

    annotation = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="yes",
        confidence=0.9,
    )

    db_session.add(annotation)
    db_session.commit()

    duplicate = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="no",
        confidence=0.5,
    )

    db_session.add(duplicate)

    with pytest.raises(Exception):
        db_session.commit()

    db_session.rollback()


def test_project_relationships(db_session):
    """Test project-to-item and project-to-annotation relationships."""

    project = Project(
        name="Relationship Test",
        label_set=["a", "b"],
    )

    annotator = Annotator(
        username="relationship_user",
        email="relationship@example.com",
    )

    db_session.add_all([project, annotator])
    db_session.commit()

    item = Item(
        project_id=project.id,
        external_id="relationship-item",
        content={"text": "Relationship test"},
    )

    db_session.add(item)
    db_session.commit()

    annotation = Annotation(
        project_id=project.id,
        item_id=item.id,
        annotator_id=annotator.id,
        label="a",
        confidence=0.95,
    )

    db_session.add(annotation)
    db_session.commit()

    assert item.project == project
    assert annotation.project == project
    assert annotation.item == item
    assert annotation.annotator == annotator
    assert annotation in project.annotations
    assert annotation in annotator.annotations
    assert item in project.items
