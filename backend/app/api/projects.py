"""
Project API endpoints.

Provides CRUD operations for annotation projects.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_role
from app.core.db import get_db
from app.models.project import Project
from app.models.user import User, UserRole
from app.schemas.project import ProjectCreate, ProjectResponse


router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)


@router.get(
    "",
    response_model=List[ProjectResponse],
)
def list_projects(
    include_archived: bool = Query(False, description="Whether to include archived projects"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List annotation projects. If empty, seed default Project 1."""

    query = db.query(Project)
    if not include_archived:
        query = query.filter(Project.is_archived.is_(False))

    projects = query.order_by(Project.id).all()

    if not projects and not include_archived:
        default_project = Project(
            name="Project 1",
            description="AQG Demo Project",
            label_set=["positive", "negative", "neutral"],
            automation_enabled=False,
            is_archived=False,
        )
        db.add(default_project)
        db.commit()
        db.refresh(default_project)
        projects = [default_project]

    return projects


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Get a project by ID."""

    project = (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )

    if project is None:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found.",
        )

    return project


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new annotation project."""

    existing_project = (
        db.query(Project)
        .filter(Project.name == project_data.name)
        .first()
    )

    if existing_project is not None:
        raise HTTPException(
            status_code=409,
            detail=f"Project '{project_data.name}' already exists.",
        )

    project = Project(
        name=project_data.name,
        description=project_data.description,
        label_set=project_data.label_set,
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


@router.post(
    "/{project_id}/duplicate",
    response_model=ProjectResponse,
    status_code=201,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
)
def duplicate_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Duplicate a project and its configuration."""
    source = db.query(Project).filter(Project.id == project_id).first()
    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found.",
        )

    # Generate unique copy name
    base_name = f"{source.name} (Copy)"
    candidate_name = base_name
    counter = 2
    while db.query(Project).filter(Project.name == candidate_name).first():
        candidate_name = f"{source.name} (Copy {counter})"
        counter += 1

    new_project = Project(
        name=candidate_name,
        description=source.description,
        label_set=list(source.label_set) if source.label_set else [],
        automation_enabled=source.automation_enabled,
        is_archived=False,
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)

    # Duplicate threshold if source has one
    if source.threshold:
        from app.models.project_threshold import ProjectThreshold
        new_threshold = ProjectThreshold(
            project_id=new_project.id,
            gold_threshold=source.threshold.gold_threshold,
            kappa_threshold=source.threshold.kappa_threshold,
            behavioral_threshold=source.threshold.behavioral_threshold,
            embedding_threshold=source.threshold.embedding_threshold,
        )
        db.add(new_threshold)
        db.commit()

    return new_project


@router.post(
    "/{project_id}/archive",
    response_model=ProjectResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
)
def archive_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Archive a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found.",
        )

    project.is_archived = True
    db.commit()
    db.refresh(project)
    return project


@router.post(
    "/{project_id}/unarchive",
    response_model=ProjectResponse,
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
)
def unarchive_project(
    project_id: int,
    db: Session = Depends(get_db),
):
    """Unarchive a project."""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=404,
            detail=f"Project with ID {project_id} not found.",
        )

    project.is_archived = False
    db.commit()
    db.refresh(project)
    return project

