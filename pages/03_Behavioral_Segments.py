import plotly.express as px
import streamlit as st

from src.pipeline_state import has_data, load_pipeline_data
from src.segmentation import compute_segments
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
# PAGE HEADER
# ============================================================

page_header(
    "Behavioral Segments",
    "Which distinct behavioral groups exist in the data?",
    "Segments are derived from K-Means clustering over journey "
    "features, then labeled by their own statistical profile",
)


# ============================================================
# PAGE-SPECIFIC STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ======================================================
       GENERAL PAGE TEXT
       ====================================================== */

    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown strong {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ======================================================
       HEADINGS
       ====================================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ======================================================
       SLIDER
       ====================================================== */

    div[data-testid="stSlider"] label {
        color: #32180F !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }

    div[data-testid="stSlider"] [data-testid="stThumbValue"] {
        color: #9B3F24 !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }

    div[data-testid="stSlider"] [data-testid="stTickBarMin"],
    div[data-testid="stSlider"] [data-testid="stTickBarMax"] {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ======================================================
       CAPTIONS
       ====================================================== */

    div[data-testid="stCaptionContainer"] p {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ======================================================
       METRIC LABELS
       ====================================================== */

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ======================================================
       METRIC VALUES
       ====================================================== */

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: #9B3F24 !important;
        opacity: 1 !important;
    }


    /* ======================================================
       DIVIDERS
       ====================================================== */

    hr {
        border-color: #D8CFC3 !important;
    }


    /* ======================================================
       ALERTS / INFO / WARNING
       ====================================================== */

    div[data-testid="stAlert"],
    div[data-testid="stAlert"] p {
        color: #32180F !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# CHECK DATA
# ============================================================

if not has_data():

    st.info(
        "No data loaded yet. Run "
        "`python scripts/run_pipeline.py --reset`."
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

sessions_pd, journeys, merged, transitions = load_pipeline_data()


if merged.empty:

    st.info(
        "Not enough data to compute engagement scores yet."
    )

    st.stop()


# ============================================================
# SLIDER
# ============================================================

st.markdown("### Number of behavioral segments")

st.caption(
    "Choose how many K-Means clusters should be used "
    "to group users by their observed journey behavior."
)


n_clusters = st.slider(
    "Number of segments",
    min_value=2,
    max_value=6,
    value=4,
    step=1,
    key="behavioral_segments_slider",
)


# ============================================================
# CURRENT SLIDER VALUE
# ============================================================

st.markdown(
    f"**Currently analyzing: {n_clusters} behavioral segments**"
)


# ============================================================
# K-MEANS
# ============================================================

assigned, summary = compute_segments(
    merged,
    n_clusters=n_clusters,
    random_state=42,
)


# ============================================================
# CHECK RESULTS
# ============================================================

if summary.empty:

    st.warning(
        "Not enough sessions to form statistically "
        "reportable segments "
        "(each segment must contain at least 5 sessions)."
    )

    st.stop()


# ============================================================
# RESULT SUMMARY
# ============================================================

st.markdown(
    f"**K-Means produced {len(summary)} reportable "
    f"behavioral groups from {len(assigned):,} sessions.**"
)


# ============================================================
# CHARTS
# ============================================================

col1, col2 = st.columns(2)


# ============================================================
# SEGMENT DISTRIBUTION
# ============================================================

with col1:

    st.markdown("### Segment distribution")

    fig = px.pie(
        summary,
        names="segment",
        values="segment_size",
        hole=0.45,
    )

    # Get the existing project layout.
    layout = plotly_layout_defaults()

    # Replace the existing font safely.
    layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
    )

    # Legend
    layout["legend"] = dict(
        font=dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
            size=13,
        )
    )

    # Background
    layout["paper_bgcolor"] = OFFWHITE
    layout["plot_bgcolor"] = OFFWHITE

    fig.update_layout(**layout)

    # Pie percentages
    fig.update_traces(
        textfont=dict(
            family="Inter, sans-serif",
            color=WHITE,
            size=13,
        ),
    )

    st.plotly_chart(
        fig,
        width="stretch",
    )


# ============================================================
# CONVERSION RATE
# ============================================================

with col2:

    st.markdown("### Conversion rate by segment")

    conversion_data = summary.sort_values(
        "conversion_rate"
    )

    fig2 = px.bar(
        conversion_data,
        x="conversion_rate",
        y="segment",
        orientation="h",
        labels={
            "conversion_rate": "Conversion rate (%)",
            "segment": "",
        },
    )

    # Get the existing project layout.
    layout2 = plotly_layout_defaults()

    # Main Plotly font.
    layout2["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
    )

    # X axis.
    layout2["xaxis"] = dict(
        title=dict(
            text="Conversion rate (%)",
            font=dict(
                family="Inter, sans-serif",
                color=ESPRESSO,
                size=14,
            ),
        ),
        tickfont=dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
            size=12,
        ),
        color=ESPRESSO,
        showline=True,
        linecolor=TAUPE,
        zeroline=False,
        gridcolor=SAND,
    )

    # Y axis.
    layout2["yaxis"] = dict(
        title=dict(
            text="",
            font=dict(
                family="Inter, sans-serif",
                color=ESPRESSO,
            ),
        ),
        tickfont=dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
            size=12,
        ),
        color=ESPRESSO,
        showline=False,
        zeroline=False,
    )

    # Background.
    layout2["paper_bgcolor"] = OFFWHITE
    layout2["plot_bgcolor"] = OFFWHITE

    fig2.update_layout(**layout2)

    # Bar color from your palette.
    fig2.update_traces(
        marker=dict(
            color=RUST,
        ),
        textfont=dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
        ),
    )

    st.plotly_chart(
        fig2,
        width="stretch",
    )


# ============================================================
# SEGMENT PROFILES
# ============================================================

st.markdown("### Segment profiles")

st.caption(
    "Each profile summarizes the observed behavior "
    "of the users assigned to that cluster."
)


for _, row in summary.iterrows():

    # --------------------------------------------------------
    # SEGMENT NAME
    # --------------------------------------------------------

    st.markdown(
        f"#### {row['segment']}"
    )


    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    c1, c2, c3, c4, c5 = st.columns(5)


    with c1:

        st.metric(
            "Sessions",
            f"{int(row['segment_size']):,}",
        )


    with c2:

        st.metric(
            "Conversion",
            f"{row['conversion_rate']}%",
        )


    with c3:

        st.metric(
            "Avg. pages",
            row["avg_journey_length"],
        )


    with c4:

        st.metric(
            "Avg. duration",
            f"{row['avg_duration']:.0f}s",
        )


    with c5:

        st.metric(
            "Engagement",
            row["avg_engagement"],
        )


    # --------------------------------------------------------
    # COMMON PATH
    # --------------------------------------------------------

    st.markdown(
        f"**Common path:** {row['common_path']}"
    )


    # --------------------------------------------------------
    # SEPARATOR
    # --------------------------------------------------------

    st.divider()


# ============================================================
# FOOTER
# ============================================================

project_footer()