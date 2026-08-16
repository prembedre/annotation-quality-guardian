"""
API routes for quality scores.
"""

from fastapi import APIRouter, Query
from typing import Optional

router = APIRouter()


@router.get("/")
async def list_scores(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    annotator_id: Optional[int] = Query(None, description="Filter by annotator ID"),
):
    """Retrieve quality scores (gold-standard accuracy, Kappa, etc.)."""
    # TODO: integrate with scoring service
    return {"scores": [], "total": 0}


@router.post("/compute")
async def compute_scores(project_id: int):
    """Trigger score computation for a given project."""
    # TODO: integrate with scoring service
    return {"status": "queued", "project_id": project_id}
