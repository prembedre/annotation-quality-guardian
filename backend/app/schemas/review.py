"""
Pydantic schemas for the review queue and human resolution.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ReviewAnnotationInfo(BaseModel):
    """Annotation details embedded within a review queue item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    annotator_id: int
    annotator_name: Optional[str] = None
    label: str
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None
    timestamp: datetime


class ReviewItemResponse(BaseModel):
    """Single flagged item in the review queue."""
    model_config = ConfigDict(from_attributes=True)

    item_id: int
    project_id: Optional[int] = None
    external_id: Optional[str] = None
    content: Dict[str, Any] = Field(default_factory=dict)
    is_gold: bool = False
    gold_label: Optional[str] = None
    annotations: List[ReviewAnnotationInfo] = Field(default_factory=list)
    trust_score: Optional[float] = None
    trust_score_breakdown: Dict[str, Any] = Field(default_factory=dict)
    flagged: bool = True
    created_at: datetime


class ReviewQueueResponse(BaseModel):
    """Paginated list of review queue items."""
    items: List[ReviewItemResponse]
    page: int = Field(..., ge=1, description="Current page number")
    page_size: int = Field(..., ge=1, description="Number of items per page")
    total: int = Field(..., ge=0, description="Total number of matching items")
    total_pages: int = Field(..., ge=0, description="Total pages available")


class ReviewResolveRequest(BaseModel):
    """Payload for resolving a flagged item."""
    ground_truth_label: str = Field(..., min_length=1, description="The assigned ground-truth label")
    notes: Optional[str] = Field(None, description="Optional reviewer notes or rationale")


class ReviewResolveResponse(BaseModel):
    """Response after resolving a review queue item."""
    success: bool
    item_id: int
    status: str = "resolved"
    gold_label: str
    message: str = "Item resolved successfully"
