"""
Business logic for scoring operations.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.services.gold_standard_service import compute_gold_accuracy


async def compute_project_scores(
    db: Session,
    project_id: int,
) -> dict[str, Any]:
    """
    Compute quality scores for a project.
    """

    gold_result = compute_gold_accuracy(
        db=db,
        project_id=project_id,
    )

    return {
        "project_id": project_id,
        "gold_accuracy": gold_result,
        "kappa": None,
        "anomalies": [],
    }
