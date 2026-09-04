from fastapi.testclient import TestClient

from loadranger.main import app


def test_health_endpoint_reports_service_is_healthy() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
