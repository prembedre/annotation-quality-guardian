"""
API routes for Automated Task Rerouting and Annotator Reassignment.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.rerouting import (
    ReroutePendingListResponse,
    RerouteAssignRequest,
    RerouteAssignResponse,
)
from app.services.rerouting_service import (
    get_pending_reroutes,
    assign_reroute_task,
)

router = APIRouter(
    prefix="/rerouting",
    tags=["Task Rerouting"],
)


@router.get(
    "/pending",
    response_model=ReroutePendingListResponse,
    summary="Get pending task rerouting queue",
)
async def list_pending_reroutes(
    project_id: Optional[int] = Query(None, description="Filter pending reroutes by project ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve items and annotations flagged for automatic or manual task rerouting.
    """
    try:
        return get_pending_reroutes(db=db, project_id=project_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch pending reroutes: {str(exc)}",
        )


@router.post(
    "/{item_id}/assign",
    response_model=RerouteAssignResponse,
    summary="Assign or reassign task to an annotator",
)
async def assign_reroute(
    item_id: int,
    payload: RerouteAssignRequest,
    db: Session = Depends(get_db),
):
    """
    Reassign a flagged item to a designated annotator and update reroute history.
    """
    try:
        return assign_reroute_task(
            db=db,
            item_id=item_id,
            reassigned_annotator_id=payload.reassigned_annotator_id,
            reason=payload.reason,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to assign task: {str(exc)}",
        )
