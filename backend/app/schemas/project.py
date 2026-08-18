"""
Pydantic schemas for projects.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class ProjectCreate(BaseModel):
    """Payload for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, description="Project description")
    label_set: List[str] = Field(..., min_length=1, description="Allowed label classes")


class ProjectResponse(BaseModel):
    """Single project response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: Optional[str] = None
    label_set: List[str]
    created_at: datetime
    updated_at: Optional[datetime] = None
