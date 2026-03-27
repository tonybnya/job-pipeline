"""
Script Name  : auth.py
Description  : Authentication dependencies for protecting routes with JWT
Author       : @tonybnya
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from uuid import UUID
from typing import Optional

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token

# OAuth2 scheme for token URL
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", scheme_name="JWT")


def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.

    Args:
        token: JWT token from Authorization header
        db: Database session

    Returns:
        User: The authenticated user

    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and validate JWT token
        payload = decode_token(token)
        if payload is None:
            raise credentials_exception

        # Extract user ID from token
        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            raise credentials_exception

        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if user is None:
            raise credentials_exception

        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is disabled",
            )

        return user

    except JWTError:
        raise credentials_exception


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Dependency to ensure user is active (already checked in get_current_user).

    Args:
        current_user: The authenticated user

    Returns:
        User: The active user

    Raises:
        HTTPException: If user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


def get_optional_user(
    token: Optional[str] = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Dependency to optionally get the current user.
    Returns None if no token provided or token is invalid.

    Args:
        token: JWT token from Authorization header (optional)
        db: Database session

    Returns:
        Optional[User]: The authenticated user or None
    """
    if not token:
        return None

    try:
        payload = decode_token(token)
        if payload is None:
            return None

        user_id: Optional[str] = payload.get("sub")
        if user_id is None:
            return None

        user = db.query(User).filter(User.id == user_id).first()
        return user

    except Exception:
        return None
