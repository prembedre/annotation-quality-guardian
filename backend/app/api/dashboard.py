"""
API routes for Dashboard analytics (Annotator Leaderboard & Inter-annotator Agreement Heatmap).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth_deps import require_role
from app.core.db import get_db
from app.models.user import UserRole
from app.schemas.dashboard import (
    DashboardLeaderboardResponse,
    DashboardAgreementHeatmapResponse,
)
from app.services.dashboard_service import (
    get_annotator_leaderboard,
    get_agreement_heatmap,
    get_dashboard_trend,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/leaderboard",
    response_model=DashboardLeaderboardResponse,
    summary="Get annotator quality and volume leaderboard",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER, UserRole.ANNOTATOR))],
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
    except Exception:
        return {
            "project_id": project_id,
            "total_annotators": 0,
            "leaderboard": [],
        }


@router.get(
    "/agreement-heatmap",
    response_model=DashboardAgreementHeatmapResponse,
    summary="Get inter-annotator agreement heatmap matrix",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER, UserRole.ANNOTATOR))],
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
    except Exception:
        return {
            "project_id": project_id,
            "annotators": [],
            "annotator_ids": [],
            "matrix": [],
            "cells": [],
            "overall_kappa": None,
        }


@router.get(
    "/trend",
    summary="Get quality and agreement trend telemetry",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER, UserRole.ANNOTATOR))],
)
async def get_trend(
    project_id: int = Query(1, ge=1, description="Target project ID"),
    time_range: str = Query("7d", description="Time window: 24h, 7d, or 30d"),
    db: Session = Depends(get_db),
):
    """
    Retrieve real-time and historical trend analytics for Trust Scores and Cohen's Kappa.
    """
    try:
        return get_dashboard_trend(db=db, project_id=project_id, time_range=time_range)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch trend data: {str(exc)}",
        )

