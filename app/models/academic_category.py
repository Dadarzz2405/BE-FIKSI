"""AcademicCategory model — groups subjects into curriculum areas."""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class AcademicCategory(Base):
    """
    Top-level curriculum category (e.g. Science, Social, Language).
    Each category contains multiple Subjects.
    """
    __tablename__ = "academic_categories"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name        = Column(String(100), unique=True, nullable=False, index=True)
    slug        = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    icon        = Column(String(50), nullable=True)  # emoji, e.g. "🔬"
    created_at  = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    subjects = relationship("Subject", back_populates="academic_category", cascade="all, delete-orphan")
