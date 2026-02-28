"""UserSubjectProgress — per-user, per-subject XP / level / rank tracking."""
from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class UserSubjectProgress(Base):
    """
    Tracks a student's XP, level, and rank points (RP) for a single subject.
    CP stays global on the User model; RP drives per-subject rank.

    One row per (user_id, subject_id) pair.
    """
    __tablename__ = "user_subject_progress"

    id          = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id     = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id  = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    xp_total    = Column(Integer, default=0, nullable=False)   # lifetime XP in this subject
    xp_current  = Column(Integer, default=0, nullable=False)   # XP within current level
    level       = Column(Integer, default=1, nullable=False)   # subject-specific level
    rank_points = Column(Integer, default=0, nullable=False)   # RP — drives per-subject rank
    updated_at  = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Constraints ────────────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("user_id", "subject_id", name="uq_user_subject"),
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    user    = relationship("User", back_populates="subject_progress")
    subject = relationship("Subject", back_populates="progress")
