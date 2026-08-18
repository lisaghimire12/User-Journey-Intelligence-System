import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.behavioral_analysis import (
    dropoff_by_stage,
    journey_length_distribution,
)
from src.data_processing import (
    apply_filters,
    clean_events,
    load_raw_events,
)
from src.journey_reconstruction import (
    compute_transition_matrix,
    top_journeys,
)
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import (
    page_header,
    plotly_layout_defaults,
    project_footer,
)


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
# PAGE-SPECIFIC COLOR STYLING
# ============================================================

st.markdown(
    f"""
    <style>

    /* ========================================================
       GENERAL TEXT
       ======================================================== */

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

    /* ========================================================
       HEADINGS
       ======================================================== */

    h3 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    h4 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       SIDEBAR
       ======================================================== */

    section[data-testid="stSidebar"] {{
        background-color: {CREAM} !important;
    }}

    section[data-testid="stSidebar"] * {{
        color: {ESPRESSO} !important;
    }}

    section[data-testid="stSidebar"] label {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    section[data-testid="stSidebar"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       CAPTIONS
       ======================================================== */

    div[data-testid="stCaptionContainer"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stCaptionContainer"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       INFO BOXES
       ======================================================== */

    div[data-testid="stAlert"] {{
        color: {ESPRESSO} !important;
    }}

    div[data-testid="stAlert"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       DATAFRAME
       ======================================================== */

    div[data-testid="stDataFrame"] {{
        border: 1px solid {TAUPE} !important;
    }}

    /* ========================================================
       RADIO BUTTONS
       ======================================================== */

    div[data-testid="stRadio"] label {{
        color: {ESPRESSO} !important;
    }}

    div[data-testid="stRadio"] p {{
        color: {ESPRESSO} !important;
    }}

    /* ========================================================
       MULTISELECT
       ======================================================== */

    div[data-testid="stMultiSelect"] label {{
        color: {ESPRESSO} !important;
    }}

    /* ========================================================
       DIVIDERS
       ======================================================== */

    hr {{
        border-color: {TAUPE} !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PAGE HEADER
# ============================================================

page_header(
    "Journey Explorer",
    "What paths do users actually take?",
    "Reconstructed, non-linear user journeys from raw event sequences",
)


# ============================================================
# CHECK WHETHER PIPELINE DATA EXISTS
# ============================================================

if not has_data():
    st.info(
        "No data loaded yet. Run "
        "`python scripts/run_pipeline.py --reset`."
    )
    st.stop()


# ============================================================
# LOAD PIPELINE DATA
# ============================================================

sessions_pd, journeys, merged, transitions = load_pipeline_data()


# ============================================================
# SIDEBAR FILTERS
# ============================================================

with st.sidebar:
    st.markdown("**Filters**")

    device = st.multiselect(
        "Device",
        sorted(
            sessions_pd["device_type"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

    platform = st.multiselect(
        "Platform",
        sorted(
            sessions_pd["platform"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

    source = st.multiselect(
        "Acquisition source",
        sorted(
            sessions_pd["acquisition_source"]
            .dropna()
            .unique()
            .tolist()
        ),
    )

    conv_filter = st.radio(
        "Conversion",
        ["all", "converted", "not_converted"],
        horizontal=False,
    )


# ============================================================
# APPLY SESSION FILTERS
# ============================================================

filtered_sessions = apply_filters(
    sessions_pd,
    device,
    platform,
    source,
    conv_filter,
)


# ============================================================
# FILTER JOURNEYS USING FILTERED SESSION IDs
# ============================================================

filtered_journeys = journeys[
    journeys["session_id"].isin(
        filtered_sessions["session_id"]
    )
].copy()


# ============================================================
# FILTER RAW EVENTS
# ============================================================

filtered_transitions = pd.DataFrame(
    columns=["source", "target", "count"]
)

if not filtered_sessions.empty:

    filtered_session_ids = set(
        filtered_sessions["session_id"]
    )

    raw_events = load_raw_events()

    if not raw_events.empty:

        filtered_events = raw_events[
            raw_events["session_id"].isin(
                filtered_session_ids
            )
        ].copy()

        if not filtered_events.empty:

            filtered_events_pl = clean_events(
                filtered_events
            )

            filtered_transitions = compute_transition_matrix(
                filtered_events_pl
            )


# ============================================================
# FILTER SUMMARY
# ============================================================

st.caption(
    f"Showing {len(filtered_sessions):,} of "
    f"{len(sessions_pd):,} sessions · "
    f"{len(filtered_journeys):,} journeys"
)


# ============================================================
# SANKEY
# ============================================================

st.markdown("### Major transition flow (Sankey)")


if not filtered_transitions.empty:

    top_edges = filtered_transitions.head(25)

    nodes = list(
        pd.unique(
            top_edges[
                ["source", "target"]
            ].values.ravel()
        )
    )

    node_index = {
        node: index
        for index, node in enumerate(nodes)
    }

    fig = go.Figure(
        data=[
            go.Sankey(

                node=dict(
                    pad=16,
                    thickness=16,
                    label=nodes,

                    # Palette
                    color=TERRACOTTA,

                    line=dict(
                        color=TAUPE,
                        width=0.5,
                    ),
                ),

                link=dict(
                    source=[
                        node_index[source]
                        for source in top_edges["source"]
                    ],

                    target=[
                        node_index[target]
                        for target in top_edges["target"]
                    ],

                    value=top_edges["count"],

                    # Transparent Terracotta
                    color="rgba(155,63,36,0.25)",
                ),
            )
        ]
    )

    # --------------------------------------------------------
    # Plotly layout
    #
    # IMPORTANT:
    # We modify the existing layout dictionary rather than
    # passing duplicate font arguments.
    # --------------------------------------------------------

    sankey_layout = plotly_layout_defaults()

    sankey_layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
        size=12,
    )

    sankey_layout["paper_bgcolor"] = OFFWHITE
    sankey_layout["plot_bgcolor"] = OFFWHITE

    sankey_layout["height"] = 420

    fig.update_layout(
        **sankey_layout
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )

else:

    st.info(
        "No transition data matches the current filters."
    )


# ============================================================
# TOP JOURNEYS + JOURNEY LENGTH DISTRIBUTION
# ============================================================

col1, col2 = st.columns(2)


# ------------------------------------------------------------
# TOP JOURNEYS
# ------------------------------------------------------------

with col1:

    st.markdown("### Top journeys")

    tj = top_journeys(
        filtered_journeys,
        n=10,
    )

    if not tj.empty:

        st.dataframe(
            tj,
            width="stretch",
            hide_index=True,
        )

    else:

        st.info(
            "No journeys match the current filters."
        )


# ------------------------------------------------------------
# JOURNEY LENGTH DISTRIBUTION
# ------------------------------------------------------------

with col2:

    st.markdown("### Journey length distribution")

    dist = journey_length_distribution(
        filtered_journeys
    )

    if not dist.empty:

        fig2 = px.histogram(
            dist,
            x="journey_length",
            nbins=20,
            labels={
                "journey_length": "Pages per journey"
            },
        )

        # ----------------------------------------------------
        # Histogram color
        # ----------------------------------------------------

        fig2.update_traces(
            marker=dict(
                color=RUST,
                line=dict(
                    color=TAUPE,
                    width=0.5,
                ),
            )
        )

        # ----------------------------------------------------
        # Plotly layout
        # ----------------------------------------------------

        histogram_layout = plotly_layout_defaults()

        histogram_layout["font"] = dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
            size=12,
        )

        histogram_layout["paper_bgcolor"] = OFFWHITE
        histogram_layout["plot_bgcolor"] = OFFWHITE

        histogram_layout["xaxis"] = dict(
            title=dict(
                text="Pages per journey",
                font=dict(
                    color=ESPRESSO,
                    size=14,
                ),
            ),
            tickfont=dict(
                color=ESPRESSO,
                size=12,
            ),
            color=ESPRESSO,
            showline=True,
            linecolor=TAUPE,
            gridcolor=TAUPE,
        )

        histogram_layout["yaxis"] = dict(
            title=dict(
                text="Count",
                font=dict(
                    color=ESPRESSO,
                    size=14,
                ),
            ),
            tickfont=dict(
                color=ESPRESSO,
                size=12,
            ),
            color=ESPRESSO,
            showline=True,
            linecolor=TAUPE,
            gridcolor=TAUPE,
        )

        fig2.update_layout(
            **histogram_layout
        )

        st.plotly_chart(
            fig2,
            width="stretch",
        )

    else:

        st.info(
            "No journeys to plot."
        )


# ============================================================
# DROP-OFF BY STAGE
# ============================================================

st.markdown("### Drop-off by stage")

dropoff = dropoff_by_stage(
    filtered_journeys
)


if not dropoff.empty:

    fig3 = px.bar(
        dropoff,
        x="stage",
        y="sessions",
        text="share_pct",
    )

    # --------------------------------------------------------
    # Bar styling
    # --------------------------------------------------------

    fig3.update_traces(
        texttemplate="%{text}%",
        textposition="outside",

        marker=dict(
            color=TERRACOTTA,
        ),

        textfont=dict(
            color=ESPRESSO,
        ),
    )

    # --------------------------------------------------------
    # Plotly layout
    # --------------------------------------------------------

    dropoff_layout = plotly_layout_defaults()

    dropoff_layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
        size=12,
    )

    dropoff_layout["paper_bgcolor"] = OFFWHITE
    dropoff_layout["plot_bgcolor"] = OFFWHITE

    dropoff_layout["xaxis"] = dict(
        title=dict(
            text="Stage",
            font=dict(
                color=ESPRESSO,
                size=14,
            ),
        ),
        tickfont=dict(
            color=ESPRESSO,
            size=12,
        ),
        color=ESPRESSO,
        showline=True,
        linecolor=TAUPE,
        gridcolor=TAUPE,
    )

    dropoff_layout["yaxis"] = dict(
        title=dict(
            text="Sessions",
            font=dict(
                color=ESPRESSO,
                size=14,
            ),
        ),
        tickfont=dict(
            color=ESPRESSO,
            size=12,
        ),
        color=ESPRESSO,
        showline=True,
        linecolor=TAUPE,
        gridcolor=TAUPE,
    )

    fig3.update_layout(
        **dropoff_layout
    )

    st.plotly_chart(
        fig3,
        width="stretch",
    )

else:

    st.info(
        "No drop-off data matches the current filters."
    )


# ============================================================
# FOOTER
# ============================================================

project_footer()