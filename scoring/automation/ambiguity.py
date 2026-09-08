"""
Ambiguous class detection for Phase 4 automation.

Uses the existing Phase 3 disagreement statistics to identify
label classes that may be unclear or difficult for annotators.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from scoring.agreement.heatmap import calculate_disagreement_statistics


@dataclass
class AmbiguousClass:
    """Analysis result for one label class."""

    label: str
    disagreements: int
    occurrences: int
    total_comparisons: int
    disagreement_rate: float
    ambiguous: bool


def detect_ambiguous_classes(
    annotations: List[Dict[str, Any]],
    disagreement_threshold: float = 0.50,
    minimum_comparisons: int = 5,
) -> List[AmbiguousClass]:
    """
    Identify label classes with high disagreement between annotators.

    A class is considered ambiguous when:

    1. It has at least `minimum_comparisons` comparison events, and
    2. Its disagreement rate is at least `disagreement_threshold`.

    Args:
        annotations:
            Annotation dictionaries containing:
            item_id, annotator_id, and label.

        disagreement_threshold:
            Minimum disagreement rate required to flag a class.

        minimum_comparisons:
            Minimum amount of comparison evidence required.

    Returns:
        List of AmbiguousClass results sorted by highest
        disagreement rate first.
    """

    if not 0.0 <= disagreement_threshold <= 1.0:
        raise ValueError(
            "disagreement_threshold must be between 0 and 1"
        )

    if minimum_comparisons < 1:
        raise ValueError(
            "minimum_comparisons must be greater than 0"
        )

    statistics = calculate_disagreement_statistics(annotations)

    results: List[AmbiguousClass] = []

    for label, stats in statistics["by_class"].items():
        disagreements = int(stats["disagreements"])
        occurrences = int(stats["occurrences"])

        total_comparisons = disagreements + occurrences

        disagreement_rate = float(
            stats["disagreement_rate"]
        )

        is_ambiguous = (
            total_comparisons >= minimum_comparisons
            and disagreement_rate >= disagreement_threshold
        )

        results.append(
            AmbiguousClass(
                label=str(label),
                disagreements=disagreements,
                occurrences=occurrences,
                total_comparisons=total_comparisons,
                disagreement_rate=round(
                    disagreement_rate,
                    4,
                ),
                ambiguous=is_ambiguous,
            )
        )

    results.sort(
        key=lambda result: (
            not result.ambiguous,
            -result.disagreement_rate,
            -result.total_comparisons,
            result.label,
        )
    )

    return results