"""Admin model for Supabase database."""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Admin(Base):
    """Administrative account linked to a user."""

    __tablename__ = "admins"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    role = Column(
        String(50),
        default="admin",
        nullable=False,
        index=True,
    )
    is_super_admin = Column(
        Boolean,
        default=False,
        nullable=False,
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="admin_profile")
