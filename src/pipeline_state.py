"""
pipeline_state.py
--------------------
Cached loaders used by the Streamlit pages so that the (moderately
expensive) journey reconstruction / engagement-scoring steps aren't
recomputed on every widget interaction. Cache TTL is configurable via
CACHE_TTL_SECONDS in .env, and every page also exposes a manual refresh
button that clears these caches (see pages/08_System_Status.py).
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from src import database
from src.behavioral_analysis import engagement_score
from src.config import settings
from src.data_processing import clean_events, clean_sessions
from src.journey_reconstruction import reconstruct_journeys, compute_transition_matrix


@st.cache_data(ttl=settings.cache_ttl_seconds, show_spinner="Loading and reconstructing journeys...")
def load_pipeline_data():
    raw_events = database.load_raw_events() if hasattr(database, "load_raw_events") else database.read_table("events")
    raw_sessions = database.read_table("sessions")

    if raw_events.empty:
        empty = pd.DataFrame()
        return empty, empty, empty, empty

    events_pl = clean_events(raw_events)
    sessions_pl = clean_sessions(raw_sessions)
    sessions_pd = sessions_pl.to_pandas()

    journeys = reconstruct_journeys(events_pl)
    merged = engagement_score(sessions_pd, journeys) if not journeys.empty else pd.DataFrame()
    transitions = compute_transition_matrix(events_pl)

    return sessions_pd, journeys, merged, transitions


def clear_all_caches():
    st.cache_data.clear()


def has_data() -> bool:
    counts = database.table_counts()
    return counts.get("events", 0) > 0
