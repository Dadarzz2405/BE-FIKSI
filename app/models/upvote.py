"""
app/models/upvote.py

Tracks which user upvoted which post or comment.
Exactly one of post_id/comment_id should be set.
"""
# Standard library imports
import uuid
from datetime import datetime

# SQLAlchemy imports
from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Upvote(Base):
    """Upvote model tracking votes on posts or comments."""
    __tablename__ = "upvotes"

    # Upvote record unique identifier
    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # User who cast the upvote
    user_id    = Column(UUID(as_uuid=True), ForeignKey("users.id",    ondelete="CASCADE"), nullable=False, index=True)
    # Post being upvoted
    post_id = Column(UUID(as_uuid=True), ForeignKey("posts.id", ondelete="CASCADE"), nullable=True, index=True)
    # Comment being upvoted
    comment_id = Column(UUID(as_uuid=True), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True, index=True)
    # When the upvote was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Constraints ────────────────────────────────────────────────────────────
    # One user can upvote a post once and a comment once.
    __table_args__ = (
        UniqueConstraint("user_id", "post_id", name="unique_post_upvote"),
        UniqueConstraint("user_id", "comment_id", name="uq_upvote_user_comment"),
        CheckConstraint(
            "(post_id IS NOT NULL AND comment_id IS NULL) OR (post_id IS NULL AND comment_id IS NOT NULL)",
            name="ck_upvotes_exactly_one_target",
        ),
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # The user who cast the vote
    voter   = relationship("User",    foreign_keys=[user_id])
    post = relationship("Post", foreign_keys=[post_id])
    # The comment being voted on
    comment = relationship("Comment", foreign_keys=[comment_id])
