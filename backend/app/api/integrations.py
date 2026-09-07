"""
API routes for External Database Connectors and Integrations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.external_connector import (
    ConnectorCreateSchema,
    ConnectorResponseSchema,
    ConnectorListResponse,
    ConnectorTestResponseSchema,
    ConnectorSyncRequestSchema,
    ConnectorSyncResponseSchema,
)
from app.services.external_connector_service import (
    create_connector,
    list_connectors,
    get_connector,
    delete_connector,
    test_connection,
    sync_annotations_from_connector,
)

router = APIRouter(
    prefix="/integrations",
    tags=["Integrations & DB Connectors"],
)


@router.post(
    "/connectors",
    response_model=ConnectorResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create read-only external database connector",
)
async def add_connector(
    payload: ConnectorCreateSchema,
    db: Session = Depends(get_db),
):
    """
    Register a new read-only database connector for external annotation platforms.
    """
    try:
        return create_connector(db=db, payload=payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create connector: {str(exc)}",
        )


@router.get(
    "/connectors",
    response_model=List[ConnectorResponseSchema],
    summary="List external database connectors",
)
async def get_connectors(
    status: Optional[str] = Query(None, description="Filter by status ('active', 'disabled')"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all registered database connectors without exposing sensitive credentials.
    """
    try:
        return list_connectors(db=db, status=status)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list connectors: {str(exc)}",
        )


@router.post(
    "/connectors/{connector_id}/test",
    response_model=ConnectorTestResponseSchema,
    summary="Test connectivity of an external database connector",
)
async def test_connector_endpoint(
    connector_id: int,
    db: Session = Depends(get_db),
):
    """
    Perform a read-only latency and connection verification test against the target database.
    """
    try:
        return test_connection(db=db, connector_id=connector_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test error: {str(exc)}",
        )


@router.delete(
    "/connectors/{connector_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete an external database connector",
)
async def remove_connector(
    connector_id: int,
    db: Session = Depends(get_db),
):
    """
    Remove a database connector configuration.
    """
    success = delete_connector(db=db, connector_id=connector_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector with ID {connector_id} not found",
        )
    return {"success": True, "message": f"Connector {connector_id} deleted successfully."}


@router.post(
    "/connectors/{connector_id}/sync",
    response_model=ConnectorSyncResponseSchema,
    summary="Sync annotations from external database",
)
async def sync_connector_endpoint(
    connector_id: int,
    payload: ConnectorSyncRequestSchema,
    db: Session = Depends(get_db),
):
    """
    Query external database (read-only), normalize records, feed into the AQG ingestion pipeline,
    and recalculate quality scores.
    """
    try:
        return sync_annotations_from_connector(
            db=db,
            connector_id=connector_id,
            project_id=payload.project_id,
            table_name=payload.table_name,
            custom_query=payload.custom_query,
            limit=payload.limit or 1000,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync annotations from connector: {str(exc)}",
        )
