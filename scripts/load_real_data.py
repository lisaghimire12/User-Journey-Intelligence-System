"""
load_real_data.py
-----------------
Loads real GA4 e-commerce event data (a BigQuery export of the classic
Google Merchandise Store demo dataset) into the existing project database,
replacing synthetic data.

Usage:
    python scripts/load_real_data.py --file "data/external/bq-results-20260818-140307-1787061830701.csv"

What happens:
    1. Reset: clears the sessions / events / journeys tables only.
       causal_results, simulations and recommendations are left intact --
       they are recomputed in a later analysis step (scripts/run_analysis.py).
    2. Reconstruct sessions from raw per-user event streams, splitting on
       any 30+ minute gap of inactivity (standard clickstream convention).
    3. Map GA4 event names onto the schema's funnel page/action model
       (see src/data_generator.py for the exact conventions used).
    4. Compute derived behavioral proxy columns from actual behavior.
       These are proxies, NOT ground truth: real GA4 data does not carry
       the latent population parameters the synthetic generator does.
    5. Write sessions / events / journeys through src.database only -- no
       new schema, no bypassed connection layer.

Caveats for this real-data pull:
    * registration_friction is explicitly NULL for every session -- there
      is no registration event in this GA4 dataset. The causal question
      "does reducing registration friction increase conversion?" CANNOT be
      answered from this data and MUST be skipped/excluded when running
      causal analysis on this dataset.
    * device_type / platform / acquisition_source are set to "unknown"
      because those dimensions were not included in this data pull.
    * population = None, intervention_exposure = False everywhere -- no
      real experiment was run on this data.
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid

import _bootstrap  # noqa: F401  (adds project root to sys.path so `src` imports work)

import numpy as np
import pandas as pd
from sqlalchemy import text

from src import database

# Exact input file this loader is written for (overridable via --file).
REAL_DATA_PATH = "data/external/bq-results-20260818-140307-1787061830701.csv"

# Standard clickstream session-splitting convention: a new session starts
# whenever two consecutive events from the same user are >= 30 minutes apart.
SESSION_GAP_MINUTES = 30

# Last event in a session has no "next event" to measure dwell against, so
# it is assigned a small default rather than 0 or NaN.
DEFAULT_DWELL_LAST_EVENT = 5.0

# Sessions with a single event have no intra-session gaps; page_delay then
# falls back to this default (mirrors the generator's page_delay semantics,
# though there it is a sampled latency, not a measurement).
DEFAULT_PAGE_DELAY = 5.0

# Upper bound on page_delay (mean real inter-event gap, in seconds). Without
# a cap, a single long idle stretch inside a session would silently distort
# every downstream simulation that consumes page_delay.
MAX_PAGE_DELAY_SECONDS = 30.0

# Funnel mapping: GA4 event_name -> (page, action, event_type).
# event_type follows the convention used in src/data_generator.py:
#   event_type = "page_view" if action == "view" else action
# so page_view/view_item/begin_checkout (action "view") are all stored as
# "page_view", while add_to_cart and purchase keep their own event types.
# page_view's page is resolved below (Home vs Search) from the URL.
EVENT_MAP = {
    "page_view":      {"page": "Search",  "action": "view",        "event_type": "page_view"},
    "view_item":      {"page": "Product", "action": "view",        "event_type": "page_view"},
    "add_to_cart":    {"page": "Cart",    "action": "add_to_cart", "event_type": "add_to_cart"},
    "begin_checkout": {"page": "Checkout", "action": "view",       "event_type": "page_view"},
    "purchase":       {"page": "Purchase", "action": "purchase",   "event_type": "purchase"},
}


def _truncate_data_tables() -> None:
    """Clears only the load-and-reconstruct tables.

    causal_results / simulations / recommendations are deliberately left
    alone -- they get recomputed in a later analysis step.
    """
    engine = database.get_engine()
    tables = ["events", "journeys", "sessions"]
    with engine.begin() as conn:
        for t in tables:
            conn.execute(text(f"DELETE FROM {t}"))


def _parse_csv(path: str) -> pd.DataFrame:
    """Reads the BigQuery CSV and converts microseconds-since-epoch to UTC."""
    # user_pseudo_id read as str so large numeric ids keep their exact digits.
    df = pd.read_csv(path, dtype={"user_pseudo_id": str, "event_name": str, "page_location": str})
    df["timestamp"] = pd.to_datetime(df["event_timestamp"].astype("int64"), unit="us", utc=True)
    return df.drop(columns=["event_timestamp"])


def _split_sessions(events: pd.DataFrame) -> list[list[pd.Series]]:
    """Groups a user's events into sessions on any >=30 minute inactivity gap."""
    sessions: list[list[pd.Series]] = []
    for _, user_events in events.sort_values("timestamp").groupby("user_pseudo_id"):
        current: list[pd.Series] = []
        for _, row in user_events.iterrows():
            if current:
                gap_seconds = (row["timestamp"] - current[-1]["timestamp"]).total_seconds()
                if gap_seconds >= SESSION_GAP_MINUTES * 60:
                    sessions.append(current)
                    current = []
            current.append(row)
        if current:
            sessions.append(current)
    return sessions


def _map_funnel(event: pd.Series) -> dict:
    """Maps one GA4 event onto the schema's page/action/event_type model."""
    meta = EVENT_MAP[event["event_name"]]
    page = meta["page"]
    # page_view => "Search" when the URL looks like a search page
    # (Google Merchandise Store uses /asearch.html); otherwise "Home".
    if event["event_name"] == "page_view":
        page = "Search" if "search" in str(event["page_location"]).lower() else "Home"
    return {
        "page": page,
        "action": meta["action"],
        "event_type": meta["event_type"],
        "timestamp": event["timestamp"],
        "page_location": str(event["page_location"]),
    }


def load_real_data(path: str) -> dict:
    print(f"Reading real GA4 events from {path} ...")
    raw = _parse_csv(path)
    print(f"  {len(raw)} raw events")

    print(f"Splitting sessions (inactivity gap >= {SESSION_GAP_MINUTES} min) ...")
    session_chunks = _split_sessions(raw)
    print(f"  {len(session_chunks)} sessions")

    # --- Pass 1: per-session raw records + dataset-level normalization ---
    # Each record keeps the ordered, funnel-mapped event list untouched so
    # pass 2 can build the three tables consistently.
    records = []
    n_events_per_session = []
    n_products_per_session = []
    checkout_reached = 0
    checkout_abandoned = 0

    for chunk in session_chunks:
        user_id = str(chunk[0]["user_pseudo_id"])
        mapped = [_map_funnel(e) for e in chunk]
        mapped.sort(key=lambda m: m["timestamp"])
        records.append({"user_id": user_id, "mapped": mapped})

        n_events = len(mapped)

        n_events = len(mapped)
        n_events_per_session.append(n_events)

        # content_exposure proxy input: distinct products viewed (distinct
        # view_item page_locations within the session).
        n_products = len({m["page_location"] for m in mapped if m["page"] == "Product"})
        n_products_per_session.append(n_products)

        converted = any(m["action"] == "purchase" for m in mapped)
        if any(m["page"] == "Checkout" for m in mapped):
            checkout_reached += 1
            if not converted:
                checkout_abandoned += 1

    # Engagement normalizer: session-length distribution (95th pct, guarded).
    ref_events = max(1, float(np.percentile(n_events_per_session, 95)))
    # Content exposure normalizer: distinct-products distribution (95th pct).
    ref_products = max(1, float(np.percentile(n_products_per_session, 95)))
    # Population-level begin_checkout-without-purchase rate.
    checkout_abandon_rate = checkout_abandoned / checkout_reached if checkout_reached else 0.0

    # --- Pass 2: build session / event / journey rows ---------------------
    session_rows, event_rows, journey_rows = [], [], []

    for record in records:
        mapped = record["mapped"]
        session_id = str(uuid.uuid4())
        pages = [m["page"] for m in mapped]
        timestamps = [m["timestamp"] for m in mapped]

        n_events = len(mapped)
        converted = any(m["action"] == "purchase" for m in mapped)

        # --- Derived behavioral proxies (proxies, NOT ground truth) -------
        # navigation_friction: share of events that are non-consecutive
        # repeats of an earlier page type (backtracking/looping), 0-100.
        seen: set[str] = set()
        prev: str | None = None
        loops = 0
        for p in pages:
            if prev is not None and p == prev:  # consecutive repeat, not a loop
                seen.add(p)
                prev = p
                continue
            if p in seen:
                loops += 1
            seen.add(p)
            prev = p
        navigation_friction = min(100.0, loops / max(1, n_events) * 100)

        # content_exposure: distinct products viewed vs the dataset's
        # 95th-percentile session, scaled to 0-100.
        n_products = len({m["page_location"] for m in mapped if m["page"] == "Product"})
        content_exposure = min(100.0, n_products / ref_products * 100)

        # checkout_friction: population-level heuristic from observed
        # begin_checkout-without-purchase behavior. Sessions that reached
        # checkout but abandoned score highest; those that reached checkout
        # and converted score lower; sessions that never reached checkout
        # score lowest (they never experienced this stage).
        if any(m["page"] == "Checkout" for m in mapped):
            if converted:
                checkout_friction = min(100.0, 20.0 + 30.0 * checkout_abandon_rate)
            else:
                checkout_friction = min(100.0, 50.0 + 50.0 * checkout_abandon_rate)
        else:
            checkout_friction = min(100.0, 10.0 * checkout_abandon_rate)

        # page_delay: average real inter-event gap in the session (seconds),
        # capped to avoid a single idle stretch skewing the proxy.
        if n_events > 1:
            gaps = [(timestamps[i + 1] - timestamps[i]).total_seconds() for i in range(n_events - 1)]
            page_delay = round(min(MAX_PAGE_DELAY_SECONDS, float(np.mean(gaps))), 2)
        else:
            page_delay = DEFAULT_PAGE_DELAY

        # prior_engagement: event count vs the dataset's session-length
        # distribution (95th pct), capped at 1.0.
        prior_engagement = round(min(1.0, n_events / ref_events), 3)

        # --- registration_friction: deliberately omitted (NULL) ------------
        # There is no registration event in this GA4 dataset, so this column
        # stays NULL for all real-data sessions. The "does reducing
        # registration friction increase conversion?" causal question must be
        # skipped/excluded when running causal analysis on this dataset.
        # -------------------------------------------------------------------

        session_start = timestamps[0]
        session_end = timestamps[-1]

        session_rows.append({
            "session_id": session_id,
            "anonymous_user_id": record["user_id"],  # already a pseudonymous GA4 id
            "session_start": session_start,
            "session_end": session_end,
            "device_type": "unknown",
            "platform": "unknown",
            "acquisition_source": "unknown",
            "population": None,
            "prior_engagement": prior_engagement,
            "registration_friction": None,          # see comment above
            "checkout_friction": round(checkout_friction, 2),
            "page_delay": page_delay,
            "content_exposure": round(content_exposure, 2),
            "navigation_friction": round(navigation_friction, 2),
            "intervention_exposure": False,
        })

        for i, m in enumerate(mapped):
            # dwell_time = seconds until the next event in the session;
            # the last event gets a small default (no next event to measure).
            if i + 1 < n_events:
                dwell = (timestamps[i + 1] - timestamps[i]).total_seconds()
            else:
                dwell = DEFAULT_DWELL_LAST_EVENT
            event_rows.append({
                "event_id": str(uuid.uuid4()),
                "session_id": session_id,
                "timestamp": m["timestamp"],
                "event_type": m["event_type"],
                "page": m["page"],
                "action": m["action"],
                "dwell_time": max(0.0, dwell),
                "sequence_number": i + 1,
                "intervention_exposure": False,
            })

        unique_pages = len(set(pages))
        journey_rows.append({
            "journey_id": str(uuid.uuid4()),
            "session_id": session_id,
            "journey_sequence": " > ".join(pages),
            "journey_length": n_events,
            "duration": (session_end - session_start).total_seconds() if n_events > 1 else 0.0,
            "converted": converted,
            # abandonment_stage matches the values used in src/data_generator.py
            # ("browse", "checkout"). There is no registration stage in this
            # data, and the generator has no "cart" stage, so sessions that
            # only reached the cart map to "browse".
            "abandonment_stage": None if converted else ("checkout" if "Checkout" in pages else "browse"),
            "unique_pages": unique_pages,
            "repeated_pages": n_events - unique_pages,
        })

    sessions_df = pd.DataFrame(session_rows)
    events_df = pd.DataFrame(event_rows)
    journeys_df = pd.DataFrame(journey_rows)

    print("Writing to database ...")
    database.write_dataframe(sessions_df, "sessions")
    database.write_dataframe(events_df, "events")
    database.write_dataframe(journeys_df, "journeys")

    return {
        "sessions": len(sessions_df),
        "events": len(events_df),
        "journeys": len(journeys_df),
        "conversion_rate": round(float(journeys_df["converted"].astype(bool).mean()) * 100, 2),
        "checkout_abandon_rate": round(checkout_abandon_rate * 100, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Load real GA4 e-commerce event data into the project database.")
    parser.add_argument("--file", default=REAL_DATA_PATH,
                        help=f"Path to the GA4 BigQuery CSV export (default: {REAL_DATA_PATH})")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f"Error: input file not found: {args.file}")
        sys.exit(1)

    database.init_schema()
    print("Clearing existing sessions / events / journeys (leaving causal_results, simulations, recommendations) ...")
    _truncate_data_tables()

    summary = load_real_data(args.file)

    print("\n=== Load summary ===")
    print(f"  sessions:      {summary['sessions']}")
    print(f"  events:        {summary['events']}")
    print(f"  journeys:      {summary['journeys']}")
    print(f"  conversion:    {summary['conversion_rate']}%")
    print(f"  checkout abandonment (population proxy): {summary['checkout_abandon_rate']}%")
    print("\nDone. Recompute analytics/causal/simulations/recommendations with:\n"
          "  python scripts/run_analysis.py")


if __name__ == "__main__":
    main()