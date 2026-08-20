"""
TrustScore model representing the final multi-signal quality assessment.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class TrustScore(Base):
    """
    Represents the aggregated trust score for an Item.

    The final score is calculated from:
    - Gold-standard accuracy
    - Annotator agreement
    - Behavioral scoring
    - Embedding/outlier scoring
    """

    __tablename__ = "trust_scores"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

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

    gold_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    agreement_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    behavioral_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    embedding_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    final_score = Column(
        Numeric(10, 6),
        nullable=False,
    )

    flagged = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    breakdown = Column(
        JSON,
        nullable=False,
        default=dict,
    )

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

    # Relationships
    project = relationship(
        "Project",
        back_populates="trust_scores",
    )

    item = relationship(
        "Item",
        back_populates="trust_scores",
    )

    trust_scores = relationship(
    "TrustScore",
    back_populates="project",
    cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<TrustScore("
            f"id={self.id}, "
            f"project_id={self.project_id}, "
            f"item_id={self.item_id}, "
            f"final_score={self.final_score}, "
            f"flagged={self.flagged}"
            f")>"
        )
