# Category model for organizing posts
import uuid
from datetime import datetime

# SQLAlchemy imports
from sqlalchemy import Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Category(Base):
    """Category model for organizing posts into topics and subjects."""
    __tablename__ = "categories"

    # Category unique identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Human-readable name (must be unique)
    name = Column(String(100), unique=True, nullable=False, index=True)
    # URL-friendly slug (e.g., "python-questions")
    slug = Column(String(100), unique=True, nullable=False, index=True)
    # Longer description of the category
    description = Column(Text, nullable=True)
    # Unicode emoji or icon representing the category
    icon = Column(String(50), nullable=True)
    # When category was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    # All posts within this category
    posts = relationship("Post", back_populates="category")