"""
Script Name  : database.py
Description  : Database connection, session management, and SQLAlchemy setup.
               Supports SQLite (Development) and PostgreSQL on Neon (Production).
Author       : @tonybnya
"""

from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

from app.config import settings


# Database engine configuration based on environment
if settings.is_production:
    # Production: PostgreSQL on Neon with SSL
    engine = create_engine(
        settings.effective_database_url,
        pool_pre_ping=True,  # Verify connections before using
        pool_size=10,  # Maximum number of connections
        max_overflow=20,  # Additional connections when pool exhausted
        pool_recycle=1800,  # Recycle connections after 30 minutes
    )
else:
    # Development: SQLite
    engine = create_engine(
        settings.effective_database_url,
        connect_args={
            "check_same_thread": False,  # Required for SQLite in multi-threaded
        },
        poolclass=StaticPool,  # Use static pool for SQLite
        echo=False,  # Set to True for SQL query logging
    )

    # Enable foreign key support for SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


# Session factory
SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit transactions
    autoflush=False,  # Don't auto-flush before queries
    bind=engine,  # Bind to our configured engine
)


# Base class for declarative models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session.

    Yields a database session that is automatically closed after use.
    This ensures proper resource cleanup even if exceptions occur.

    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()

    Yields:
        Session: SQLAlchemy database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """
    Create a new database session (for use outside FastAPI dependencies).

    Returns:
        Session: SQLAlchemy database session

    Note:
        Caller is responsible for closing the session using db.close()
    """
    return SessionLocal()


def init_db() -> None:
    """
    Initialize the database by creating all tables.

    This is useful for development setup but should NOT be used in production.
    In production, use Alembic migrations instead.

    Usage:
        # In development only
        init_db()
    """
    # Import all models to ensure they're registered with Base
    from app.models.user import User
    from app.models.job import JobApplication

    Base.metadata.create_all(bind=engine)


def check_db_connection() -> bool:
    """
    Check if database connection is working.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False


# Connection pool monitoring (optional, useful for debugging)
def get_pool_status() -> dict:
    """
    Get current connection pool status (PostgreSQL only).

    Returns:
        dict: Pool status information
    """
    if settings.is_production:
        return {
            "pool_size": engine.pool.size(),
            "checked_in": engine.pool.checkedin(),
            "checked_out": engine.pool.checkedout(),
        }
    return {"message": "Connection pooling not available for SQLite"}
