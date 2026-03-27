"""
Script Name  : test_health.py
Description  : Tests for health check endpoints
Author       : @tonybnya
"""

import pytest


class TestHealthCheck:
    """Test health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns welcome message."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "documentation" in data
        assert "version" in data
        assert data["version"] == "v1.0.0"

    def test_health_endpoint(self, client):
        """Test health endpoint returns healthy status."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
