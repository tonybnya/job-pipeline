"""
Script Name  : test_jobs.py
Description  : Tests for job applications endpoints
Author       : @tonybnya
"""

import pytest
from fastapi import status
from uuid import uuid4


class TestJobApplications:
    """Test job application CRUD operations."""

    @pytest.fixture
    def sample_job_data(self):
        """Sample job application data."""
        return {
            "role": "Senior Software Engineer",
            "company": "Google",
            "location": "Mountain View, CA",
            "job_type": "remote",
            "stage": "applied",
            "status": "unopened",
            "salary_range": "$150k-$200k",
            "url": "https://careers.google.com/jobs/123",
            "notes": "Applied through referral"
        }

    def test_create_job_success(self, client, test_user, sample_job_data):
        """Test successful job creation."""
        response = client.post(
            "/api/v1/jobs/",
            json=sample_job_data,
            headers=test_user["headers"]
        )
        assert response.status_code == status.HTTP_201_CREATED
        
        data = response.json()
        assert data["role"] == sample_job_data["role"]
        assert data["company"] == sample_job_data["company"]
        assert "id" in data

    def test_list_jobs_success(self, client, test_user, sample_job_data):
        """Test listing jobs with pagination."""
        client.post("/api/v1/jobs/", json=sample_job_data, headers=test_user["headers"])
        
        response = client.get("/api/v1/jobs/", headers=test_user["headers"])
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "data" in data
        assert "pagination" in data


class TestJobStatistics:
    """Test job statistics endpoint."""

    def test_get_statistics_success(self, client, test_user):
        """Test getting job statistics."""
        response = client.get("/api/v1/jobs/stats", headers=test_user["headers"])
        assert response.status_code == status.HTTP_200_OK
        
        data = response.json()
        assert "total_applications" in data
        assert "by_stage" in data
