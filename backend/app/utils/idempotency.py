"""
Script Name  : idempotency.py
Description  : Idempotency key handling for preventing duplicate operations
Author       : @tonybnya
"""

import hashlib
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.config import settings


def generate_idempotency_key() -> str:
    """
    Generate a new unique idempotency key.

    Returns:
        str: UUID v4 string
    """
    return str(uuid.uuid4())


def hash_request_body(request_body: dict) -> str:
    """
    Hash the request body to detect changes.

    Args:
        request_body: The request body dictionary

    Returns:
        str: SHA-256 hash of the request body
    """
    body_str = json.dumps(request_body, sort_keys=True)
    return hashlib.sha256(body_str.encode()).hexdigest()


def get_cache_key(idempotency_key: str, user_id: str) -> str:
    """
    Generate a unique cache key for idempotency.

    Args:
        idempotency_key: The idempotency key from request
        user_id: The user ID

    Returns:
        str: Unique cache key
    """
    return f"idempotency:{user_id}:{idempotency_key}"


# In-memory cache for development (use Redis in production)
_idempotency_cache: dict = {}


def get_cached_response(
    idempotency_key: str, user_id: str, request_body_hash: str
) -> Optional[dict]:
    """
    Check if a cached response exists for this idempotency key.

    Args:
        idempotency_key: The idempotency key from request
        user_id: The user ID
        request_body_hash: Hash of the current request body

    Returns:
        Optional[dict]: The cached response if found and request matches, None otherwise

    Raises:
        HTTPException: If request body hash doesn't match (different payload)
    """
    cache_key = get_cache_key(idempotency_key, user_id)

    if cache_key in _idempotency_cache:
        cached = _idempotency_cache[cache_key]

        # Check if cache has expired
        if cached["expires_at"] < datetime.utcnow():
            del _idempotency_cache[cache_key]
            return None

        # Check if request body hash matches
        if cached["request_body_hash"] != request_body_hash:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key already used with different payload",
            )

        return cached["response"]

    return None


def cache_response(
    idempotency_key: str,
    user_id: str,
    request_body_hash: str,
    response: dict,
    expires_hours: int = 24,
) -> None:
    """
    Cache the response for idempotency.

    Args:
        idempotency_key: The idempotency key from request
        user_id: The user ID
        request_body_hash: Hash of the request body
        response: The response to cache
        expires_hours: How long to cache (default: 24 hours)
    """
    cache_key = get_cache_key(idempotency_key, user_id)

    _idempotency_cache[cache_key] = {
        "request_body_hash": request_body_hash,
        "response": response,
        "expires_at": datetime.utcnow() + timedelta(hours=expires_hours),
    }


def clean_expired_cache() -> int:
    """
    Clean expired entries from the idempotency cache.

    Returns:
        int: Number of entries removed
    """
    now = datetime.utcnow()
    expired_keys = [
        key for key, value in _idempotency_cache.items() if value["expires_at"] < now
    ]

    for key in expired_keys:
        del _idempotency_cache[key]

    return len(expired_keys)


class IdempotencyContext:
    """
    Context manager for idempotency key handling.

    Usage:
        with IdempotencyContext(idempotency_key, user_id, request_body) as ctx:
            if ctx.cached_response:
                return ctx.cached_response

            # Perform operation
            result = create_resource(...)

            # Cache the response
            ctx.set_response(result)
            return result
    """

    def __init__(
        self,
        idempotency_key: Optional[str],
        user_id: str,
        request_body: Optional[dict] = None,
    ):
        self.idempotency_key = idempotency_key
        self.user_id = user_id
        self.request_body = request_body or {}
        self.request_body_hash = (
            hash_request_body(self.request_body) if request_body else ""
        )
        self.cached_response: Optional[dict] = None
        self._should_cache = False

    def __enter__(self):
        """
        Enter context and check for cached response.
        """
        if self.idempotency_key:
            self.cached_response = get_cached_response(
                self.idempotency_key, self.user_id, self.request_body_hash
            )
            self._should_cache = True

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit context (cleanup if needed).
        """
        pass

    def set_response(self, response: dict) -> None:
        """
        Cache the response if idempotency key was provided.

        Args:
            response: The response to cache
        """
        if self._should_cache and self.idempotency_key:
            cache_response(
                self.idempotency_key, self.user_id, self.request_body_hash, response
            )
