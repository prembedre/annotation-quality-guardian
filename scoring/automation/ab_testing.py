"""
A/B testing analysis for Phase 4 label schema experiments.

Compares annotation quality and workflow metrics between
schema variants A and B.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from scoring.gold_checker.checker import gold_accuracy


@dataclass
class ABVariantResult:
    """Metrics calculated for one A/B schema variant."""

    variant: str
    total_annotations: int
    gold_annotations: int
    gold_correct: int
    accuracy: Optional[float]
    average_confidence: Optional[float]
    average_duration_ms: Optional[float]


@dataclass
class ABTestAnalysis:
    """Complete comparison between schema variants A and B."""

    experiment_name: str
    variant_a: ABVariantResult
    variant_b: ABVariantResult
    accuracy_difference: Optional[float]
    recommended_variant: Optional[str]
    recommendation_reason: str


def analyze_ab_test(
    experiment_name: str,
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
    schema_field: str = "schema_version",
) -> ABTestAnalysis:
    """
    Compare annotation performance between schema versions A and B.

    Each annotation should contain its schema version inside metadata,
    for example:

        {
            "item_id": "item-1",
            "annotator_id": 1,
            "label": "Positive",
            "metadata": {
                "schema_version": "A"
            }
        }

    Only annotations explicitly assigned to A or B are analyzed.

    Accuracy is calculated using the project's existing gold-standard
    checker.
    """

    variant_annotations = {
        "A": [],
        "B": [],
    }

    for annotation in annotations:
        metadata = annotation.get("metadata")

        if not isinstance(metadata, dict):
            metadata = annotation.get("metadata_")

        if not isinstance(metadata, dict):
            continue

        variant = str(metadata.get(schema_field, "")).strip().upper()

        if variant in variant_annotations:
            variant_annotations[variant].append(annotation)

    variant_a = _calculate_variant_result(
        variant="A",
        annotations=variant_annotations["A"],
        gold_items=gold_items,
    )

    variant_b = _calculate_variant_result(
        variant="B",
        annotations=variant_annotations["B"],
        gold_items=gold_items,
    )

    accuracy_difference: Optional[float] = None
    recommended_variant: Optional[str] = None
    recommendation_reason = (
        "Insufficient gold-standard data to recommend a schema variant."
    )

    if (
        variant_a.accuracy is not None
        and variant_b.accuracy is not None
    ):
        accuracy_difference = round(
            variant_a.accuracy - variant_b.accuracy,
            4,
        )

        if accuracy_difference > 0:
            recommended_variant = "A"
            recommendation_reason = (
                f"Schema A has higher gold accuracy by "
                f"{abs(accuracy_difference):.4f}."
            )
        elif accuracy_difference < 0:
            recommended_variant = "B"
            recommendation_reason = (
                f"Schema B has higher gold accuracy by "
                f"{abs(accuracy_difference):.4f}."
            )
        else:
            recommended_variant = None
            recommendation_reason = (
                "Schemas A and B have equal gold accuracy."
            )

    return ABTestAnalysis(
        experiment_name=experiment_name,
        variant_a=variant_a,
        variant_b=variant_b,
        accuracy_difference=accuracy_difference,
        recommended_variant=recommended_variant,
        recommendation_reason=recommendation_reason,
    )


def _calculate_variant_result(
    variant: str,
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
) -> ABVariantResult:
    """Calculate metrics for a single schema variant."""

    accuracy_result = gold_accuracy(
        annotations=annotations,
        gold_items=gold_items,
    )

    per_annotator = accuracy_result["per_annotator"]

    gold_correct = sum(
        stats["correct"]
        for stats in per_annotator.values()
    )

    gold_annotations = sum(
        stats["total"]
        for stats in per_annotator.values()
    )

    confidence_values = [
        _to_float(annotation.get("confidence"))
        for annotation in annotations
        if annotation.get("confidence") is not None
    ]

    duration_values = [
        _to_float(annotation.get("duration_ms"))
        for annotation in annotations
        if annotation.get("duration_ms") is not None
    ]

    return ABVariantResult(
        variant=variant,
        total_annotations=len(annotations),
        gold_annotations=gold_annotations,
        gold_correct=gold_correct,
        accuracy=(
            round(gold_correct / gold_annotations, 4)
            if gold_annotations > 0
            else None
        ),
        average_confidence=(
            round(
                sum(confidence_values) / len(confidence_values),
                4,
            )
            if confidence_values
            else None
        ),
        average_duration_ms=(
            round(
                sum(duration_values) / len(duration_values),
                2,
            )
            if duration_values
            else None
        ),
    )


def _to_float(value: Any) -> Optional[float]:
    """Safely convert a value to float."""

    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None