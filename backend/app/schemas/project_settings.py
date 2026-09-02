"""
Pydantic schemas for Project Scoring Threshold Settings.
"""

from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ProjectSettingsSchema(BaseModel):
    """Project quality scoring thresholds schema."""
    model_config = ConfigDict(from_attributes=True)

    project_id: Optional[int] = Field(None, description="Project ID")
    gold_threshold: float = Field(
        default=90.0,
        ge=0.0,
        le=100.0,
        description="Minimum gold-standard accuracy percentage threshold (0-100)",
    )
    kappa_threshold: float = Field(
        default=0.7,
        ge=-1.0,
        le=1.0,
        description="Minimum Cohen/Fleiss Kappa agreement threshold (-1.0 to 1.0)",
    )
    behavior_threshold: float = Field(
        default=75.0,
        ge=0.0,
        le=100.0,
        description="Minimum behavioral score percentage threshold (0-100)",
    )
    embedding_threshold: float = Field(
        default=80.0,
        ge=0.0,
        le=100.0,
        description="Minimum embedding similarity/outlier threshold percentage (0-100)",
    )


class ProjectSettingsUpdateSchema(BaseModel):
    """Payload to update project scoring thresholds."""
    gold_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Minimum gold-standard accuracy percentage threshold (0-100)",
    )
    kappa_threshold: Optional[float] = Field(
        None,
        ge=-1.0,
        le=1.0,
        description="Minimum Cohen/Fleiss Kappa agreement threshold (-1.0 to 1.0)",
    )
    behavior_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Minimum behavioral score percentage threshold (0-100)",
    )
    embedding_threshold: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Minimum embedding similarity/outlier threshold percentage (0-100)",
    )
