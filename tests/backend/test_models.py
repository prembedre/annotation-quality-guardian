"""
Unit tests verifying SQLAlchemy models and relationships.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.db import Base
from app.models import Item, Annotator, Annotation, TrustScore


@pytest.fixture
def db_session():
    """In-memory SQLite test database session."""
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def test_create_item_and_annotator(db_session):
    item = Item(source="sentiment_dataset", content={"text": "Outstanding support experience."})
    annotator = Annotator(name="Alex Smith", email="alex@example.com")
    
    db_session.add_all([item, annotator])
    db_session.commit()

    assert item.id is not None
    assert annotator.id is not None


def test_create_annotation_and_trust_score(db_session):
    item = Item(source="qa_dataset", content={"question": "What is AQG?"})
    annotator = Annotator(name="Sam", email="sam@example.com")
    db_session.add_all([item, annotator])
    db_session.commit()

    annotation = Annotation(
        item_id=item.id,
        annotator_id=annotator.id,
        label="positive",
        confidence=0.98,
    )
    trust_score = TrustScore(
        item_id=item.id,
        score=0.92,
        breakdown={"gold_accuracy": 1.0, "agreement": 0.88, "anomaly": 0.0},
        flagged=False,
    )

    db_session.add_all([annotation, trust_score])
    db_session.commit()

    assert annotation.id is not None
    assert trust_score.id is not None
    assert len(item.annotations) == 1
    assert len(item.trust_scores) == 1
    assert item.annotations[0].label == "positive"
