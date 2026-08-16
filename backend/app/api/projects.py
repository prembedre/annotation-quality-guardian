"""
API routes for project management.
"""

from fastapi import APIRouter, HTTPException
from app.schemas.project import ProjectCreate, ProjectResponse

router = APIRouter()


@router.get("/")
async def list_projects():
    """Retrieve all projects."""
    # TODO: integrate with database service
    return {"projects": [], "total": 0}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    """Retrieve a single project by ID."""
    # TODO: integrate with database service
    raise HTTPException(status_code=404, detail="Project not found")


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(payload: ProjectCreate):
    """Create a new project."""
    # TODO: integrate with database service
    raise HTTPException(status_code=501, detail="Not yet implemented")
