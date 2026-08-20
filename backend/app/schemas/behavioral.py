"""
Pydantic schemas for Behavioral Anomaly scoring.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class BehavioralScoreCreate(BaseModel):
    """Payload for submitting behavioral evaluation results."""
    project_id: int
    annotator_id: int
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score between 0.0 and 1.0")
    item_id: Optional[int] = Field(None, description="Optional specific item ID")
    time_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Duration/speed metric score")
    streak_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Repetition/streak metric score")
    anomaly_flag: bool = Field(False, description="Flag indicating anomalous behavior")
    reason: Optional[str] = Field(None, description="Explanation for anomaly flag")
    details: Dict[str, Any] = Field(default_factory=dict)


class BehavioralScoreResponse(BaseModel):
    """Response model for behavioral scoring record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    annotator_id: int
    item_id: Optional[int] = None
    anomaly_score: Optional[float] = None
    time_score: Optional[float] = None
    streak_score: Optional[float] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    computed_at: datetime
