# Database session configuration and management

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import DATABASE_URL


engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # No connection pooling
    connect_args={
        "prepare_threshold": None,  # Disable prepared statements for psycopg3
        "connect_timeout": 20,  # Increased for Render production cold starts
    }
    if "postgresql" in DATABASE_URL
    else {},
    echo=False,  # Set to True for SQL query logging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.
    Automatically handles cleanup and closing of connections.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
