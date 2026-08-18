"""
Item model representing a data unit to be annotated.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, JSON, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from app.core.db import Base


class Item(Base):
    """
    Represents an individual item (e.g. text prompt, review, image URL)
    subject to annotation and quality scoring.
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=True, index=True)
    external_id = Column(String(255), nullable=True, index=True, doc="External identifier from dataset")
    source = Column(String(255), nullable=False, default="default", index=True, doc="Origin or dataset source name")
    content = Column(JSON, nullable=False, default=dict, doc="Raw payload, text, or reference metadata")
    is_gold = Column(Boolean, default=False, nullable=False, index=True)
    gold_label = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="items")
    annotations = relationship("Annotation", back_populates="item", cascade="all, delete-orphan")
    trust_scores = relationship("TrustScore", back_populates="item", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_items_project_external", "project_id", "external_id"),
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, project_id={self.project_id}, external_id='{self.external_id}')>"
