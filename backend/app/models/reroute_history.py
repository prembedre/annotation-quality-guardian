"""
RerouteHistory model representing automated task rerouting and annotator reassignments.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class RerouteHistory(Base):
    """
    Tracks task rerouting events when flagged items or low-performing
    annotator tasks are reassigned to different annotators.
    """

    __tablename__ = "reroute_histories"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Item being reassigned/rerouted",
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Project ID for the rerouted item",
    )

    original_annotator_id = Column(
        Integer,
        ForeignKey("annotators.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Annotator who originally submitted the flagged/low-confidence annotation",
    )

    reassigned_annotator_id = Column(
        Integer,
        ForeignKey("annotators.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Annotator to whom the item has been reassigned",
    )

    reason = Column(
        Text,
        nullable=True,
        doc="Automated trigger reason (e.g., 'Low trust score 0.35', 'Disagreement outlier')",
    )

    trust_score_snapshot = Column(
        Numeric(10, 6),
        nullable=True,
        doc="Snapshot of the item trust score when rerouting was triggered",
    )

    reroute_status = Column(
        String(50),
        nullable=False,
        default="PENDING",
        index=True,
        doc="Status of reroute: 'PENDING', 'ASSIGNED', 'COMPLETED', 'CANCELLED'",
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
    item = relationship(
        "Item",
        back_populates="reroute_histories",
    )

    project = relationship(
        "Project",
        back_populates="reroute_histories",
    )

    original_annotator = relationship(
        "Annotator",
        foreign_keys=[original_annotator_id],
        back_populates="rerouted_from_tasks",
    )

    reassigned_annotator = relationship(
        "Annotator",
        foreign_keys=[reassigned_annotator_id],
        back_populates="rerouted_to_tasks",
    )

    def __repr__(self) -> str:
        return (
            f"<RerouteHistory("
            f"id={self.id}, "
            f"item_id={self.item_id}, "
            f"status='{self.reroute_status}', "
            f"from={self.original_annotator_id}->to={self.reassigned_annotator_id}"
            f")>"
        )
