from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine

from src import api, database
from src.event_mapping import SESSION_GAP_MINUTES


@pytest.fixture
def client(tmp_path):
    original_engine = database._ENGINE
    database._ENGINE = create_engine(
        f"sqlite:///{tmp_path / 'ingestion_test.db'}",
        connect_args={"check_same_thread": False},
        future=True,
    )
    database.init_schema()
    try:
        yield TestClient(api.app)
    finally:
        database._ENGINE.dispose()
        database._ENGINE = original_engine


def _payload(**overrides):
    payload = {
        "raw_user_id": "user-123",
        "raw_session_id": "browser-session-123",
        "event_name": "page_view",
        "page_url": "https://shop.example/",
        "timestamp": "2026-09-05T12:00:00+00:00",
    }
    payload.update(overrides)
    return payload


def test_valid_event_is_stored_with_pseudonymized_session_id(client):
    response = client.post("/api/events", json=_payload())

    assert response.status_code == 201
    stored = database.read_table("events")
    assert len(stored) == 1
    assert stored.iloc[0]["session_id"] != "browser-session-123"


def test_unexpected_fields_are_ignored_before_storage(client):
    response = client.post("/api/events", json=_payload(email="person@example.com"))

    assert response.status_code == 201
    stored_event = database.read_table("events").iloc[0].to_dict()
    assert "email" not in stored_event


def test_missing_event_name_is_rejected_without_writing(client):
    payload = _payload()
    del payload["event_name"]

    response = client.post("/api/events", json=payload)

    assert response.status_code == 422
    assert len(database.read_table("events")) == 0
    assert len(database.read_table("sessions")) == 0


def test_session_reuse_and_boundary(client):
    first_timestamp = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
    within_gap = first_timestamp + timedelta(minutes=SESSION_GAP_MINUTES - 1)
    beyond_gap = within_gap + timedelta(minutes=SESSION_GAP_MINUTES + 1)

    first = client.post("/api/events", json=_payload(timestamp=first_timestamp.isoformat()))
    second = client.post(
        "/api/events",
        json=_payload(
            event_name="view_item",
            timestamp=within_gap.isoformat(),
        ),
    )
    third = client.post(
        "/api/events",
        json=_payload(
            event_name="add_to_cart",
            timestamp=beyond_gap.isoformat(),
        ),
    )

    assert first.status_code == second.status_code == third.status_code == 201
    assert second.json()["session_id"] == first.json()["session_id"]
    assert third.json()["session_id"] != first.json()["session_id"]
    assert len(database.read_table("events")) == 3