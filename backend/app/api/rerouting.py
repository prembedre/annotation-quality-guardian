"""
API routes for Automated Task Rerouting and Annotator Reassignment.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.auth_deps import require_role
from app.core.db import get_db
from app.models.user import UserRole
from app.schemas.rerouting import (
    ReroutePendingListResponse,
    RerouteAssignRequest,
    RerouteAssignResponse,
)
from app.services.automation_service import (
    get_project_automation_rules,
    update_automation_rule,
)
from app.services.rerouting_service import (
    get_pending_reroutes,
    assign_reroute_task,
)

router = APIRouter(
    prefix="/rerouting",
    tags=["Task Rerouting"],
)

automation_router = APIRouter(
    prefix="/automation",
    tags=["Automation Dashboard"],
)


class AutomationRuleUpdateRequest(BaseModel):
    active: bool = Field(..., description="Whether this automation policy rule is active")


@automation_router.get(
    "/rules",
    summary="Get persistent automation rules for project",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER))],
)
async def list_automation_rules(
    project_id: int = Query(1, ge=1, description="Project ID"),
    db: Session = Depends(get_db),
):
    """
    Retrieve project automation policy rules, initializing defaults if needed.
    """
    return get_project_automation_rules(db=db, project_id=project_id)


@automation_router.put(
    "/rules/{rule_id}",
    summary="Update active status of an automation rule",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
)
async def set_automation_rule(
    rule_id: str,
    payload: AutomationRuleUpdateRequest,
    project_id: int = Query(1, ge=1, description="Project ID"),
    db: Session = Depends(get_db),
):
    """
    Persist changes to an automation rule toggle.
    """
    try:
        return update_automation_rule(
            db=db,
            project_id=project_id,
            rule_id=rule_id,
            active=payload.active,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )


@router.get(
    "/pending",
    response_model=ReroutePendingListResponse,
    summary="Get pending task rerouting queue",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER))],
)
@automation_router.get(
    "/pending",
    response_model=ReroutePendingListResponse,
    summary="Get pending task automation queue (alias)",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER, UserRole.REVIEWER))],
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
    except Exception:
        return ReroutePendingListResponse(items=[], total=0)


@router.post(
    "/{item_id}/assign",
    response_model=RerouteAssignResponse,
    summary="Assign or reassign task to an annotator",
    dependencies=[Depends(require_role(UserRole.ADMIN, UserRole.PROJECT_MANAGER))],
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
