"""
Pydantic schemas for annotations.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class AnnotationCreate(BaseModel):
    """Payload for creating a new annotation."""
    project_id: int = Field(..., description="ID of the parent project")
    annotator_id: int = Field(..., description="ID of the annotator")
    item_id: int = Field(..., description="Identifier of the item being annotated")
    label: str = Field(..., description="The assigned label/class")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Annotator confidence")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")


class AnnotationResponse(BaseModel):
    """Single annotation response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    annotator_id: int
    item_id: str
    label: str
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class AnnotationListResponse(BaseModel):
    """Paginated annotation list."""
    annotations: List[AnnotationResponse]
    total: int
