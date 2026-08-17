from datetime import datetime, timedelta

import polars as pl

from src.journey_reconstruction import reconstruct_journeys, compute_transition_matrix


def _make_events():
    base = datetime(2026, 1, 1)
    rows = [
        {"session_id": "s1", "sequence_number": 1, "page": "Home", "action": "view", "timestamp": base},
        {"session_id": "s1", "sequence_number": 2, "page": "Product", "action": "view", "timestamp": base + timedelta(seconds=10)},
        {"session_id": "s1", "sequence_number": 3, "page": "Cart", "action": "add_to_cart", "timestamp": base + timedelta(seconds=20)},
        {"session_id": "s1", "sequence_number": 4, "page": "Checkout", "action": "view", "timestamp": base + timedelta(seconds=30)},
        {"session_id": "s1", "sequence_number": 5, "page": "Purchase", "action": "purchase", "timestamp": base + timedelta(seconds=40)},
        {"session_id": "s2", "sequence_number": 1, "page": "Home", "action": "view", "timestamp": base},
        {"session_id": "s2", "sequence_number": 2, "page": "Search", "action": "view", "timestamp": base + timedelta(seconds=5)},
        {"session_id": "s2", "sequence_number": 3, "page": "Exit", "action": "exit", "timestamp": base + timedelta(seconds=8)},
    ]
    return pl.DataFrame(rows)


def test_reconstruct_journeys_basic():
    events = _make_events()
    journeys = reconstruct_journeys(events)
    assert len(journeys) == 2
    converted_row = journeys[journeys["session_id"] == "s1"].iloc[0]
    assert bool(converted_row["converted"]) is True
    not_converted_row = journeys[journeys["session_id"] == "s2"].iloc[0]
    assert bool(not_converted_row["converted"]) is False


def test_transition_matrix():
    events = _make_events()
    matrix = compute_transition_matrix(events)
    assert not matrix.empty
    assert {"source", "target", "count"}.issubset(matrix.columns)
