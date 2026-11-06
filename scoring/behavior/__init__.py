"""
Behavioral anomaly detection package.

Provides real behavioral anomaly scoring:
- Duration z-score velocity calculation
- Repetition and streak detection
- Label distribution drift (Total Variation Distance)
"""

from scoring.behavior.anomaly_detector import (
    calculate_duration_zscore,
    calculate_streak_score,
    calculate_distribution_drift,
    evaluate_behavioral_anomaly,
)

__all__ = [
    "calculate_duration_zscore",
    "calculate_streak_score",
    "calculate_distribution_drift",
    "evaluate_behavioral_anomaly",
]
