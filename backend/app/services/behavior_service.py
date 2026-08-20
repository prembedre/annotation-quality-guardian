"""
Behavioral Anomaly Integration Service.
Handles storage, retrieval, and integration of annotator behavioral anomaly scores.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.behavioral_score import BehavioralScore
from app.models.project import Project
from app.models.annotator import Annotator
from app.models.item import Item


def record_behavioral_score(
    db: Session,
    project_id: int,
    annotator_id: int,
    anomaly_score: float,
    item_id: Optional[int] = None,
    time_score: Optional[float] = None,
    streak_score: Optional[float] = None,
    anomaly_flag: bool = False,
    reason: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> BehavioralScore:
    """
    Store or update a behavioral anomaly score record in PostgreSQL.

    Args:
        db: Database session
        project_id: Target project ID
        annotator_id: Target annotator ID
        anomaly_score: Anomaly score between 0.0 (normal) and 1.0 (anomalous)
        item_id: Optional specific item ID
        time_score: Optional response/duration metric score (0.0 to 1.0)
        streak_score: Optional repetition/streak metric score (0.0 to 1.0)
        anomaly_flag: Boolean flag indicating if behavior is anomalous
        reason: Optional text explanation of the anomaly
        details: Optional dictionary with extra metadata

    Returns:
        The created or updated BehavioralScore instance.
    """
    score_details = dict(details or {})
    score_details["anomaly_flag"] = anomaly_flag
    if reason:
        score_details["reason"] = reason

    # Check for existing record matching project, annotator, and item
    query = db.query(BehavioralScore).filter(
        BehavioralScore.project_id == project_id,
        BehavioralScore.annotator_id == annotator_id,
    )
    if item_id is not None:
        query = query.filter(BehavioralScore.item_id == item_id)
    else:
        query = query.filter(BehavioralScore.item_id.is_(None))

    record = query.first()

    if record:
        record.anomaly_score = anomaly_score
        record.time_score = time_score
        record.streak_score = streak_score
        record.details = score_details
        record.computed_at = datetime.utcnow()
    else:
        record = BehavioralScore(
            project_id=project_id,
            annotator_id=annotator_id,
            item_id=item_id,
            anomaly_score=anomaly_score,
            time_score=time_score,
            streak_score=streak_score,
            details=score_details,
            computed_at=datetime.utcnow(),
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def get_behavioral_scores_by_project(
    db: Session,
    project_id: int,
    limit: int = 100,
    offset: int = 0,
) -> List[BehavioralScore]:
    """Retrieve behavioral scores for a given project."""
    return (
        db.query(BehavioralScore)
        .filter(BehavioralScore.project_id == project_id)
        .order_by(BehavioralScore.id.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_behavioral_score_for_item(
    db: Session,
    project_id: int,
    item_id: int,
) -> Optional[BehavioralScore]:
    """Retrieve behavioral score for a specific item in a project."""
    return (
        db.query(BehavioralScore)
        .filter(
            BehavioralScore.project_id == project_id,
            BehavioralScore.item_id == item_id,
        )
        .order_by(BehavioralScore.computed_at.desc())
        .first()
    )


def get_behavioral_score_for_annotator(
    db: Session,
    project_id: int,
    annotator_id: int,
) -> Optional[BehavioralScore]:
    """Retrieve aggregate behavioral score for an annotator in a project."""
    return (
        db.query(BehavioralScore)
        .filter(
            BehavioralScore.project_id == project_id,
            BehavioralScore.annotator_id == annotator_id,
            BehavioralScore.item_id.is_(None),
        )
        .order_by(BehavioralScore.computed_at.desc())
        .first()
    )
