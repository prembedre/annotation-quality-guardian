"""
Reusable agreement heatmap and disagreement statistics services.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


def generate_agreement_heatmap(
    annotations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Generate annotator-to-annotator agreement data.

    Each annotation should contain:
        item_id
        annotator_id
        label

    Returns:
        Annotator list, agreement matrix, and detailed cells.
    """
    by_item: Dict[str, Dict[str, str]] = defaultdict(dict)

    for annotation in annotations:
        item_id = str(annotation["item_id"])
        annotator_id = str(annotation["annotator_id"])
        by_item[item_id][annotator_id] = annotation["label"]

    annotator_ids = sorted(
        {
            str(annotation["annotator_id"])
            for annotation in annotations
        }
    )

    matrix: List[List[float]] = []
    cells: List[Dict[str, Any]] = []

    for annotator_a in annotator_ids:
        row: List[float] = []

        for annotator_b in annotator_ids:
            if annotator_a == annotator_b:
                agreement = 1.0
                overlap = sum(
                    1
                    for labels in by_item.values()
                    if annotator_a in labels
                )
            else:
                comparisons = [
                    (labels[annotator_a], labels[annotator_b])
                    for labels in by_item.values()
                    if annotator_a in labels and annotator_b in labels
                ]

                overlap = len(comparisons)

                if overlap == 0:
                    agreement = 0.0
                else:
                    agreement = sum(
                        label_a == label_b
                        for label_a, label_b in comparisons
                    ) / overlap

            agreement = round(float(agreement), 4)
            row.append(agreement)

            cells.append(
                {
                    "annotator_a": annotator_a,
                    "annotator_b": annotator_b,
                    "agreement_rate": agreement,
                    "overlap_count": overlap,
                }
            )

        matrix.append(row)

    return {
        "annotator_ids": annotator_ids,
        "matrix": matrix,
        "cells": cells,
    }


def calculate_disagreement_statistics(
    annotations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate disagreement statistics by class and annotator.

    A disagreement occurs when two annotators label the same item
    with different labels.

    Returns:
        Statistics for disagreement pairs, classes, and annotators.
    """
    by_item: Dict[str, Dict[str, str]] = defaultdict(dict)

    for annotation in annotations:
        item_id = str(annotation["item_id"])
        annotator_id = str(annotation["annotator_id"])
        by_item[item_id][annotator_id] = annotation["label"]

    class_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"disagreements": 0, "occurrences": 0}
    )

    annotator_stats: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {"disagreements": 0, "comparisons": 0}
    )

    disagreement_pairs: List[Dict[str, Any]] = []

    for item_id, labels in by_item.items():
        annotators = sorted(labels)

        for index, annotator_a in enumerate(annotators):
            for annotator_b in annotators[index + 1:]:
                label_a = labels[annotator_a]
                label_b = labels[annotator_b]

                annotator_stats[annotator_a]["comparisons"] += 1
                annotator_stats[annotator_b]["comparisons"] += 1

                if label_a == label_b:
                    class_stats[label_a]["occurrences"] += 1
                    continue

                annotator_stats[annotator_a]["disagreements"] += 1
                annotator_stats[annotator_b]["disagreements"] += 1

                class_stats[label_a]["disagreements"] += 1
                class_stats[label_b]["disagreements"] += 1

                disagreement_pairs.append(
                    {
                        "item_id": item_id,
                        "annotator_a": annotator_a,
                        "annotator_b": annotator_b,
                        "label_a": label_a,
                        "label_b": label_b,
                    }
                )

    by_class = {}

    for label, stats in class_stats.items():
        disagreements = stats["disagreements"]
        occurrences = stats["occurrences"]

        by_class[label] = {
            "disagreements": disagreements,
            "occurrences": occurrences,
            "disagreement_rate": round(
                disagreements / (disagreements + occurrences),
                4,
            )
            if disagreements + occurrences > 0
            else 0.0,
        }

    by_annotator = {}

    for annotator_id, stats in annotator_stats.items():
        comparisons = stats["comparisons"]
        disagreements = stats["disagreements"]

        by_annotator[annotator_id] = {
            "disagreements": disagreements,
            "comparisons": comparisons,
            "disagreement_rate": round(
                disagreements / comparisons,
                4,
            )
            if comparisons > 0
            else 0.0,
        }

    return {
        "by_class": by_class,
        "by_annotator": by_annotator,
        "disagreement_pairs": disagreement_pairs,
    }