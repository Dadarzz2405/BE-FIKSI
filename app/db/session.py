# Database session configuration and management

from typing import Generator
import socket

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import DATABASE_URL


def _install_ipv4_dns_override_for_db_host(database_url: str) -> None:
    """
    Force IPv4 DNS resolution for the database hostname only.

    Render free instances may not support outbound IPv6, while some managed DB
    hostnames resolve AAAA records first. This override is intentionally scoped
    to the DB host so the rest of the application keeps default DNS behavior.
    """
    if "postgresql" not in database_url:
        return

    db_host = make_url(database_url).host
    if not db_host:
        return

    original_getaddrinfo = socket.getaddrinfo

    # Avoid stacking wrappers on module reload.
    if getattr(original_getaddrinfo, "_db_ipv4_override", False):
        return

    def _getaddrinfo_ipv4_only_for_db(host, port, family=0, type=0, proto=0, flags=0):
        if host == db_host:
            # Restrict DB host resolution to IPv4 only.
            return original_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
        return original_getaddrinfo(host, port, family, type, proto, flags)

    setattr(_getaddrinfo_ipv4_only_for_db, "_db_ipv4_override", True)
    socket.getaddrinfo = _getaddrinfo_ipv4_only_for_db


# Apply DNS override before any DB connections/engine creation.
_install_ipv4_dns_override_for_db_host(DATABASE_URL)


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
