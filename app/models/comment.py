# Comment model for answers and discussions
import uuid
from datetime import datetime

# SQLAlchemy imports
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Comment(Base):
    """Comment model representing answers, replies, or discussions on posts."""
    __tablename__ = "comments"

    # Comment unique identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Reference to the post this comment is on
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # User who created this comment
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Comment text content
    content = Column(Text, nullable=False)
    # Whether this comment is marked as the accepted/best answer
    is_accepted = Column(Boolean, default=False, nullable=False)
    # When the comment was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # When the comment was last updated
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # The post this comment belongs to
    post = relationship("Post", back_populates="comments")
    # The user who authored this comment
    author = relationship("User", back_populates="comments")