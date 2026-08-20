"""
Celery asynchronous tasks for behavioral anomaly detection.
"""

from typing import Dict, Any, List, Optional
from app.celery_app import celery_app
from app.core import db as core_db
from app.services.behavior_service import record_behavioral_score


@celery_app.task(name="app.tasks.compute_behavioral_score_task", bind=True)
def compute_behavioral_score_task(
    self,
    project_id: int,
    annotator_id: int,
    anomaly_score: float,
    item_id: Optional[int] = None,
    time_score: Optional[float] = None,
    streak_score: Optional[float] = None,
    anomaly_flag: bool = False,
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously record behavioral anomaly evaluation for an annotator/item.
    """
    db = core_db.SessionLocal()
    try:
        score_rec = record_behavioral_score(
            db=db,
            project_id=project_id,
            annotator_id=annotator_id,
            anomaly_score=anomaly_score,
            item_id=item_id,
            time_score=time_score,
            streak_score=streak_score,
            anomaly_flag=anomaly_flag,
            reason=reason,
            details=details,
        )
        return {
            "status": "COMPLETED",
            "score_id": score_rec.id,
            "project_id": score_rec.project_id,
            "annotator_id": score_rec.annotator_id,
            "item_id": score_rec.item_id,
            "anomaly_score": float(score_rec.anomaly_score) if score_rec.anomaly_score is not None else None,
            "anomaly_flag": anomaly_flag,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_batch_behavioral_task", bind=True)
def process_batch_behavioral_task(
    self,
    project_id: int,
    batch_records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Process a batch of behavioral score inputs asynchronously.
    """
    db = SessionLocal()
    processed = 0
    try:
        for rec in batch_records:
            record_behavioral_score(
                db=db,
                project_id=project_id,
                annotator_id=rec["annotator_id"],
                anomaly_score=rec["anomaly_score"],
                item_id=rec.get("item_id"),
                time_score=rec.get("time_score"),
                streak_score=rec.get("streak_score"),
                anomaly_flag=rec.get("anomaly_flag", False),
                reason=rec.get("reason"),
                details=rec.get("details"),
            )
            processed += 1
        return {
            "status": "COMPLETED",
            "project_id": project_id,
            "processed_count": processed,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()
