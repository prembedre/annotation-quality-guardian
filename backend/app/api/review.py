"""
API routes for flagged-item review queue and human resolution.
"""

import math
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.db import get_db
from app.models import Item, Annotation, TrustScore, Annotator
from app.schemas.review import (
    ReviewQueueResponse,
    ReviewItemResponse,
    ReviewAnnotationInfo,
    ReviewResolveRequest,
    ReviewResolveResponse,
)

router = APIRouter()


@router.get("/queue", response_model=ReviewQueueResponse, summary="Retrieve flagged review queue")
async def get_review_queue(
    project_id: Optional[int] = Query(None, description="Filter by project ID"),
    flagged: Optional[bool] = Query(None, description="Filter by flagged status (default: true)"),
    min_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum trust score filter"),
    max_score: Optional[float] = Query(None, ge=0.0, le=1.0, description="Maximum trust score filter"),
    annotator_id: Optional[int] = Query(None, description="Filter items annotated by a specific annotator"),
    search: Optional[str] = Query(None, description="Search term in item external_id or content"),
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    db: Session = Depends(get_db),
):
    """
    Retrieve paginated items needing human review based on trust scores and anomaly flags.
    """
    query = db.query(Item).outerjoin(TrustScore, Item.id == TrustScore.item_id)

    # Filter by project_id
    if project_id is not None:
        query = query.filter(Item.project_id == project_id)

    # Filter by flagged status (if explicitly passed or default to True if trust scores exist)
    if flagged is not None:
        query = query.filter(TrustScore.flagged == flagged)

    # Score filters
    if min_score is not None:
        query = query.filter(TrustScore.score >= min_score)
    if max_score is not None:
        query = query.filter(TrustScore.score <= max_score)

    # Filter by annotator involvement
    if annotator_id is not None:
        query = query.join(Annotation, Item.id == Annotation.item_id).filter(
            Annotation.annotator_id == annotator_id
        )

    # Text search
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Item.external_id.ilike(search_pattern),
                Item.source.ilike(search_pattern),
            )
        )

    # Calculate total count with database query
    total = query.distinct().count()
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    # Paginated query
    offset = (page - 1) * page_size
    items = query.order_by(Item.id.desc()).offset(offset).limit(page_size).all()

    # Pre-cache annotators for name lookup
    annotators_map = {a.id: a.name for a in db.query(Annotator).all()}

    results: List[ReviewItemResponse] = []
    for item in items:
        # Fetch latest trust score
        ts = db.query(TrustScore).filter(TrustScore.item_id == item.id).first()
        trust_score_val = ts.score if ts else None
        trust_breakdown = ts.breakdown if ts else {}
        is_flagged = ts.flagged if ts else False

        # Gather annotations for this item
        annotations_list = []
        for ann in item.annotations:
            ann_name = annotators_map.get(ann.annotator_id, f"Annotator {ann.annotator_id}")
            annotations_list.append(
                ReviewAnnotationInfo(
                    id=ann.id,
                    annotator_id=ann.annotator_id,
                    annotator_name=ann_name,
                    label=ann.label,
                    confidence=ann.confidence,
                    duration_ms=ann.duration_ms,
                    timestamp=ann.created_at,
                )
            )

        results.append(
            ReviewItemResponse(
                item_id=item.id,
                project_id=item.project_id,
                external_id=item.external_id or str(item.id),
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


@router.post("/{item_id}/resolve", response_model=ReviewResolveResponse, summary="Resolve flagged item")
async def resolve_review_item(
    item_id: int,
    payload: ReviewResolveRequest,
    db: Session = Depends(get_db),
):
    """
    Resolve a flagged item by assigning a ground-truth label and clearing review flags.
    """
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item with ID {item_id} not found",
        )

    # Assign gold ground truth label
    item.gold_label = payload.ground_truth_label.strip()
    item.is_gold = True

    # Update associated trust scores to unflag
    trust_scores = db.query(TrustScore).filter(TrustScore.item_id == item.id).all()
    for ts in trust_scores:
        ts.flagged = False
        if "resolution" not in ts.breakdown:
            ts.breakdown = dict(ts.breakdown)
        ts.breakdown["resolved_gold_label"] = payload.ground_truth_label.strip()
        if payload.notes:
            ts.breakdown["resolution_notes"] = payload.notes.strip()

    try:
        db.commit()
        db.refresh(item)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to resolve review item: {str(exc)}",
        )

    return ReviewResolveResponse(
        success=True,
        item_id=item.id,
        status="resolved",
        gold_label=item.gold_label,
        message=f"Item {item.id} resolved with gold label '{item.gold_label}'",
    )
