from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_query_validation() -> None:
    response = client.get("/notes", params={"q": "python", "limit": 5})
    assert response.status_code == 200
    assert response.json()["filters"] == {"q": "python", "limit": 5}


def test_note_preview_success() -> None:
    response = client.post(
        "/notes/preview",
        json={"title": "合法标题", "priority": "high", "tags": ["python"]},
    )
    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_note_preview_returns_422() -> None:
    response = client.post(
        "/notes/preview",
        json={"title": "<非法标题>", "tags": ["1", "2", "3", "4", "5", "6"]},
    )
    assert response.status_code == 422
    assert response.json()["detail"]
