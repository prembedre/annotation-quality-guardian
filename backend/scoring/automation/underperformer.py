"""
Underperforming annotator detection for Phase 4 automation.

Combines the existing Phase 3 gold-standard accuracy calculation
with TrustScore history to identify annotators who may need
automatic task rerouting.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from scoring.leaderboard.service import calculate_rolling_accuracy


@dataclass
class AnnotatorPerformance:
    """Aggregated quality metrics for one annotator."""

    annotator_id: str
    total_annotations: int
    rolling_accuracy: float
    gold_correct: int
    gold_annotations: int
    average_trust_score: Optional[float]
    underperforming: bool
    reasons: List[str]


def detect_underperformers(
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
    trust_scores: List[Dict[str, Any]],
    gold_threshold: float = 0.90,
    trust_threshold: float = 0.60,
    minimum_annotations: int = 10,
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> List[AnnotatorPerformance]:
    """
    Identify annotators whose recent performance is below quality thresholds.

    An annotator is considered underperforming when they have at least
    minimum_annotations in the rolling window and either:

    1. Rolling gold accuracy is below gold_threshold, or
    2. Average trust score is below trust_threshold.
    """

    if not 0.0 <= gold_threshold <= 1.0:
        raise ValueError("gold_threshold must be between 0 and 1")

    if not 0.0 <= trust_threshold <= 1.0:
        raise ValueError("trust_threshold must be between 0 and 1")

    if minimum_annotations < 1:
        raise ValueError("minimum_annotations must be greater than 0")

    if window_days <= 0:
        raise ValueError("window_days must be greater than 0")

    rolling_accuracy = calculate_rolling_accuracy(
        annotations=annotations,
        gold_items=gold_items,
        window_days=window_days,
        as_of=as_of,
    )

    recent_annotations = _filter_recent_annotations(
        annotations=annotations,
        window_days=window_days,
        as_of=as_of,
    )

    annotator_annotations: Dict[str, List[Dict[str, Any]]] = {}

    for annotation in recent_annotations:
        annotator_id = str(annotation["annotator_id"])
        annotator_annotations.setdefault(annotator_id, []).append(annotation)

    trust_by_item: Dict[str, float] = {}

    for trust_score in trust_scores:
        item_id = trust_score.get("item_id")
        final_score = trust_score.get("final_score")

        if item_id is None or final_score is None:
            continue

        try:
            trust_by_item[str(item_id)] = float(final_score)
        except (TypeError, ValueError):
            continue

    results: List[AnnotatorPerformance] = []

    for annotator_id, records in annotator_annotations.items():

        stats = rolling_accuracy.get(
            annotator_id,
            {
                "accuracy": 0.0,
                "correct": 0,
                "total": 0,
            },
        )

        accuracy = float(stats["accuracy"])
        gold_correct = int(stats["correct"])
        gold_annotations = int(stats["total"])

        annotator_trust_scores: List[float] = []

        for annotation in records:
            item_id = annotation.get("item_id")

            if item_id is None:
                continue

            trust_score = trust_by_item.get(str(item_id))

            if trust_score is not None:
                annotator_trust_scores.append(trust_score)

        average_trust_score = (
            sum(annotator_trust_scores) / len(annotator_trust_scores)
            if annotator_trust_scores
            else None
        )

        reasons: List[str] = []

        if len(records) >= minimum_annotations:

            if accuracy < gold_threshold and gold_annotations > 0:
                reasons.append(
                    f"Rolling accuracy {accuracy:.2f} "
                    f"is below threshold {gold_threshold:.2f}"
                )

            if (
                average_trust_score is not None
                and average_trust_score < trust_threshold
            ):
                reasons.append(
                    f"Average trust score {average_trust_score:.2f} "
                    f"is below threshold {trust_threshold:.2f}"
                )

        results.append(
            AnnotatorPerformance(
                annotator_id=annotator_id,
                total_annotations=len(records),
                rolling_accuracy=accuracy,
                gold_correct=gold_correct,
                gold_annotations=gold_annotations,
                average_trust_score=(
                    round(average_trust_score, 4)
                    if average_trust_score is not None
                    else None
                ),
                underperforming=bool(reasons),
                reasons=reasons,
            )
        )

    results.sort(
        key=lambda result: (
            not result.underperforming,
            result.rolling_accuracy,
        )
    )

    return results


def _filter_recent_annotations(
    annotations: List[Dict[str, Any]],
    window_days: int,
    as_of: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Return annotations inside the rolling evaluation window."""

    dated_annotations = [
        annotation
        for annotation in annotations
        if isinstance(annotation.get("created_at"), datetime)
    ]

    if not dated_annotations:
        return []

    reference_time = as_of or max(
        annotation["created_at"]
        for annotation in dated_annotations
    )

    window_start = reference_time - timedelta(days=window_days)

    return [
        annotation
        for annotation in dated_annotations
        if window_start <= annotation["created_at"] <= reference_time
    ]