"""
Ambiguous class insights API.

Exposes Member 3's ambiguity detection logic to the frontend.
"""

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.annotation import Annotation
from scoring.automation.ambiguity import detect_ambiguous_classes


router = APIRouter(
    prefix="/ambiguity",
    tags=["Ambiguity Insights"],
)


@router.get("/classes")
def get_ambiguous_classes(
    project_id: int = Query(1, ge=1),
    disagreement_threshold: float = Query(
        0.50,
        ge=0.0,
        le=1.0,
    ),
    minimum_comparisons: int = Query(
        5,
        ge=1,
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze annotation disagreement and return class-level
    ambiguity insights.
    """

    annotations = (
        db.query(Annotation)
        .filter(
            Annotation.project_id == project_id
        )
        .all()
    )

    annotation_data: List[Dict[str, Any]] = []

    for annotation in annotations:
        annotation_data.append(
            {
                "item_id": annotation.item_id,
                "annotator_id": annotation.annotator_id,
                "label": annotation.label,
            }
        )

    results = detect_ambiguous_classes(
        annotations=annotation_data,
        disagreement_threshold=disagreement_threshold,
        minimum_comparisons=minimum_comparisons,
    )

    classes = [
        {
            "label": result.label,
            "disagreements": result.disagreements,
            "occurrences": result.occurrences,
            "total_comparisons": result.total_comparisons,
            "disagreement_rate": result.disagreement_rate,
            "ambiguous": result.ambiguous,
        }
        for result in results
    ]

    ambiguous_count = sum(
        1
        for result in results
        if result.ambiguous
    )

    return {
        "project_id": project_id,
        "disagreement_threshold": disagreement_threshold,
        "minimum_comparisons": minimum_comparisons,
        "total_classes": len(classes),
        "ambiguous_classes": ambiguous_count,
        "classes": classes,
    }
