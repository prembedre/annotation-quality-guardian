"""
Item model representing a data unit to be annotated.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    JSON,
    DateTime,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class Item(Base):
    """
    Represents an individual item subject to annotation
    and quality scoring.
    """

    __tablename__ = "items"

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

    def __init__(self, *args, **kwargs):
        kwargs.pop("source", None)
        super().__init__(*args, **kwargs)

    # Relationships

    project = relationship(
        "Project",
        back_populates="items",
    )

    annotations = relationship(
        "Annotation",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    trust_scores = relationship(
        "TrustScore",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    behavioral_scores = relationship(
        "BehavioralScore",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    embedding_results = relationship(
        "EmbeddingResult",
        foreign_keys="EmbeddingResult.item_id",
        back_populates="item",
        cascade="all, delete-orphan",
    )

    reviewer_decisions = relationship(
        "ReviewerDecision",
        back_populates="item",
        cascade="all, delete-orphan",
    )


    def __repr__(self) -> str:
        return (
            f"<Item("
            f"id={self.id}, "
            f"external_id='{self.external_id}', "
            f"is_gold={self.is_gold}"
            f")>"
        )
