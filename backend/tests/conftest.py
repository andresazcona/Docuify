"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture
def app():
    """Create test application instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)
