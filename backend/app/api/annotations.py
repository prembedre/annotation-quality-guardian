"""
API routes for annotation management and file upload ingestion.
"""

import os
import tempfile
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, File, UploadFile, Form
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Annotation, Item, Project, Annotator
from app.schemas.annotation import (
    AnnotationCreate,
    AnnotationResponse,
    AnnotationListResponse,
)
from app.schemas.ingestion import IngestionResponse
from app.services.ingestion_service import ingest_file

router = APIRouter()


@router.post("/upload", response_model=IngestionResponse, summary="Upload CSV/JSON annotation dataset")
async def upload_annotations(
    file: UploadFile = File(..., description="CSV or JSON dataset file"),
    project_id: Optional[int] = Form(None, description="Optional default project ID to assign"),
    db: Session = Depends(get_db),
):
    """
    Upload a batch CSV or JSON dataset of annotations.
    Validates structure, types, project label constraints, deduplicates, and inserts records.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    extension = os.path.splitext(file.filename)[1].lower()
    if extension not in {".csv", ".json"}:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{extension}'. Only .csv and .json files are allowed.",
        )

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=extension) as temp_file:
            content = await file.read()
            if not content or len(content.strip()) == 0:
                raise HTTPException(status_code=400, detail="Uploaded file is empty.")
            temp_file.write(content)
            temp_file_path = temp_file.name

        result = ingest_file(
            db=db,
            file_path=temp_file_path,
            default_project_id=project_id,
        )
        result["filename"] = file.filename
        return result

    except HTTPException:
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to ingest annotation file: {str(exc)}",
        )
    finally:
        if "temp_file_path" in locals() and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


@router.get("/", response_model=AnnotationListResponse)
async def list_annotations(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    annotator_id: Optional[int] = Query(None, description="Filter by annotator ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve a paginated list of annotations with optional filters."""
    query = db.query(Annotation)
    if project_id is not None:
        query = query.filter(Annotation.project_id == project_id)
    if annotator_id is not None:
        query = query.filter(Annotation.annotator_id == annotator_id)

    total = query.count()
    annotations = query.order_by(Annotation.id.desc()).offset(offset).limit(limit).all()

    # Format response items
    items_out = []
    for a in annotations:
        ext_item_id = str(a.item.external_id) if a.item and a.item.external_id else str(a.item_id)
        items_out.append(
            AnnotationResponse(
                id=a.id,
                project_id=a.project_id or 0,
                annotator_id=a.annotator_id,
                item_id=ext_item_id,
                label=a.label,
                confidence=a.confidence,
                metadata=a.metadata_ or {},
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )

    return {"annotations": items_out, "total": total}


@router.get("/{annotation_id}", response_model=AnnotationResponse)
async def get_annotation(annotation_id: int, db: Session = Depends(get_db)):
    """Retrieve a single annotation by ID."""
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail=f"Annotation with ID {annotation_id} not found")

    ext_item_id = str(annotation.item.external_id) if annotation.item and annotation.item.external_id else str(annotation.item_id)
    return AnnotationResponse(
        id=annotation.id,
        project_id=annotation.project_id or 0,
        annotator_id=annotation.annotator_id,
        item_id=ext_item_id,
        label=annotation.label,
        confidence=annotation.confidence,
        metadata=annotation.metadata_ or {},
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
    )


@router.post("/", response_model=AnnotationResponse, status_code=201)
async def create_annotation(payload: AnnotationCreate, db: Session = Depends(get_db)):
    """Create a new single annotation record."""
    # Verify project if exists
    project = db.query(Project).filter(Project.id == payload.project_id).first()
    if project and project.label_set and payload.label not in project.label_set:
        raise HTTPException(
            status_code=400,
            detail=f"Label '{payload.label}' is not valid for project '{project.name}'. Allowed labels: {project.label_set}",
        )

    # Ensure annotator exists
    annotator = db.query(Annotator).filter(Annotator.id == payload.annotator_id).first()
    if not annotator:
        annotator = Annotator(id=payload.annotator_id, name=f"Annotator_{payload.annotator_id}")
        db.add(annotator)
        db.flush()

    # Find or create item
    item = (
        db.query(Item)
        .filter(Item.project_id == payload.project_id, Item.external_id == payload.item_id)
        .first()
    )
    if not item:
        item = Item(
            project_id=payload.project_id,
            external_id=payload.item_id,
            content={"item_id": payload.item_id},
            source=f"project_{payload.project_id}",
        )
        db.add(item)
        db.flush()

    # Check duplicate
    existing = (
        db.query(Annotation)
        .filter(Annotation.item_id == item.id, Annotation.annotator_id == payload.annotator_id)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Annotation already exists for item '{payload.item_id}' and annotator {payload.annotator_id}",
        )

    annotation = Annotation(
        project_id=payload.project_id,
        item_id=item.id,
        annotator_id=payload.annotator_id,
        label=payload.label,
        confidence=payload.confidence,
        metadata_=payload.metadata or {},
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)

    return AnnotationResponse(
        id=annotation.id,
        project_id=annotation.project_id,
        annotator_id=annotation.annotator_id,
        item_id=payload.item_id,
        label=annotation.label,
        confidence=annotation.confidence,
        metadata=annotation.metadata_ or {},
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
    )
