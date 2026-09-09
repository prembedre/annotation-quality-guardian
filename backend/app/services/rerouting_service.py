"""
Automated Task Rerouting Service.

Handles task reassignments, pending reroute queries, and history tracking.
Also respects the Phase 4 project-level automation setting.
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

from app.services.project_settings_service import (
    get_project_settings,
)


def get_pending_reroutes(
    db: Session,
    project_id: Optional[int] = None,
) -> ReroutePendingListResponse:
    """
    Retrieve all pending reroute tasks for review or reassignment.

    Includes:
    1. Explicit PENDING RerouteHistory records.
    2. Flagged TrustScore items that do not have any resolved reroute
       history.

    When Phase 4 automation is disabled for the project, no pending
    reroute candidates are returned.

    Items with an ASSIGNED or otherwise resolved reroute are excluded
    from the fallback flagged-item queue.
    """

    # ---------------------------------------------------------------
    # Phase 4 automation master switch
    # ---------------------------------------------------------------

    settings_project_id = project_id or 1

    project_settings = get_project_settings(
        db=db,
        project_id=settings_project_id,
    )

    automation_enabled = project_settings.get(
        "automation_enabled",
        True,
    )

    if not automation_enabled:
        return ReroutePendingListResponse(
            total=0,
            items=[],
        )

    # ---------------------------------------------------------------
    # 1. Fetch explicit pending RerouteHistory records
    # ---------------------------------------------------------------

    query = db.query(RerouteHistory).filter(
        RerouteHistory.reroute_status == "PENDING"
    )

    if project_id:
        query = query.filter(
            RerouteHistory.project_id == project_id
        )

    pending_records = query.order_by(
        RerouteHistory.created_at.desc()
    ).all()

    # ---------------------------------------------------------------
    # Annotator lookup
    # ---------------------------------------------------------------

    annotators_map = {
        annotator.id: annotator.username
        for annotator in db.query(Annotator).all()
    }

    results: List[RerouteItemPendingResponse] = []
    seen_item_ids = set()

    # ---------------------------------------------------------------
    # Convert explicit pending reroutes
    # ---------------------------------------------------------------

    for record in pending_records:
        item = record.item

        if not item:
            continue

        original_name = (
            annotators_map.get(
                record.original_annotator_id
            )
            if record.original_annotator_id
            else None
        )

        trust_score_value = (
            float(record.trust_score_snapshot)
            if record.trust_score_snapshot is not None
            else None
        )

        results.append(
            RerouteItemPendingResponse(
                reroute_id=record.id,
                item_id=item.id,
                project_id=record.project_id,
                external_id=item.external_id or str(item.id),
                original_annotator_id=(
                    record.original_annotator_id
                ),
                original_annotator_name=original_name,
                reason=(
                    record.reason
                    or "Flagged for task rerouting"
                ),
                trust_score=trust_score_value,
                flagged=True,
                reroute_status=record.reroute_status,
                content=item.content or {},
                created_at=record.created_at,
            )
        )

        seen_item_ids.add(item.id)

    # ---------------------------------------------------------------
    # 2. Check flagged TrustScores that do not have a resolved
    # reroute record.
    # ---------------------------------------------------------------

    flagged_ts_query = db.query(TrustScore).filter(
        TrustScore.flagged == True
    )

    if project_id:
        flagged_ts_query = flagged_ts_query.filter(
            TrustScore.project_id == project_id
        )

    flagged_ts_list = flagged_ts_query.all()

    for trust_score in flagged_ts_list:

        if trust_score.item_id in seen_item_ids:
            continue

        # IMPORTANT:
        #
        # A flagged item must not appear as pending if it already
        # has a resolved reroute such as ASSIGNED.
        resolved_reroute = (
            db.query(RerouteHistory)
            .filter(
                RerouteHistory.item_id
                == trust_score.item_id,
                RerouteHistory.reroute_status
                != "PENDING",
            )
            .order_by(
                RerouteHistory.id.desc()
            )
            .first()
        )

        if resolved_reroute:
            continue

        # -----------------------------------------------------------
        # Find the item
        # -----------------------------------------------------------

        item = (
            db.query(Item)
            .filter(
                Item.id == trust_score.item_id
            )
            .first()
        )

        if not item:
            continue

        # -----------------------------------------------------------
        # Find original annotator from annotations
        # -----------------------------------------------------------

        annotation = (
            db.query(Annotation)
            .filter(
                Annotation.item_id == item.id
            )
            .first()
        )

        original_annotator_id = (
            annotation.annotator_id
            if annotation
            else None
        )

        original_annotator_name = (
            annotators_map.get(
                original_annotator_id
            )
            if original_annotator_id
            else None
        )

        score_value = (
            float(trust_score.final_score)
            if trust_score.final_score is not None
            else None
        )

        # -----------------------------------------------------------
        # Add flagged item as pending reroute
        # -----------------------------------------------------------

        results.append(
            RerouteItemPendingResponse(
                reroute_id=None,
                item_id=item.id,
                project_id=item.project_id,
                external_id=(
                    item.external_id
                    or str(item.id)
                ),
                original_annotator_id=(
                    original_annotator_id
                ),
                original_annotator_name=(
                    original_annotator_name
                ),
                reason=(
                    f"Low trust score ({score_value}) - "
                    "flagged for reassignment"
                ),
                trust_score=score_value,
                flagged=True,
                reroute_status="PENDING",
                content=item.content or {},
                created_at=item.created_at,
            )
        )

        seen_item_ids.add(item.id)

    # ---------------------------------------------------------------
    # Return pending reroutes
    # ---------------------------------------------------------------

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
    """
    Create a new pending reroute history record.

    This function respects the project automation setting.
    """

    project_settings = get_project_settings(
        db=db,
        project_id=project_id,
    )

    if not project_settings.get(
        "automation_enabled",
        True,
    ):
        raise ValueError(
            "Phase 4 automation is disabled for this project."
        )

    reroute = RerouteHistory(
        item_id=item_id,
        project_id=project_id,
        original_annotator_id=original_annotator_id,
        reason=(
            reason
            or "Task rerouting triggered"
        ),
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
    Assign or reassign an item to a new annotator,
    updating reroute status to ASSIGNED.

    Manual assignment remains available even when automatic
    rerouting is disabled.
    """

    # ---------------------------------------------------------------
    # Find item
    # ---------------------------------------------------------------

    item = (
        db.query(Item)
        .filter(
            Item.id == item_id
        )
        .first()
    )

    if not item:
        raise ValueError(
            f"Item with ID {item_id} not found."
        )

    # ---------------------------------------------------------------
    # Find reassigned annotator
    # ---------------------------------------------------------------

    reassigned_annotator = (
        db.query(Annotator)
        .filter(
            Annotator.id
            == reassigned_annotator_id
        )
        .first()
    )

    if not reassigned_annotator:
        raise ValueError(
            "Annotator with ID "
            f"{reassigned_annotator_id} not found."
        )

    # ---------------------------------------------------------------
    # Check for an existing pending reroute
    # ---------------------------------------------------------------

    reroute = (
        db.query(RerouteHistory)
        .filter(
            RerouteHistory.item_id == item_id,
            RerouteHistory.reroute_status == "PENDING",
        )
        .order_by(
            RerouteHistory.id.desc()
        )
        .first()
    )

    if not reroute:

        # -----------------------------------------------------------
        # Find original annotator
        # -----------------------------------------------------------

        annotation = (
            db.query(Annotation)
            .filter(
                Annotation.item_id == item_id
            )
            .first()
        )

        original_annotator_id = (
            annotation.annotator_id
            if annotation
            else None
        )

        # -----------------------------------------------------------
        # Find latest trust score
        # -----------------------------------------------------------

        trust_score = (
            db.query(TrustScore)
            .filter(
                TrustScore.item_id == item_id
            )
            .order_by(
                TrustScore.id.desc()
            )
            .first()
        )

        trust_score_value = (
            float(trust_score.final_score)
            if (
                trust_score
                and trust_score.final_score is not None
            )
            else None
        )

        # -----------------------------------------------------------
        # Create assigned reroute history
        # -----------------------------------------------------------

        reroute = RerouteHistory(
            item_id=item_id,
            project_id=item.project_id,
            original_annotator_id=(
                original_annotator_id
            ),
            reassigned_annotator_id=(
                reassigned_annotator_id
            ),
            reason=(
                reason
                or "Task reassigned by supervisor"
            ),
            trust_score_snapshot=(
                trust_score_value
            ),
            reroute_status="ASSIGNED",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        db.add(reroute)

    else:

        # -----------------------------------------------------------
        # Resolve existing pending reroute
        # -----------------------------------------------------------

        reroute.reassigned_annotator_id = (
            reassigned_annotator_id
        )

        reroute.reroute_status = "ASSIGNED"

        if reason:
            reroute.reason = reason

        reroute.updated_at = datetime.utcnow()

    # ---------------------------------------------------------------
    # Save changes
    # ---------------------------------------------------------------

    db.commit()
    db.refresh(reroute)

    return RerouteAssignResponse(
        success=True,
        reroute_id=reroute.id,
        item_id=item.id,
        project_id=item.project_id,
        original_annotator_id=(
            reroute.original_annotator_id
        ),
        reassigned_annotator_id=(
            reassigned_annotator_id
        ),
        reroute_status="ASSIGNED",
        message=(
            f"Item {item.id} successfully rerouted "
            "and assigned to Annotator "
            f"{reassigned_annotator.username}."
        ),
        assigned_at=(
            reroute.updated_at
            or reroute.created_at
        ),
    )