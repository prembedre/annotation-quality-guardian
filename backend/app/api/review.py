"""
API routes for flagged-item review queue and human resolution.
"""

import math
from collections import Counter
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import Item, Annotation, TrustScore, Annotator
from app.schemas.review import (
    ReviewQueueResponse,
    ReviewItemResponse,
    ReviewAnnotationInfo,
    ReviewResolveRequest,
    ReviewResolveResponse,
)
from app.services.trust_score_service import compute_and_save_item_trust_score



router = APIRouter()


@router.get(
    "/queue",
    response_model=ReviewQueueResponse,
    summary="Retrieve flagged review queue",
)
async def get_review_queue(
    project_id: Optional[int] = Query(
        None,
        description="Filter by project ID",
    ),
    flagged: Optional[bool] = Query(
        None,
        description="Filter by flagged status",
    ),
    min_score: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Minimum trust score filter",
    ),
    max_score: Optional[float] = Query(
        None,
        ge=0.0,
        le=1.0,
        description="Maximum trust score filter",
    ),
    annotator_id: Optional[int] = Query(
        None,
        description="Filter items annotated by a specific annotator",
    ),
    search: Optional[str] = Query(
        None,
        description="Search term in item external ID",
    ),
    page: int = Query(
        1,
        ge=1,
        description="Page number (1-indexed)",
    ),
    page_size: int = Query(
        20,
        ge=1,
        le=100,
        description="Number of items per page",
    ),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated items needing human review
    based on trust scores and anomaly flags.
    """

    query = db.query(Item).outerjoin(
        TrustScore,
        Item.id == TrustScore.item_id,
    )

    # ---------------------------------------------------------
    # Project filter
    # ---------------------------------------------------------

    if project_id is not None:
        query = query.filter(
            Item.project_id == project_id
        )

    # ---------------------------------------------------------
    # Flagged filter
    # ---------------------------------------------------------

    if flagged is not None:
        query = query.filter(
            TrustScore.flagged == flagged
        )

    # ---------------------------------------------------------
    # Trust score filters
    # ---------------------------------------------------------

    if min_score is not None:
        query = query.filter(
            TrustScore.final_score >= min_score
        )

    if max_score is not None:
        query = query.filter(
            TrustScore.final_score <= max_score
        )

    # ---------------------------------------------------------
    # Annotator filter
    # ---------------------------------------------------------

    if annotator_id is not None:
        query = query.join(
            Annotation,
            Item.id == Annotation.item_id,
        ).filter(
            Annotation.annotator_id == annotator_id
        )

    # ---------------------------------------------------------
    # Search filter
    # ---------------------------------------------------------

    if search:
        search_pattern = f"%{search.strip()}%"

        query = query.filter(
            Item.external_id.ilike(search_pattern)
        )

    # ---------------------------------------------------------
    # Pagination
    # ---------------------------------------------------------

    total = query.distinct().count()

    total_pages = (
        math.ceil(total / page_size)
        if total > 0
        else 0
    )

    offset = (page - 1) * page_size

    items = (
        query
        .order_by(Item.id.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    # ---------------------------------------------------------
    # Annotator lookup
    # ---------------------------------------------------------

    annotators_map = {
        annotator.id: annotator.username
        for annotator in db.query(Annotator).all()
    }

    # ---------------------------------------------------------
    # Build response
    # ---------------------------------------------------------

    results: List[ReviewItemResponse] = []

    for item in items:

        # Get trust score
        trust_score = (
            db.query(TrustScore)
            .filter(
                TrustScore.item_id == item.id
            )
            .order_by(
                TrustScore.id.desc()
            )
            .first()
        )

        trust_score_val = (
            float(trust_score.final_score)
            if trust_score
            and trust_score.final_score is not None
            else None
        )

        trust_breakdown = (
            trust_score.breakdown
            if trust_score
            and trust_score.breakdown
            else {}
        )

        is_flagged = (
            trust_score.flagged
            if trust_score
            else False
        )

        # -----------------------------------------------------
        # Gather annotations
        # -----------------------------------------------------

        annotations_list = []

        for annotation in item.annotations:

            annotator_name = annotators_map.get(
                annotation.annotator_id,
                f"Annotator {annotation.annotator_id}",
            )

            annotations_list.append(
                ReviewAnnotationInfo(
                    id=annotation.id,
                    annotator_id=annotation.annotator_id,
                    annotator_name=annotator_name,
                    label=annotation.label,
                    confidence=annotation.confidence,
                    duration_ms=annotation.duration_ms,
                    timestamp=annotation.created_at,
                )
            )

        # -----------------------------------------------------
        # Create review item response
        # -----------------------------------------------------

        results.append(
            ReviewItemResponse(
                item_id=item.id,
                project_id=item.project_id,
                external_id=(
                    item.external_id
                    or str(item.id)
                ),
                content=item.content or {},
                is_gold=item.is_gold,
                gold_label=item.gold_label,
                annotations=annotations_list,
                trust_score=trust_score_val,
                trust_score_breakdown=trust_breakdown,
                flagged=is_flagged,
                created_at=item.created_at,
            )
        )

    return ReviewQueueResponse(
        items=results,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )


@router.post(
    "/{item_id}/resolve",
    response_model=ReviewResolveResponse,
    summary="Resolve flagged item",
)
async def resolve_review_item(
    item_id: int,
    payload: ReviewResolveRequest,
    db: Session = Depends(get_db),
):
    """
    Resolve a flagged item by reviewer action (confirm, correct, or escalate),
    assigning a ground-truth label, updating flags, and recalculating Trust Score.
    """
    item = (
        db.query(Item)
        .filter(Item.id == item_id)
        .first()
    )

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item with ID {item_id} not found",
        )

    # Determine action
    raw_action = payload.action.lower().strip() if payload.action else None
    if not raw_action:
        if payload.ground_truth_label or payload.correct_label:
            action = "correct"
        else:
            action = "confirm"
    else:
        action = raw_action

    if action not in {"confirm", "correct", "escalate"}:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action '{action}'. Allowed actions are 'confirm', 'correct', 'escalate'.",
        )

    # 1. Action: CORRECT
    if action == "correct":
        new_label = payload.correct_label or payload.ground_truth_label
        if not new_label or not new_label.strip():
            raise HTTPException(
                status_code=400,
                detail="A correct_label or ground_truth_label is required for 'correct' action.",
            )
        item.gold_label = new_label.strip()
        item.is_gold = True

    # 2. Action: CONFIRM
    elif action == "confirm":
        new_label = payload.correct_label or payload.ground_truth_label
        if new_label and new_label.strip():
            item.gold_label = new_label.strip()
        elif item.gold_label:
            pass
        elif item.annotations:
            counts = Counter(a.label for a in item.annotations)
            item.gold_label = counts.most_common(1)[0][0]
        else:
            raise HTTPException(
                status_code=400,
                detail="Cannot confirm item without existing label or annotations.",
            )
        item.is_gold = True

    # 3. Action: ESCALATE
    elif action == "escalate":
        pass

    try:
        db.commit()
        db.refresh(item)

        # Recalculate Trust Score for the item
        updated_ts = compute_and_save_item_trust_score(
            db=db,
            project_id=item.project_id,
            item_id=item.id,
        )

        # Update breakdown with resolution metadata
        if updated_ts:
            breakdown = dict(updated_ts.breakdown or {})
            breakdown["resolution_action"] = action
            if action in {"confirm", "correct"}:
                breakdown["resolved_gold_label"] = item.gold_label
                updated_ts.flagged = False
            elif action == "escalate":
                breakdown["escalated"] = True
                updated_ts.flagged = True

            if payload.notes:
                breakdown["resolution_notes"] = payload.notes.strip()

            updated_ts.breakdown = breakdown
            db.commit()
            db.refresh(updated_ts)

        final_score = float(updated_ts.final_score) if updated_ts and updated_ts.final_score is not None else None
        is_flagged = updated_ts.flagged if updated_ts else False

        status_str = "escalated" if action == "escalate" else "resolved"
        message_str = f"Item {item.id} {action}ed successfully"
        if item.gold_label and action in {"confirm", "correct"}:
            message_str += f" with gold label '{item.gold_label}'"

        return ReviewResolveResponse(
            success=True,
            item_id=item.id,
            status=status_str,
            action=action,
            gold_label=item.gold_label,
            trust_score=final_score,
            flagged=is_flagged,
            message=message_str,
        )

    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve review item: {str(exc)}",
        )

