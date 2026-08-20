"""
Celery asynchronous tasks for unified Trust Score calculation.
"""

from typing import Dict, Any, Optional
from app.celery_app import celery_app
from app.core import db as core_db
from app.services.trust_score_service import compute_and_save_project_trust_scores, compute_and_save_item_trust_score


@celery_app.task(name="app.tasks.compute_project_trust_scores_task", bind=True)
def compute_project_trust_scores_task(
    self,
    project_id: int,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously calculate and update unified TrustScores for all items in a project.
    """
    db = core_db.SessionLocal()
    try:
        res = compute_and_save_project_trust_scores(
            db=db,
            project_id=project_id,
            weights=weights,
        )
        return res
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()


@celery_app.task(name="app.tasks.compute_item_trust_score_task", bind=True)
def compute_item_trust_score_task(
    self,
    project_id: int,
    item_id: int,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously calculate and update unified TrustScore for a single item.
    """
    db = core_db.SessionLocal()
    try:
        ts = compute_and_save_item_trust_score(
            db=db,
            project_id=project_id,
            item_id=item_id,
            weights=weights,
        )
        return {
            "status": "COMPLETED",
            "trust_score_id": ts.id,
            "project_id": ts.project_id,
            "item_id": ts.item_id,
            "final_score": float(ts.final_score) if ts.final_score is not None else None,
            "flagged": ts.flagged,
            "breakdown": ts.breakdown,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()
