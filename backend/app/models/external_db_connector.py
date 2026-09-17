"""
ExternalDBConnector model representing read-only external labeling database connections.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime
from app.core.db import Base


class ExternalDBConnector(Base):
    """
    Represents a read-only external database connection configuration.
    Allows AQG to query external annotation databases without write permissions.
    """

    __tablename__ = "external_db_connectors"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    connection_name = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique identifier name for this connector",
    )

    database_type = Column(
        String(50),
        nullable=False,
        default="postgresql",
        doc="Database engine type: 'postgresql', 'mysql', 'sqlite'",
    )

    host = Column(
        String(255),
        nullable=True,
        doc="Database host address",
    )

    port = Column(
        Integer,
        nullable=True,
        default=5432,
        doc="Database network port",
    )

    database_name = Column(
        String(255),
        nullable=False,
        doc="Database catalog or file path",
    )

    username = Column(
        String(255),
        nullable=True,
        doc="Database user credentials",
    )

    password_encrypted = Column(
        String(500),
        nullable=True,
        doc="Fernet-encrypted password (falls back to base64 if cryptography unavailable)",
    )

    status = Column(
        String(50),
        nullable=False,
        default="active",
        index=True,
        doc="Connector status: 'active', 'disabled', 'error'",
    )

    read_only = Column(
        Boolean,
        nullable=False,
        default=True,
        doc="Strict read-only safety flag (always True)",
    )

    query_config = Column(
        JSON,
        nullable=False,
        default=dict,
        doc="Configuration for fetching annotations (table_name, column_mapping, query)",
    )

    # ── Telemetry columns ───────────────────────────────────────────

    last_sync_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp of last successful data synchronization",
    )

    synced_rows_count = Column(
        Integer,
        nullable=False,
        default=0,
        doc="Cumulative total of annotation rows ingested via this connector",
    )

    last_tested_at = Column(
        DateTime,
        nullable=True,
        doc="Timestamp of last connection test (ping)",
    )

    # ── Audit columns ───────────────────────────────────────────────

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ExternalDBConnector("
            f"id={self.id}, "
            f"name='{self.connection_name}', "
            f"type='{self.database_type}', "
            f"status='{self.status}'"
            f")>"
        )
