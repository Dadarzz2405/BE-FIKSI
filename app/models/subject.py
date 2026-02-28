"""Subject model — individual school subjects (Matematika, Fisika, etc.)."""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Subject(Base):
    """
    A school subject belonging to an AcademicCategory.
    Each subject has its own rank ladder (SubjectRank) and
    per-student progress tracking (UserSubjectProgress).
    """
    __tablename__ = "subjects"

    id                   = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    academic_category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("academic_categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name    = Column(String(100), unique=True, nullable=False, index=True)
    slug    = Column(String(100), unique=True, nullable=False, index=True)
    icon    = Column(String(50), nullable=True)  # emoji, e.g. "📐"
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    academic_category = relationship("AcademicCategory", back_populates="subjects")
    ranks             = relationship("SubjectRank", back_populates="subject", cascade="all, delete-orphan")
    progress          = relationship("UserSubjectProgress", back_populates="subject", cascade="all, delete-orphan")
