"""
Annotation model representing a label given to an Item by an Annotator.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.db import Base


class Annotation(Base):
    """
    Represents an annotation decision submitted by an Annotator for a specific Item.
    """
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    annotator_id = Column(Integer, ForeignKey("annotators.id", ondelete="CASCADE"), nullable=False, index=True)
    label = Column(String(255), nullable=False, index=True)
    confidence = Column(Float, nullable=True, doc="Confidence score between 0.0 and 1.0")
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    item = relationship("Item", back_populates="annotations")
    annotator = relationship("Annotator", back_populates="annotations")

    __table_args__ = (
        Index("ix_item_annotator", "item_id", "annotator_id", unique=True),
    )

    def __repr__(self) -> str:
        return f"<Annotation(id={self.id}, item_id={self.item_id}, label='{self.label}')>"
