"""
Behavioral Anomaly Detection Engine.

Computes statistical anomaly scores from annotator behavior telemetry:
1. Annotation duration z-scores (speed-running / outlier detection)
2. Repetition & streak detection (straight-lining identical labels)
3. Label distribution drift (Total Variation Distance against dataset baseline)
"""

import math
from typing import List, Dict, Any, Optional, Tuple


def calculate_duration_zscore(
    durations: List[float],
    current_duration: Optional[float] = None,
) -> Tuple[float, float]:
    """
    Compute z-score and normalized duration anomaly score (0.0 to 1.0).

    Speed-running (very short duration) is heavily penalized as anomalous.
    Abnormally long durations are also flagged.

    Returns:
        (z_score, duration_anomaly_score)
    """
    valid = [d for d in durations if d is not None and d > 0]
    if len(valid) < 2:
        return 0.0, 0.0

    mean_d = sum(valid) / len(valid)
    variance = sum((x - mean_d) ** 2 for x in valid) / len(valid)
    std_d = math.sqrt(variance)

    target_d = current_duration if current_duration is not None else mean_d
    if std_d < 1e-6:
        # If all durations are nearly identical and extremely fast (< 500ms), flag it
        if mean_d < 500:
            return 0.0, 0.85
        return 0.0, 0.0

    z = (target_d - mean_d) / std_d

    # Speed-running penalty: if z < -1.5 (much faster than annotator's average)
    if z < -2.0 or target_d < 300:
        score = min(1.0, 0.7 + 0.15 * abs(z))
    elif z < -1.0 or target_d < 800:
        score = min(0.7, 0.3 + 0.2 * abs(z))
    elif z > 2.5:
        # Extremely slow (idle/inattentive)
        score = min(0.6, 0.2 + 0.1 * z)
    else:
        score = max(0.0, min(0.2, abs(z) * 0.05))

    return round(z, 3), round(score, 4)


def calculate_streak_score(
    labels: List[str],
    max_normal_streak: int = 4,
) -> Tuple[int, float]:
    """
    Detect repetitive straight-lining (streaks of consecutive identical labels).

    Returns:
        (max_streak_length, streak_anomaly_score)
    """
    if not labels:
        return 0, 0.0

    max_streak = 1
    curr_streak = 1

    for i in range(1, len(labels)):
        if labels[i] == labels[i - 1]:
            curr_streak += 1
            if curr_streak > max_streak:
                max_streak = curr_streak
        else:
            curr_streak = 1

    if max_streak <= max_normal_streak:
        # Low or normal streak
        streak_score = max_streak * 0.05
    else:
        # Elevated streak penalty
        excess = max_streak - max_normal_streak
        streak_score = min(1.0, 0.3 + 0.15 * excess)

    return max_streak, round(streak_score, 4)


def calculate_distribution_drift(
    annotator_labels: List[str],
    project_labels: Optional[List[str]] = None,
    label_set: Optional[List[str]] = None,
) -> float:
    """
    Compute Total Variation Distance (TVD) between the annotator's label distribution
    and the project baseline distribution.

    Returns:
        drift_score between 0.0 (identical distribution) and 1.0 (maximally drifted).
    """
    if not annotator_labels or len(annotator_labels) < 3:
        return 0.0

    # Collect vocabulary
    classes = set(annotator_labels)
    if project_labels:
        classes.update(project_labels)
    if label_set:
        classes.update(label_set)

    if not classes:
        return 0.0

    # Annotator distribution
    ann_n = len(annotator_labels)
    ann_dist = {c: annotator_labels.count(c) / ann_n for c in classes}

    # Reference baseline distribution (use project labels if >= 5 samples, else uniform over classes)
    if project_labels and len(project_labels) >= 5:
        proj_n = len(project_labels)
        ref_dist = {c: project_labels.count(c) / proj_n for c in classes}
    else:
        uniform_p = 1.0 / len(classes)
        ref_dist = {c: uniform_p for c in classes}

    # Total Variation Distance: 0.5 * sum(|P(x) - Q(x)|)
    tvd = 0.5 * sum(abs(ann_dist[c] - ref_dist[c]) for c in classes)
    return round(min(1.0, tvd), 4)


def evaluate_behavioral_anomaly(
    durations: List[float],
    current_duration: Optional[float] = None,
    labels: Optional[List[str]] = None,
    project_labels: Optional[List[str]] = None,
    label_set: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Synthesize velocity z-scores, streak repetition, and distribution drift into
    a comprehensive behavioral anomaly assessment.
    """
    labels = labels or []
    durations = [d for d in durations if d is not None]

    z_score, time_score = calculate_duration_zscore(durations, current_duration)
    max_streak, streak_score = calculate_streak_score(labels)
    drift_score = calculate_distribution_drift(labels, project_labels, label_set)

    # Weighted composite score
    anomaly_score = (
        0.45 * time_score +
        0.35 * streak_score +
        0.20 * drift_score
    )
    anomaly_score = round(min(1.0, max(0.0, anomaly_score)), 4)

    reasons = []
    if time_score >= 0.6:
        reasons.append(f"Abnormally rapid annotation pace (z = {z_score}, time_score = {time_score})")
    if streak_score >= 0.5:
        reasons.append(f"Repetitive straight-lining pattern detected (streak of {max_streak})")
    if drift_score >= 0.4:
        reasons.append(f"High label distribution drift against baseline (TVD = {drift_score})")

    anomaly_flag = anomaly_score >= 0.5 or bool(reasons)

    return {
        "anomaly_score": anomaly_score,
        "time_score": time_score,
        "streak_score": streak_score,
        "drift_score": drift_score,
        "z_score": z_score,
        "max_streak": max_streak,
        "anomaly_flag": anomaly_flag,
        "reason": "; ".join(reasons) if reasons else "Normal behavioral profile",
    }
