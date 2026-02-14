"""Friendship model for Supabase database."""
from datetime import datetime
import enum
import uuid

from sqlalchemy import Column, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from app.db.base import Base


class FriendshipStatus(str, enum.Enum):
    """Enum for friendship status."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    REJECTED = "rejected"  # Added rejected status


class Friendship(Base):
    """Friendship/connection between users."""
    
    __tablename__ = "friendships"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    addressee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    status = Column(
        Enum(FriendshipStatus),
        default=FriendshipStatus.PENDING,
        nullable=False,
        index=True
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id])
    addressee = relationship("User", foreign_keys=[addressee_id])

    # Constraints
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="unique_friendship"),
    )