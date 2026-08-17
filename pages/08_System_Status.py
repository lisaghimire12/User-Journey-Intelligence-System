import datetime as dt

import streamlit as st

from src import database
from src.config import settings
from src.pipeline_state import clear_all_caches
from src.ui_theme import page_header, project_footer

page_header(
    "System Status",
    "Is the pipeline healthy?",
    "Live connection, record counts, and processing state",
)

col1, col2 = st.columns([2, 1])

with col1:
    st.markdown("### Database connection")
    try:
        counts = database.table_counts()
        connected = True
    except Exception as exc:
        connected = False
        counts = {}
        st.error(f"Database connection failed: {exc}")

    if connected:
        st.markdown(
            f'<div class="card"><b>Status:</b> Connected &nbsp;&middot;&nbsp; '
            f'<b>Backend:</b> {"PostgreSQL" if database.is_postgres() else "SQLite (local dev fallback)"}</div>',
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        c1.metric("Sessions", f"{counts.get('sessions', 0):,}")
        c2.metric("Events", f"{counts.get('events', 0):,}")
        c3.metric("Journeys", f"{counts.get('journeys', 0):,}")

        c4, c5, c6 = st.columns(3)
        c4.metric("Causal results", f"{counts.get('causal_results', 0):,}")
        c5.metric("Simulations logged", f"{counts.get('simulations', 0):,}")
        c6.metric("Recommendations", f"{counts.get('recommendations', 0):,}")

        latest_ts = database.latest_event_timestamp()
        st.markdown(f"**Latest event timestamp:** {latest_ts if latest_ts is not None else 'n/a'}")

with col2:
    st.markdown("### Actions")
    st.markdown(f"**Last checked:** {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    if st.button("Refresh now"):
        clear_all_caches()
        st.rerun()
    st.caption(f"Auto-refresh is {'enabled' if settings.auto_refresh_enabled else 'disabled'} "
               f"(cache TTL: {settings.cache_ttl_seconds}s). Use this button for an immediate refresh.")

st.markdown("### Processing state")
st.markdown(
    "- **Data source:** synthetic event generator (`src/data_generator.py`), designed to be "
    "swapped for anonymized real event data without changing downstream code.\n"
    "- **Model state:** causal estimates and recommendations are recomputed on demand from the "
    "current database contents — nothing is cached beyond the configured TTL.\n"
    "- **Pipeline stages:** Event Data → Privacy/Minimization → Database → Processing → Journey "
    "Reconstruction → Behavioral Analytics → Segmentation → Causal Inference → Intervention "
    "Identification → What-If Simulation → Intervention Ranking → Explainable Recommendation → "
    "this Dashboard.\n"
)

project_footer()
