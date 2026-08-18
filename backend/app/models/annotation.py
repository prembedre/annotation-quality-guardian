"""
Annotation model representing a label given to an Item by an Annotator.
"""

from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    JSON,
    Index,
)
from sqlalchemy.orm import relationship
from app.core.db import Base


class Annotation(Base):
    """
    Represents an annotation decision submitted by an Annotator
    for a specific Item.
    """
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    annotator_id = Column(
        Integer,
        ForeignKey("annotators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    label = Column(
        String(255),
        nullable=False,
        index=True,
    )

    confidence = Column(
        Float,
        nullable=True,
        doc="Confidence score between 0.0 and 1.0",
    )

    duration_ms = Column(
        Integer,
        nullable=True,
    )

    metadata = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    updated_at = Column(
        DateTime,
        nullable=True,
        onupdate=datetime.utcnow,
    )

    # Relationships
    project = relationship(
        "Project",
        back_populates="annotations",
    )

    item = relationship(
        "Item",
        back_populates="annotations",
    )

    annotator = relationship(
        "Annotator",
        back_populates="annotations",
    )

    __table_args__ = (
        Index(
            "ix_item_annotator",
            "item_id",
            "annotator_id",
            unique=True,
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Annotation("
            f"id={self.id}, "
            f"item_id={self.item_id}, "
            f"annotator_id={self.annotator_id}, "
            f"label='{self.label}'"
            f")>"
        )
