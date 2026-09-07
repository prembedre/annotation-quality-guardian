"""
Pydantic schemas for External Database Connectors (read-only integration).
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, ConfigDict


class ConnectorCreateSchema(BaseModel):
    """Schema for creating a new read-only database connector."""
    connection_name: str = Field(..., min_length=1, max_length=255, description="Unique connection name")
    database_type: str = Field(default="postgresql", description="Database engine ('postgresql', 'sqlite', 'mysql')")
    host: Optional[str] = Field(None, description="Database host/IP")
    port: Optional[int] = Field(5432, ge=1, le=65535, description="Port number")
    database_name: str = Field(..., min_length=1, max_length=255, description="Database name or path")
    username: Optional[str] = Field(None, max_length=255, description="Database username")
    password: Optional[str] = Field(None, description="Database password (will be securely handled)")
    status: Optional[str] = Field(default="active", description="Initial status ('active', 'disabled')")
    query_config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Table & column mapping configurations")


class ConnectorUpdateSchema(BaseModel):
    """Schema for updating an existing connector."""
    connection_name: Optional[str] = Field(None, min_length=1, max_length=255)
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    status: Optional[str] = None
    query_config: Optional[Dict[str, Any]] = None


class ConnectorResponseSchema(BaseModel):
    """Safe schema for connector response without exposing credentials."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    connection_name: str
    database_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database_name: str
    username: Optional[str] = None
    status: str
    read_only: bool = True
    query_config: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None


class ConnectorListResponse(BaseModel):
    """List response for connectors."""
    total: int
    connectors: List[ConnectorResponseSchema]


class ConnectorTestResponseSchema(BaseModel):
    """Response returned after testing connection."""
    success: bool
    connector_id: Optional[int] = None
    connection_name: Optional[str] = None
    database_type: Optional[str] = None
    latency_ms: Optional[float] = None
    message: str
    read_only_verified: bool = True


class ConnectorSyncRequestSchema(BaseModel):
    """Request schema for syncing annotations from an external database."""
    project_id: int = Field(..., description="Target AQG project ID")
    table_name: Optional[str] = Field(None, description="External table name to query")
    custom_query: Optional[str] = Field(None, description="Optional read-only SELECT query")
    limit: Optional[int] = Field(1000, ge=1, le=50000, description="Max rows to fetch")


class ConnectorSyncResponseSchema(BaseModel):
    """Summary response of sync operation."""
    success: bool
    connector_id: int
    project_id: int
    total_fetched: int
    inserted_records: int
    duplicate_records: int
    failed_records: int
    message: str
