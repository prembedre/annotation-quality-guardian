"""
Embedding Outlier Integration Service.
Handles storage, retrieval, and async execution tracking for embedding outlier detection.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.embedding_result import EmbeddingResult
from app.models.item import Item
from app.models.project import Project


def record_embedding_result(
    db: Session,
    project_id: int,
    item_id: int,
    model_name: str,
    outlier_score: float,
    is_outlier: bool = False,
    embedding: Optional[List[float]] = None,
    nearest_item_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None,
) -> EmbeddingResult:
    """
    Store or update an embedding and outlier result for an item.

    Args:
        db: Database session
        project_id: Target project ID
        item_id: Item ID
        model_name: Name/identifier of embedding model used
        outlier_score: Outlier score between 0.0 (inlier) and 1.0 (strong outlier)
        is_outlier: Boolean flag indicating if item is an outlier
        embedding: Vector representation (list of floats)
        nearest_item_id: ID of closest neighbor item in embedding space
        details: Additional metadata

    Returns:
        The created or updated EmbeddingResult record.
    """
    res_details = dict(details or {})
    res_details["is_outlier"] = is_outlier
    if nearest_item_id is not None:
        res_details["nearest_item_id"] = nearest_item_id

    # Check for existing record
    record = (
        db.query(EmbeddingResult)
        .filter(
            EmbeddingResult.project_id == project_id,
            EmbeddingResult.item_id == item_id,
            EmbeddingResult.model_name == model_name,
        )
        .first()
    )

    if record:
        record.outlier_score = outlier_score
        record.is_outlier = is_outlier
        record.embedding = embedding
        record.nearest_item_id = nearest_item_id
        record.details = res_details
        record.computed_at = datetime.utcnow()
    else:
        record = EmbeddingResult(
            project_id=project_id,
            item_id=item_id,
            model_name=model_name,
            outlier_score=outlier_score,
            is_outlier=is_outlier,
            embedding=embedding,
            nearest_item_id=nearest_item_id,
            details=res_details,
            computed_at=datetime.utcnow(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def get_embedding_results_by_project(
    db: Session,
    project_id: int,
    outliers_only: bool = False,
    limit: int = 100,
    offset: int = 0,
) -> List[EmbeddingResult]:
    """Retrieve embedding results for a project with optional outlier filter."""
    query = db.query(EmbeddingResult).filter(EmbeddingResult.project_id == project_id)
    if outliers_only:
        query = query.filter(EmbeddingResult.is_outlier.is_(True))
    return query.order_by(EmbeddingResult.id.desc()).offset(offset).limit(limit).all()


def get_embedding_result_for_item(
    db: Session,
    project_id: int,
    item_id: int,
) -> Optional[EmbeddingResult]:
    """Retrieve embedding result for a specific item."""
    return (
        db.query(EmbeddingResult)
        .filter(
            EmbeddingResult.project_id == project_id,
            EmbeddingResult.item_id == item_id,
        )
        .order_by(EmbeddingResult.computed_at.desc())
        .first()
    )
