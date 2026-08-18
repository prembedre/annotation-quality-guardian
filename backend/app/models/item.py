"""
Item model representing a data unit to be annotated.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class Item(Base):
    """
    Represents an individual item subject to annotation and quality scoring.
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    external_id = Column(
        String(255),
        nullable=False,
    )

    content = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    is_gold = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    gold_label = Column(
        String(255),
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    project = relationship("Project", back_populates="items")

    annotations = relationship(
        "Annotation",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Item(id={self.id}, external_id='{self.external_id}', is_gold={self.is_gold})>"
