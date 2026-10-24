from unittest.mock import patch

from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_analysis_endpoint_returns_data():
    with (
        patch("main.fetch_actual_generation", return_value=[]),
        patch("main.fetch_forecast_generation", return_value=[]),
    ):
        response = client.get("/api/analysis")

    assert response.status_code == 200
    assert response.json()["message"] == "No actual-generation records found."
    assert response.json()["metrics"] == {}


def test_analysis_endpoint_handles_elexon_failure():
    with patch(
        "main.fetch_actual_generation",
        side_effect=Exception("Elexon service unavailable"),
    ):
        response = client.get("/api/analysis")

    assert response.status_code == 502
    assert "Unable to retrieve or analyse Elexon data" in response.json()["detail"]