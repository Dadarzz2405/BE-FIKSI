"""User model for Supabase database."""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class User(Base):
    """User account model."""
    
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4, 
        index=True
    )
    real_name = Column(
        String(255),
        nullable=True, 
        index=True
    )
    username = Column(
        String(50), 
        unique=True, 
        nullable=False, 
        index=True
    )
    email = Column(
        String(255), 
        unique=True, 
        nullable=False, 
        index=True
    )
    hashed_password = Column(
        String(255), 
        nullable=False
    )
    is_active = Column(
        Boolean, 
        default=False, 
        nullable=False
    )
    subscription = Column(
        String(50), 
        default="Free", 
        nullable=False
    )
    bio = Column(
        Text, 
        default="", 
        nullable=False
    )
    avatar_url = Column(
        String(500), 
        nullable=True
    )  
    created_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    posts = relationship(
        "Post", 
        back_populates="author", 
        cascade="all, delete-orphan"
    )
    quizzes = relationship(
        "Quiz", 
        back_populates="author", 
        cascade="all, delete-orphan"
    )
    admin_profile = relationship(
        "Admin",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
