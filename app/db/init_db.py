from app.db.session import engine
from app.db.base import Base
# Import all models to ensure they're registered with Base
from app.models.user import User
from app.models.post import Post
from app.models.quiz import Quiz
from app.models.admin import Admin
from app.models.friendship import Friendship
from app.models.assets import Asset


def init_db() -> None:
    # Create all tables defined in models
    Base.metadata.create_all(bind=engine)
    print("Database tables created/verified successfully.")


if __name__ == "__main__":
    init_db()