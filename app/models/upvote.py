import uuid
from sqlalchemy import Column, ForeignKey, String, Text, Boolean, DateTime, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.base import Base

class Upvote(Base):
    __tablename__ = "upvotes"
    id = Column(UUID, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID, ForeignKey("users.id", ondelete="CASCADE"))
    post_id = Column(UUID, ForeignKey("posts.id", ondelete="CASCADE"), nullable=True)
    comment_id = Column(UUID, ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    # unique constraint: one user, one vote per post/comment