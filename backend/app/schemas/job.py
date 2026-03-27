"""
Script Name  : job.py
Description  : Pydantic schemas for JobApplication model with pagination and filtering
Author       : @tonybnya
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from enum import Enum as PythonEnum


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
    """Application status enumeration."""

    OPENED = "opened"
    UNOPENED = "unopened"


class JobApplicationBase(BaseModel):
    """
    Base job application schema with common attributes.
    """

    role: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Job title/position",
        examples=["Senior Software Engineer"],
    )
    company: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Company name",
        examples=["Google"],
    )
    location: Optional[str] = Field(
        None,
        max_length=255,
        description="Job location (city, country, or remote)",
        examples=["Mountain View, CA"],
    )
    job_type: Optional[JobType] = Field(
        None,
        description="Type of job",
    )
    stage: JobStage = Field(
        default=JobStage.APPLIED,
        description="Current application stage",
    )
    status: ApplicationStatus = Field(
        default=ApplicationStatus.UNOPENED,
        description="Whether application email was opened/unopened",
    )
    salary_range: Optional[str] = Field(
        None,
        max_length=100,
        description="Salary range for the position",
        examples=["$150k-$200k"],
    )
    url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to job posting",
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes about the application",
    )


class JobApplicationCreate(JobApplicationBase):
    """
    Schema for creating a new job application.
    """

    pass


class JobApplicationUpdate(BaseModel):
    """
    Schema for updating a job application.
    All fields are optional to allow partial updates.
    """

    role: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Job title/position",
    )
    company: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="Company name",
    )
    location: Optional[str] = Field(
        None,
        max_length=255,
        description="Job location",
    )
    job_type: Optional[JobType] = Field(
        None,
        description="Type of job",
    )
    stage: Optional[JobStage] = Field(
        None,
        description="Current application stage",
    )
    status: Optional[ApplicationStatus] = Field(
        None,
        description="Application status",
    )
    follow_ups_sent: Optional[int] = Field(
        None,
        ge=0,
        description="Number of follow-up emails sent",
    )
    salary_range: Optional[str] = Field(
        None,
        max_length=100,
        description="Salary range",
    )
    url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL to job posting",
    )
    notes: Optional[str] = Field(
        None,
        description="Additional notes",
    )


class JobApplicationResponse(JobApplicationBase):
    """
    Schema for job application response (returned from API).
    Includes all fields from database.
    """

    id: UUID = Field(
        ...,
        description="Job application unique identifier",
    )
    user_id: UUID = Field(
        ...,
        description="User ID who owns this application",
    )
    follow_ups_sent: int = Field(
        ...,
        description="Number of follow-up emails sent",
    )
    created_at: datetime = Field(
        ...,
        description="When application was submitted",
    )
    updated_at: datetime = Field(
        ...,
        description="When application was last updated",
    )

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "123e4567-e89b-12d3-a456-426614174001",
                "role": "Senior Software Engineer",
                "company": "Google",
                "location": "Mountain View, CA",
                "job_type": "remote",
                "stage": "interview",
                "status": "opened",
                "follow_ups_sent": 1,
                "salary_range": "$150k-$200k",
                "url": "https://careers.google.com/...",
                "notes": "Applied through referral",
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-16T14:20:00Z",
            }
        }


class PaginationCursor(BaseModel):
    """
    Schema for cursor-based pagination response.
    """

    next_cursor: Optional[str] = Field(
        None,
        description="Cursor for next page",
    )
    has_more: bool = Field(
        ...,
        description="Whether there are more results",
    )
    total_count: int = Field(
        ...,
        description="Total number of results",
    )


class JobListResponse(BaseModel):
    """
    Schema for paginated list of job applications.
    """

    data: List[JobApplicationResponse] = Field(
        ...,
        description="List of job applications",
    )
    pagination: PaginationCursor = Field(
        ...,
        description="Pagination information",
    )


class JobQueryParams(BaseModel):
    """
    Schema for job query parameters (filtering & sorting).
    Used for request validation in GET /api/v1/jobs endpoint.
    """

    cursor: Optional[str] = Field(
        None,
        description="Pagination cursor",
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page (default: 20, max: 100)",
    )
    stage: Optional[JobStage] = Field(
        None,
        description="Filter by application stage",
    )
    company: Optional[str] = Field(
        None,
        description="Filter by company name (partial match)",
    )
    location: Optional[str] = Field(
        None,
        description="Filter by location",
    )
    job_type: Optional[JobType] = Field(
        None,
        description="Filter by job type",
    )
    status: Optional[ApplicationStatus] = Field(
        None,
        description="Filter by application status",
    )
    sort: Optional[str] = Field(
        default="-created_at",
        description="Sort fields (prefix - for descending). Example: -created_at,company",
    )

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, v: Optional[str]) -> Optional[str]:
        """Validate sort parameter format."""
        if v is None:
            return "-created_at"
        # Allow comma-separated fields with optional - prefix
        fields = v.split(",")
        for field in fields:
            clean_field = field.lstrip("-")
            if not clean_field.isalnum() and "_" not in clean_field:
                raise ValueError(f"Invalid sort field: {field}")
        return v


class StageCounts(BaseModel):
    """
    Schema for application counts by stage.
    """

    applied: int = Field(default=0, description="Applications in 'applied' stage")
    screening: int = Field(default=0, description="Applications in 'screening' stage")
    interview: int = Field(default=0, description="Applications in 'interview' stage")
    offer: int = Field(default=0, description="Applications in 'offer' stage")
    rejected: int = Field(default=0, description="Applications in 'rejected' stage")
    ghosted: int = Field(default=0, description="Applications in 'ghosted' stage")
    withdrawn: int = Field(default=0, description="Applications in 'withdrawn' stage")


class JobStatistics(BaseModel):
    """
    Schema for job application statistics.
    """

    # Total count
    total_applications: int = Field(
        ...,
        description="Total number of applications",
    )

    # Stage breakdown
    by_stage: StageCounts = Field(
        ...,
        description="Count of applications by each stage",
    )

    # Active vs Closed
    active_applications: int = Field(
        ...,
        description="Applications in active stages (applied, screening, interview)",
    )
    closed_applications: int = Field(
        ...,
        description="Applications in closed stages (rejected, ghosted, withdrawn)",
    )

    # Open rate (email tracking)
    opened_count: int = Field(
        ...,
        description="Number of applications where email was opened",
    )
    unopened_count: int = Field(
        ...,
        description="Number of applications where email was not opened",
    )
    open_rate: float = Field(
        ...,
        description="Percentage of applications that were opened",
    )

    # Interview metrics
    interviews_count: int = Field(
        ...,
        description="Number of applications that reached interview stage",
    )
    interview_rate: float = Field(
        ...,
        description="Percentage of applications that reached interview stage",
    )

    # Offers
    offers_count: int = Field(
        ...,
        description="Number of applications that received offers",
    )
    offer_rate: float = Field(
        ...,
        description="Percentage of applications that received offers",
    )

    # Follow-ups needed
    need_follow_up: int = Field(
        ...,
        description="Applications that need follow-up (unopened after 7 days with no response)",
    )
    follow_up_rate: float = Field(
        ...,
        description="Percentage of applications that need follow-up",
    )

    # Response metrics
    responses_count: int = Field(
        ...,
        description="Number of applications with responses (any stage beyond applied)",
    )
    response_rate: float = Field(
        ...,
        description="Percentage of applications with responses",
    )

    # Time-based metrics
    average_days_to_response: Optional[float] = Field(
        None,
        description="Average days to get first response",
    )
    applications_this_week: int = Field(
        ...,
        description="Applications submitted this week",
    )
    applications_this_month: int = Field(
        ...,
        description="Applications submitted this month",
    )
    by_stage: dict = Field(
        ...,
        description="Count of applications by stage",
    )
    by_status: dict = Field(
        ...,
        description="Count of applications by status",
    )
    response_rate: float = Field(
        ...,
        description="Percentage of applications with responses",
    )
