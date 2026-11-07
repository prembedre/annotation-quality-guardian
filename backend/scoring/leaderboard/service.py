"""
Reusable scoring services for annotator leaderboard calculations.

The service operates on annotation dictionaries so it can be reused
independently of the database/backend layer.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from scoring.gold_checker.checker import gold_accuracy


def calculate_rolling_accuracy(
    annotations: List[Dict[str, Any]],
    gold_items: Dict[str, str],
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate rolling gold-standard accuracy for every annotator.

    Only annotations within the rolling time window are considered.

    Each annotation should contain:
        item_id
        annotator_id
        label
        created_at

    Args:
        annotations: Annotation records.
        gold_items: Mapping of item_id to gold label.
        window_days: Number of days included in the rolling window.
        as_of: End of the rolling window. Defaults to the latest
               annotation timestamp.

    Returns:
        Per-annotator rolling accuracy statistics.
    """
    if window_days <= 0:
        raise ValueError("window_days must be greater than 0")

    dated_annotations = [
        annotation
        for annotation in annotations
        if isinstance(annotation.get("created_at"), datetime)
    ]

    if not dated_annotations:
        return {}

    if as_of is None:
        as_of = max(
            annotation["created_at"]
            for annotation in dated_annotations
        )

    start_time = as_of - timedelta(days=window_days)

    rolling_annotations = [
        annotation
        for annotation in dated_annotations
        if start_time <= annotation["created_at"] <= as_of
    ]

    result = gold_accuracy(
        annotations=rolling_annotations,
        gold_items=gold_items,
    )

    return result["per_annotator"]


def calculate_leaderboard(
    annotations: List[Dict[str, Any]],
    gold_items: Optional[Dict[str, str]] = None,
    gold_threshold: float = 0.90,
    window_days: int = 30,
    as_of: Optional[datetime] = None,
) -> Dict[str, Any]:
    """
    Build an annotator leaderboard.

    The leaderboard includes annotation volume, rolling accuracy,
    and a configurable quality flag.

    Args:
        annotations: Annotation records.
        gold_items: Optional mapping of item_id to gold label.
        gold_threshold: Minimum acceptable rolling accuracy.
        window_days: Rolling accuracy window in days.
        as_of: End timestamp for the rolling window.

    Returns:
        Dictionary containing leaderboard rows and metadata.
    """
    if not 0.0 <= gold_threshold <= 1.0:
        raise ValueError("gold_threshold must be between 0 and 1")

    if gold_items is None:
        gold_items = {}

    annotator_annotations: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for annotation in annotations:
        annotator_id = str(annotation["annotator_id"])
        annotator_annotations[annotator_id].append(annotation)

    rolling_accuracy = calculate_rolling_accuracy(
        annotations=annotations,
        gold_items=gold_items,
        window_days=window_days,
        as_of=as_of,
    )

    leaderboard: List[Dict[str, Any]] = []

    for annotator_id, records in annotator_annotations.items():
        stats = rolling_accuracy.get(
            annotator_id,
            {
                "accuracy": 0.0,
                "correct": 0,
                "total": 0,
            },
        )

        accuracy = float(stats["accuracy"])

        leaderboard.append(
            {
                "annotator_id": annotator_id,
                "total_annotations": len(records),
                "rolling_accuracy": accuracy,
                "gold_correct": stats["correct"],
                "gold_annotations": stats["total"],
                "flagged": accuracy < gold_threshold,
            }
        )

    # Highest quality first, then higher annotation volume.
    leaderboard.sort(
        key=lambda row: (
            row["rolling_accuracy"],
            row["total_annotations"],
        ),
        reverse=True,
    )

    for rank, row in enumerate(leaderboard, start=1):
        row["rank"] = rank

    return {
        "total_annotators": len(leaderboard),
        "window_days": window_days,
        "gold_threshold": gold_threshold,
        "leaderboard": leaderboard,
    }