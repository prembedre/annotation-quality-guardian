"""
Pydantic schemas for Webhook annotation ingestion.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class WebhookAnnotationPayload(BaseModel):
    """Payload received from external annotation tools via webhook."""
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    project_id: int = Field(..., description="Target project ID")
    item_id: str = Field(..., min_length=1, description="External item/dataset identifier")
    annotator_id: int = Field(..., description="ID of the annotator")
    label: str = Field(..., min_length=1, description="Annotation label assigned")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score between 0.0 and 1.0")
    duration_ms: Optional[int] = Field(None, ge=0, description="Time taken to annotate in milliseconds")
    timestamp: Optional[datetime] = Field(None, description="ISO-8601 timestamp of annotation")
    content: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Item payload/content data")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional metadata")


class WebhookAnnotationResponse(BaseModel):
    """Structured response after processing a webhook annotation."""
    success: bool
    message: str
    project_id: int
    item_id: int
    external_id: str
    annotation_id: int
    trust_score: Optional[float] = None
    flagged: Optional[bool] = None
    is_duplicate: bool = False
