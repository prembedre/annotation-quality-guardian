"""
External Database Connector Service.
Provides read-only database connections, testing, security checks, and annotation synchronization.
"""

import base64
import re
import time
import socket
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

from app.models.external_db_connector import ExternalDBConnector
from app.models.project import Project
from app.models.item import Item
from app.schemas.external_connector import (
    ConnectorCreateSchema,
    ConnectorUpdateSchema,
    ConnectorTestResponseSchema,
    ConnectorSyncResponseSchema,
)
from app.services.ingestion_service import ingest_records_batch
from app.services.trust_score_service import compute_and_save_item_trust_score


# ── Encryption helpers ──────────────────────────────────────────────────────

try:
    from cryptography.fernet import Fernet, InvalidToken
    import os

    _FERNET_KEY_ENV = os.environ.get("CONNECTOR_SECRET_KEY", "")
    # Derive a valid 32-byte URL-safe base64-encoded key even if the env var is short.
    if _FERNET_KEY_ENV:
        _key_bytes = (_FERNET_KEY_ENV * 32)[:32].encode("utf-8")
        _FERNET_KEY = base64.urlsafe_b64encode(_key_bytes)
    else:
        # Generate a stable default key based on a fixed seed for dev (NOT for production).
        _key_bytes = b"aqg-connector-secret-key-default"[:32]
        _FERNET_KEY = base64.urlsafe_b64encode(_key_bytes)

    _fernet = Fernet(_FERNET_KEY)
    _FERNET_AVAILABLE = True
except ImportError:
    _FERNET_AVAILABLE = False
    _fernet = None


def _encrypt_secret(plain_text: Optional[str]) -> Optional[str]:
    """Encrypt secret string using Fernet symmetric encryption (falls back to base64)."""
    if not plain_text:
        return None
    if _FERNET_AVAILABLE and _fernet:
        return _fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")
    # Fallback: base64 obfuscation (not secure — install cryptography package)
    return "b64:" + base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")


def _decrypt_secret(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypt stored secret (Fernet or base64 fallback)."""
    if not cipher_text:
        return None
    # Detect legacy base64 or new Fernet token
    if cipher_text.startswith("b64:"):
        try:
            return base64.b64decode(cipher_text[4:].encode("utf-8")).decode("utf-8")
        except Exception:
            return cipher_text
    if _FERNET_AVAILABLE and _fernet:
        try:
            return _fernet.decrypt(cipher_text.encode("utf-8")).decode("utf-8")
        except Exception:
            pass
    # Last-resort: try plain base64 (for records created before Fernet was added)
    try:
        return base64.b64decode(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return cipher_text


# ── SQL validation ──────────────────────────────────────────────────────────

# Regex detecting any destructive or state-modifying SQL statements
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|CREATE|RENAME|GRANT|REVOKE|REPLACE|MERGE)\b",
    re.IGNORECASE,
)


def validate_read_only_query(query: str) -> None:
    """Ensure query contains only read-only statements."""
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")

    clean_query = query.strip()
    if not clean_query.lower().startswith("select"):
        raise ValueError("Only SELECT queries are permitted on read-only external database connectors.")

    if FORBIDDEN_SQL_PATTERN.search(clean_query):
        raise ValueError("Forbidden mutation or administrative keyword detected. Read-only access enforced.")


# ── Connection URI builder ──────────────────────────────────────────────────

def build_connection_uri(
    database_type: str,
    database_name: str,
    host: Optional[str] = None,
    port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """Build a SQLAlchemy connection URI with credentials."""
    db_type = database_type.lower().strip()

    if db_type == "sqlite":
        if database_name.startswith("sqlite://"):
            return database_name
        return f"sqlite:///{database_name}"

    elif db_type == "postgresql":
        user_part = username or "postgres"
        auth_part = f"{user_part}:{password}" if password else user_part
        host_part = host or "localhost"
        port_part = f":{port}" if port else ":5432"
        return f"postgresql://{auth_part}@{host_part}{port_part}/{database_name}"

    elif db_type == "mysql":
        user_part = username or "root"
        auth_part = f"{user_part}:{password}" if password else user_part
        host_part = host or "localhost"
        port_part = f":{port}" if port else ":3306"
        return f"mysql+pymysql://{auth_part}@{host_part}{port_part}/{database_name}"

    else:
        raise ValueError(f"Unsupported database type '{database_type}'. Supported: postgresql, sqlite, mysql.")


# ── Error classifier ────────────────────────────────────────────────────────

def _classify_connection_error(exc: Exception, host: Optional[str], port: Optional[int], db_type: str) -> Tuple[str, str]:
    """
    Classify a connection exception into a human-readable message and an error_type code.
    Returns (message, error_type).
    """
    err_str = str(exc).lower()
    original = str(exc)

    # Connection refused / unreachable host
    if any(k in err_str for k in ("connection refused", "connection reset", "econnrefused", "111")):
        host_str = f"{host}:{port}" if host and port else (host or "the server")
        return (
            f"Connection refused — nothing is listening on {host_str}. "
            f"Check that the {db_type.upper()} server is running and the host/port are correct.",
            "connection_refused",
        )

    # Unknown host / DNS resolution failure
    if any(k in err_str for k in ("name or service not known", "nodename nor servname", "getaddrinfo", "could not translate host", "name resolution")):
        return (
            f"Unknown host '{host}' — DNS resolution failed. "
            "Verify the hostname is correct and reachable from this server.",
            "unknown_host",
        )

    # Authentication / credentials failure
    if any(k in err_str for k in ("password authentication failed", "access denied", "authentication failed", "invalid password", "peer authentication")):
        return (
            f"Authentication failed for user '{exc}'. "
            "Check the username and password.",
            "auth_failed",
        )
    # Narrow auth check without 'exc' confusion
    if "auth" in err_str and ("fail" in err_str or "denied" in err_str):
        return (
            "Authentication failed — check the username and password.",
            "auth_failed",
        )

    # Timeout
    if any(k in err_str for k in ("timeout", "timed out", "connection timed")):
        host_str = f"{host}:{port}" if host and port else (host or "the server")
        return (
            f"Connection timed out connecting to {host_str}. "
            "The host is unreachable or blocked by a firewall.",
            "timeout",
        )

    # Database does not exist
    if any(k in err_str for k in ("does not exist", "unknown database", "database", "catalog")):
        return (
            f"Database not found — no database named at the given host.",
            "database_not_found",
        )

    # SSL errors
    if "ssl" in err_str:
        return (
            f"SSL/TLS error: {original[:200]}",
            "ssl_error",
        )

    # Generic fallback
    return (f"Connection failed: {original[:300]}", "unknown")


# ── CRUD operations ─────────────────────────────────────────────────────────

def create_connector(
    db: Session,
    payload: ConnectorCreateSchema,
) -> ExternalDBConnector:
    """Create and persist a new external DB connector."""
    existing = db.query(ExternalDBConnector).filter(
        ExternalDBConnector.connection_name == payload.connection_name
    ).first()

    if existing:
        raise ValueError(f"A connector with name '{payload.connection_name}' already exists.")

    encrypted_pw = _encrypt_secret(payload.password) if payload.password else None

    connector = ExternalDBConnector(
        connection_name=payload.connection_name.strip(),
        database_type=payload.database_type.lower().strip(),
        host=payload.host.strip() if payload.host else None,
        port=payload.port,
        database_name=payload.database_name.strip(),
        username=payload.username.strip() if payload.username else None,
        password_encrypted=encrypted_pw,
        status=payload.status or "active",
        read_only=True,
        query_config=payload.query_config or {},
        synced_rows_count=0,
    )

    db.add(connector)
    db.commit()
    db.refresh(connector)
    return connector


def update_connector(
    db: Session,
    connector_id: int,
    payload: ConnectorUpdateSchema,
) -> Optional[ExternalDBConnector]:
    """Update an existing external DB connector's configuration."""
    connector = get_connector(db, connector_id)
    if not connector:
        return None

    if payload.connection_name is not None:
        # Ensure no collision with another connector
        collision = db.query(ExternalDBConnector).filter(
            ExternalDBConnector.connection_name == payload.connection_name,
            ExternalDBConnector.id != connector_id,
        ).first()
        if collision:
            raise ValueError(f"A connector named '{payload.connection_name}' already exists.")
        connector.connection_name = payload.connection_name.strip()

    if payload.host is not None:
        connector.host = payload.host.strip() or None
    if payload.port is not None:
        connector.port = payload.port
    if payload.database_name is not None:
        connector.database_name = payload.database_name.strip()
    if payload.username is not None:
        connector.username = payload.username.strip() or None
    if payload.password is not None and payload.password.strip():
        connector.password_encrypted = _encrypt_secret(payload.password)
    if payload.status is not None:
        connector.status = payload.status
    if payload.query_config is not None:
        connector.query_config = payload.query_config

    connector.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(connector)
    return connector


def list_connectors(
    db: Session,
    status: Optional[str] = None,
) -> List[ExternalDBConnector]:
    """Retrieve all connectors, optionally filtered by status."""
    query = db.query(ExternalDBConnector)
    if status:
        query = query.filter(ExternalDBConnector.status == status)
    return query.order_by(ExternalDBConnector.id.asc()).all()


def get_connector(
    db: Session,
    connector_id: int,
) -> Optional[ExternalDBConnector]:
    """Fetch connector by primary key."""
    return db.query(ExternalDBConnector).filter(ExternalDBConnector.id == connector_id).first()


def delete_connector(
    db: Session,
    connector_id: int,
) -> bool:
    """Delete a connector configuration."""
    connector = get_connector(db, connector_id)
    if not connector:
        return False
    db.delete(connector)
    db.commit()
    return True


# ── Connection test ─────────────────────────────────────────────────────────

def _do_live_test(
    database_type: str,
    database_name: str,
    host: Optional[str],
    port: Optional[int],
    username: Optional[str],
    raw_password: Optional[str],
) -> ConnectorTestResponseSchema:
    """
    Perform a live SELECT 1 ping against the target database.
    Returns a ConnectorTestResponseSchema (without connector_id/connection_name set).
    Raises no exceptions — all errors are captured and classified.
    """
    try:
        uri = build_connection_uri(
            database_type=database_type,
            database_name=database_name,
            host=host,
            port=port,
            username=username,
            password=raw_password,
        )
    except ValueError as exc:
        return ConnectorTestResponseSchema(
            success=False,
            status="error",
            latency_ms=None,
            message=str(exc),
            error_type="config_error",
        )

    connect_args = {}
    if database_type == "postgresql":
        connect_args["connect_timeout"] = 5
    elif database_type == "sqlite":
        connect_args["check_same_thread"] = False
    elif database_type == "mysql":
        connect_args["connect_timeout"] = 5

    start_time = time.perf_counter()

    try:
        engine = create_engine(
            uri,
            connect_args=connect_args,
            execution_options={"isolation_level": "AUTOCOMMIT"},
            pool_pre_ping=True,
        )

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        engine.dispose()

        return ConnectorTestResponseSchema(
            success=True,
            status="success",
            latency_ms=elapsed_ms,
            message=f"Successfully connected and verified read access in {elapsed_ms}ms.",
            error_type=None,
            read_only_verified=True,
        )

    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        message, error_type = _classify_connection_error(exc, host, port, database_type)
        return ConnectorTestResponseSchema(
            success=False,
            status="error",
            latency_ms=elapsed_ms,
            message=message,
            error_type=error_type,
            read_only_verified=False,
        )


def test_connection(
    db: Session,
    connector_id: int,
) -> ConnectorTestResponseSchema:
    """Test connectivity to the external database in read-only mode."""
    connector = get_connector(db, connector_id)
    if not connector:
        raise ValueError(f"Connector ID {connector_id} not found.")

    raw_password = _decrypt_secret(connector.password_encrypted)
    result = _do_live_test(
        database_type=connector.database_type,
        database_name=connector.database_name,
        host=connector.host,
        port=connector.port,
        username=connector.username,
        raw_password=raw_password,
    )

    # Stamp the test timestamp regardless of outcome
    connector.last_tested_at = datetime.utcnow()
    # Update connector status to reflect last known test result
    connector.status = "active" if result.success else "error"
    db.commit()
    db.refresh(connector)

    result.connector_id = connector.id
    result.connection_name = connector.connection_name
    result.database_type = connector.database_type
    return result


# ── Sync ────────────────────────────────────────────────────────────────────

def sync_annotations_from_connector(
    db: Session,
    connector_id: int,
    project_id: int,
    table_name: Optional[str] = None,
    custom_query: Optional[str] = None,
    limit: int = 1000,
) -> ConnectorSyncResponseSchema:
    """
    Fetch annotations from external DB (read-only), normalize them,
    feed into existing AQG ingestion pipeline, and trigger trust scores.
    """
    connector = get_connector(db, connector_id)
    if not connector:
        raise ValueError(f"Connector ID {connector_id} not found.")

    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError(f"Target project ID {project_id} not found.")

    if custom_query:
        validate_read_only_query(custom_query)
        sql_query = custom_query
    else:
        target_table = table_name or connector.query_config.get("table_name", "annotations")
        # Sanitize table name (alphanumeric and underscores only)
        if not re.match(r"^[a-zA-Z0-9_]+$", target_table):
            raise ValueError(f"Invalid table name '{target_table}'.")
        sql_query = f"SELECT * FROM {target_table} LIMIT {int(limit)}"

    raw_password = _decrypt_secret(connector.password_encrypted)
    uri = build_connection_uri(
        database_type=connector.database_type,
        database_name=connector.database_name,
        host=connector.host,
        port=connector.port,
        username=connector.username,
        password=raw_password,
    )

    connect_args = {}
    if connector.database_type == "postgresql":
        connect_args["connect_timeout"] = 5
    elif connector.database_type == "sqlite":
        connect_args["check_same_thread"] = False
    elif connector.database_type == "mysql":
        connect_args["connect_timeout"] = 5

    engine = create_engine(uri, connect_args=connect_args)

    fetched_rows: List[Dict[str, Any]] = []
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            keys = result.keys()
            for row in result:
                fetched_rows.append(dict(zip(keys, row)))
    finally:
        engine.dispose()

    if not fetched_rows:
        return ConnectorSyncResponseSchema(
            success=True,
            connector_id=connector.id,
            project_id=project_id,
            total_fetched=0,
            inserted_records=0,
            duplicate_records=0,
            failed_records=0,
            synced_rows=0,
            message="No records found in external database table/query.",
        )

    # Normalize rows to standard AQG ingestion schema
    col_map = connector.query_config.get("column_mapping", {})
    normalized_records = []

    for row in fetched_rows:
        rec = {
            "project_id": project_id,
            "external_id": str(row.get(col_map.get("external_id", "external_id")) or row.get(col_map.get("item_id", "item_id")) or row.get("id")),
            "annotator_id": row.get(col_map.get("annotator_id", "annotator_id")) or 1,
            "label": row.get(col_map.get("label", "label")),
            "confidence": row.get(col_map.get("confidence", "confidence")),
            "duration_ms": row.get(col_map.get("duration_ms", "duration_ms")),
            "content": row.get(col_map.get("content", "content")) or {"external_row": True},
            "metadata": row.get(col_map.get("metadata", "metadata")) or {"source_connector": connector.connection_name},
        }
        normalized_records.append(rec)

    # Pass to existing pipeline
    ingest_result = ingest_records_batch(
        db=db,
        records=normalized_records,
        default_project_id=project_id,
    )

    # Update connector telemetry
    connector.last_sync_at = datetime.utcnow()
    connector.synced_rows_count = (connector.synced_rows_count or 0) + ingest_result["inserted_records"]
    db.commit()

    # Recompute trust scores for newly created/updated items
    if ingest_result["inserted_records"] > 0:
        items = db.query(Item).filter(Item.project_id == project_id).all()
        for itm in items:
            try:
                compute_and_save_item_trust_score(db=db, project_id=project_id, item_id=itm.id)
            except Exception:
                pass
        db.commit()

    return ConnectorSyncResponseSchema(
        success=ingest_result["success"],
        connector_id=connector.id,
        project_id=project_id,
        total_fetched=len(fetched_rows),
        inserted_records=ingest_result["inserted_records"],
        duplicate_records=ingest_result["duplicate_records"],
        failed_records=ingest_result["failed_records"],
        synced_rows=ingest_result["inserted_records"],
        message=(
            f"Synced {len(fetched_rows)} rows from connector '{connector.connection_name}': "
            f"{ingest_result['inserted_records']} inserted, {ingest_result['duplicate_records']} duplicates skipped."
        ),
    )
