"""
Script Name  : conftest.py
Description  : Pytest fixtures for testing
Author       : @tonybnya
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import settings
from app.database import Base, get_db
from app.main import app

# Use TEST_DATABASE_URL from environment variables, fallback to in-memory SQLite
SQLALCHEMY_DATABASE_URL = settings.TEST_DATABASE_URL or "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override get_db dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create a fresh database session for each test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database session."""

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    del app.dependency_overrides[get_db]


@pytest.fixture(scope="function")
def test_user(client):
    """Create a test user and return user data with token."""
    user_data = {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
    }

    # Register user
    response = client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201

    # Login to get token
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": user_data["email"], "password": user_data["password"]},
    )
    assert login_response.status_code == 200

    token_data = login_response.json()

    return {
        "user": response.json(),
        "token": token_data["access_token"],
        "token_type": token_data["token_type"],
        "headers": {"Authorization": f"Bearer {token_data['access_token']}"},
    }
