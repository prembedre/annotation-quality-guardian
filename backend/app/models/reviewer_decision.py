"""
ReviewerDecision model representing reviewer resolutions on flagged annotation items.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.db import Base


class ReviewerDecision(Base):
    """
    Represents a reviewer resolution decision for a flagged item or annotation.

    Supported actions (review_status):
    - CONFIRM: Confirm existing annotation label or gold label
    - CORRECT: Provide corrected label
    - ESCALATE: Escalate item for further review
    """

    __tablename__ = "reviewer_decisions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    item_id = Column(
        Integer,
        ForeignKey("items.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    annotation_id = Column(
        Integer,
        ForeignKey("annotations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    review_status = Column(
        String(50),
        nullable=False,
        index=True,
        doc="Action status: 'CONFIRM', 'CORRECT', or 'ESCALATE'",
    )

    reviewed_by = Column(
        Integer,
        ForeignKey("annotators.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Annotator ID of the reviewer who resolved the item",
    )

    reviewed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=True,
    )

    corrected_label = Column(
        String(255),
        nullable=True,
        doc="Corrected label supplied during resolution if status is CORRECT or CONFIRM",
    )

    review_notes = Column(
        Text,
        nullable=True,
        doc="Optional notes, rationale, or comments from the reviewer",
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
        back_populates="reviewer_decisions",
    )

    item = relationship(
        "Item",
        back_populates="reviewer_decisions",
    )

    annotation = relationship(
        "Annotation",
        back_populates="reviewer_decisions",
    )

    reviewer = relationship(
        "Annotator",
        foreign_keys=[reviewed_by],
        back_populates="reviewed_decisions",
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewerDecision("
            f"id={self.id}, "
            f"item_id={self.item_id}, "
            f"status='{self.review_status}', "
            f"reviewed_by={self.reviewed_by}"
            f")>"
        )
