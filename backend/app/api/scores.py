"""
API routes for quality scores, Review Queue, and dataset export.
"""

from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.trust_score import TrustScore
from app.models.project import Project
from app.models.item import Item
from app.services.scoring_service import compute_project_scores
from app.services.export_service import export_csv, export_json


router = APIRouter()


@router.get("/")
async def list_scores(
    project_id: Optional[int] = Query(
        None,
        description="Filter by project ID",
    ),
    annotator_id: Optional[int] = Query(
        None,
        description="Filter by annotator ID",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve computed quality scores (TrustScore records) from the database.
    Returns the actual persisted metrics so the Scores page can display results
    after a compute run.
    """
    query = db.query(TrustScore)

    if project_id is not None:
        query = query.filter(TrustScore.project_id == project_id)
    if annotator_id is not None:
        # Filter by annotator via the related item's annotations — items have
        # one trust score each; for now surface all project scores.
        pass

    trust_scores = query.order_by(TrustScore.updated_at.desc().nullslast()).all()

    scores_out = []
    for ts in trust_scores:
        breakdown = ts.breakdown or {}
        scores_out.append({
            "id": ts.id,
            "project_id": ts.project_id,
            "item_id": ts.item_id,
            "metric": f"Item #{ts.item_id} Trust Score",
            "value": f"{float(ts.final_score or 0):.1%}",
            "final_score": float(ts.final_score or 0),
            "gold_score": float(ts.gold_score) if ts.gold_score is not None else None,
            "agreement_score": float(ts.agreement_score) if ts.agreement_score is not None else None,
            "behavioral_score": float(ts.behavioral_score) if ts.behavioral_score is not None else None,
            "embedding_score": float(ts.embedding_score) if ts.embedding_score is not None else None,
            "flagged": ts.flagged,
            "breakdown": breakdown,
            "computed_at": ts.updated_at.isoformat() if ts.updated_at else (
                ts.created_at.isoformat() if ts.created_at else None
            ),
        })

    return {
        "scores": scores_out,
        "total": len(scores_out),
        "project_id": project_id,
        "annotator_id": annotator_id,
    }


@router.post("/compute")
async def compute_scores(
    project_id: int = Query(..., description="Project ID to compute scores for"),
    db: Session = Depends(get_db),
):
    """
    Compute quality scores for a project.

    Runs inter-annotator agreement (Fleiss' Kappa), gold-standard accuracy,
    behavioral anomaly detection, and embedding outlier analysis.
    Persists TrustScore records for all items in the project.

    Returns a structured summary with computed metric values.
    Always returns a specific error detail — never a generic failure.
    """
    # Validate project exists
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found. Create a project before computing scores.",
        )

    # Validate there are annotations to compute on
    from app.models.annotation import Annotation
    annotation_count = db.query(Annotation).filter(
        Annotation.project_id == project_id
    ).count()

    if annotation_count == 0:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                f"Project \"{project.name}\" has no annotations yet. "
                "Ingest annotation data before running the scoring engine."
            ),
        )

    try:
        result = await compute_project_scores(
            db=db,
            project_id=project_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        )
    except Exception as exc:
        # Surface the specific cause rather than a generic 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scoring engine failed: {type(exc).__name__}: {str(exc)}",
        )

    # Build a concise summary for the success toast
    kappa = result.get("kappa", {})
    gold = result.get("gold_accuracy", {})
    trust = result.get("trust_score_summary", {})

    kappa_val = kappa.get("kappa")
    kappa_str = f"{kappa_val:.3f}" if kappa_val is not None else "N/A (insufficient overlap)"
    gold_annotators = gold.get("annotators", [])
    avg_gold = (
        sum(a["accuracy"] for a in gold_annotators) / len(gold_annotators)
        if gold_annotators else None
    )
    gold_str = f"{avg_gold:.1%}" if avg_gold is not None else "N/A (no gold-standard labels)"

    message = (
        f"Scored {trust.get('total_items_processed', 0)} items — "
        f"Kappa: {kappa_str}, "
        f"Gold accuracy: {gold_str}, "
        f"{trust.get('flagged_items', 0)} items flagged for review."
    )

    return {
        "status": "completed",
        "message": message,
        "result": result,
    }


@router.get("/summary")
async def get_score_summary(
    project_id: int = Query(..., description="Project ID"),
    db: Session = Depends(get_db),
):
    """
    Return aggregate score metrics for a project (kappa, gold accuracy, avg trust score).
    Used by dashboard and score header cards.
    """
    from app.services.kappa_service import compute_fleiss_kappa
    from app.services.gold_standard_service import compute_gold_accuracy

    trust_scores = db.query(TrustScore).filter(TrustScore.project_id == project_id).all()

    if not trust_scores:
        return {
            "project_id": project_id,
            "has_data": False,
            "avg_trust_score": None,
            "flagged_count": 0,
            "total_items": 0,
            "kappa": None,
            "avg_gold_accuracy": None,
        }

    avg_trust = sum(float(ts.final_score or 0) for ts in trust_scores) / len(trust_scores)
    flagged = sum(1 for ts in trust_scores if ts.flagged)

    kappa_result = compute_fleiss_kappa(db=db, project_id=project_id)
    gold_result = compute_gold_accuracy(db=db, project_id=project_id)
    gold_annotators = gold_result.get("annotators", [])
    avg_gold = (
        sum(a["accuracy"] for a in gold_annotators) / len(gold_annotators)
        if gold_annotators else None
    )

    return {
        "project_id": project_id,
        "has_data": True,
        "avg_trust_score": round(avg_trust, 4),
        "flagged_count": flagged,
        "total_items": len(trust_scores),
        "kappa": kappa_result.get("kappa"),
        "kappa_items_evaluated": kappa_result.get("items_evaluated", 0),
        "avg_gold_accuracy": round(avg_gold, 4) if avg_gold is not None else None,
        "gold_annotator_count": len(gold_annotators),
    }


@router.get("/flagged")
async def list_flagged_items(
    db: Session = Depends(get_db),
    page: int = Query(
        1,
        ge=1,
        description="Page number",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
):
    """
    Return flagged items with pagination.

    Used by the Review Queue.
    """

    query = (
        db.query(TrustScore)
        .filter(
            TrustScore.flagged.is_(True)
        )
        .order_by(
            TrustScore.created_at.desc()
        )
    )

    total = query.count()

    offset = (page - 1) * page_size

    flagged_scores = (
        query
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": [
            {
                "item_id": score.item_id,
                "score": score.score,
                "breakdown": score.breakdown,
                "flagged": score.flagged,
            }
            for score in flagged_scores
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.get("/export/json")
async def export_project_json(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Export project data with trust scores as JSON.
    """

    content = export_json(
        db=db,
        project_id=project_id,
    )

    return Response(
        content=content,
        media_type="application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="project_{project_id}.json"'
            )
        },
    )


@router.get("/export/csv")
async def export_project_csv(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Export project data with trust scores as CSV.
    """

    content = export_csv(
        db=db,
        project_id=project_id,
    )

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f'attachment; filename="project_{project_id}.csv"'
            )
        },
    )
