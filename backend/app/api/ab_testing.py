"""
A/B testing API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.ab_test_experiment import ABTestExperiment
from app.models.annotation import Annotation
from app.models.item import Item
from app.schemas.ab_testing import (
    ABTestExperimentCreateSchema,
    ABTestExperimentListResponse,
    ABTestExperimentResponseSchema,
)

from scoring.automation.ab_testing import analyze_ab_test


router = APIRouter(prefix="/ab-testing", tags=["A/B Testing"])


@router.get(
    "/experiments",
    response_model=ABTestExperimentListResponse,
)
def list_experiments(
    project_id: int | None = None,
    db: Session = Depends(get_db),
):
    """List A/B testing experiments."""
    query = db.query(ABTestExperiment)

    if project_id is not None:
        query = query.filter(ABTestExperiment.project_id == project_id)

    experiments = query.order_by(
        ABTestExperiment.created_at.desc()
    ).all()

    return {
        "total": len(experiments),
        "experiments": experiments,
    }


@router.post(
    "/experiments",
    response_model=ABTestExperimentResponseSchema,
)
def create_experiment(
    payload: ABTestExperimentCreateSchema,
    db: Session = Depends(get_db),
):
    """Create a new A/B testing experiment."""

    experiment = ABTestExperiment(
        experiment_name=payload.experiment_name,
        project_id=payload.project_id,
        schema_version_a=payload.schema_version_a,
        schema_version_b=payload.schema_version_b,
        annotator_group=payload.annotator_group,
        assigned_version=payload.assigned_version,
        status=payload.status,
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    return experiment


@router.get(
    "/experiments/{experiment_id}",
    response_model=ABTestExperimentResponseSchema,
)
def get_experiment(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """Get a single A/B testing experiment."""

    experiment = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.id == experiment_id)
        .first()
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="A/B testing experiment not found",
        )

    return experiment


@router.get("/experiments/{experiment_id}/results")
def get_experiment_results(
    experiment_id: int,
    db: Session = Depends(get_db),
):
    """
    Analyze the results of an A/B testing experiment.
    """

    experiment = (
        db.query(ABTestExperiment)
        .filter(ABTestExperiment.id == experiment_id)
        .first()
    )

    if experiment is None:
        raise HTTPException(
            status_code=404,
            detail="A/B testing experiment not found",
        )

    annotations = (
        db.query(Annotation)
        .filter(
            Annotation.project_id == experiment.project_id
        )
        .all()
    )

    gold_items = (
        db.query(Item)
        .filter(
            Item.project_id == experiment.project_id,
            Item.is_gold.is_(True),
        )
        .all()
    )

    gold_lookup: Dict[str, str] = {}

    for item in gold_items:
        gold_lookup[str(item.id)] = item.gold_label

        if item.external_id:
            gold_lookup[str(item.external_id)] = item.gold_label

    annotation_data: List[Dict[str, Any]] = []

    for annotation in annotations:
        metadata = annotation.metadata_ or {}

        annotation_data.append(
            {
                "id": annotation.id,
                "item_id": annotation.item_id,
                "annotator_id": annotation.annotator_id,
                "label": annotation.label,
                "confidence": annotation.confidence,
                "duration_ms": annotation.duration_ms,
                "metadata": metadata,
            }
        )

    result = analyze_ab_test(
        experiment_name=experiment.experiment_name,
        annotations=annotation_data,
        gold_items=gold_lookup,
    )

    return {
        "experiment_id": experiment.id,
        "experiment_name": experiment.experiment_name,
        "status": experiment.status,
        "created_at": experiment.created_at,
        "completed_at": experiment.completed_at,
        "variant_a": {
            "total_annotations": result.variant_a.total_annotations,
            "gold_annotations": result.variant_a.gold_annotations,
            "gold_correct": result.variant_a.gold_correct,
            "accuracy": result.variant_a.accuracy,
            "average_confidence": result.variant_a.average_confidence,
            "average_duration_ms": result.variant_a.average_duration_ms,
        },
        "variant_b": {
            "total_annotations": result.variant_b.total_annotations,
            "gold_annotations": result.variant_b.gold_annotations,
            "gold_correct": result.variant_b.gold_correct,
            "accuracy": result.variant_b.accuracy,
            "average_confidence": result.variant_b.average_confidence,
            "average_duration_ms": result.variant_b.average_duration_ms,
        },
        "accuracy_difference": result.accuracy_difference,
        "recommended_variant": result.recommended_variant,
        "recommendation_reason": result.recommendation_reason,
    }