"""
Script Name  : config.py
Description  : Configuration settings using Pydantic Settings
Author       : @tonybnya
"""

from functools import lru_cache
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, validator


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Supports both local development and production (Neon/Upstash).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database Configuration
    # Development (SQLite)
    DEV_DATABASE_URL: str = Field(
        default="sqlite:///./jobs.db",
        description="Development database URL (SQLite)",
    )

    # Testing (SQLite in-memory or file)
    TEST_DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Testing database URL (defaults to SQLite in-memory if not set)",
    )

    # Production (Neon PostgreSQL)
    PROD_DATABASE_URL: Optional[str] = Field(
        default=None,
        description="Production Neon PostgreSQL connection URL",
    )

    # Security
    SECRET_KEY: str = Field(
        default="your-super-secret-key-change-in-production",
        description="Secret key for JWT token generation",
    )
    ALGORITHM: str = Field(
        default="HS256",
        description="JWT algorithm",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=1440,
        description="Access token expiration time in minutes (24 hours)",
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=7,
        description="Refresh token expiration time in days",
    )

    # Rate Limiting - Redis Configuration
    # Local Redis for development, Upstash for production
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        description="Local Redis URL for development",
    )

    # Upstash Redis (Production)
    UPSTASH_REDIS_URL: Optional[str] = Field(
        default=None,
        description="Upstash Redis URL (rediss://...)",
    )
    UPSTASH_REDIS_TOKEN: Optional[str] = Field(
        default=None,
        description="Upstash Redis token",
    )

    RATE_LIMIT_PER_MINUTE: int = Field(
        default=100,
        description="Rate limit per minute for authenticated users",
    )
    RATE_LIMIT_AUTH_PER_MINUTE: int = Field(
        default=5,
        description="Rate limit per minute for auth endpoints",
    )

    # CORS
    CORS_ORIGINS: str = Field(
        default="http://localhost:5173,http://localhost:3000",
        description="Comma-separated list of allowed origins",
    )

    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if isinstance(self.CORS_ORIGINS, str):
            return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
        return self.CORS_ORIGINS

    @property
    def effective_database_url(self) -> str:
        """
        Return the effective database URL.
        Uses Neon in production if available, otherwise SQLite.
        """
        if self.PROD_DATABASE_URL:
            return self.PROD_DATABASE_URL
        return self.DEV_DATABASE_URL

    @property
    def effective_redis_url(self) -> str:
        """
        Return the effective Redis URL.
        Uses Upstash in production if available, otherwise local Redis.
        """
        if self.UPSTASH_REDIS_URL:
            return self.UPSTASH_REDIS_URL
        return self.REDIS_URL

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.PROD_DATABASE_URL is not None


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to avoid reloading settings on every request.
    """
    return Settings()


# Global settings instance
settings = get_settings()
