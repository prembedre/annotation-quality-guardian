"""
Phase 4 scoring and automation facade.

Provides a single reusable entry point for backend integration.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from datetime import datetime

from scoring.automation.ab_testing import ABTestAnalysis, analyze_ab_test
from scoring.automation.ambiguity import (
    AmbiguousClass,
    detect_ambiguous_classes,
)
from scoring.automation.rerouting import (
    RerouteRecommendation,
    recommend_annotator,
)
from scoring.automation.underperformer import (
    AnnotatorPerformance,
    detect_underperformers,
)


def build_underperformer_analytics(
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
    trust_scores: List[Dict[str, Any]],
    gold_threshold: float = 0.90,
    trust_threshold: float = 0.60,
    minimum_annotations: int = 10,
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> List[AnnotatorPerformance]:
    """Build Phase 4 underperformer analytics."""

    return detect_underperformers(
        annotations=annotations,
        gold_items=gold_items,
        trust_scores=trust_scores,
        gold_threshold=gold_threshold,
        trust_threshold=trust_threshold,
        minimum_annotations=minimum_annotations,
        window_days=window_days,
        as_of=as_of,
    )


def build_rerouting_recommendation(
    item_id: str,
    original_annotator_id: Optional[str],
    annotator_performance: List[Dict[str, Any]],
    minimum_accuracy: float = 0.90,
    minimum_trust: float = 0.60,
) -> RerouteRecommendation:
    """Build a replacement-annotator recommendation."""

    return recommend_annotator(
        item_id=item_id,
        original_annotator_id=original_annotator_id,
        annotator_performance=annotator_performance,
        minimum_accuracy=minimum_accuracy,
        minimum_trust=minimum_trust,
    )


def build_ab_test_analytics(
    experiment_name: str,
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
    schema_field: str = "schema_version",
) -> ABTestAnalysis:
    """Build A/B schema experiment analytics."""

    return analyze_ab_test(
        experiment_name=experiment_name,
        annotations=annotations,
        gold_items=gold_items,
        schema_field=schema_field,
    )


def build_ambiguity_analytics(
    annotations: List[Dict[str, Any]],
    disagreement_threshold: float = 0.50,
    minimum_comparisons: int = 5,
) -> List[AmbiguousClass]:
    """Build ambiguous-class analytics."""

    return detect_ambiguous_classes(
        annotations=annotations,
        disagreement_threshold=disagreement_threshold,
        minimum_comparisons=minimum_comparisons,
    )


__all__ = [
    "AnnotatorPerformance",
    "RerouteRecommendation",
    "ABTestAnalysis",
    "AmbiguousClass",
    "build_underperformer_analytics",
    "build_rerouting_recommendation",
    "build_ab_test_analytics",
    "build_ambiguity_analytics",
]