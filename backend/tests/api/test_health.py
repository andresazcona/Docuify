"""Tests for health endpoints."""

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/healthz")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_readiness_check(client: AsyncClient) -> None:
    """Test readiness check endpoint."""
    response = await client.get("/readyz")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test root endpoint."""
    response = await client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_api_meta(client: AsyncClient) -> None:
    """Test API meta endpoint."""
    response = await client.get("/api/v1/meta")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "environment" in data
    assert "features" in data
    assert "limits" in data


@pytest.mark.asyncio
async def test_error_handling(client: AsyncClient) -> None:
    """Test error handling with non-existent endpoint."""
    response = await client.get("/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    # FastAPI's default 404 response has 'detail'
    assert "detail" in data
