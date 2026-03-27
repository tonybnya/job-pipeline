"""
Script Name  : test_auth.py
Description  : Tests for authentication endpoints
Author       : @tonybnya
"""

import pytest
from fastapi import status


class TestAuthRegistration:
    """Test user registration endpoint."""

    def test_register_user_success(self, client):
        """Test successful user registration."""
        user_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_201_CREATED

        data = response.json()
        assert "id" in data
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert "hashed_password" not in data
        assert "password" not in data
        assert data["is_active"] is True
        assert "created_at" in data
        assert "updated_at" in data

    def test_register_duplicate_email(self, client, test_user):
        """Test registration with duplicate email fails."""
        user_data = {
            "email": test_user["user"]["email"],
            "username": "differentusername",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "detail" in response.json()

    def test_register_duplicate_username(self, client, test_user):
        """Test registration with duplicate username fails."""
        user_data = {
            "email": "different@example.com",
            "username": test_user["user"]["username"],
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_409_CONFLICT
        assert "detail" in response.json()

    def test_register_weak_password(self, client):
        """Test registration with weak password fails."""
        user_data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_invalid_email(self, client):
        """Test registration with invalid email fails."""
        user_data = {
            "email": "invalid-email",
            "username": "testuser",
            "password": "StrongPass123!",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestAuthLogin:
    """Test user login endpoint."""

    def test_login_success(self, client, test_user):
        """Test successful login with valid credentials."""
        login_data = {
            "username": test_user["user"]["email"],
            "password": "TestPassword123!",
        }

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data
        assert data["expires_in"] > 0

    def test_login_wrong_password(self, client, test_user):
        """Test login with wrong password fails."""
        login_data = {
            "username": test_user["user"]["email"],
            "password": "WrongPassword123!",
        }

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user fails."""
        login_data = {
            "username": "nonexistent@example.com",
            "password": "AnyPassword123!",
        }

        response = client.post("/api/v1/auth/login", data=login_data)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "detail" in response.json()


class TestAuthLogout:
    """Test logout endpoint."""

    def test_logout(self, client, test_user):
        """Test logout endpoint."""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "action" in data
