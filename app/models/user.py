"""User model — includes gamification columns."""
# Standard library imports
from datetime import datetime
import uuid

# SQLAlchemy imports for column types and relationships
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base for ORM
from app.db.base import Base


class User(Base):
    """
    User model representing platform users with authentication and gamification data.
    """
    __tablename__ = "users"

    # ── Authentication & Profile ────────────────────────────────────────────
    id            = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    real_name     = Column(String(255), nullable=True, index=True)
    username      = Column(String(50),  unique=True, nullable=False, index=True)
    email         = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active     = Column(Boolean, default=False, nullable=False)
    subscription  = Column(String(50), default="Free", nullable=False)
    bio           = Column(Text, default="", nullable=False)
    avatar_url    = Column(String(500), nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at    = Column(DateTime, default=datetime.utcnow,
                           onupdate=datetime.utcnow, nullable=False)

    # ── Gamification ──────────────────────────────────────────────────────────
    xp_total    = Column(Integer, default=0, nullable=False)  # lifetime XP (never resets)
    xp_current  = Column(Integer, default=0, nullable=False)  # XP within current level
    level       = Column(Integer, default=1, nullable=False)  # current level
    reputation  = Column(Integer, default=0, nullable=False)  # drives rank tier
    cp_total    = Column(Integer, default=0, nullable=False)  # challenge points (competitive)

    # ── Relationships ───────────────────────────────────────────────────────────
    # User's posts with cascade delete for data cleanup
    posts         = relationship("Post",    back_populates="author", cascade="all, delete-orphan")
    # User's quizzes created
    quizzes       = relationship("Quiz",    back_populates="author", cascade="all, delete-orphan")
    # User's comments on posts
    comments      = relationship("Comment", back_populates="author", cascade="all, delete-orphan")
    # Optional admin profile
    admin_profile = relationship("Admin",   back_populates="user",
                                 uselist=False, cascade="all, delete-orphan")
    # Per-subject XP / level / rank progress
    subject_progress = relationship("UserSubjectProgress", back_populates="user",
                                    cascade="all, delete-orphan")