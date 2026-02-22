import uuid

from sqlalchemy import Column, ForeignKey, String, Text, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Comment(Base):
    __tablename__ = "comments"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    post_id = Column(UUID, ForeignKey("posts.id", ondelete="CASCADE"))
    author_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    content = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False)  # "best answer" mark
    created_at = Column(DateTime, default=datetime.utcnow)
    post = relationship("Post", back_populates="comments")
    author = relationship("User")