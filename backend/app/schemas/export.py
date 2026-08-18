"""
Pydantic schemas for dataset export.
"""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class ExportItemAnnotation(BaseModel):
    """Annotation details in dataset export."""
    annotation_id: int
    annotator_id: int
    annotator_name: Optional[str] = None
    label: str
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None
    metadata: Dict[str, Any] = {}
    created_at: datetime


class DatasetExportItem(BaseModel):
    """Item record in structured dataset export."""
    item_id: int
    external_id: Optional[str] = None
    content: Dict[str, Any] = {}
    is_gold: bool = False
    gold_label: Optional[str] = None
    trust_score: Optional[float] = None
    trust_score_breakdown: Dict[str, Any] = {}
    flagged: bool = False
    annotations: List[ExportItemAnnotation] = []


class DatasetExportResponse(BaseModel):
    """Full dataset JSON export structure."""
    project_id: int
    project_name: str
    total_items: int
    total_annotations: int
    items: List[DatasetExportItem]
