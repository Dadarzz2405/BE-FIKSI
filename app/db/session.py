from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

from app.core.config import DATABASE_URL

# Create SQLAlchemy engine with NullPool to avoid prepared statement issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # No connection pooling - fresh connections every time
    connect_args={
        "prepared_statement_cache_size": 0  # Disable prepared statement cache
    } if "postgresql" in DATABASE_URL else {},
    echo=False,
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()