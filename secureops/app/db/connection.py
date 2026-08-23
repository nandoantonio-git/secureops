"""Database engine and session management for SecureOps."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_db_session() -> Generator[Session, None, None]:
    """Yield a database session and close it after use."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


get_db = get_db_session


__all__ = ["Base", "SessionLocal", "engine", "get_db", "get_db_session"]
