from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Post(Base):
    
    __tablename__ = "posts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(
        String(500), 
        nullable=False, 
        index=True
    )
    content = Column(
        Text, 
        nullable=False
    )
    image_url = Column(
        String(500), 
        nullable=True
    )
    is_published = Column(
        Boolean, 
        default=False, 
        nullable=False, 
        index=True
    )
    excerpt = Column(
        Text, 
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
    author = relationship(
        "User", 
        back_populates="posts"
    )
    assets = relationship(
        "Asset", 
        back_populates="post", 
        cascade="all, delete-orphan"
    )