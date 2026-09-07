"""
Pydantic schemas for Label Schema A/B Testing Experiments.
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ABTestExperimentCreateSchema(BaseModel):
    """Schema for creating a new A/B testing experiment."""
    experiment_name: str = Field(..., min_length=1, max_length=255, description="Experiment title")
    project_id: int = Field(..., description="Project ID")
    schema_version_a: Dict[str, Any] = Field(..., description="Control schema configuration")
    schema_version_b: Dict[str, Any] = Field(..., description="Variant schema configuration")
    annotator_group: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Annotator allocation rules")
    assigned_version: Optional[str] = Field("SPLIT_50_50", description="Active assignment rule ('A', 'B', 'SPLIT_50_50')")
    status: Optional[str] = Field("active", description="Status ('active', 'completed', 'draft')")


class ABTestExperimentResponseSchema(BaseModel):
    """Schema for returning A/B experiment data."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    experiment_name: str
    project_id: int
    schema_version_a: Dict[str, Any]
    schema_version_b: Dict[str, Any]
    annotator_group: Optional[Dict[str, Any]] = None
    assigned_version: Optional[str] = None
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None


class ABTestExperimentListResponse(BaseModel):
    """List of A/B test experiments."""
    total: int
    experiments: List[ABTestExperimentResponseSchema]
