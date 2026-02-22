from app.db.session import engine
from app.db.base import Base

# Import ALL models so SQLAlchemy registers their metadata before create_all
from app.models.user import User          # noqa: F401
from app.models.category import Category  # noqa: F401
from app.models.post import Post          # noqa: F401
from app.models.comment import Comment    # noqa: F401
from app.models.quiz import Quiz          # noqa: F401
from app.models.admin import Admin        # noqa: F401
from app.models.friendship import Friendship  # noqa: F401
from app.models.assets import Asset       # noqa: F401


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified successfully.")


if __name__ == "__main__":
    init_db()