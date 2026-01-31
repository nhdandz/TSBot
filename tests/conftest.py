"""Pytest configuration and fixtures."""

import asyncio
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.api.main import app
from src.core.config import Settings, settings
from src.database.models import Base
from src.database.postgres import get_db_session


# Test settings override
@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Override settings for testing."""
    return Settings(
        app_env="test",
        debug=True,
        postgres_host="localhost",
        postgres_db="tsbot_test",
    )


# Async event loop
@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# In-memory SQLite database for testing
@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """Create test database session."""
    # Use in-memory SQLite for tests
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


# FastAPI test client
@pytest.fixture(scope="function")
def client(test_db) -> Generator[TestClient, None, None]:
    """Create test client."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db_session] = override_get_db

    with TestClient(app) as c:
        yield c

    app.dependency_overrides.clear()


# Async HTTP client
@pytest_asyncio.fixture(scope="function")
async def async_client(test_db) -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""

    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db_session] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# Sample data fixtures
@pytest.fixture
def sample_truong_data() -> dict:
    """Sample school data."""
    return {
        "ma_truong": "TEST001",
        "ten_truong": "Trường Test",
        "loai_truong": "quan_doi",
        "dia_chi": "123 Test Street",
    }


@pytest.fixture
def sample_nganh_data() -> dict:
    """Sample program data."""
    return {
        "ma_nganh": "TESTNGANH",
        "ten_nganh": "Ngành Test",
    }


@pytest.fixture
def sample_diem_chuan_data() -> dict:
    """Sample admission score data."""
    return {
        "nam": 2024,
        "diem_chuan": 25.5,
        "chi_tieu": 50,
    }
