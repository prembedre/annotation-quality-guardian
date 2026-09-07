"""
Pydantic schemas for Automated Task Rerouting.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class RerouteItemPendingResponse(BaseModel):
    """Pending reroute item detail."""
    model_config = ConfigDict(from_attributes=True)

    reroute_id: Optional[int] = None
    item_id: int
    project_id: int
    external_id: str
    original_annotator_id: Optional[int] = None
    original_annotator_name: Optional[str] = None
    reason: Optional[str] = None
    trust_score: Optional[float] = None
    flagged: bool = True
    reroute_status: str = "PENDING"
    content: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ReroutePendingListResponse(BaseModel):
    """Response containing list of pending reroute tasks."""
    total: int
    items: List[RerouteItemPendingResponse]


class RerouteAssignRequest(BaseModel):
    """Request payload to assign or reassign an item to a new annotator."""
    reassigned_annotator_id: int = Field(..., description="Target annotator ID to reassign the task to")
    reason: Optional[str] = Field(None, description="Reason for assignment / notes")


class RerouteAssignResponse(BaseModel):
    """Response after assigning reroute task."""
    success: bool
    reroute_id: int
    item_id: int
    project_id: int
    original_annotator_id: Optional[int] = None
    reassigned_annotator_id: int
    reroute_status: str
    message: str
    assigned_at: datetime


class RerouteHistorySchema(BaseModel):
    """Full reroute history record schema."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    item_id: int
    project_id: int
    original_annotator_id: Optional[int] = None
    reassigned_annotator_id: Optional[int] = None
    reason: Optional[str] = None
    trust_score_snapshot: Optional[float] = None
    reroute_status: str
    created_at: datetime
    updated_at: Optional[datetime] = None
