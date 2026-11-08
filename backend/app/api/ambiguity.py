"""
Ambiguous class insights API.

Exposes Member 3's ambiguity detection logic to the frontend.
"""

from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.auth_deps import require_role
from app.core.db import get_db
from app.models.annotation import Annotation
from app.models.project import Project
from app.models.user import UserRole
from scoring.automation.ambiguity import detect_ambiguous_classes


router = APIRouter(
    prefix="/ambiguity",
    tags=["Ambiguity Insights"],
)


def compute_pairwise_confusion_matrix(
    annotations: List[Annotation],
    label_set: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute real pairwise label confusion matrix from overlapping annotations.
    """
    by_item = defaultdict(list)
    observed_labels = set()
    for a in annotations:
        if a.label:
            by_item[a.item_id].append(str(a.label))
            observed_labels.add(str(a.label))

    categories = []
    if label_set:
        for l in label_set:
            sl = str(l)
            if sl not in categories:
                categories.append(sl)
    for l in sorted(observed_labels):
        if l not in categories:
            categories.append(l)

    if not categories:
        categories = ["Positive", "Neutral", "Negative"]

    cat_idx = {c: i for i, c in enumerate(categories)}
    n = len(categories)
    counts = [[0 for _ in range(n)] for _ in range(n)]

    total_pairs = 0
    for item_id, item_labels in by_item.items():
        if len(item_labels) < 2:
            continue
        for i in range(len(item_labels)):
            for j in range(i + 1, len(item_labels)):
                l1 = item_labels[i]
                l2 = item_labels[j]
                if l1 in cat_idx and l2 in cat_idx:
                    idx1 = cat_idx[l1]
                    idx2 = cat_idx[l2]
                    total_pairs += 1
                    if idx1 == idx2:
                        counts[idx1][idx1] += 2
                    else:
                        counts[idx1][idx2] += 1
                        counts[idx2][idx1] += 1

    matrix = []
    top_pair = None
    top_rate = 0.0

    for i in range(n):
        row_sum = sum(counts[i])
        row = []
        for j in range(n):
            if row_sum > 0:
                val = round(counts[i][j] / row_sum, 4)
            else:
                val = 1.0 if i == j else 0.0
            row.append(val)
            if i != j and val > top_rate:
                top_rate = val
                top_pair = (categories[i], categories[j])
        matrix.append(row)

    return {
        "categories": categories,
        "matrix": matrix,
        "total_pairs_evaluated": total_pairs,
        "top_confusion_pair": top_pair,
        "top_confusion_rate": top_rate,
    }


def generate_ambiguity_recommendations(
    classes: List[Dict[str, Any]],
    confusion_info: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Generate actionable taxonomy recommendations based on real ambiguity statistics.
    """
    recommendations = []

    # 1. Most disputed class
    ambiguous_classes = [c for c in classes if c.get("ambiguous")]
    top_class = ambiguous_classes[0] if ambiguous_classes else (classes[0] if classes else None)
    if top_class and top_class.get("disagreement_rate", 0) > 0:
        rate_pct = f"{top_class['disagreement_rate'] * 100:.1f}%"
        disagreements = top_class.get("disagreements", 0)
        recommendations.append({
            "title": f"Clarify Boundary for '{top_class['label']}'",
            "detail": f"{rate_pct} disagreement rate across {disagreements} disputed item comparisons. Add explicit positive/negative inclusion markers and edge-case boundary anchors in task guidelines.",
            "severity": "high" if top_class.get("ambiguous") else "medium",
        })

    # 2. Top confusion pair from matrix
    top_pair = confusion_info.get("top_confusion_pair")
    top_rate = confusion_info.get("top_confusion_rate", 0)
    if top_pair and top_rate > 0.05:
        c1, c2 = top_pair
        rate_pct = f"{top_rate * 100:.1f}%"
        recommendations.append({
            "title": f"Resolve Pairwise Confusion Between '{c1}' and '{c2}'",
            "detail": f"{rate_pct} of pairwise comparisons show confusion between '{c1}' and '{c2}'. Add contrastive side-by-side examples in annotation instructions illustrating subtle distinctions.",
            "severity": "high" if top_rate >= 0.20 else "medium",
        })
    else:
        recommendations.append({
            "title": "Maintain Consistent Boundary Anchor Definitions",
            "detail": "Inter-annotator consensus is stable across classes. Continue periodic audits to maintain labeling consistency.",
            "severity": "low",
        })

    # 3. Action recommendation
    if ambiguous_classes or top_rate >= 0.15:
        target_name = top_class['label'] if top_class else 'Ambiguous'
        recommendations.append({
            "title": "Launch A/B Guideline Trial & Enable Auto-Reroute",
            "detail": f"Validate revised instructions for '{target_name}' using an A/B split trial, and route low-confidence items to senior reviewers.",
            "severity": "medium",
        })
    else:
        recommendations.append({
            "title": "Automated Confidence Thresholding",
            "detail": "Low overall class confusion detected. High-confidence annotations can be approved automatically.",
            "severity": "low",
        })

    return recommendations


@router.get("/classes",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER, UserRole.ANNOTATOR))],
)
def get_ambiguous_classes(
    project_id: int = Query(1, ge=1),
    disagreement_threshold: float = Query(
        0.50,
        ge=0.0,
        le=1.0,
    ),
    minimum_comparisons: int = Query(
        5,
        ge=1,
    ),
    db: Session = Depends(get_db),
):
    """
    Analyze annotation disagreement and return class-level ambiguity insights,
    real pairwise confusion matrix, and dynamic guidance.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    label_set = project.label_set if project else []

    annotations = (
        db.query(Annotation)
        .filter(Annotation.project_id == project_id)
        .all()
    )

    annotation_data: List[Dict[str, Any]] = []
    for annotation in annotations:
        annotation_data.append(
            {
                "item_id": annotation.item_id,
                "annotator_id": annotation.annotator_id,
                "label": annotation.label,
            }
        )

    results = detect_ambiguous_classes(
        annotations=annotation_data,
        disagreement_threshold=disagreement_threshold,
        minimum_comparisons=minimum_comparisons,
    )

    classes = [
        {
            "label": result.label,
            "disagreements": result.disagreements,
            "occurrences": result.occurrences,
            "total_comparisons": result.total_comparisons,
            "disagreement_rate": result.disagreement_rate,
            "ambiguous": result.ambiguous,
        }
        for result in results
    ]

    ambiguous_count = sum(1 for result in results if result.ambiguous)

    confusion_info = compute_pairwise_confusion_matrix(annotations, label_set)
    recommendations = generate_ambiguity_recommendations(classes, confusion_info)

    return {
        "project_id": project_id,
        "disagreement_threshold": disagreement_threshold,
        "minimum_comparisons": minimum_comparisons,
        "total_classes": len(classes),
        "ambiguous_classes": ambiguous_count,
        "classes": classes,
        "confusion_matrix": confusion_info,
        "recommendations": recommendations,
    }


@router.get("/confusion-matrix",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER))],
)
def get_confusion_matrix(
    project_id: int = Query(1, ge=1),
    db: Session = Depends(get_db),
):
    """
    Compute pairwise confusion matrix for an active project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    label_set = project.label_set if project else []

    annotations = (
        db.query(Annotation)
        .filter(Annotation.project_id == project_id)
        .all()
    )

    return compute_pairwise_confusion_matrix(annotations, label_set)

