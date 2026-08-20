"""
EmbeddingResult model representing Phase 2 embedding analysis results.
"""

from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    Boolean,
    JSON,
    DateTime,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship

from app.core.db import Base


class EmbeddingResult(Base):
    """
    Stores embedding and outlier detection results for an Item.
    """

    __tablename__ = "embedding_results"

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

    model_name = Column(
        String(255),
        nullable=False,
    )

    embedding = Column(
        JSON,
        nullable=True,
    )

    outlier_score = Column(
        Numeric(10, 6),
        nullable=True,
    )

    is_outlier = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    nearest_item_id = Column(
        Integer,
        ForeignKey("items.id", ondelete="SET NULL"),
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
        back_populates="embedding_results",
    )

    item = relationship(
        "Item",
        foreign_keys=[item_id],
        back_populates="embedding_results",
    )

    nearest_item = relationship(
        "Item",
        foreign_keys=[nearest_item_id],
    )

    __table_args__ = (
        Index("idx_embedding_results_project", "project_id"),
        Index("idx_embedding_results_item", "item_id"),
        Index(
            "idx_embedding_results_outlier",
            "project_id",
            "is_outlier",
            postgresql_where=is_outlier.is_(True),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<EmbeddingResult("
            f"id={self.id}, "
            f"item_id={self.item_id}, "
            f"model_name='{self.model_name}', "
            f"is_outlier={self.is_outlier}"
            f")>"
        )
