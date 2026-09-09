"""
Project schemas.

Provides request and response schemas for annotation projects.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    """Shared project fields."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Project name",
    )

    description: Optional[str] = Field(
        None,
        description="Project description",
    )

    label_set: List[str] = Field(
        default_factory=list,
        description="List of valid label strings",
    )


class ProjectCreate(ProjectBase):
    """Schema for creating a project."""

    pass


class ProjectResponse(ProjectBase):
    """Schema returned for a project."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None