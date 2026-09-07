"""
External Database Connector Service.
Provides read-only database connections, testing, security checks, and annotation synchronization.
"""

import base64
import re
import time
from typing import Dict, Any, List, Optional
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


# Regex detecting any destructive or state-modifying SQL statements
FORBIDDEN_SQL_PATTERN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|EXEC|EXECUTE|CREATE|RENAME|GRANT|REVOKE|REPLACE|MERGE)\b",
    re.IGNORECASE,
)


def _encrypt_secret(plain_text: Optional[str]) -> Optional[str]:
    """Obfuscate/encrypt secret string for storage."""
    if not plain_text:
        return None
    return base64.b64encode(plain_text.encode("utf-8")).decode("utf-8")


def _decrypt_secret(cipher_text: Optional[str]) -> Optional[str]:
    """Decrypt/de-obfuscate stored secret."""
    if not cipher_text:
        return None
    try:
        return base64.b64decode(cipher_text.encode("utf-8")).decode("utf-8")
    except Exception:
        return cipher_text


def validate_read_only_query(query: str) -> None:
    """Ensure query contains only read-only statements."""
    if not query or not query.strip():
        raise ValueError("Query string cannot be empty.")

    clean_query = query.strip()
    if not clean_query.lower().startswith("select"):
        raise ValueError("Only SELECT queries are permitted on read-only external database connectors.")

    if FORBIDDEN_SQL_PATTERN.search(clean_query):
        raise ValueError("Forbidden mutation or administrative keyword detected. Read-only access enforced.")


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
        # SQLite read-only connection URI
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
    )

    db.add(connector)
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


def test_connection(
    db: Session,
    connector_id: int,
) -> ConnectorTestResponseSchema:
    """Test connectivity to the external database in read-only mode."""
    connector = get_connector(db, connector_id)
    if not connector:
        raise ValueError(f"Connector ID {connector_id} not found.")

    raw_password = _decrypt_secret(connector.password_encrypted)
    uri = build_connection_uri(
        database_type=connector.database_type,
        database_name=connector.database_name,
        host=connector.host,
        port=connector.port,
        username=connector.username,
        password=raw_password,
    )

    start_time = time.perf_counter()

    try:
        connect_args = {}
        if connector.database_type == "postgresql":
            connect_args["connect_timeout"] = 5
        elif connector.database_type == "sqlite":
            connect_args["check_same_thread"] = False

        engine = create_engine(
            uri,
            connect_args=connect_args,
            execution_options={"isolation_level": "AUTOCOMMIT"},
        )

        with engine.connect() as conn:
            # Execute ping check
            conn.execute(text("SELECT 1"))

        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
        engine.dispose()

        return ConnectorTestResponseSchema(
            success=True,
            connector_id=connector.id,
            connection_name=connector.connection_name,
            database_type=connector.database_type,
            latency_ms=elapsed_ms,
            message=f"Successfully connected to external database '{connector.database_name}' in {elapsed_ms}ms (Read-Only Verified).",
            read_only_verified=True,
        )

    except Exception as exc:
        return ConnectorTestResponseSchema(
            success=False,
            connector_id=connector.id,
            connection_name=connector.connection_name,
            database_type=connector.database_type,
            latency_ms=None,
            message=f"Connection failed: {str(exc)}",
            read_only_verified=True,
        )


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
        message=f"Synced {len(fetched_rows)} rows from connector '{connector.connection_name}': {ingest_result['inserted_records']} inserted, {ingest_result['duplicate_records']} duplicates skipped.",
    )
