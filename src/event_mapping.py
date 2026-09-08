"""Shared event-name-to-funnel-stage mappings."""

from __future__ import annotations


SESSION_GAP_MINUTES = 30


# Funnel mapping: event name -> (page, action, event type).
# event_type follows the convention used in src/data_generator.py:
# event_type = "page_view" if action == "view" else action.
EVENT_MAP = {
    "page_view":      {"page": "Search",  "action": "view",        "event_type": "page_view"},
    "view_item":      {"page": "Product", "action": "view",        "event_type": "page_view"},
    "add_to_cart":    {"page": "Cart",    "action": "add_to_cart", "event_type": "add_to_cart"},
    "begin_checkout": {"page": "Checkout", "action": "view",       "event_type": "page_view"},
    "purchase":       {"page": "Purchase", "action": "purchase",   "event_type": "purchase"},
}


def map_live_event(event_name: str) -> dict:
    """Return the funnel mapping for a live event name."""
    return EVENT_MAP[event_name].copy()