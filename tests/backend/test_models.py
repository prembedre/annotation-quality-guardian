"""
Unit tests verifying SQLAlchemy models and relationships.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.db import Base
from app.models import Project, Item, Annotator, Annotation, TrustScore


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
    """Test annotation and trust score relationships."""

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
        item_id=item.id,
        score=0.92,
        breakdown={
            "gold_accuracy": 1.0,
            "agreement": 0.88,
            "anomaly": 0.0,
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

    assert trust_score.item_id == item.id
    assert trust_score.score == 0.92
    assert trust_score.flagged is False

    # Relationship checks
    assert len(item.annotations) == 1
    assert len(item.trust_scores) == 1
    assert item.annotations[0].label == "positive"
    assert item.annotations[0].annotator.username == "sam"
    assert item.annotations[0].project.name == "Quality Test"

    assert item.project.name == "Quality Test"
    assert len(project.items) == 1
    assert len(project.annotations) == 1
    assert len(annotator.annotations) == 1


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
