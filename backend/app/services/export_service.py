"""
Service for exporting annotation data with trust scores.
"""

import csv
import io
import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.annotation import Annotation
from app.models.item import Item
from app.models.trust_score import TrustScore


def get_export_data(
    db: Session,
    project_id: int,
) -> list[dict[str, Any]]:
    """
    Collect annotations, item data, and trust scores
    for a project.
    """

    rows = (
        db.query(Annotation, Item, TrustScore)
        .join(Item, Annotation.item_id == Item.id)
        .outerjoin(
            TrustScore,
            TrustScore.item_id == Item.id,
        )
        .filter(Annotation.project_id == project_id)
        .all()
    )

    return [
        {
            "item_id": item.id,
            "annotator_id": annotation.annotator_id,
            "label": annotation.label,
            "confidence": annotation.confidence,
            "content": item.content,
            "trust_score": score.score if score else None,
            "trust_breakdown": score.breakdown if score else None,
            "flagged": score.flagged if score else False,
        }
        for annotation, item, score in rows
    ]


def export_json(
    db: Session,
    project_id: int,
) -> str:
    """Export project data as JSON."""

    data = get_export_data(
        db=db,
        project_id=project_id,
    )

    return json.dumps(
        data,
        indent=2,
        default=str,
    )


def export_csv(
    db: Session,
    project_id: int,
) -> str:
    """Export project data as CSV."""

    data = get_export_data(
        db=db,
        project_id=project_id,
    )

    output = io.StringIO()

    fieldnames = [
        "item_id",
        "annotator_id",
        "label",
        "confidence",
        "content",
        "trust_score",
        "trust_breakdown",
        "flagged",
    ]

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames,
    )

    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()
