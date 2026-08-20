"""
Unified Trust Score Pipeline Service.
Combines Gold Accuracy, Annotator Agreement, Behavioral Anomaly, and Embedding Outlier
signals into a single robust Trust Score (0.0–1.0) with detailed explainability breakdown.
"""

from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.trust_score import TrustScore
from app.models.item import Item
from app.models.annotation import Annotation
from app.models.behavioral_score import BehavioralScore
from app.models.embedding_result import EmbeddingResult
from app.models.project import Project
from app.services.gold_standard_service import compute_gold_accuracy
from app.services.kappa_service import compute_fleiss_kappa


# Configurable default signal weights (sum to 1.0)
DEFAULT_SIGNAL_WEIGHTS = {
    "gold": 0.35,
    "agreement": 0.25,
    "behavioral": 0.20,
    "embedding": 0.20,
}

# Trust score threshold below which an item is flagged for human review
DEFAULT_FLAG_THRESHOLD = 0.60


def normalize_signal(value: Optional[float], signal_type: str) -> Optional[float]:
    """
    Normalize signal value to [0.0, 1.0] where 1.0 represents highest quality/trust.

    Args:
        value: Raw signal value (or None if unavailable)
        signal_type: One of 'gold', 'agreement', 'behavioral', 'embedding'
    """
    if value is None:
        return None

    try:
        val = float(value)
    except (ValueError, TypeError):
        return None

    if signal_type == "gold":
        return max(0.0, min(1.0, val))

    elif signal_type == "agreement":
        # Kappa ranges from -1.0 to 1.0. Normalize to [0.0, 1.0]
        # (val + 1.0) / 2.0 maps -1 -> 0, 0 -> 0.5, 1 -> 1.0
        normalized = (val + 1.0) / 2.0
        return max(0.0, min(1.0, normalized))

    elif signal_type == "behavioral":
        # If input represents anomaly_score (where 1.0 = anomaly), convert to quality trust metric (1.0 - anomaly)
        # Otherwise ensure [0.0, 1.0] range
        return max(0.0, min(1.0, val))

    elif signal_type == "embedding":
        # If input is outlier_score, quality trust metric is (1.0 - outlier)
        return max(0.0, min(1.0, val))

    return max(0.0, min(1.0, val))


def calculate_trust_score(
    gold_score: Optional[float] = None,
    agreement_score: Optional[float] = None,
    behavioral_score: Optional[float] = None,
    embedding_score: Optional[float] = None,
    weights: Optional[Dict[str, float]] = None,
    flag_threshold: float = DEFAULT_FLAG_THRESHOLD,
    anomaly_flag: bool = False,
    is_outlier: bool = False,
) -> Tuple[float, Dict[str, Any], bool, Optional[str]]:
    """
    Combine available signals into a final Trust Score.

    Missing signals are omitted and weights are dynamically normalized
    among active signals.

    Returns:
        (final_score, breakdown_dict, flagged_bool, flag_reason_str)
    """
    base_weights = dict(weights or DEFAULT_SIGNAL_WEIGHTS)

    # Normalize inputs
    norm_gold = normalize_signal(gold_score, "gold")
    norm_agreement = normalize_signal(agreement_score, "agreement")
    norm_behavioral = normalize_signal(behavioral_score, "behavioral")
    norm_embedding = normalize_signal(embedding_score, "embedding")

    signals = {
        "gold": norm_gold,
        "agreement": norm_agreement,
        "behavioral": norm_behavioral,
        "embedding": norm_embedding,
    }

    # Filter active signals
    active_signals = {k: v for k, v in signals.items() if v is not None}

    if not active_signals:
        # Default baseline when no signals available
        final_score = 1.0
        active_weights = {}
    else:
        total_active_weight = sum(base_weights.get(k, 0.0) for k in active_signals)
        if total_active_weight > 0:
            active_weights = {
                k: base_weights.get(k, 0.0) / total_active_weight
                for k in active_signals
            }
        else:
            equal_w = 1.0 / len(active_signals)
            active_weights = {k: equal_w for k in active_signals}

        final_score = sum(active_signals[k] * active_weights[k] for k in active_signals)

    final_score = round(max(0.0, min(1.0, final_score)), 4)

    # Determine flag status and reason
    flag_reasons = []
    if final_score < flag_threshold:
        flag_reasons.append(f"Trust score ({final_score:.2f}) below threshold ({flag_threshold:.2f})")
    if anomaly_flag:
        flag_reasons.append("Behavioral anomaly detected in annotator activity")
    if is_outlier:
        flag_reasons.append("Embedding outlier detected in dataset distribution")
    if norm_gold is not None and norm_gold < 0.5:
        flag_reasons.append("Gold standard verification mismatch")

    is_flagged = len(flag_reasons) > 0
    flag_reason_str = "; ".join(flag_reasons) if flag_reasons else None

    breakdown = {
        "gold": norm_gold,
        "agreement": norm_agreement,
        "behavioral": norm_behavioral,
        "embedding": norm_embedding,
        "raw_gold": gold_score,
        "raw_agreement": agreement_score,
        "raw_behavioral": behavioral_score,
        "raw_embedding": embedding_score,
        "weights_applied": active_weights,
        "flag_threshold": flag_threshold,
        "flag_reason": flag_reason_str,
        "anomaly_flag": anomaly_flag,
        "is_outlier": is_outlier,
    }

    return final_score, breakdown, is_flagged, flag_reason_str


def compute_and_save_item_trust_score(
    db: Session,
    project_id: int,
    item_id: int,
    weights: Optional[Dict[str, float]] = None,
) -> TrustScore:
    """
    Compute multi-signal TrustScore for an individual item and persist to database.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ValueError(f"Item {item_id} not found.")

    # 1. Gold score
    gold_score = None
    if item.is_gold and item.gold_label:
        annotations = item.annotations
        if annotations:
            correct = sum(1 for a in annotations if a.label == item.gold_label)
            gold_score = correct / len(annotations)

    # 2. Agreement score (majority agreement ratio for this item)
    agreement_score = None
    annotations = item.annotations
    if len(annotations) >= 2:
        from collections import Counter
        counts = Counter(a.label for a in annotations)
        most_common_count = counts.most_common(1)[0][1]
        agreement_score = most_common_count / len(annotations)

    # 3. Behavioral score
    behavioral_rec = (
        db.query(BehavioralScore)
        .filter(
            BehavioralScore.project_id == project_id,
            BehavioralScore.item_id == item_id,
        )
        .order_by(BehavioralScore.computed_at.desc())
        .first()
    )
    behavioral_score = None
    anomaly_flag = False
    if behavioral_rec:
        # Convert anomaly score (0=normal, 1=anomaly) to quality score (1-anomaly)
        raw_anomaly = float(behavioral_rec.anomaly_score) if behavioral_rec.anomaly_score is not None else 0.0
        behavioral_score = 1.0 - raw_anomaly
        anomaly_flag = behavioral_rec.details.get("anomaly_flag", False) if behavioral_rec.details else False

    # 4. Embedding score
    embedding_rec = (
        db.query(EmbeddingResult)
        .filter(
            EmbeddingResult.project_id == project_id,
            EmbeddingResult.item_id == item_id,
        )
        .order_by(EmbeddingResult.computed_at.desc())
        .first()
    )
    embedding_score = None
    is_outlier = False
    if embedding_rec:
        raw_outlier = float(embedding_rec.outlier_score) if embedding_rec.outlier_score is not None else 0.0
        embedding_score = 1.0 - raw_outlier
        is_outlier = embedding_rec.is_outlier

    # Calculate unified score
    final_score, breakdown, flagged, flag_reason = calculate_trust_score(
        gold_score=gold_score,
        agreement_score=agreement_score,
        behavioral_score=behavioral_score,
        embedding_score=embedding_score,
        weights=weights,
        anomaly_flag=anomaly_flag,
        is_outlier=is_outlier,
    )

    # Check for existing TrustScore record
    trust_score = (
        db.query(TrustScore)
        .filter(
            TrustScore.project_id == project_id,
            TrustScore.item_id == item_id,
        )
        .first()
    )

    if trust_score:
        trust_score.gold_score = gold_score
        trust_score.agreement_score = agreement_score
        trust_score.behavioral_score = behavioral_score
        trust_score.embedding_score = embedding_score
        trust_score.final_score = final_score
        trust_score.flagged = flagged
        trust_score.breakdown = breakdown
        trust_score.updated_at = datetime.utcnow()
    else:
        trust_score = TrustScore(
            project_id=project_id,
            item_id=item_id,
            gold_score=gold_score,
            agreement_score=agreement_score,
            behavioral_score=behavioral_score,
            embedding_score=embedding_score,
            final_score=final_score,
            flagged=flagged,
            breakdown=breakdown,
            created_at=datetime.utcnow(),
        )
        db.add(trust_score)

    db.commit()
    db.refresh(trust_score)
    return trust_score


def compute_and_save_project_trust_scores(
    db: Session,
    project_id: int,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Compute and update unified TrustScores for all items in a project.
    """
    items = db.query(Item).filter(Item.project_id == project_id).all()
    updated_count = 0
    flagged_count = 0

    for item in items:
        ts = compute_and_save_item_trust_score(
            db=db,
            project_id=project_id,
            item_id=item.id,
            weights=weights,
        )
        updated_count += 1
        if ts.flagged:
            flagged_count += 1

    return {
        "project_id": project_id,
        "total_items_processed": updated_count,
        "flagged_items": flagged_count,
        "status": "completed",
    }
