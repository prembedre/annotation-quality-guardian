"""
Pydantic schemas for projects.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    label_set: List[str] = Field(..., min_length=1, description="Allowed label classes")


class ProjectResponse(BaseModel):
    """Single project response."""
    id: int
    name: str
    description: Optional[str] = None
    label_set: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
