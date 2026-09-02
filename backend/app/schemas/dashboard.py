"""
Pydantic schemas for Dashboard backend APIs (Leaderboard & Agreement Heatmap).
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class AnnotatorLeaderboardItem(BaseModel):
    """Leaderboard entry for an annotator."""
    model_config = ConfigDict(from_attributes=True)

    rank: int = Field(..., description="Annotator ranking (1-based)")
    annotator_id: int = Field(..., description="Annotator ID")
    annotator_name: str = Field(..., description="Annotator name or handle")
    total_annotations: int = Field(..., description="Total annotations submitted")
    gold_accuracy: Optional[float] = Field(None, description="Accuracy on gold standard items (0.0–1.0)")
    avg_confidence: Optional[float] = Field(None, description="Average confidence score")
    avg_duration_ms: Optional[float] = Field(None, description="Average duration in ms")
    trust_score: Optional[float] = Field(None, description="Aggregate trust score (0.0–1.0)")


class DashboardLeaderboardResponse(BaseModel):
    """Response model for the annotator leaderboard API."""
    project_id: Optional[int] = Field(None, description="Project ID filter applied, if any")
    total_annotators: int = Field(..., description="Number of annotators on leaderboard")
    leaderboard: List[AnnotatorLeaderboardItem] = Field(default_factory=list)


class AgreementHeatmapCell(BaseModel):
    """Pairwise agreement between two annotators."""
    annotator_a_id: int
    annotator_a_name: str
    annotator_b_id: int
    annotator_b_name: str
    agreement_rate: float = Field(..., ge=0.0, le=1.0, description="Observed percentage agreement (0.0–1.0)")
    overlap_count: int = Field(..., ge=0, description="Number of co-annotated items")


class DashboardAgreementHeatmapResponse(BaseModel):
    """Response model for the inter-annotator agreement heatmap API."""
    project_id: int = Field(..., description="Target project ID")
    annotators: List[str] = Field(default_factory=list, description="Ordered list of annotator names")
    annotator_ids: List[int] = Field(default_factory=list, description="Ordered list of annotator IDs")
    matrix: List[List[float]] = Field(default_factory=list, description="NxN pairwise agreement matrix")
    cells: List[AgreementHeatmapCell] = Field(default_factory=list, description="Flattened cell details")
    overall_kappa: Optional[float] = Field(None, description="Overall Fleiss / Cohen Kappa for project")
