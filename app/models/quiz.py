"""Quiz model for Supabase database."""
# Standard library imports
from datetime import datetime
import uuid

# SQLAlchemy imports
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Quiz(Base):
    """Quiz/assessment model for creating quizzes and tracking attempts."""
    
    __tablename__ = "quizzes"

    # Quiz unique identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # User who created this quiz
    author_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Quiz title
    title = Column(String(500), nullable=False, index=True)
    # Optional longer description
    description = Column(Text, nullable=True)
    # Whether the quiz is publicly available
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    # When this quiz attempt started
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # When the quiz was completed (null if not finished)
    finished_at = Column(DateTime, nullable=True)  
    # Time spent on the quiz in seconds
    time_used_seconds = Column(Integer, nullable=True)  
    # Minimum score percentage needed to pass
    passing_score = Column(Integer, default=70, nullable=False)  # Percentage
    # -1 for unlimited attempts, otherwise max number
    attempts_allowed = Column(Integer, default=-1, nullable=False)  # -1 for unlimited
    # Show correct answers after completion
    show_answers = Column(Boolean, default=True, nullable=False)
    # Randomize question order for each attempt
    randomize_questions = Column(Boolean, default=False, nullable=False)
    # When the quiz was created
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    # When the quiz was last updated
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # ── Relationships ──────────────────────────────────────────────────────────
    # User who authored this quiz
    author = relationship("User", back_populates="quizzes")
    # Note: QuizQuestion relationship removed - not currently implemented