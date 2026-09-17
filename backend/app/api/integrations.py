"""
API routes for External Database Connectors and Integrations.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.external_connector import (
    ConnectorCreateSchema,
    ConnectorUpdateSchema,
    ConnectorResponseSchema,
    ConnectorListResponse,
    ConnectorTestResponseSchema,
    ConnectorSyncRequestSchema,
    ConnectorSyncResponseSchema,
)
from app.services.external_connector_service import (
    create_connector,
    update_connector,
    list_connectors,
    get_connector,
    delete_connector,
    test_connection,
    _do_live_test,
    _decrypt_secret,
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
    summary="Create external database connector (with live connection test)",
)
async def add_connector(
    payload: ConnectorCreateSchema,
    db: Session = Depends(get_db),
):
    """
    Register a new read-only database connector for external annotation platforms.

    Performs a live connection test before saving. If the connection fails,
    returns HTTP 422 with a specific error_type and message so the frontend
    can display a meaningful error without losing form state.
    """
    # ── Step 1: Live connection test before saving ──────────────────
    if payload.database_type.lower() != "sqlite":
        test_result = _do_live_test(
            database_type=payload.database_type,
            database_name=payload.database_name,
            host=payload.host,
            port=payload.port,
            username=payload.username,
            raw_password=payload.password,
        )

        if not test_result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": test_result.message,
                    "error_type": test_result.error_type,
                },
            )

    # ── Step 2: Save connector ──────────────────────────────────────
    try:
        connector = create_connector(db=db, payload=payload)
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

    # ── Step 3: Stamp last_tested_at since test already passed ──────
    from datetime import datetime
    connector.last_tested_at = datetime.utcnow()
    connector.status = "active"
    db.commit()
    db.refresh(connector)

    return connector


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


@router.put(
    "/connectors/{connector_id}",
    response_model=ConnectorResponseSchema,
    summary="Update an external database connector",
)
async def edit_connector(
    connector_id: int,
    payload: ConnectorUpdateSchema,
    db: Session = Depends(get_db),
):
    """
    Update configuration for an existing database connector.
    If a new password is provided, it will be re-encrypted.
    Triggers a fresh connection test if host/port/credentials changed.
    """
    existing = get_connector(db, connector_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector with ID {connector_id} not found.",
        )

    # If connection params changed, run a live test first
    credentials_changed = any([
        payload.host is not None,
        payload.port is not None,
        payload.database_name is not None,
        payload.username is not None,
        payload.password is not None,
    ])

    if credentials_changed and existing.database_type.lower() != "sqlite":
        # Resolve what the final values would be after the update
        test_host = payload.host if payload.host is not None else existing.host
        test_port = payload.port if payload.port is not None else existing.port
        test_db_name = payload.database_name if payload.database_name is not None else existing.database_name
        test_user = payload.username if payload.username is not None else existing.username
        test_pass = payload.password if (payload.password is not None and payload.password.strip()) else _decrypt_secret(existing.password_encrypted)

        test_result = _do_live_test(
            database_type=existing.database_type,
            database_name=test_db_name,
            host=test_host,
            port=test_port,
            username=test_user,
            raw_password=test_pass,
        )

        if not test_result.success:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "message": test_result.message,
                    "error_type": test_result.error_type,
                },
            )

    try:
        connector = update_connector(db=db, connector_id=connector_id, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if not connector:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector with ID {connector_id} not found.",
        )

    return connector


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
    Returns specific error_type on failure: connection_refused, auth_failed, timeout, unknown_host, etc.
    Always returns HTTP 200 — success/failure is in the response body.
    """
    existing = get_connector(db, connector_id)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Connector ID {connector_id} not found.",
        )
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
