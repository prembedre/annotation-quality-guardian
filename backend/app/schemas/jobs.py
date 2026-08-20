"""
Pydantic schemas for asynchronous Celery job triggers and status tracking.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


class BehavioralJobRequest(BaseModel):
    """Payload to trigger an asynchronous behavioral scoring task."""
    project_id: int
    annotator_id: int
    anomaly_score: float = Field(..., ge=0.0, le=1.0)
    item_id: Optional[int] = None
    time_score: Optional[float] = None
    streak_score: Optional[float] = None
    anomaly_flag: bool = False
    reason: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class EmbeddingJobRequest(BaseModel):
    """Payload to trigger an asynchronous embedding analysis task."""
    project_id: int
    model_name: str = Field("text-embedding-3-small", description="Embedding model name")
    outlier_threshold: float = Field(0.75, ge=0.0, le=1.0, description="Threshold for outlier flagging")


class TrustScoreJobRequest(BaseModel):
    """Payload to trigger an asynchronous unified trust score calculation task."""
    project_id: int
    item_id: Optional[int] = None
    weights: Optional[Dict[str, float]] = None


class JobStatusResponse(BaseModel):
    """Standardized response schema for asynchronous job queries."""
    job_id: str
    status: str = Field(..., description="Job status: PENDING, RUNNING, COMPLETED, FAILED")
    task_name: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_available: bool = False
    result: Optional[Any] = None
    error: Optional[str] = None
