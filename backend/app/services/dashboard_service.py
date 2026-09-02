"""
Dashboard Service.
Backend integration point for Dashboard endpoints (Leaderboard & Agreement Heatmap).
Integrates database queries and delegates scoring computations to Member 3's scoring services.
"""

from typing import Dict, Any, List, Optional
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.annotator import Annotator
from app.models.annotation import Annotation
from app.models.item import Item
from app.models.project import Project
from app.models.trust_score import TrustScore
from app.services.kappa_service import compute_fleiss_kappa
from app.services.gold_standard_service import compute_gold_accuracy


def get_annotator_leaderboard(
    db: Session,
    project_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Fetch and format annotator ranking and performance metrics.
    Integrates annotation records and gold-standard verification results.
    """
    if project_id is not None:
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise ValueError(f"Project with ID {project_id} not found.")

    # Base query for annotations
    query = db.query(Annotation)
    if project_id is not None:
        query = query.filter(Annotation.project_id == project_id)

    annotations = query.all()
    if not annotations:
        return {
            "project_id": project_id,
            "total_annotators": 0,
            "leaderboard": [],
        }

    # Group annotations by annotator
    annotator_map = {a.id: a for a in db.query(Annotator).all()}
    annotator_annotations = defaultdict(list)
    for ann in annotations:
        annotator_annotations[ann.annotator_id].append(ann)

    # Pre-fetch items to evaluate gold standard accuracy per annotator
    item_ids = {a.item_id for a in annotations}
    items_by_id = {item.id: item for item in db.query(Item).filter(Item.id.in_(item_ids)).all()} if item_ids else {}

    raw_leaderboard = []

    for ann_id, ann_list in annotator_annotations.items():
        annotator = annotator_map.get(ann_id)
        name = annotator.username if annotator else f"Annotator_{ann_id}"

        total_count = len(ann_list)
        confidences = [a.confidence for a in ann_list if a.confidence is not None]
        durations = [a.duration_ms for a in ann_list if a.duration_ms is not None]

        avg_conf = round(sum(confidences) / len(confidences), 4) if confidences else None
        avg_dur = round(sum(durations) / len(durations), 2) if durations else None

        # Calculate gold accuracy for this annotator
        gold_total = 0
        gold_correct = 0
        for a in ann_list:
            item = items_by_id.get(a.item_id)
            if item and item.is_gold and item.gold_label:
                gold_total += 1
                if a.label == item.gold_label:
                    gold_correct += 1

        gold_acc = round(gold_correct / gold_total, 4) if gold_total > 0 else None

        # Trust score estimate (combined gold acc + avg confidence or default)
        if gold_acc is not None and avg_conf is not None:
            trust = round(0.6 * gold_acc + 0.4 * avg_conf, 4)
        elif gold_acc is not None:
            trust = gold_acc
        elif avg_conf is not None:
            trust = avg_conf
        else:
            trust = 1.0

        raw_leaderboard.append({
            "annotator_id": ann_id,
            "annotator_name": name,
            "total_annotations": total_count,
            "gold_accuracy": gold_acc,
            "avg_confidence": avg_conf,
            "avg_duration_ms": avg_dur,
            "trust_score": trust,
        })

    # Sort descending by trust_score, then total_annotations
    raw_leaderboard.sort(key=lambda x: (x["trust_score"] or 0.0, x["total_annotations"]), reverse=True)

    # Assign ranks
    leaderboard = []
    for idx, entry in enumerate(raw_leaderboard):
        entry["rank"] = idx + 1
        leaderboard.append(entry)

    return {
        "project_id": project_id,
        "total_annotators": len(leaderboard),
        "leaderboard": leaderboard,
    }


def get_agreement_heatmap(
    db: Session,
    project_id: int,
) -> Dict[str, Any]:
    """
    Build inter-annotator agreement matrix and heatmap data for a given project.
    Integrates with Member 3's Kappa / agreement scoring service.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Project with ID {project_id} not found.")

    # Fetch annotations for project
    annotations = db.query(Annotation).filter(Annotation.project_id == project_id).all()
    annotators_db = db.query(Annotator).all()
    annotator_names = {a.id: a.username for a in annotators_db}

    # Distinct annotators who participated in this project
    project_ann_ids = sorted(list({a.annotator_id for a in annotations}))

    if not project_ann_ids:
        return {
            "project_id": project_id,
            "annotators": [],
            "annotator_ids": [],
            "matrix": [],
            "cells": [],
            "overall_kappa": None,
        }

    # Group annotations by item_id -> annotator_id -> label
    item_annotator_labels = defaultdict(dict)
    for ann in annotations:
        item_annotator_labels[ann.item_id][ann.annotator_id] = ann.label

    # Compute pairwise agreements
    n = len(project_ann_ids)
    matrix = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    cells = []

    for i, id_a in enumerate(project_ann_ids):
        name_a = annotator_names.get(id_a, f"Annotator_{id_a}")
        for j, id_b in enumerate(project_ann_ids):
            name_b = annotator_names.get(id_b, f"Annotator_{id_b}")

            if i == j:
                agreement_rate = 1.0
                overlap_count = sum(1 for item_labels in item_annotator_labels.values() if id_a in item_labels)
            else:
                overlap_items = [
                    item_id for item_id, labels in item_annotator_labels.items()
                    if id_a in labels and id_b in labels
                ]
                overlap_count = len(overlap_items)
                if overlap_count == 0:
                    agreement_rate = 0.0
                else:
                    agreed = sum(
                        1 for item_id in overlap_items
                        if item_annotator_labels[item_id][id_a] == item_annotator_labels[item_id][id_b]
                    )
                    agreement_rate = round(agreed / overlap_count, 4)

            matrix[i][j] = agreement_rate
            cells.append({
                "annotator_a_id": id_a,
                "annotator_a_name": name_a,
                "annotator_b_id": id_b,
                "annotator_b_name": name_b,
                "agreement_rate": agreement_rate,
                "overlap_count": overlap_count,
            })

    # Call overall project kappa
    try:
        kappa_res = compute_fleiss_kappa(db=db, project_id=project_id)
        overall_kappa = kappa_res.get("fleiss_kappa")
    except Exception:
        overall_kappa = None

    annotator_names_list = [annotator_names.get(ann_id, f"Annotator_{ann_id}") for ann_id in project_ann_ids]

    return {
        "project_id": project_id,
        "annotators": annotator_names_list,
        "annotator_ids": project_ann_ids,
        "matrix": matrix,
        "cells": cells,
        "overall_kappa": overall_kappa,
    }
