"""
Script Name  : jobs.py
Description  : Job applications router with CRUD, pagination, filtering, and statistics
Author       : @tonybnya
"""

import base64
import json
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy import desc, asc, func

from app.config import settings
from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.job import JobApplication, JobStage, JobType, ApplicationStatus
from app.models.user import User
from app.schemas.job import (
    JobApplicationCreate,
    JobApplicationResponse,
    JobApplicationUpdate,
    JobListResponse,
    JobQueryParams,
    JobStatistics,
    StageCounts,
)

router = APIRouter(tags=["Job Applications"])
limiter = Limiter(key_func=get_remote_address)


def encode_cursor(job_id: str) -> str:
    """Encode job ID to base64 cursor."""
    cursor_data = {"id": job_id}
    return base64.b64encode(json.dumps(cursor_data).encode()).decode()


def decode_cursor(cursor: str) -> dict:
    """Decode base64 cursor to get pagination info."""
    try:
        return json.loads(base64.b64decode(cursor.encode()).decode())
    except Exception:
        return None


@router.get(
    "/",
    response_model=JobListResponse,
    summary="List job applications",
    description="Get all job applications for the authenticated user with pagination, filtering, and sorting.",
)
async def list_jobs(
    cursor: Optional[str] = Query(None, description="Pagination cursor"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    stage: Optional[JobStage] = Query(None, description="Filter by stage"),
    company: Optional[str] = Query(None, description="Filter by company"),
    location: Optional[str] = Query(None, description="Filter by location"),
    job_type: Optional[JobType] = Query(None, description="Filter by job type"),
    status: Optional[ApplicationStatus] = Query(None, description="Filter by status"),
    sort: str = Query("-created_at", description="Sort by field(s)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all job applications for the authenticated user.

    Supports:
    - **Cursor-based pagination** (use cursor parameter)
    - **Filtering** (stage, company, location, job_type, status)
    - **Sorting** (prefix with - for descending, e.g., -created_at)
    """
    query = db.query(JobApplication).filter(
        JobApplication.user_id == str(current_user.id)
    )

    # Apply filters
    if stage:
        query = query.filter(JobApplication.stage == stage)
    if company:
        query = query.filter(JobApplication.company.ilike(f"%{company}%"))
    if location:
        query = query.filter(JobApplication.location.ilike(f"%{location}%"))
    if job_type:
        query = query.filter(JobApplication.job_type == job_type)
    if status:
        query = query.filter(JobApplication.status == status)

    # Get total count before pagination
    total_count = query.count()

    # Apply cursor-based pagination
    if cursor:
        cursor_data = decode_cursor(cursor)
        if cursor_data and "id" in cursor_data:
            query = query.filter(JobApplication.id > cursor_data["id"])

    # Apply sorting
    sort_fields = sort.split(",")
    for field in sort_fields:
        if field.startswith("-"):
            query = query.order_by(desc(getattr(JobApplication, field[1:])))
        else:
            query = query.order_by(asc(getattr(JobApplication, field)))

    # Get results with limit
    jobs = query.limit(limit + 1).all()

    # Check if there are more results
    has_more = len(jobs) > limit
    if has_more:
        jobs = jobs[:-1]  # Remove extra item

    # Generate next cursor
    next_cursor = None
    if has_more and jobs:
        next_cursor = encode_cursor(jobs[-1].id)

    return {
        "data": jobs,
        "pagination": {
            "next_cursor": next_cursor,
            "has_more": has_more,
            "total_count": total_count,
        },
    }


@router.post(
    "/",
    response_model=JobApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create job application",
    description="Create a new job application.",
)
async def create_job(
    job_data: JobApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new job application.

    - **role**: Job title/position (required)
    - **company**: Company name (required)
    - **location**: Job location (optional)
    - **job_type**: Type of job (optional)
    - **stage**: Application stage (default: applied)
    - **status**: Email status (default: unopened)
    - **salary_range**: Salary information (optional)
    - **url**: Job posting URL (optional)
    - **notes**: Additional notes (optional)
    """
    db_job = JobApplication(
        user_id=str(current_user.id),
        role=job_data.role,
        company=job_data.company,
        location=job_data.location,
        job_type=job_data.job_type,
        stage=job_data.stage,
        status=job_data.status,
        salary_range=job_data.salary_range,
        url=job_data.url,
        notes=job_data.notes,
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


@router.get(
    "/{job_id}",
    response_model=JobApplicationResponse,
    summary="Get job application",
    description="Get a specific job application by ID.",
)
async def get_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get a specific job application by ID.
    """
    job = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == str(job_id),
            JobApplication.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )

    return job


@router.put(
    "/{job_id}",
    response_model=JobApplicationResponse,
    summary="Update job application",
    description="Full update of a job application (all fields required).",
)
async def update_job(
    job_id: UUID,
    job_data: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Full update of a job application.
    All fields must be provided.
    """
    job = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == str(job_id),
            JobApplication.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )

    # Update all fields
    for field, value in job_data.model_dump(exclude_unset=True).items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job


@router.patch(
    "/{job_id}",
    response_model=JobApplicationResponse,
    summary="Partial update job application",
    description="Partial update of a job application (only provided fields updated).",
)
async def patch_job(
    job_id: UUID,
    job_data: JobApplicationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partial update of a job application.
    Only provided fields will be updated.
    """
    job = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == str(job_id),
            JobApplication.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )

    # Update only provided fields
    update_data = job_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(job, field, value)

    db.commit()
    db.refresh(job)

    return job


@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete job application",
    description="Delete a job application by ID.",
)
async def delete_job(
    job_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete a job application.
    """
    job = (
        db.query(JobApplication)
        .filter(
            JobApplication.id == str(job_id),
            JobApplication.user_id == str(current_user.id),
        )
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job application not found",
        )

    db.delete(job)
    db.commit()

    return None


@router.get(
    "/stats",
    response_model=JobStatistics,
    summary="Get job statistics",
    description="Get comprehensive statistics about job applications.",
)
async def get_statistics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive job application statistics.

    Returns:
    - Total applications
    - Applications by stage
    - Open rate
    - Interview rate
    - Offer rate
    - Follow-ups needed
    - Response rate
    - Time-based metrics
    """
    # Base query for user's jobs
    base_query = db.query(JobApplication).filter(
        JobApplication.user_id == str(current_user.id)
    )

    total = base_query.count()

    if total == 0:
        return JobStatistics(
            total_applications=0,
            by_stage=StageCounts(),
            active_applications=0,
            closed_applications=0,
            opened_count=0,
            unopened_count=0,
            open_rate=0.0,
            interviews_count=0,
            interview_rate=0.0,
            offers_count=0,
            offer_rate=0.0,
            need_follow_up=0,
            follow_up_rate=0.0,
            responses_count=0,
            response_rate=0.0,
            average_days_to_response=None,
            applications_this_week=0,
            applications_this_month=0,
        )

    # Count by stage
    stage_counts = {}
    for stage in JobStage:
        count = base_query.filter(JobApplication.stage == stage).count()
        stage_counts[stage.value] = count

    # Active vs Closed
    active_stages = [JobStage.APPLIED, JobStage.SCREENING, JobStage.INTERVIEW]
    active_count = base_query.filter(JobApplication.stage.in_(active_stages)).count()
    closed_count = total - active_count

    # Open rate
    opened_count = base_query.filter(
        JobApplication.status == ApplicationStatus.OPENED
    ).count()
    unopened_count = total - opened_count
    open_rate = (opened_count / total) * 100 if total > 0 else 0.0

    # Interview metrics
    interviews_count = base_query.filter(
        JobApplication.stage == JobStage.INTERVIEW
    ).count()
    interview_rate = (interviews_count / total) * 100 if total > 0 else 0.0

    # Offers
    offers_count = base_query.filter(JobApplication.stage == JobStage.OFFER).count()
    offer_rate = (offers_count / total) * 100 if total > 0 else 0.0

    # Need follow-up (unopened after 7 days with no response)
    seven_days_ago = datetime.utcnow() - timedelta(days=7)
    need_follow_up = base_query.filter(
        JobApplication.status == ApplicationStatus.UNOPENED,
        JobApplication.created_at < seven_days_ago,
        JobApplication.stage.in_([JobStage.APPLIED, JobStage.SCREENING]),
    ).count()
    follow_up_rate = (need_follow_up / total) * 100 if total > 0 else 0.0

    # Response rate (any stage beyond applied)
    response_count = base_query.filter(JobApplication.stage != JobStage.APPLIED).count()
    response_rate = (response_count / total) * 100 if total > 0 else 0.0

    # Time-based metrics
    one_week_ago = datetime.utcnow() - timedelta(days=7)
    one_month_ago = datetime.utcnow() - timedelta(days=30)

    applications_this_week = base_query.filter(
        JobApplication.created_at >= one_week_ago
    ).count()

    applications_this_month = base_query.filter(
        JobApplication.created_at >= one_month_ago
    ).count()

    return JobStatistics(
        total_applications=total,
        by_stage=StageCounts(**stage_counts),
        active_applications=active_count,
        closed_applications=closed_count,
        opened_count=opened_count,
        unopened_count=unopened_count,
        open_rate=round(open_rate, 2),
        interviews_count=interviews_count,
        interview_rate=round(interview_rate, 2),
        offers_count=offers_count,
        offer_rate=round(offer_rate, 2),
        need_follow_up=need_follow_up,
        follow_up_rate=round(follow_up_rate, 2),
        responses_count=response_count,
        response_rate=round(response_rate, 2),
        average_days_to_response=None,  # Would require more complex calculation
        applications_this_week=applications_this_week,
        applications_this_month=applications_this_month,
    )
