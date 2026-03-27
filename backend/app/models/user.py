"""
Script Name  : user.py
Description  : SQLAlchemy User model for authentication and user management
Author       : @tonybnya
"""

import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.database import Base

if TYPE_CHECKING:
    from app.models.job import JobApplication


class User(Base):
    """
    User model for authentication and profile management.

    Attributes:
        id: Primary key UUID
        username: Unique username for the user
        email: Unique email address
        hashed_password: Bcrypt hashed password
        is_active: Whether the user account is active
        created_at: Timestamp when user was created
        updated_at: Timestamp when user was last updated
        jobs: Relationship to user's job applications
    """

    __tablename__ = "users"

    # Primary key with PostgreSQL UUID type (works with SQLite too)
    id: Mapped[str] = mapped_column(
        PostgreSQLUUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # User credentials
    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for the user",
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User's email address",
    )

    hashed_password: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password",
    )

    # Account status
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether the account is active",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when user was created",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when user was last updated",
    )

    # Relationships
    jobs: Mapped[List["JobApplication"]] = relationship(
        "JobApplication",
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    def __repr__(self) -> str:
        """String representation of User."""
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"

    def to_dict(self) -> dict:
        """Convert user to dictionary (excludes password)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
