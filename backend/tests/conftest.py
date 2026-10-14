"""Test configuration and fixtures."""

import asyncio
import os
import tempfile

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import get_settings
from app.main import create_app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_db():
    """Create a temporary database file for each test."""
    # Clear the settings cache to ensure fresh settings for each test
    get_settings.cache_clear()

    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)

    # Set the DATABASE_URL to use the temporary database
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"

    yield db_path

    # Cleanup
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]

    # Remove the temporary database file
    if os.path.exists(db_path):
        os.remove(db_path)

    # Clear the cache again after test
    get_settings.cache_clear()


@pytest.fixture
def app(test_db):
    """Create test application instance with isolated database."""
    return create_app()


@pytest_asyncio.fixture
async def client(app):
    """Create async test client with lifespan."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://testserver", follow_redirects=True
    ) as ac:
        # Manually trigger the lifespan by entering the app context
        async with app.router.lifespan_context(app):
            yield ac
