"""
Project Settings API.

Provides endpoints for reading and updating project-level
quality thresholds and Phase 4 automation controls.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.project_settings import (
    ProjectSettingsSchema,
    ProjectSettingsUpdateSchema,
)
from app.services.project_settings_service import (
    get_project_settings,
    update_project_settings,
)


router = APIRouter(
    prefix="/projects",
    tags=["Project Settings"],
)


@router.get(
    "/{project_id}/settings",
    response_model=ProjectSettingsSchema,
)
def get_settings(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Get project scoring thresholds and Phase 4 automation settings.
    """

    try:
        return get_project_settings(
            db=db,
            project_id=project_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@router.put(
    "/{project_id}/settings",
    response_model=ProjectSettingsSchema,
)
def update_settings(
    project_id: int,
    settings: ProjectSettingsUpdateSchema,
    db: Session = Depends(get_db),
):
    """
    Update project scoring thresholds and Phase 4 automation settings.
    """

    try:
        updates = settings.model_dump(
            exclude_unset=True,
        )

        return update_project_settings(
            db=db,
            project_id=project_id,
            updates=updates,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc