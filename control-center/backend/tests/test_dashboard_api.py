from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_endpoint():
    response = client.get("/api/v1/dashboard")

    assert response.status_code == 200

    payload = response.json()

    assert payload["success"] is True
    assert "data" in payload