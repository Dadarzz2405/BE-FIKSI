# Asset model for tracking post attachments
from datetime import datetime
import uuid

# SQLAlchemy imports
from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

# Import declarative base
from app.db.base import Base


class Asset(Base):
    """Asset model for tracking files attached to posts."""
    __tablename__ = "assets"

    # Asset unique identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Reference to the post this asset is attached to
    post_id = Column(
        UUID(as_uuid=True),
        ForeignKey("posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # URL or file path to the stored asset
    file_url = Column(String, nullable=False)
    # MIME type of the file (e.g., "image/png", "application/pdf")
    media_type = Column(String, nullable=False, index=True)
    # When the asset was uploaded
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # ── Relationships ──────────────────────────────────────────────────────────
    # The post this asset belongs to
    post = relationship("Post", back_populates="assets")