"""
Celery asynchronous tasks for embedding generation and outlier scoring.
"""

from typing import Dict, Any, List, Optional
from app.celery_app import celery_app
from app.core import db as core_db
from app.services.embedding_service import record_embedding_result
from app.models.item import Item


@celery_app.task(name="app.tasks.compute_embedding_outlier_task", bind=True)
def compute_embedding_outlier_task(
    self,
    project_id: int,
    item_id: int,
    model_name: str,
    outlier_score: float,
    is_outlier: bool = False,
    embedding: Optional[List[float]] = None,
    nearest_item_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Asynchronously record embedding and outlier computation for an item.
    """
    db = core_db.SessionLocal()
    try:
        rec = record_embedding_result(
            db=db,
            project_id=project_id,
            item_id=item_id,
            model_name=model_name,
            outlier_score=outlier_score,
            is_outlier=is_outlier,
            embedding=embedding,
            nearest_item_id=nearest_item_id,
            details=details,
        )
        return {
            "status": "COMPLETED",
            "result_id": rec.id,
            "project_id": rec.project_id,
            "item_id": rec.item_id,
            "model_name": rec.model_name,
            "outlier_score": float(rec.outlier_score) if rec.outlier_score is not None else None,
            "is_outlier": rec.is_outlier,
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()


@celery_app.task(name="app.tasks.process_project_embeddings_task", bind=True)
def process_project_embeddings_task(
    self,
    project_id: int,
    model_name: str = "tfidf-centroid-pca",
    outlier_threshold: float = 0.70,
) -> Dict[str, Any]:
    """
    Run embedding analysis across all items of a project asynchronously using real TF-IDF & PCA.
    """
    db = core_db.SessionLocal()
    try:
        from app.services.embedding_service import compute_project_embedding_outliers
        result = compute_project_embedding_outliers(
            db=db,
            project_id=project_id,
            model_name=model_name,
            outlier_threshold=outlier_threshold,
        )
        return {
            "status": "COMPLETED",
            "project_id": project_id,
            "items_processed": result["items_processed"],
            "outliers_detected": result["outliers_detected"],
        }
    except Exception as exc:
        db.rollback()
        raise self.retry(exc=exc, countdown=5, max_retries=3) if not celery_app.conf.task_always_eager else exc
    finally:
        db.close()
