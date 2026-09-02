"""
API routes for Dashboard analytics (Annotator Leaderboard & Inter-annotator Agreement Heatmap).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.dashboard import (
    DashboardLeaderboardResponse,
    DashboardAgreementHeatmapResponse,
)
from app.services.dashboard_service import (
    get_annotator_leaderboard,
    get_agreement_heatmap,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/leaderboard",
    response_model=DashboardLeaderboardResponse,
    summary="Get annotator quality and volume leaderboard",
)
async def get_leaderboard(
    project_id: Optional[int] = Query(
        None,
        description="Filter leaderboard metrics by project ID",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve ranked list of annotators based on trust score, gold accuracy, and throughput.
    """
    try:
        return get_annotator_leaderboard(db=db, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate leaderboard: {str(exc)}",
        )


@router.get(
    "/agreement-heatmap",
    response_model=DashboardAgreementHeatmapResponse,
    summary="Get inter-annotator agreement heatmap matrix",
)
async def get_heatmap(
    project_id: int = Query(
        ...,
        description="Target project ID",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve pairwise inter-annotator agreement matrix and overall Fleiss/Cohen Kappa for a project.
    """
    try:
        return get_agreement_heatmap(db=db, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate agreement heatmap: {str(exc)}",
        )
