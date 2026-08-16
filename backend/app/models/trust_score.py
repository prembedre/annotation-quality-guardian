"""
TrustScore model representing computed multi-signal quality assessment for an Item.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, Float, Boolean, JSON, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.db import Base


class TrustScore(Base):
    """
    Represents the aggregated trust score and breakdown for an Item.
    Derived from gold checks, agreement, behavioral anomalies, and embeddings.
    """
    __tablename__ = "trust_scores"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, ForeignKey("items.id", ondelete="CASCADE"), nullable=False, index=True)
    score = Column(Float, nullable=False, doc="Composite trust score (0.0 to 1.0)")
    breakdown = Column(
        JSON,
        nullable=False,
        default=dict,
        doc="Detailed metric breakdown (gold_accuracy, agreement, anomaly, embedding)",
    )
    flagged = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        doc="True if item is flagged as low trust / outlier",
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    item = relationship("Item", back_populates="trust_scores")

    def __repr__(self) -> str:
        return f"<TrustScore(id={self.id}, item_id={self.item_id}, score={self.score}, flagged={self.flagged})>"
