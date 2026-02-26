"""Admin model for Supabase database."""
# Standard library imports
from datetime import datetime
import uuid

# SQLAlchemy imports
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Admin(Base):
    """Administrative account linked to a user."""

    __tablename__ = "admins"

    # Admin profile unique identifier
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    # Reference to the user account (one-to-one relationship)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # Only one admin profile per user
        nullable=False,
        index=True,
    )
    # Admin role (e.g., "admin", "moderator", "editor")
    role = Column(
        String(50),
        default="admin",
        nullable=False,
        index=True,
    )
    # Whether this is a super admin with full permissions
    is_super_admin = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    # When admin privileges were granted
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    # When admin profile was last updated
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # Back reference to the user account
    user = relationship("User", back_populates="admin_profile")
