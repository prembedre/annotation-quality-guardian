"""
Annotator model representing human or model annotators.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from app.core.db import Base


class Annotator(Base):
    """
    Represents an annotator (human worker or automated agent) providing labels.
    """
    __tablename__ = "annotators"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    annotations = relationship("Annotation", back_populates="annotator", cascade="all, delete-orphan")

    @property
    def username(self) -> str:
        return self.name

    @username.setter
    def username(self, val: str) -> None:
        self.name = val

    def __repr__(self) -> str:
        return f"<Annotator(id={self.id}, name='{self.name}')>"
