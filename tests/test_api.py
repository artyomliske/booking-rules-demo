from fastapi.testclient import TestClient

from app.main import create_app


def test_resource_and_booking_can_be_created() -> None:
    with TestClient(create_app("sqlite+pysqlite:///:memory:")) as client:
        resource = client.post("/resources", json={"name": "Studio A"})
        assert resource.status_code == 201

        booking = client.post(
            "/bookings",
            json={
                "resource_id": resource.json()["id"],
                "starts_at": "2026-09-01T10:00:00Z",
                "ends_at": "2026-09-01T12:00:00Z",
                "buffer_after_min": 15,
            },
        )

    assert booking.status_code == 201
    # SQLite does not preserve a timezone suffix; PostgreSQL runtime stores TIMESTAMPTZ.
    assert booking.json()["occupied_end"] == "2026-09-01T12:15:00"


def test_unknown_resource_returns_not_found() -> None:
    with TestClient(create_app("sqlite+pysqlite:///:memory:")) as client:
        response = client.post(
            "/bookings",
            json={
                "resource_id": 99,
                "starts_at": "2026-09-01T10:00:00Z",
                "ends_at": "2026-09-01T12:00:00Z",
            },
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resource not found"


def test_invalid_interval_returns_unprocessable_entity() -> None:
    with TestClient(create_app("sqlite+pysqlite:///:memory:")) as client:
        resource = client.post("/resources", json={"name": "Studio A"})
        response = client.post(
            "/bookings",
            json={
                "resource_id": resource.json()["id"],
                "starts_at": "2026-09-01T12:00:00Z",
                "ends_at": "2026-09-01T10:00:00Z",
            },
        )

    assert response.status_code == 422
    assert "strictly later" in response.json()["detail"]
