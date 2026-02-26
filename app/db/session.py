# Database session configuration and management

# SQLAlchemy core and ORM imports
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from typing import Generator

# Import database URL from configuration
from app.core.config import DATABASE_URL

# Create SQLAlchemy engine with NullPool to avoid prepared statement issues
engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # No connection pooling
    connect_args={
        "prepare_threshold": None,  # Disable prepared statements for psycopg3
    } if "postgresql" in DATABASE_URL else {},
    echo=False,  # Set to True for SQL query logging
)

# Create session factory bound to our engine
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for getting database sessions.
    Automatically handles cleanup and closing of connections.
    """
    db = SessionLocal()
    try:
        # Provide session to the endpoint
        yield db
    finally:
        # Always close the session after use
        db.close()