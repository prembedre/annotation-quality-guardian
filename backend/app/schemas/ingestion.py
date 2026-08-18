"""
Pydantic schemas for data ingestion results and validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Any


class IngestionErrorDetail(BaseModel):
    """Details of an error encountered on a specific row/record during ingestion."""
    row: int = Field(..., description="1-indexed row number in the uploaded file")
    error: Optional[str] = Field(None, description="Single error description")
    errors: Optional[List[str]] = Field(None, description="List of validation errors for this record")


class IngestionResponse(BaseModel):
    """Response returned after processing a CSV or JSON file upload."""
    success: bool = Field(..., description="Whether ingestion completed successfully")
    message: str = Field(..., description="Summary status message")
    filename: Optional[str] = Field(None, description="Name of the processed file")
    total_records: int = Field(0, description="Total records detected in file")
    inserted_records: int = Field(0, description="Number of valid records inserted into database")
    duplicate_records: int = Field(0, description="Number of duplicate records skipped")
    failed_records: int = Field(0, description="Number of invalid records that failed validation")
    errors: List[Any] = Field(default_factory=list, description="List of per-record error objects")
