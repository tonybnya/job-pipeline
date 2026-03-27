"""
Script Name  : job.py
Description  : SQLAlchemy JobApplication model for tracking job applications
Author       : @tonybnya
"""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from enum import Enum as PythonEnum

from app.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class JobType(str, PythonEnum):
    """Job type enumeration."""

    REMOTE = "remote"
    HYBRID = "hybrid"
    ON_SITE = "on-site"
    PART_TIME = "part-time"
    CONTRACT = "contract"
    FREELANCE = "freelance"
    INTERNSHIP = "internship"


class JobStage(str, PythonEnum):
    """Job application stage enumeration."""

    APPLIED = "applied"
    SCREENING = "screening"
    INTERVIEW = "interview"
    OFFER = "offer"
    REJECTED = "rejected"
    GHOSTED = "ghosted"
    WITHDRAWN = "withdrawn"


class ApplicationStatus(str, PythonEnum):
    """Application status enumeration (opened/unopened)."""

    OPENED = "opened"
    UNOPENED = "unopened"


class JobApplication(Base):
    """
    JobApplication model for tracking job applications.

    Attributes:
        id: Primary key UUID
        user_id: Foreign key to User
        role: Job title/position
        company: Company name
        location: Job location (city, country, or remote)
        job_type: Type of job (remote, hybrid, etc.)
        stage: Current application stage
        status: Whether application was opened/unopened
        follow_ups_sent: Number of follow-up emails sent
        notes: Additional notes about the application
        url: URL to job posting
        salary_range: Salary range for the position
        created_at: When application was created (date applied)
        updated_at: When application was last updated
        user: Relationship to User model
    """

    __tablename__ = "jobs"

    # Primary key with PostgreSQL UUID type (works with SQLite too)
    id: Mapped[str] = mapped_column(
        PostgreSQLUUID(as_uuid=False),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )

    # Foreign key to user
    user_id: Mapped[str] = mapped_column(
        PostgreSQLUUID(as_uuid=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Job details
    role: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Job title/position",
    )

    company: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Company name",
    )

    location: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Job location (city, country, or remote)",
    )

    job_type: Mapped[Optional[JobType]] = mapped_column(
        SQLEnum(JobType, name="jobtype", create_type=False),
        nullable=True,
        comment="Type of job (remote, hybrid, on-site, etc.)",
    )

    # Application tracking
    stage: Mapped[JobStage] = mapped_column(
        SQLEnum(JobStage, name="jobstage", create_type=False),
        nullable=False,
        default=JobStage.APPLIED,
        index=True,
        comment="Current application stage",
    )

    status: Mapped[ApplicationStatus] = mapped_column(
        SQLEnum(ApplicationStatus, name="applicationstatus", create_type=False),
        nullable=False,
        default=ApplicationStatus.UNOPENED,
        comment="Whether application email was opened/unopened",
    )

    follow_ups_sent: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of follow-up emails sent",
    )

    # Additional details
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="Additional notes about the application",
    )

    url: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        comment="URL to job posting",
    )

    salary_range: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        comment="Salary range for the position",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="When application was submitted",
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="When application was last updated",
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="jobs",
        lazy="joined",
    )

    def __repr__(self) -> str:
        """String representation of JobApplication."""
        return f"<JobApplication(id={self.id}, role={self.role}, company={self.company}, stage={self.stage})>"

    def to_dict(self) -> dict:
        """Convert job application to dictionary."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "role": self.role,
            "company": self.company,
            "location": self.location,
            "job_type": self.job_type.value if self.job_type else None,
            "stage": self.stage.value,
            "status": self.status.value,
            "follow_ups_sent": self.follow_ups_sent,
            "notes": self.notes,
            "url": self.url,
            "salary_range": self.salary_range,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
