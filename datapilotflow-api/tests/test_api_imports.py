"""
Test API package imports and health endpoint.
"""

import pytest


class TestAPIImports:
    """Test that API package imports correctly."""

    def test_import_api_app(self):
        """Test importing API app factory."""
        from datapilotflow.api import create_app

        assert create_app is not None

    def test_create_app(self):
        """Test creating FastAPI application."""
        from datapilotflow.api import create_app

        app = create_app()
        assert app is not None
        assert app.title == "DataPilotFlow API"

    def test_app_has_routers(self):
        """Test that app has all required routers."""
        from datapilotflow.api import create_app

        app = create_app()
        routes = [route.path for route in app.routes]

        # Check that routers are included
        assert any("/api/v1/health" in route for route in routes)
        assert any("/api/v1/agents" in route for route in routes)
        assert any("/api/v1/conversations" in route for route in routes)
        assert any("/api/v1/knowledge" in route for route in routes)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_exists(self):
        """Test that health endpoint exists."""
        from fastapi.testclient import TestClient
        from datapilotflow.api import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health/")
        assert response.status_code == 200

    def test_health_response_format(self):
        """Test health endpoint response format."""
        from fastapi.testclient import TestClient
        from datapilotflow.api import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/api/v1/health/")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "message" in data
        assert data["status"] == "healthy"
