"""Friendship model for managing user connections."""
# Standard library imports
from datetime import datetime
import enum
import uuid

# SQLAlchemy imports
from sqlalchemy import Column, DateTime, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class FriendshipStatus(str, enum.Enum):
    """Enum for friendship request and connection status."""
    PENDING = "pending"   # Request sent, awaiting response
    ACCEPTED = "accepted" # Both users connected
    BLOCKED = "blocked"   # Connection blocked
    REJECTED = "rejected" # Request was rejected


class Friendship(Base):
    """Friendship/connection between users."""
    
    __tablename__ = "friendships"

    # Friendship record unique identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # User who initiated the friend request
    requester_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # User who receives the friend request
    addressee_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Current status of the friendship (pending, accepted, blocked, rejected)
    status = Column(
        Enum(FriendshipStatus),
        default=FriendshipStatus.PENDING,
        nullable=False,
        index=True
    )
    # When the friendship record was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # When the friendship status was last updated
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # User who sent the request
    requester = relationship("User", foreign_keys=[requester_id])
    # User who received the request
    addressee = relationship("User", foreign_keys=[addressee_id])

    # ── Constraints ────────────────────────────────────────────────────────────
    # Ensure each unique pair of users can only have one friendship record
    __table_args__ = (
        UniqueConstraint("requester_id", "addressee_id", name="unique_friendship"),
    )