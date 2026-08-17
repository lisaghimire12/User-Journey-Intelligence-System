"""
privacy.py
----------
Concrete privacy-aware processing utilities used throughout the pipeline.

This module implements, as real code rather than marketing language:
  * pseudonymization of raw user identifiers into stable but non-reversible
    session/user tokens
  * data minimization helpers (a strict allow-list of retained fields)
  * aggregation guards (refuse to report on groups below a minimum size)
  * a configurable retention policy check

No claim of legal compliance (GDPR / DPDP / etc.) is made anywhere in this
module or in the UI that consumes it. This is a data-minimization design,
not a certified compliance product.
"""

from __future__ import annotations

import hashlib
import hmac
from datetime import datetime, timedelta, timezone

from src.config import settings

# Fields the system is allowed to retain per event. Anything not on this
# list must never be written to the events table.
EVENT_FIELD_ALLOWLIST = {
    "event_id",
    "session_id",
    "timestamp",
    "event_type",
    "page",
    "action",
    "dwell_time",
    "sequence_number",
    "intervention_exposure",
}

SESSION_FIELD_ALLOWLIST = {
    "session_id",
    "anonymous_user_id",
    "session_start",
    "session_end",
    "device_type",
    "platform",
    "acquisition_source",
}

# Minimum group size before a statistic is allowed to be surfaced in an
# aggregated report. Protects against re-identification of small cohorts.
MIN_AGGREGATION_GROUP_SIZE = 5


def pseudonymize(raw_identifier: str) -> str:
    """
    Deterministically turn a raw identifier (e.g. a device fingerprint or
    a raw account id) into a pseudonymous token using an HMAC keyed with a
    project-local salt. The transform is one-way in practice: recovering
    raw_identifier from the output requires the salt and is computationally
    infeasible to reverse via lookup for a large identifier space.
    """
    if not raw_identifier:
        raise ValueError("raw_identifier must be non-empty")
    digest = hmac.new(
        settings.pseudonymization_salt.encode("utf-8"),
        raw_identifier.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return f"session_{digest[:10].upper()}"


def minimize_event(record: dict) -> dict:
    """Drop any field not on the explicit allow-list before persistence."""
    return {k: v for k, v in record.items() if k in EVENT_FIELD_ALLOWLIST}


def minimize_session(record: dict) -> dict:
    return {k: v for k, v in record.items() if k in SESSION_FIELD_ALLOWLIST}


def is_group_reportable(group_size: int) -> bool:
    """
    Aggregation guard: a segment/group statistic is only safe to display
    once it represents at least MIN_AGGREGATION_GROUP_SIZE sessions.
    """
    return group_size >= MIN_AGGREGATION_GROUP_SIZE


def retention_cutoff() -> datetime:
    """
    Returns the timestamp before which event data is eligible for purge,
    based on the configurable DATA_RETENTION_DAYS setting.
    """
    return datetime.now(timezone.utc) - timedelta(days=settings.data_retention_days)


def is_expired(event_timestamp: datetime) -> bool:
    ts = event_timestamp
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts < retention_cutoff()


PRIVACY_PRINCIPLES = [
    (
        "Pseudonymous identifiers",
        "Every session and user is represented by a generated token "
        "(e.g. session_8F29A1) derived via a keyed one-way hash. No name, "
        "email, phone number, or account identifier is ever stored.",
    ),
    (
        "Data minimization",
        "Only the fields required for behavioral analytics are retained. "
        "An explicit allow-list is enforced in code before any record is "
        "written to the database.",
    ),
    (
        "Aggregated reporting",
        f"Segment- and cohort-level statistics are only surfaced once a "
        f"group contains at least {MIN_AGGREGATION_GROUP_SIZE} sessions, "
        f"to reduce the risk of re-identifying an individual from a small "
        f"group.",
    ),
    (
        "Configurable retention",
        f"Event-level data is treated as eligible for purge after "
        f"{settings.data_retention_days} days (configurable via "
        f"DATA_RETENTION_DAYS in .env).",
    ),
]
