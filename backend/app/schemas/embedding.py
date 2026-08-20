"""
Pydantic schemas for Embedding Outlier detection.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class EmbeddingResultCreate(BaseModel):
    """Payload for submitting embedding and outlier results."""
    project_id: int
    item_id: int
    model_name: str = Field("text-embedding-3-small", description="Model used for embedding generation")
    outlier_score: float = Field(..., ge=0.0, le=1.0, description="Outlier score between 0.0 and 1.0")
    is_outlier: bool = Field(False, description="Flag indicating if the item is an outlier")
    embedding: Optional[List[float]] = Field(None, description="Embedding vector")
    nearest_item_id: Optional[int] = Field(None, description="ID of closest neighbor item")
    details: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingResultResponse(BaseModel):
    """Response model for embedding analysis record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    item_id: int
    model_name: str
    outlier_score: Optional[float] = None
    is_outlier: bool = False
    embedding: Optional[List[float]] = None
    nearest_item_id: Optional[int] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime
