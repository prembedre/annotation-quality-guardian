"""
Business logic for scoring operations.
"""

from typing import Any

from sqlalchemy.orm import Session

from app.services.gold_standard_service import compute_gold_accuracy
from app.services.kappa_service import compute_fleiss_kappa
from app.services.trust_score_service import compute_and_save_project_trust_scores
from app.services.behavior_service import get_behavioral_scores_by_project
from app.services.embedding_service import get_embedding_results_by_project


async def compute_project_scores(
    db: Session,
    project_id: int,
) -> dict[str, Any]:
    """
    Compute quality scores for a project across all Phase 1 and Phase 2 signals.
    """

    gold_result = compute_gold_accuracy(
        db=db,
        project_id=project_id,
    )

    kappa_result = compute_fleiss_kappa(
        db=db,
        project_id=project_id,
    )

    # Compute and persist unified trust scores
    trust_summary = compute_and_save_project_trust_scores(
        db=db,
        project_id=project_id,
    )

    # Fetch anomalies / outliers
    behavioral_records = get_behavioral_scores_by_project(db=db, project_id=project_id)
    anomalies = [
        {
            "annotator_id": b.annotator_id,
            "item_id": b.item_id,
            "anomaly_score": float(b.anomaly_score) if b.anomaly_score is not None else None,
            "details": b.details,
        }
        for b in behavioral_records
        if b.details.get("anomaly_flag", False)
    ]

    outlier_records = get_embedding_results_by_project(db=db, project_id=project_id, outliers_only=True)
    outliers = [
        {
            "item_id": e.item_id,
            "model_name": e.model_name,
            "outlier_score": float(e.outlier_score) if e.outlier_score is not None else None,
        }
        for e in outlier_records
    ]

    return {
        "project_id": project_id,
        "gold_accuracy": gold_result,
        "kappa": kappa_result,
        "anomalies": anomalies,
        "outliers": outliers,
        "trust_score_summary": trust_summary,
    }
