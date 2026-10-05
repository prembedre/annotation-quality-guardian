"""
Project API endpoints.

Provides CRUD operations for annotation projects.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
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
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """List all annotation projects. If empty, seed default Project 1."""

    projects = (
        db.query(Project)
        .order_by(Project.id)
        .all()
    )

    if not projects:
        default_project = Project(
            name="Project 1",
            description="AQG Demo Project",
            label_set=["positive", "negative", "neutral"],
            automation_enabled=False,
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
