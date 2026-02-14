"""Quiz model for Supabase database."""
from datetime import datetime
import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class Quiz(Base):
    """Quiz/assessment model."""
    
    __tablename__ = "quizzes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    title = Column(String(500), nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    finished_at = Column(DateTime, nullable=True)  
    time_used_seconds = Column(Integer, nullable=True)  
    passing_score = Column(Integer, default=70, nullable=False)  # Percentage
    attempts_allowed = Column(Integer, default=-1, nullable=False)  # -1 for unlimited
    show_answers = Column(Boolean, default=True, nullable=False)  # Show correct answers after completion
    randomize_questions = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    author = relationship("User", back_populates="quizzes")
    # Removed QuizQuestion relationship since we're not using quizzes yet
    # questions = relationship("QuizQuestion", back_populates="quiz", cascade="all, delete-orphan")