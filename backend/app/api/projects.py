"""
API routes for project management and project-level operations.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectResponse
from app.api.export import export_project_dataset

router = APIRouter()


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Retrieve all projects with pagination."""
    projects = db.query(Project).order_by(Project.id.desc()).offset(offset).limit(limit).all()
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: Session = Depends(get_db)):
    """Retrieve a single project by ID."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail=f"Project with ID {project_id} not found")
    return project


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new annotation project."""
    existing = db.query(Project).filter(Project.name == payload.name).first()
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Project with name '{payload.name}' already exists",
        )

    project = Project(
        name=payload.name,
        description=payload.description,
        label_set=payload.label_set,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}/export")
async def export_project(
    project_id: int,
    format: str = Query("csv", description="Output format: 'csv' or 'json'"),
    db: Session = Depends(get_db),
):
    """Export project annotations and quality/trust score dataset."""
    return await export_project_dataset(project_id=project_id, format=format, db=db)
