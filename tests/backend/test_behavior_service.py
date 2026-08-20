"""
Unit tests for Behavioral Anomaly Integration Service.
"""

from app.models import Project, Annotator, Item, BehavioralScore
from app.services.behavior_service import (
    record_behavioral_score,
    get_behavioral_scores_by_project,
    get_behavioral_score_for_item,
    get_behavioral_score_for_annotator,
)


def test_record_and_update_behavioral_score(db_session):
    """Test recording and updating behavioral anomaly results."""
    project = Project(id=210, name="Behavior Service Test", label_set=["cat", "dog"])
    annotator = Annotator(id=501, username="test_annotator_501")
    item = Item(id=601, project_id=210, external_id="beh_item_1", content={})
    db_session.add_all([project, annotator, item])
    db_session.commit()

    # Record initial score
    score1 = record_behavioral_score(
        db=db_session,
        project_id=210,
        annotator_id=501,
        anomaly_score=0.25,
        item_id=601,
        time_score=0.90,
        streak_score=0.80,
        anomaly_flag=False,
    )
    assert score1.id is not None
    assert float(score1.anomaly_score) == 0.25
    assert score1.details["anomaly_flag"] is False

    # Update with anomalous values
    score2 = record_behavioral_score(
        db=db_session,
        project_id=210,
        annotator_id=501,
        anomaly_score=0.88,
        item_id=601,
        time_score=0.10,
        streak_score=0.20,
        anomaly_flag=True,
        reason="Repeated click duration under 10ms",
    )
    assert score2.id == score1.id
    assert float(score2.anomaly_score) == 0.88
    assert score2.details["anomaly_flag"] is True
    assert "Repeated click" in score2.details["reason"]


def test_query_behavioral_scores(db_session):
    """Test querying behavioral scores by project and annotator."""
    project = Project(id=211, name="Behavior Query Test", label_set=["yes", "no"])
    annotator = Annotator(id=502, username="query_annotator")
    db_session.add_all([project, annotator])
    db_session.commit()

    record_behavioral_score(
        db=db_session,
        project_id=211,
        annotator_id=502,
        anomaly_score=0.15,
        item_id=None,  # Annotator-level aggregate
    )

    ann_score = get_behavioral_score_for_annotator(db=db_session, project_id=211, annotator_id=502)
    assert ann_score is not None
    assert float(ann_score.anomaly_score) == 0.15

    proj_scores = get_behavioral_scores_by_project(db=db_session, project_id=211)
    assert len(proj_scores) == 1
