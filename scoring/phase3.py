"""
Phase 3 scoring services.

Provides a single reusable interface for leaderboard and
agreement analytics used by the backend dashboard.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from scoring.agreement.heatmap import (
    calculate_disagreement_statistics,
    generate_agreement_heatmap,
)
from scoring.leaderboard.service import calculate_leaderboard


def build_leaderboard(
    annotations: List[Dict[str, Any]],
    gold_items: Optional[Dict[str, str]] = None,
    gold_threshold: float = 0.90,
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build reusable annotator leaderboard data."""
    return calculate_leaderboard(
        annotations=annotations,
        gold_items=gold_items,
        gold_threshold=gold_threshold,
        window_days=window_days,
        as_of=as_of,
    )


def build_agreement_analytics(
    annotations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build reusable agreement heatmap and disagreement data."""
    heatmap = generate_agreement_heatmap(annotations)
    disagreements = calculate_disagreement_statistics(annotations)

    return {
        "annotator_ids": heatmap["annotator_ids"],
        "matrix": heatmap["matrix"],
        "cells": heatmap["cells"],
        "by_class": disagreements["by_class"],
        "by_annotator": disagreements["by_annotator"],
        "disagreement_pairs": disagreements["disagreement_pairs"],
    }