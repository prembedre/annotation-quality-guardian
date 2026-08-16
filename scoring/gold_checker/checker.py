"""
Gold-standard validation.

Compares annotator labels against known gold-standard labels
to compute per-annotator and overall accuracy.
"""

from typing import Dict, List, Any


def gold_accuracy(
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
) -> Dict[str, Any]:
    """
    Compute accuracy of annotations against gold-standard labels.

    Args:
        annotations: List of annotation dicts, each with 'item_id',
                     'annotator_id', and 'label' keys.
        gold_items:  Mapping of item_id → gold label.

    Returns:
        Dictionary with 'overall_accuracy' and 'per_annotator' breakdown.
    """
    annotator_stats: Dict[str, Dict[str, int]] = {}

    for ann in annotations:
        item_id = ann["item_id"]
        if item_id not in gold_items:
            continue

        annotator = str(ann["annotator_id"])
        if annotator not in annotator_stats:
            annotator_stats[annotator] = {"correct": 0, "total": 0}

        annotator_stats[annotator]["total"] += 1
        if ann["label"] == gold_items[item_id]:
            annotator_stats[annotator]["correct"] += 1

    per_annotator = {}
    total_correct = 0
    total_count = 0

    for annotator, stats in annotator_stats.items():
        acc = stats["correct"] / stats["total"] if stats["total"] > 0 else 0.0
        per_annotator[annotator] = {
            "accuracy": round(acc, 4),
            "correct": stats["correct"],
            "total": stats["total"],
        }
        total_correct += stats["correct"]
        total_count += stats["total"]

    overall = total_correct / total_count if total_count > 0 else 0.0

    return {
        "overall_accuracy": round(overall, 4),
        "per_annotator": per_annotator,
    }
