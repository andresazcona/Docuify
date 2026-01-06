"""Tests for health endpoints."""
import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint."""
    response = client.get("/healthz")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data
    assert "timestamp" in data


def test_readiness_check(client: TestClient) -> None:
    """Test readiness check endpoint."""
    response = client.get("/readyz")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "version" in data


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "service" in data
    assert "version" in data
    assert "docs" in data


def test_api_meta(client: TestClient) -> None:
    """Test API meta endpoint."""
    response = client.get("/api/v1/meta")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "version" in data
    assert "environment" in data
    assert "features" in data
    assert "limits" in data


def test_error_handling(client: TestClient) -> None:
    """Test error handling with non-existent endpoint."""
    response = client.get("/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "code" in data
    assert "message" in data
    assert "trace_id" in data
