"""SubjectRank model — rank ladder tiers per subject."""
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class SubjectRank(Base):
    """
    One tier in a subject's rank ladder.
    Each subject has its own set of ranks (Bronze → Diamond).
    Stored in DB so themes/names can vary per subject in the future.

    Example rows for Matematika:
        tier=1, name="Bronze",   icon="🥉", min_rp=0
        tier=2, name="Silver",   icon="🥈", min_rp=100
        tier=3, name="Gold",     icon="🥇", min_rp=500
        tier=4, name="Platinum", icon="⚡",  min_rp=1500
        tier=5, name="Diamond",  icon="💎",  min_rp=5000
    """
    __tablename__ = "subject_ranks"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    subject_id = Column(
        UUID(as_uuid=True),
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tier   = Column(Integer, nullable=False)            # 1, 2, 3, 4, 5
    name   = Column(String(50), nullable=False)         # "Bronze", "Silver", ...
    icon   = Column(String(50), nullable=False)         # "🥉", "🥈", ...
    min_rp = Column(Integer, nullable=False, default=0) # rank points needed

    # ── Constraints ────────────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("subject_id", "tier", name="uq_subject_rank_tier"),
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    subject = relationship("Subject", back_populates="ranks")
