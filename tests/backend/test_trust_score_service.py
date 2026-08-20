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


def test_calculate_trust_score_all_signals():
    """Test unified trust calculation with all 4 signals present."""
    # Gold=1.0, Agreement Kappa=1.0 (normalized 1.0), Behavioral=0.9, Embedding=0.8
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=1.0,
        agreement_score=1.0,
        behavioral_score=0.9,
        embedding_score=0.8,
    )
    # Expected: 1.0*0.35 + 1.0*0.25 + 0.9*0.20 + 0.8*0.20 = 0.35 + 0.25 + 0.18 + 0.16 = 0.94
    assert round(score, 2) == 0.94
    assert flagged is False
    assert breakdown["gold"] == 1.0
    assert breakdown["behavioral"] == 0.9
    assert breakdown["embedding"] == 0.8


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
    score, breakdown, flagged, reason = calculate_trust_score(
        gold_score=0.2,
        agreement_score=-0.5,
        behavioral_score=0.3,
        embedding_score=0.3,
    )
    assert flagged is True
    assert "below threshold" in reason

    # Outlier flag overrides
    score2, breakdown2, flagged2, reason2 = calculate_trust_score(
        gold_score=0.9,
        agreement_score=0.8,
        behavioral_score=0.9,
        embedding_score=0.9,
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
