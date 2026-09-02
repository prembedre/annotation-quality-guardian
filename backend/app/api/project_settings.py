"""
API routes for Project Scoring Settings and Quality Thresholds.
"""

from fastapi import APIRouter, Depends, HTTPException, status
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
    summary="Get project scoring thresholds",
)
async def read_project_settings(
    project_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve current quality scoring thresholds for a project.
    """
    try:
        return get_project_settings(db=db, project_id=project_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch project settings: {str(exc)}",
        )


@router.put(
    "/{project_id}/settings",
    response_model=ProjectSettingsSchema,
    summary="Update project scoring thresholds",
)
async def modify_project_settings(
    project_id: int,
    payload: ProjectSettingsUpdateSchema,
    db: Session = Depends(get_db),
):
    """
    Update quality scoring thresholds for a project.
    """
    try:
        updates = payload.model_dump(exclude_unset=True)
        return update_project_settings(
            db=db,
            project_id=project_id,
            updates=updates,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update project settings: {str(exc)}",
        )
