"""
Inter-annotator agreement calculation using Fleiss' Kappa.
"""

from collections import Counter, defaultdict
from typing import Any

from sqlalchemy.orm import Session

from app.models.annotation import Annotation


def compute_fleiss_kappa(
    db: Session,
    project_id: int,
) -> dict[str, Any]:
    """
    Calculate Fleiss' Kappa for annotations in a project.

    Items with fewer than two annotations are ignored.
    """

    annotations = (
        db.query(Annotation)
        .filter(Annotation.project_id == project_id)
        .all()
    )

    item_labels: dict[int, list[str]] = defaultdict(list)

    for annotation in annotations:
        item_labels[annotation.item_id].append(annotation.label)

    # Only multi-annotated items can be used for agreement.
    multi_annotated = {
        item_id: labels
        for item_id, labels in item_labels.items()
        if len(labels) >= 2
    }

    if not multi_annotated:
        return {
            "project_id": project_id,
            "kappa": None,
            "items_evaluated": 0,
            "message": "Not enough multi-annotated items.",
        }

    # Collect all possible labels.
    categories = sorted(
        {
            label
            for labels in multi_annotated.values()
            for label in labels
        }
    )

    n_items = len(multi_annotated)
    n_raters = max(
        len(labels)
        for labels in multi_annotated.values()
    )

    # Agreement per item.
    agreement_sum = 0.0

    category_totals = Counter()
    total_ratings = 0

    for labels in multi_annotated.values():
        counts = Counter(labels)

        for category in categories:
            category_totals[category] += counts.get(
                category,
                0,
            )

        total = len(labels)

        if total < 2:
            continue

        pair_count = sum(
            count * (count - 1)
            for count in counts.values()
        )

        item_agreement = pair_count / (
            total * (total - 1)
        )

        agreement_sum += item_agreement
        total_ratings += total

    p_bar = agreement_sum / n_items

    # Expected agreement.
    p_e = sum(
        (count / total_ratings) ** 2
        for count in category_totals.values()
    )

    if p_e == 1:
        kappa = 1.0
    else:
        kappa = (p_bar - p_e) / (1 - p_e)

    return {
        "project_id": project_id,
        "kappa": round(kappa, 4),
        "items_evaluated": n_items,
        "categories": categories,
    }
