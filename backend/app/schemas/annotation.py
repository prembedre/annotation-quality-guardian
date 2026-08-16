"""
Pydantic schemas for annotations.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class AnnotationCreate(BaseModel):
    """Payload for creating a new annotation."""
    project_id: int = Field(..., description="ID of the parent project")
    annotator_id: int = Field(..., description="ID of the annotator")
    item_id: str = Field(..., description="Identifier of the item being annotated")
    label: str = Field(..., description="The assigned label/class")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Annotator confidence")
    metadata: Optional[dict] = Field(default_factory=dict, description="Additional metadata")


class AnnotationResponse(BaseModel):
    """Single annotation response."""
    id: int
    project_id: int
    annotator_id: int
    item_id: str
    label: str
    confidence: Optional[float] = None
    metadata: dict = {}
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    """Paginated annotation list."""
    annotations: List[AnnotationResponse]
    total: int
