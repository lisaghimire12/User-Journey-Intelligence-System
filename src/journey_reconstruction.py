"""
journey_reconstruction.py
--------------------------
Reconstructs per-session user journeys from an ordered event stream.

Even though the synthetic generator also emits a journeys table directly
(mirroring how a lightweight ETL might pre-materialize journeys), this
module is the real reconstruction logic: given nothing but a raw,
sequence-numbered events table, it independently derives journey length,
duration, unique/repeated pages, transitions, loops, exit stage and
conversion. This is what would run against genuinely raw event data.
"""

from __future__ import annotations

import pandas as pd
import polars as pl

CONVERSION_EVENT = "purchase"
EXIT_STAGE_ORDER = ["registration", "checkout", "browse", "converted"]


def reconstruct_journeys(events_pl: pl.DataFrame) -> pd.DataFrame:
    if events_pl.is_empty():
        return pd.DataFrame()

    rows = []
    for session_id, group in events_pl.sort(["session_id", "sequence_number"]).group_by("session_id", maintain_order=True):
        g = group.sort("sequence_number")
        pages = g["page"].to_list()
        actions = g["action"].to_list()
        timestamps = g["timestamp"].to_list()

        journey_length = len(pages)
        unique_pages = len(set(pages))
        repeated_pages = journey_length - unique_pages
        duration = (timestamps[-1] - timestamps[0]).total_seconds() if len(timestamps) > 1 else 0.0

        converted = CONVERSION_EVENT in actions
        if converted:
            abandonment_stage = None
        elif "Registration" in pages and "Cart" not in pages:
            abandonment_stage = "registration"
        elif "Checkout" in pages:
            abandonment_stage = "checkout"
        else:
            abandonment_stage = "browse"

        # loop detection: any page that appears more than once non-contiguously
        seen_positions: dict[str, list[int]] = {}
        for idx, p in enumerate(pages):
            seen_positions.setdefault(p, []).append(idx)
        loop_count = sum(1 for _, idxs in seen_positions.items() if len(idxs) > 1)

        rows.append({
            "session_id": session_id[0] if isinstance(session_id, tuple) else session_id,
            "journey_sequence": " > ".join(pages),
            "journey_length": journey_length,
            "duration": duration,
            "unique_pages": unique_pages,
            "repeated_pages": repeated_pages,
            "loop_count": loop_count,
            "converted": converted,
            "abandonment_stage": abandonment_stage,
            "entry_page": pages[0],
            "exit_page": pages[-1],
        })

    return pd.DataFrame(rows)


def compute_transition_matrix(events_pl: pl.DataFrame) -> pd.DataFrame:
    """Returns a (from_page, to_page, count) edge list for Sankey/flow charts."""
    if events_pl.is_empty():
        return pd.DataFrame(columns=["source", "target", "count"])

    df = events_pl.sort(["session_id", "sequence_number"]).to_pandas()
    edges: dict[tuple[str, str], int] = {}
    for _, group in df.groupby("session_id"):
        pages = group["page"].tolist()
        for a, b in zip(pages[:-1], pages[1:]):
            edges[(a, b)] = edges.get((a, b), 0) + 1

    out = pd.DataFrame(
        [{"source": a, "target": b, "count": c} for (a, b), c in edges.items()]
    )
    return out.sort_values("count", ascending=False).reset_index(drop=True)


def top_journeys(journeys_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    if journeys_df.empty:
        return journeys_df
    grouped = (
        journeys_df.groupby("journey_sequence")
        .agg(
            sessions=("session_id", "count"),
            conversion_rate=("converted", "mean"),
            avg_duration=("duration", "mean"),
        )
        .reset_index()
        .sort_values("sessions", ascending=False)
        .head(n)
    )
    grouped["conversion_rate"] = (grouped["conversion_rate"] * 100).round(1)
    grouped["avg_duration"] = grouped["avg_duration"].round(1)
    return grouped
