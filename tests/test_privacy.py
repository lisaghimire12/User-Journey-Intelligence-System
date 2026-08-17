from datetime import datetime, timedelta, timezone

from src.privacy import (
    is_group_reportable,
    is_expired,
    minimize_event,
    minimize_session,
    pseudonymize,
)


def test_pseudonymize_is_deterministic_and_prefixed():
    a = pseudonymize("raw-user-123")
    b = pseudonymize("raw-user-123")
    c = pseudonymize("raw-user-456")
    assert a == b
    assert a != c
    assert a.startswith("session_")


def test_minimize_event_drops_unlisted_fields():
    record = {"event_id": "e1", "session_id": "s1", "email": "someone@example.com"}
    cleaned = minimize_event(record)
    assert "email" not in cleaned
    assert cleaned == {"event_id": "e1", "session_id": "s1"}


def test_minimize_session_drops_unlisted_fields():
    record = {"session_id": "s1", "anonymous_user_id": "u1", "full_name": "Jane Doe"}
    cleaned = minimize_session(record)
    assert "full_name" not in cleaned


def test_group_reportable_threshold():
    assert is_group_reportable(5) is True
    assert is_group_reportable(4) is False


def test_expiry():
    old = datetime.now(timezone.utc) - timedelta(days=9999)
    recent = datetime.now(timezone.utc)
    assert is_expired(old) is True
    assert is_expired(recent) is False
