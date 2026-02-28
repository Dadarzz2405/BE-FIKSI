# Database initialization and table creation

from app.db.session import engine
from app.db.base import Base

# Import ALL models so SQLAlchemy registers their metadata before create_all
# Without these imports, tables won't be created
from app.models.user import User          # noqa: F401
from app.models.post import Post          # noqa: F401
from app.models.comment import Comment    # noqa: F401
from app.models.upvote import Upvote      # noqa: F401
from app.models.quiz import Quiz          # noqa: F401
from app.models.admin import Admin        # noqa: F401
from app.models.friendship import Friendship  # noqa: F401
from app.models.assets import Asset       # noqa: F401
from app.models.academic_category import AcademicCategory  # noqa: F401
from app.models.subject import Subject                     # noqa: F401
from app.models.subject_rank import SubjectRank            # noqa: F401
from app.models.user_subject_progress import UserSubjectProgress  # noqa: F401


def init_db() -> None:
    """Create all tables defined in models if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified successfully.")


if __name__ == "__main__":
    init_db()
