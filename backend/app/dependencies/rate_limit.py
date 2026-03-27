"""
Script Name  : rate_limit.py
Description  : Rate limiting configuration using slowapi
Author       : @tonybnya
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Create limiter instance
# Uses client IP address as the rate limiting key
rate_limiter = Limiter(key_func=get_remote_address)


def get_rate_limit_headers(limit: int, remaining: int, reset_time: int) -> dict:
    """
    Generate rate limit headers for responses.

    Args:
        limit: Maximum requests allowed
        remaining: Remaining requests
        reset_time: Unix timestamp when limit resets

    Returns:
        dict: Rate limit headers
    """
    return {
        "X-RateLimit-Limit": str(limit),
        "X-RateLimit-Remaining": str(remaining),
        "X-RateLimit-Reset": str(reset_time),
    }
