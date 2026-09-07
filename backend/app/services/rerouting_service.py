"""
Automated Task Rerouting Service.
Handles task reassignments, pending reroute queries, and history tracking.
"""

from datetime import datetime
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.models.reroute_history import RerouteHistory
from app.models.item import Item
from app.models.annotator import Annotator
from app.models.trust_score import TrustScore
from app.models.annotation import Annotation
from app.schemas.rerouting import (
    RerouteItemPendingResponse,
    ReroutePendingListResponse,
    RerouteAssignResponse,
)


def get_pending_reroutes(
    db: Session,
    project_id: Optional[int] = None,
) -> ReroutePendingListResponse:
    """
    Retrieve all pending reroute tasks for review or reassignment.
    Includes both explicit pending RerouteHistory records and flagged items.
    """
    # 1. Fetch pending RerouteHistory records
    query = db.query(RerouteHistory).filter(RerouteHistory.reroute_status == "PENDING")
    if project_id:
        query = query.filter(RerouteHistory.project_id == project_id)

    pending_records = query.order_by(RerouteHistory.created_at.desc()).all()
    annotators_map = {a.id: a.username for a in db.query(Annotator).all()}

    results: List[RerouteItemPendingResponse] = []
    seen_item_ids = set()

    for rec in pending_records:
        item = rec.item
        if not item:
            continue

        orig_name = annotators_map.get(rec.original_annotator_id) if rec.original_annotator_id else None
        ts_val = float(rec.trust_score_snapshot) if rec.trust_score_snapshot is not None else None

        results.append(
            RerouteItemPendingResponse(
                reroute_id=rec.id,
                item_id=item.id,
                project_id=rec.project_id,
                external_id=item.external_id or str(item.id),
                original_annotator_id=rec.original_annotator_id,
                original_annotator_name=orig_name,
                reason=rec.reason or "Flagged for task rerouting",
                trust_score=ts_val,
                flagged=True,
                reroute_status=rec.reroute_status,
                content=item.content or {},
                created_at=rec.created_at,
            )
        )
        seen_item_ids.add(item.id)

    # 2. Also check flagged items from TrustScores that do not yet have a resolved reroute record
    flagged_ts_query = (
        db.query(TrustScore)
        .filter(TrustScore.flagged == True)
    )
    if project_id:
        flagged_ts_query = flagged_ts_query.filter(TrustScore.project_id == project_id)

    flagged_ts_list = flagged_ts_query.all()

    for ts in flagged_ts_list:
        if ts.item_id in seen_item_ids:
            continue

        item = db.query(Item).filter(Item.id == ts.item_id).first()
        if not item:
            continue

        # Find original annotator from item annotations
        ann = db.query(Annotation).filter(Annotation.item_id == item.id).first()
        orig_ann_id = ann.annotator_id if ann else None
        orig_name = annotators_map.get(orig_ann_id) if orig_ann_id else None

        score_val = float(ts.final_score) if ts.final_score is not None else None

        results.append(
            RerouteItemPendingResponse(
                reroute_id=None,
                item_id=item.id,
                project_id=item.project_id,
                external_id=item.external_id or str(item.id),
                original_annotator_id=orig_ann_id,
                original_annotator_name=orig_name,
                reason=f"Low trust score ({score_val}) - flagged for reassignment",
                trust_score=score_val,
                flagged=True,
                reroute_status="PENDING",
                content=item.content or {},
                created_at=item.created_at,
            )
        )
        seen_item_ids.add(item.id)

    return ReroutePendingListResponse(
        total=len(results),
        items=results,
    )


def create_reroute_task(
    db: Session,
    item_id: int,
    project_id: int,
    original_annotator_id: Optional[int] = None,
    reason: Optional[str] = None,
    trust_score_snapshot: Optional[float] = None,
) -> RerouteHistory:
    """Create a new pending reroute history record."""
    reroute = RerouteHistory(
        item_id=item_id,
        project_id=project_id,
        original_annotator_id=original_annotator_id,
        reason=reason or "Task rerouting triggered",
        trust_score_snapshot=trust_score_snapshot,
        reroute_status="PENDING",
        created_at=datetime.utcnow(),
    )
    db.add(reroute)
    db.commit()
    db.refresh(reroute)
    return reroute


def assign_reroute_task(
    db: Session,
    item_id: int,
    reassigned_annotator_id: int,
    reason: Optional[str] = None,
) -> RerouteAssignResponse:
    """
    Assign or reassign an item to a new annotator, updating reroute status to 'ASSIGNED'.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise ValueError(f"Item with ID {item_id} not found.")

    reassigned_annotator = db.query(Annotator).filter(Annotator.id == reassigned_annotator_id).first()
    if not reassigned_annotator:
        raise ValueError(f"Annotator with ID {reassigned_annotator_id} not found.")

    # Check if a pending reroute record exists
    reroute = (
        db.query(RerouteHistory)
        .filter(
            RerouteHistory.item_id == item_id,
            RerouteHistory.reroute_status == "PENDING",
        )
        .order_by(RerouteHistory.id.desc())
        .first()
    )

    if not reroute:
        # Check original annotator
        ann = db.query(Annotation).filter(Annotation.item_id == item_id).first()
        orig_ann_id = ann.annotator_id if ann else None

        ts = db.query(TrustScore).filter(TrustScore.item_id == item_id).order_by(TrustScore.id.desc()).first()
        ts_val = float(ts.final_score) if ts and ts.final_score is not None else None

        reroute = RerouteHistory(
            item_id=item_id,
            project_id=item.project_id,
            original_annotator_id=orig_ann_id,
            reassigned_annotator_id=reassigned_annotator_id,
            reason=reason or "Task reassigned by supervisor",
            trust_score_snapshot=ts_val,
            reroute_status="ASSIGNED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        db.add(reroute)
    else:
        reroute.reassigned_annotator_id = reassigned_annotator_id
        reroute.reroute_status = "ASSIGNED"
        if reason:
            reroute.reason = reason
        reroute.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(reroute)

    return RerouteAssignResponse(
        success=True,
        reroute_id=reroute.id,
        item_id=item.id,
        project_id=item.project_id,
        original_annotator_id=reroute.original_annotator_id,
        reassigned_annotator_id=reassigned_annotator_id,
        reroute_status="ASSIGNED",
        message=f"Item {item.id} successfully rerouted and assigned to Annotator {reassigned_annotator.username}.",
        assigned_at=reroute.updated_at or reroute.created_at,
    )
