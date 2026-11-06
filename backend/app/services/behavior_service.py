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
from app.models.annotation import Annotation
from scoring.behavior.anomaly_detector import (
    evaluate_behavioral_anomaly,
    calculate_duration_zscore,
)


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


def compute_annotator_behavioral_score(
    db: Session,
    project_id: int,
    annotator_id: int,
    project_labels: Optional[List[str]] = None,
    label_set: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute real behavioral metrics for an annotator in a project based on
    actual historical annotation data: duration z-scores, streak length,
    and label distribution drift.
    """
    annotations = (
        db.query(Annotation)
        .filter(
            Annotation.project_id == project_id,
            Annotation.annotator_id == annotator_id,
        )
        .order_by(Annotation.id.asc())
        .all()
    )

    if not annotations:
        return {
            "annotator_id": annotator_id,
            "project_id": project_id,
            "anomaly_score": 0.0,
            "time_score": 0.0,
            "streak_score": 0.0,
            "drift_score": 0.0,
            "anomaly_flag": False,
            "reason": "No annotations found for annotator",
        }

    durations = [float(a.duration_ms) for a in annotations if a.duration_ms is not None]
    labels = [a.label for a in annotations if a.label]

    eval_result = evaluate_behavioral_anomaly(
        durations=durations,
        current_duration=None,
        labels=labels,
        project_labels=project_labels,
        label_set=label_set,
    )

    record = record_behavioral_score(
        db=db,
        project_id=project_id,
        annotator_id=annotator_id,
        item_id=None,
        anomaly_score=eval_result["anomaly_score"],
        time_score=eval_result["time_score"],
        streak_score=eval_result["streak_score"],
        anomaly_flag=eval_result["anomaly_flag"],
        reason=eval_result["reason"],
        details=eval_result,
    )

    return {
        "score_id": record.id,
        "annotator_id": annotator_id,
        "project_id": project_id,
        **eval_result,
    }


def compute_project_behavioral_scores(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """
    Compute and persist real behavioral anomaly scores for all annotators
    and items in a project based on duration telemetry, streaks, and drift.
    """
    annotations = (
        db.query(Annotation)
        .filter(Annotation.project_id == project_id)
        .order_by(Annotation.id.asc())
        .all()
    )

    if not annotations:
        return {
            "project_id": project_id,
            "annotators_evaluated": 0,
            "items_scored": 0,
            "anomalies_detected": 0,
        }

    project = db.query(Project).filter(Project.id == project_id).first()
    label_set = project.label_set if project else []
    project_labels = [a.label for a in annotations if a.label]

    # Group by annotator
    annotator_map = {}
    for a in annotations:
        annotator_map.setdefault(a.annotator_id, []).append(a)

    annotators_evaluated = 0
    anomalies_detected = 0
    items_scored = 0

    for ann_id, ann_list in annotator_map.items():
        durations = [float(a.duration_ms) for a in ann_list if a.duration_ms is not None]
        labels = [a.label for a in ann_list if a.label]

        ann_eval = evaluate_behavioral_anomaly(
            durations=durations,
            current_duration=None,
            labels=labels,
            project_labels=project_labels,
            label_set=label_set,
        )

        record_behavioral_score(
            db=db,
            project_id=project_id,
            annotator_id=ann_id,
            item_id=None,
            anomaly_score=ann_eval["anomaly_score"],
            time_score=ann_eval["time_score"],
            streak_score=ann_eval["streak_score"],
            anomaly_flag=ann_eval["anomaly_flag"],
            reason=ann_eval["reason"],
            details=ann_eval,
        )
        annotators_evaluated += 1
        if ann_eval["anomaly_flag"]:
            anomalies_detected += 1

        # Also score each item annotated by this annotator
        for a in ann_list:
            curr_dur = float(a.duration_ms) if a.duration_ms is not None else None
            _, item_time_score = calculate_duration_zscore(durations, curr_dur)
            item_anomaly = round(
                min(1.0, 0.45 * item_time_score + 0.35 * ann_eval["streak_score"] + 0.20 * ann_eval["drift_score"]),
                4,
            )
            item_flag = item_anomaly >= 0.5

            record_behavioral_score(
                db=db,
                project_id=project_id,
                annotator_id=ann_id,
                item_id=a.item_id,
                anomaly_score=item_anomaly,
                time_score=item_time_score,
                streak_score=ann_eval["streak_score"],
                anomaly_flag=item_flag,
                reason=f"Velocity score={item_time_score}; {ann_eval['reason']}" if item_flag else "Normal",
                details={**ann_eval, "item_time_score": item_time_score},
            )
            items_scored += 1

    return {
        "project_id": project_id,
        "annotators_evaluated": annotators_evaluated,
        "items_scored": items_scored,
        "anomalies_detected": anomalies_detected,
    }

