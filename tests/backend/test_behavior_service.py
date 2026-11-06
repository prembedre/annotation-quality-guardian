"""
Unit tests for Behavioral Anomaly Integration Service.
"""

from app.models import Project, Annotator, Item, Annotation, BehavioralScore
from app.services.behavior_service import (
    record_behavioral_score,
    get_behavioral_scores_by_project,
    get_behavioral_score_for_item,
    get_behavioral_score_for_annotator,
    compute_annotator_behavioral_score,
    compute_project_behavioral_scores,
)
from scoring.behavior import (
    calculate_duration_zscore,
    calculate_streak_score,
    calculate_distribution_drift,
    evaluate_behavioral_anomaly,
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


def test_calculate_duration_zscore():
    durations = [2500, 2400, 2600, 2550, 2450]
    # Normal pace near mean
    z, score = calculate_duration_zscore(durations, 2500)
    assert abs(z) < 0.5
    assert score < 0.2

    # Extreme speed-running (100ms)
    z_fast, score_fast = calculate_duration_zscore(durations, 100)
    assert z_fast < -2.0
    assert score_fast >= 0.7


def test_calculate_streak_score():
    # Normal diversity
    labels_normal = ["pos", "neg", "pos", "neu", "pos"]
    streak_norm, score_norm = calculate_streak_score(labels_normal)
    assert streak_norm <= 4
    assert score_norm <= 0.25

    # Straight-lining (10 identical labels)
    labels_repetitive = ["pos"] * 10
    streak_rep, score_rep = calculate_streak_score(labels_repetitive)
    assert streak_rep == 10
    assert score_rep >= 0.75


def test_calculate_distribution_drift():
    project_labels = ["cat"] * 50 + ["dog"] * 50
    # Balanced annotator matches project
    ann_balanced = ["cat"] * 5 + ["dog"] * 5
    drift_low = calculate_distribution_drift(ann_balanced, project_labels)
    assert drift_low == 0.0

    # Highly drifted annotator (all 'cat')
    ann_skewed = ["cat"] * 10
    drift_high = calculate_distribution_drift(ann_skewed, project_labels)
    assert drift_high >= 0.5


def test_compute_project_behavioral_scores(db_session):
    proj = Project(name="Real Behavior Scoring Project", label_set=["pos", "neg"])
    db_session.add(proj)
    db_session.commit()

    # Normal annotator
    ann_good = Annotator(name="Normal Annotator")
    # Anomalous speed-runner who straight-lines
    ann_bot = Annotator(name="Bot Annotator")
    db_session.add_all([ann_good, ann_bot])
    db_session.commit()

    # Create items
    items = [
        Item(project_id=proj.id, external_id=f"beh_it_{i}", content={"text": f"item {i}"})
        for i in range(10)
    ]
    db_session.add_all(items)
    db_session.commit()

    # Normal annotator has varied durations and balanced labels
    for i in range(10):
        db_session.add(
            Annotation(
                project_id=proj.id,
                item_id=items[i].id,
                annotator_id=ann_good.id,
                label="pos" if i % 2 == 0 else "neg",
                duration_ms=2500 + (i * 50),
            )
        )

    # Bot annotator has 50ms durations and 100% "pos" labels
    for i in range(10):
        db_session.add(
            Annotation(
                project_id=proj.id,
                item_id=items[i].id,
                annotator_id=ann_bot.id,
                label="pos",
                duration_ms=50,
            )
        )
    db_session.commit()

    result = compute_project_behavioral_scores(db=db_session, project_id=proj.id)
    assert result["annotators_evaluated"] == 2
    assert result["items_scored"] == 20
    assert result["anomalies_detected"] >= 1

    good_score = get_behavioral_score_for_annotator(db_session, proj.id, ann_good.id)
    bot_score = get_behavioral_score_for_annotator(db_session, proj.id, ann_bot.id)

    assert good_score is not None
    assert bot_score is not None
    assert float(good_score.anomaly_score) < float(bot_score.anomaly_score)
    assert bot_score.details["anomaly_flag"] is True

