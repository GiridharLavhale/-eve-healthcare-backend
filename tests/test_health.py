"""Health check API tests."""

from fastapi.testclient import TestClient


def test_health_check_endpoint(client: TestClient):
    """Verifies that the /health endpoint returns service health and connected database."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert "version" in data
    assert "timestamp" in data
