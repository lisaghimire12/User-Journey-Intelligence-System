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
#
# THIS IS THE IMPORTANT FIX.
#
# Previously the Sankey was always using the original
# `transitions` dataframe, so changing the sidebar filters
# did not change the Sankey.
#
# Now we take only the events belonging to the filtered
# sessions and rebuild the transition matrix.
# ============================================================

filtered_transitions = pd.DataFrame(
    columns=["source", "target", "count"]
)

if not filtered_sessions.empty:

    # Get the session IDs that survived the filters
    filtered_session_ids = set(
        filtered_sessions["session_id"]
    )

    # Load raw events from the database
    raw_events = load_raw_events()

    if not raw_events.empty:

        # Keep only events belonging to filtered sessions
        filtered_events = raw_events[
            raw_events["session_id"].isin(
                filtered_session_ids
            )
        ].copy()

        if not filtered_events.empty:

            # Clean/type-normalize events using the existing
            # project preprocessing function
            filtered_events_pl = clean_events(
                filtered_events
            )

            # Rebuild the transition matrix ONLY from the
            # filtered events
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

    # Take the 25 most common transitions AFTER filtering
    top_edges = filtered_transitions.head(25)

    # Get unique page names
    nodes = list(
        pd.unique(
            top_edges[
                ["source", "target"]
            ].values.ravel()
        )
    )

    # Map each node to a numeric index
    node_index = {
        node: index
        for index, node in enumerate(nodes)
    }

    # Create Sankey diagram
    fig = go.Figure(
        data=[
            go.Sankey(

                node=dict(
                    pad=16,
                    thickness=16,
                    label=nodes,
                    color="#9B3F24",
                    line=dict(
                        color="#D8CFC3",
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

                    color="rgba(155,63,36,0.25)",
                ),
            )
        ]
    )

    fig.update_layout(
        **plotly_layout_defaults(),
        height=420,
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

        fig2.update_layout(
            **plotly_layout_defaults()
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

    fig3.update_traces(
        texttemplate="%{text}%",
        textposition="outside",
    )

    fig3.update_layout(
        **plotly_layout_defaults()
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