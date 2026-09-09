import datetime as dt

import streamlit as st

from src import database
from src.config import settings
from src.pipeline_state import clear_all_caches
from src.data_processing import clean_events, clean_sessions
from src.journey_reconstruction import reconstruct_journeys
from src.behavioral_analysis import compute_kpis
from src import causal_analysis
from src.recommendation_engine import build_recommendations
from src.explanation_engine import build_explanation
from src.ui_theme import page_header, project_footer


# ============================================================
# COLOR PALETTE
# ============================================================

ESPRESSO = "#32180F"
TERRACOTTA = "#9B3F24"
RUST = "#A84A2A"
CREAM = "#F7F1E8"
OFFWHITE = "#FCFAF6"
TAUPE = "#D8CFC3"
SAND = "#E9DED1"
WHITE = "#FFFFFF"


# ============================================================
# PAGE HEADER
# ============================================================

page_header(
    "System Status",
    "Is the pipeline healthy?",
    "Live connection, record counts, and processing state",
)


# ============================================================
# PAGE-SPECIFIC COLOR STYLING
# ============================================================

st.markdown(
    f"""
    <style>

    .stMarkdown p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .stMarkdown li {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .stMarkdown strong {{
        color: {ESPRESSO} !important;
    }}

    h3 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    h4 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .card {{
        background-color: {OFFWHITE} !important;
        border: 1px solid {TAUPE} !important;
        color: {ESPRESSO} !important;
    }}

    .card b {{
        color: {TERRACOTTA} !important;
    }}

    .card span {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricLabel"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricValue"] {{
        color: {TERRACOTTA} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricValue"] > div {{
        color: {TERRACOTTA} !important;
    }}

    div[data-testid="stMetricDelta"] {{
        color: {RUST} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricDelta"] svg {{
        fill: {RUST} !important;
    }}

    div[data-testid="stCaptionContainer"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stCaptionContainer"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stAlert"] {{
        color: {ESPRESSO} !important;
    }}

    div[data-testid="stAlert"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stException"] {{
        color: {ESPRESSO} !important;
    }}

    div.stButton > button {{
        background-color: {TERRACOTTA} !important;
        color: {WHITE} !important;
        border: 1px solid {TERRACOTTA} !important;
    }}

    div.stButton > button:hover {{
        background-color: {RUST} !important;
        color: {WHITE} !important;
        border-color: {RUST} !important;
    }}

    div.stButton > button:focus {{
        color: {WHITE} !important;
        border-color: {TERRACOTTA} !important;
        box-shadow: 0 0 0 2px {SAND} !important;
    }}

    hr {{
        border-color: {TAUPE} !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# RECOMPUTE PIPELINE
# ============================================================

def recompute_pipeline():
    """
    Re-run the analytics pipeline against the current database contents.

    This intentionally does NOT regenerate synthetic data.
    It processes whatever events and sessions currently exist.
    """

    raw_events = database.read_table("events")
    raw_sessions = database.read_table("sessions")

    if raw_events.empty:
        raise RuntimeError(
            "No events found in the database. "
            "Load event data before recomputing the pipeline."
        )

    events_pl = clean_events(raw_events)
    sessions_pl = clean_sessions(raw_sessions)

    reconstructed = reconstruct_journeys(events_pl)

    sessions_pd = sessions_pl.to_pandas()

    kpis = compute_kpis(
        reconstructed,
        sessions_pd,
    )

    # --------------------------------------------------------
    # Causal analysis
    # --------------------------------------------------------

    causal_df = reconstructed.merge(
        sessions_pd,
        on="session_id",
        how="left",
    )

    causal_results = []

    for question in causal_analysis.CAUSAL_QUESTIONS:

        result = causal_analysis.estimate_effect(
            causal_df,
            question["treatment_raw"],
            question["outcome"],
            question["confounders"],
            treatment_label=question["treatment_label"],
            beneficial_direction=question.get(
                "beneficial_direction",
                "low",
            ),
        )

        causal_results.append(result)

    # --------------------------------------------------------
    # Recommendations
    # --------------------------------------------------------

    recommendations = build_recommendations(
        reconstructed,
        sessions_pd,
        kpis["conversion_rate"],
    )

    records = []

    for recommendation in recommendations:

        explanation = build_explanation(
            recommendation
        )

        records.append(
            {
                "intervention": recommendation.label,
                "expected_benefit": (
                    recommendation.causal_effect_pct
                    or recommendation.simulated_improvement_pct
                    or 0.0
                ),
                "evidence": recommendation.evidence,
                "confidence": recommendation.confidence,
                "complexity": recommendation.complexity,
                "risk": recommendation.risk,
                "recommendation_score": recommendation.recommendation_score,
                "explanation": explanation,
            }
        )

    if records:
        database.write_recommendations(records)

    return {
        "sessions": kpis["total_sessions"],
        "conversion_rate": kpis["conversion_rate"],
        "recommendations": len(recommendations),
        "causal_results": len(causal_results),
    }


# ============================================================
# DATABASE / ACTIONS
# ============================================================

col1, col2 = st.columns([2, 1])


# ============================================================
# DATABASE CONNECTION
# ============================================================

with col1:

    st.markdown("### Database connection")

    try:
        counts = database.table_counts()
        connected = True

    except Exception as exc:
        connected = False
        counts = {}
        st.error(
            f"Database connection failed: {exc}"
        )

    if connected:

        st.markdown(
            f"""
            <div class="card">
                <b>Status:</b> Connected
                &nbsp;&middot;&nbsp;
                <b>Backend:</b>
                {"PostgreSQL" if database.is_postgres() else "SQLite (local dev fallback)"}
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)

        c1.metric(
            "Sessions",
            f"{counts.get('sessions', 0):,}",
        )

        c2.metric(
            "Events",
            f"{counts.get('events', 0):,}",
        )

        c3.metric(
            "Journeys",
            f"{counts.get('journeys', 0):,}",
        )

        c4, c5, c6 = st.columns(3)

        c4.metric(
            "Causal results",
            f"{counts.get('causal_results', 0):,}",
        )

        c5.metric(
            "Simulations logged",
            f"{counts.get('simulations', 0):,}",
        )

        c6.metric(
            "Recommendations",
            f"{counts.get('recommendations', 0):,}",
        )

        latest_ts = database.latest_event_timestamp()

        st.markdown(
            f"""
            **Latest event timestamp:**
            {latest_ts if latest_ts is not None else 'n/a'}
            """
        )


# ============================================================
# ACTIONS
# ============================================================

with col2:

    st.markdown("### Actions")

    st.markdown(
        f"""
        **Last checked:**
        {dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
    )

    # --------------------------------------------------------
    # RECOMPUTE
    # --------------------------------------------------------

    if st.button(
        "Recompute Now",
        use_container_width=True,
    ):

        with st.spinner(
            "Recomputing journeys, behavioral analytics, causal analysis, and recommendations..."
        ):

            try:

                results = recompute_pipeline()

                clear_all_caches()

                st.success(
                    "Pipeline recomputed successfully."
                )

                st.info(
                    f"Processed {results['sessions']:,} sessions · "
                    f"Conversion: {results['conversion_rate']}% · "
                    f"{results['recommendations']} recommendations generated."
                )

            except Exception as exc:

                st.error(
                    f"Pipeline recomputation failed: {exc}"
                )

    # --------------------------------------------------------
    # REFRESH
    # --------------------------------------------------------

    if st.button(
        "Refresh now",
        use_container_width=True,
    ):
        clear_all_caches()
        st.rerun()

    st.caption(
        f"Auto-refresh is "
        f"{'enabled' if settings.auto_refresh_enabled else 'disabled'} "
        f"(cache TTL: {settings.cache_ttl_seconds}s). "
        f"Use Recompute Now to re-run analysis against the current "
        f"database contents."
    )


# ============================================================
# PROCESSING STATE
# ============================================================

st.markdown("### Processing state")

st.markdown(
    "- **Data source:** current events and sessions stored in the database. "
    "The pipeline can process synthetic research data as well as anonymized "
    "live behavioral events.\n"
    "- **Privacy:** incoming identifiers are pseudonymized before analytics "
    "processing, while downstream analysis operates on privacy-preserving data.\n"
    "- **Model state:** causal estimates and recommendations can be recomputed "
    "on demand from the current database contents.\n"
    "- **Pipeline stages:** Event Data → Privacy/Minimization → Database → "
    "Processing → Journey Reconstruction → Behavioral Analytics → Segmentation → "
    "Causal Inference → Intervention Identification → What-If Simulation → "
    "Intervention Ranking → Explainable Recommendation → Dashboard.\n"
)


# ============================================================
# FOOTER
# ============================================================

project_footer()