"""
Script Name  : user.py
Description  : Pydantic schemas for User model (request/response validation)
Author       : @tonybnya
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from uuid import UUID


class UserBase(BaseModel):
    """
    Base user schema with common attributes.
    """

    username: str = Field(
        ...,
        min_length=3,
        max_length=100,
        description="Unique username for the user",
        examples=["johndoe"],
    )
    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )


class UserCreate(UserBase):
    """
    Schema for creating a new user (registration).
    """

    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="User's password (min 8 characters)",
        examples=["SecurePass123!"],
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Validate password strength.
        """
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters long")
        return v


class UserLogin(BaseModel):
    """
    Schema for user login.
    """

    email: EmailStr = Field(
        ...,
        description="User's email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=1,
        description="User's password",
        examples=["SecurePass123!"],
    )


class UserUpdate(BaseModel):
    """
    Schema for updating user profile.
    All fields are optional to allow partial updates.
    """

    username: Optional[str] = Field(
        None,
        min_length=3,
        max_length=100,
        description="New username",
    )
    email: Optional[EmailStr] = Field(
        None,
        description="New email address",
    )
    password: Optional[str] = Field(
        None,
        min_length=8,
        max_length=100,
        description="New password",
    )


class UserResponse(UserBase):
    """
    Schema for user response (returned from API).
    Excludes password for security.
    """

    id: UUID = Field(
        ...,
        description="User's unique identifier",
    )
    is_active: bool = Field(
        ...,
        description="Whether the user account is active",
    )
    created_at: datetime = Field(
        ...,
        description="When user was created",
    )
    updated_at: datetime = Field(
        ...,
        description="When user was last updated",
    )

    class Config:
        """
        Pydantic config.
        """

        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "username": "johndoe",
                "email": "user@example.com",
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        }


class Token(BaseModel):
    """
    Schema for JWT token response.
    """

    access_token: str = Field(
        ...,
        description="JWT access token",
    )
    token_type: str = Field(
        default="bearer",
        description="Token type",
    )
    expires_in: int = Field(
        ...,
        description="Token expiration time in seconds",
    )


class TokenData(BaseModel):
    """
    Schema for decoded token data.
    """

    user_id: Optional[UUID] = None
    email: Optional[EmailStr] = None


class UserInDB(UserBase):
    """
    Schema for user data from database (internal use).
    Includes hashed password for authentication.
    """

    id: UUID
    hashed_password: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
