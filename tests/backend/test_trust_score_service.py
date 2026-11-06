"""
Unit tests for Unified Trust Score Pipeline Service.
"""

from app.models import Project, Item, Annotator, Annotation, BehavioralScore, EmbeddingResult, TrustScore
from app.services.trust_score_service import (
    calculate_trust_score,
    compute_and_save_item_trust_score,
    compute_and_save_project_trust_scores,
    normalize_signal,
)


def test_normalize_signal():
    """Verify normalization of various signal ranges."""
    assert normalize_signal(0.8, "gold") == 0.8
    # Kappa range -1.0 to 1.0 mapped to 0.0 to 1.0
    assert normalize_signal(0.0, "agreement") == 0.5
    assert normalize_signal(1.0, "agreement") == 1.0
    assert normalize_signal(-1.0, "agreement") == 0.0
    assert normalize_signal(None, "behavioral") is None


def test_normalize_signal_inversion():
    """Verify anomaly and outlier scores are inverted so 1.0 = bad → low trust."""
    # High anomaly (1.0 = maximally anomalous) → 0.0 trust
    assert normalize_signal(1.0, "behavioral") == 0.0
    # Low anomaly (0.0 = normal) → 1.0 trust
    assert normalize_signal(0.0, "behavioral") == 1.0
    # Mid anomaly
    assert normalize_signal(0.5, "behavioral") == 0.5

    # High outlier (1.0 = strong outlier) → 0.0 trust
    assert normalize_signal(1.0, "embedding") == 0.0
    # Low outlier (0.0 = inlier) → 1.0 trust
    assert normalize_signal(0.0, "embedding") == 1.0

    # Gold accuracy should NOT be inverted
    assert normalize_signal(1.0, "gold") == 1.0
    assert normalize_signal(0.0, "gold") == 0.0


def test_high_anomaly_gives_low_trust():
    """A high anomaly score (0.95) should result in a low trust score."""
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=None,
        agreement_score=None,
        behavioral_score=0.95,  # raw anomaly: 0.95 = very anomalous
        embedding_score=None,
    )
    # normalize_signal inverts: 1.0 - 0.95 = 0.05
    assert score <= 0.10
    assert flagged is True
    assert "below threshold" in reason


def test_low_anomaly_gives_high_trust():
    """A low anomaly score (0.05) should result in a high trust score."""
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=None,
        agreement_score=None,
        behavioral_score=0.05,  # raw anomaly: 0.05 = nearly normal
        embedding_score=None,
    )
    # normalize_signal inverts: 1.0 - 0.05 = 0.95
    assert score >= 0.90
    assert flagged is False


def test_calculate_trust_score_all_signals():
    """Test unified trust calculation with all 4 signals present.

    Inputs are raw scores:
      - gold=1.0 (accuracy), agreement kappa=1.0
      - behavioral anomaly=0.1 (low anomaly → inverted to 0.9)
      - embedding outlier=0.2 (low outlier → inverted to 0.8)
    """
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=1.0,
        agreement_score=1.0,
        behavioral_score=0.1,   # raw anomaly → inverted to 0.9
        embedding_score=0.2,    # raw outlier → inverted to 0.8
    )
    # Expected: 1.0*0.35 + 1.0*0.25 + 0.9*0.20 + 0.8*0.20 = 0.94
    assert round(score, 2) == 0.94
    assert flagged is False
    assert breakdown["gold"] == 1.0
    assert breakdown["behavioral"] == 0.9  # inverted from 0.1
    assert breakdown["embedding"] == 0.8   # inverted from 0.2


def test_calculate_trust_score_missing_signals_redistribution():
    """Test weight redistribution when signals are partially missing."""
    # Only Gold (0.8) and Agreement (0.6, kappa 0.2->0.6)
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=0.8,
        agreement_score=0.2, # normalized -> 0.6
        behavioral_score=None,
        embedding_score=None,
    )
    # Total active weights: gold(0.35) + agreement(0.25) = 0.60
    # Gold weight: 0.35/0.60 = 7/12 (~0.5833), Agreement: 0.25/0.60 = 5/12 (~0.4167)
    # Score = 0.8*(7/12) + 0.6*(5/12) = (5.6 + 3.0)/12 = 8.6/12 = 0.7167
    assert round(score, 2) == 0.72
    assert flagged is False


def test_calculate_trust_score_flagging_conditions():
    """Test flagging triggered by score threshold, anomaly flag, or outlier."""
    # Score below threshold (0.60)
    # behavioral=0.7 → inverted to 0.3, embedding=0.7 → inverted to 0.3
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=0.2,
        agreement_score=-0.5,
        behavioral_score=0.7,
        embedding_score=0.7,
    )
    assert flagged is True
    assert "below threshold" in reason

    # Outlier flag overrides even if score is OK
    score2, breakdown2, flagged2, reason2 = calculate_trust_score(
        gold_score=0.9,
        agreement_score=0.8,
        behavioral_score=0.1,   # low anomaly → 0.9 trust contribution
        embedding_score=0.1,    # low outlier → 0.9 trust contribution
        is_outlier=True,
    )
    assert flagged2 is True
    assert "Embedding outlier" in reason2


def test_compute_and_save_item_trust_score(db_session):
    """Test end-to-end multi-signal DB computation and persistence."""
    project = Project(id=230, name="Trust Pipeline DB Test", label_set=["cat", "dog"])
    annotator1 = Annotator(id=801, username="ann_801")
    annotator2 = Annotator(id=802, username="ann_802")
    item = Item(id=901, project_id=230, external_id="trust_db_item", is_gold=True, gold_label="cat", content={})
    db_session.add_all([project, annotator1, annotator2, item])
    db_session.flush()

    ann1 = Annotation(project_id=230, item_id=901, annotator_id=801, label="cat")
    ann2 = Annotation(project_id=230, item_id=901, annotator_id=802, label="cat")
    beh = BehavioralScore(project_id=230, annotator_id=801, item_id=901, anomaly_score=0.05, details={"anomaly_flag": False})
    emb = EmbeddingResult(project_id=230, item_id=901, model_name="v1", outlier_score=0.10, is_outlier=False)
    db_session.add_all([ann1, ann2, beh, emb])
    db_session.commit()

    ts = compute_and_save_item_trust_score(db=db_session, project_id=230, item_id=901)
    assert ts.id is not None
    assert float(ts.final_score) >= 0.90
    assert ts.flagged is False
    assert "weights_applied" in ts.breakdown

    # Project batch computation
    summary = compute_and_save_project_trust_scores(db=db_session, project_id=230)
    assert summary["total_items_processed"] == 1
    assert summary["status"] == "completed"
