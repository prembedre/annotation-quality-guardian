"""
API routes for quality scores, Review Queue, and dataset export.
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.trust_score import TrustScore
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
):
    """
    Retrieve quality scores.
    """

    return {
        "scores": [],
        "total": 0,
        "project_id": project_id,
        "annotator_id": annotator_id,
    }


@router.post("/compute")
async def compute_scores(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Compute quality scores for a project.
    """

    result = await compute_project_scores(
        db=db,
        project_id=project_id,
    )

    return {
        "status": "completed",
        "result": result,
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
