"""
Intelligent annotator selection for Phase 4 task rerouting.

This module recommends the best eligible annotator for a task
that needs to be rerouted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RerouteRecommendation:
    """Recommended annotator for a rerouted task."""

    item_id: str
    original_annotator_id: Optional[str]
    recommended_annotator_id: Optional[str]
    recommendation_score: Optional[float]
    reason: str
    eligible_candidates: List[str]


def recommend_annotator(
    item_id: str,
    original_annotator_id: Optional[str],
    annotator_performance: List[Dict[str, Any]],
    minimum_accuracy: float = 0.90,
    minimum_trust: float = 0.60,
) -> RerouteRecommendation:
    """
    Recommend the strongest eligible annotator for a rerouted task.

    Candidates are rejected when they:
    - are the original annotator,
    - are explicitly marked as underperforming,
    - have accuracy below minimum_accuracy, or
    - have trust below minimum_trust when trust data is available.

    Eligible candidates are ranked primarily by rolling accuracy
    and secondarily by average trust score.

    Args:
        item_id:
            ID of the item being rerouted.

        original_annotator_id:
            Annotator who originally handled the item.

        annotator_performance:
            Performance dictionaries containing:
            annotator_id, rolling_accuracy,
            average_trust_score, and underperforming.

        minimum_accuracy:
            Minimum acceptable rolling accuracy.

        minimum_trust:
            Minimum acceptable trust score.

    Returns:
        RerouteRecommendation containing the selected annotator
        and the reason for the recommendation.
    """

    if not 0.0 <= minimum_accuracy <= 1.0:
        raise ValueError("minimum_accuracy must be between 0 and 1")

    if not 0.0 <= minimum_trust <= 1.0:
        raise ValueError("minimum_trust must be between 0 and 1")

    eligible: List[Dict[str, Any]] = []

    for performance in annotator_performance:
        annotator_id = performance.get("annotator_id")

        if annotator_id is None:
            continue

        annotator_id = str(annotator_id)

        # Never send a rerouted task back to the original annotator.
        if (
            original_annotator_id is not None
            and annotator_id == str(original_annotator_id)
        ):
            continue

        # Do not use an annotator already identified as underperforming.
        if performance.get("underperforming", False):
            continue

        accuracy = _to_float(performance.get("rolling_accuracy"))

        if accuracy is None or accuracy < minimum_accuracy:
            continue

        trust = _to_float(performance.get("average_trust_score"))

        # If trust information exists, enforce the trust threshold.
        if trust is not None and trust < minimum_trust:
            continue

        eligible.append(
            {
                "annotator_id": annotator_id,
                "accuracy": accuracy,
                "trust": trust,
            }
        )

    eligible_ids = [
        candidate["annotator_id"]
        for candidate in eligible
    ]

    if not eligible:
        return RerouteRecommendation(
            item_id=str(item_id),
            original_annotator_id=(
                str(original_annotator_id)
                if original_annotator_id is not None
                else None
            ),
            recommended_annotator_id=None,
            recommendation_score=None,
            reason="No eligible annotator meets the configured quality thresholds.",
            eligible_candidates=[],
        )

    # Accuracy is the primary signal. Trust is the secondary signal.
    eligible.sort(
        key=lambda candidate: (
            candidate["accuracy"],
            candidate["trust"] if candidate["trust"] is not None else 0.0,
        ),
        reverse=True,
    )

    selected = eligible[0]

    trust_text = (
        f"{selected['trust']:.2f}"
        if selected["trust"] is not None
        else "unavailable"
    )

    reason = (
        f"Recommended annotator {selected['annotator_id']} "
        f"with rolling accuracy {selected['accuracy']:.2f} "
        f"and average trust score {trust_text}."
    )

    return RerouteRecommendation(
        item_id=str(item_id),
        original_annotator_id=(
            str(original_annotator_id)
            if original_annotator_id is not None
            else None
        ),
        recommended_annotator_id=selected["annotator_id"],
        recommendation_score=round(
            selected["accuracy"],
            4,
        ),
        reason=reason,
        eligible_candidates=eligible_ids,
    )


def _to_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None