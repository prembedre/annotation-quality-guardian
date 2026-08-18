"""
Gold-standard accuracy calculation service.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.models.annotation import Annotation
from app.models.item import Item


def compute_gold_accuracy(
    db: Session,
    project_id: int,
) -> dict[str, Any]:
    """
    Calculate gold-standard accuracy for each annotator
    in a project.

    An annotation is correct when its label matches
    the item's gold_label.
    """

    rows = (
        db.query(Annotation, Item)
        .join(Item, Annotation.item_id == Item.id)
        .filter(
            Annotation.project_id == project_id,
            Item.gold_label.isnot(None),
        )
        .all()
    )

    annotator_stats: dict[int, dict[str, int]] = {}

    for annotation, item in rows:
        annotator_id = annotation.annotator_id

        if annotator_id not in annotator_stats:
            annotator_stats[annotator_id] = {
                "total": 0,
                "correct": 0,
            }

        annotator_stats[annotator_id]["total"] += 1

        if annotation.label == item.gold_label:
            annotator_stats[annotator_id]["correct"] += 1

    results = []

    for annotator_id, stats in annotator_stats.items():
        total = stats["total"]
        correct = stats["correct"]

        accuracy = correct / total if total else 0.0

        results.append({
            "annotator_id": annotator_id,
            "total_gold_annotations": total,
            "correct": correct,
            "accuracy": round(accuracy, 4),
        })

    return {
        "project_id": project_id,
        "annotators": results,
    }
