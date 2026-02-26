# Post model for blog posts and questions
from datetime import datetime
import uuid

# SQLAlchemy imports
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Post(Base):
    """Post model representing blog posts, questions, or articles."""

    __tablename__ = "posts"

    # Core fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Author cascade delete if user is removed
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Category can be null (uncategorized posts allowed)
    category_id = Column(
        UUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    title = Column(String(500), nullable=False, index=True)
    content = Column(Text, nullable=False)
    image_url = Column(String(500), nullable=True)  # Thumbnail or featured image
    is_published = Column(Boolean, default=False, nullable=False, index=True)
    excerpt = Column(Text, nullable=True)  # Short summary for preview
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # Post author
    author = relationship("User", back_populates="posts")
    # Category this post belongs to
    category = relationship("Category", back_populates="posts")
    # Attached files (images, PDFs, etc.)
    assets = relationship("Asset", back_populates="post", cascade="all, delete-orphan")
    # Comments and answers on this post
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")