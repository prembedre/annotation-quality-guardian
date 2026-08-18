"""
API routes for quality scores and metric computation.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.project import Project
from app.services.gold_standard_service import compute_gold_accuracy
from app.services.kappa_service import compute_fleiss_kappa

router = APIRouter()


@router.get("/")
async def list_scores(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    db: Session = Depends(get_db),
):
    """Retrieve quality scores (gold-standard accuracy, Kappa, etc.)."""
    if project_id is None:
        return {"scores": [], "total": 0}

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    gold_stats = compute_gold_accuracy(db=db, project_id=project_id)
    kappa_stats = compute_fleiss_kappa(db=db, project_id=project_id)

    return {
        "project_id": project_id,
        "gold_standard": gold_stats,
        "agreement": kappa_stats,
    }


@router.post("/compute")
async def compute_scores(project_id: int, db: Session = Depends(get_db)):
    """Trigger score computation for a given project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")

    gold_stats = compute_gold_accuracy(db=db, project_id=project_id)
    kappa_stats = compute_fleiss_kappa(db=db, project_id=project_id)

    return {
        "status": "completed",
        "project_id": project_id,
        "gold_accuracy": gold_stats,
        "fleiss_kappa": kappa_stats,
    }
