"""
BehavioralScore model representing Phase 2 behavioral scoring results.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    Numeric,
    JSON,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class BehavioralScore(Base):
    """
    Stores behavioral scoring results for an annotator.
    """

    __tablename__ = "behavioral_scores"

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

    annotator_id = Column(
        Integer,
        ForeignKey("annotators.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    time_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    streak_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    anomaly_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    details = Column(
        JSON,
        nullable=False,
        default=dict,
    )

    computed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    project = relationship(
        "Project",
        back_populates="behavioral_scores",
    )

    annotator = relationship(
        "Annotator",
        back_populates="behavioral_scores",
    )

    item = relationship(
        "Item",
        back_populates="behavioral_scores",
    )

    __table_args__ = (
        Index("idx_behavioral_scores_project", "project_id"),
        Index("idx_behavioral_scores_annotator", "annotator_id"),
        Index("idx_behavioral_scores_item", "item_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<BehavioralScore("
            f"id={self.id}, "
            f"project_id={self.project_id}, "
            f"annotator_id={self.annotator_id}"
            f")>"
        )
