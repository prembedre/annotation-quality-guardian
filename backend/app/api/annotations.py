"""
API routes for annotation management.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationListResponse,
)

router = APIRouter()


@router.get("/", response_model=AnnotationListResponse)
async def list_annotations(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    annotator_id: Optional[int] = Query(None, description="Filter by annotator ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """Retrieve a paginated list of annotations with optional filters."""
    # TODO: integrate with database service
    return {"annotations": [], "total": 0}


@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(annotation_id: int):
    """Retrieve a single annotation by ID."""
    # TODO: integrate with database service
    raise HTTPException(status_code=404, detail="Annotation not found")


@router.post("/", response_model=AnnotationResponse, status_code=201)
async def create_annotation(payload: AnnotationCreate):
    """Create a new annotation record."""
    # TODO: integrate with database service
    raise HTTPException(status_code=501, detail="Not yet implemented")
