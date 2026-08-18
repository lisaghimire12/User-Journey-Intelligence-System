import pandas as pd
import streamlit as st
import plotly.express as px

from src import database
from src.behavioral_analysis import compute_kpis, dropoff_by_stage
from src.config import PROJECT_TITLE
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import page_header, project_footer, plotly_layout_defaults


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
    "Research Prototype",
    "How are users moving through the platform?",
    PROJECT_TITLE,
)


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
       SUBTEXT
       ======================================================== */

    .subtext {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       NORMAL CARDS
       ======================================================== */

    .card {{
        background-color: {OFFWHITE} !important;
        border: 1px solid {TAUPE} !important;
        color: {ESPRESSO} !important;
    }}

    .card b {{
        color: {ESPRESSO} !important;
    }}

    .card p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .card span {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       EYEBROW
       ======================================================== */

    .eyebrow {{
        color: {TERRACOTTA} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       HEADLINE
       ======================================================== */

    .headline {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       METRIC LABELS
       ======================================================== */

    div[data-testid="stMetricLabel"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       METRIC VALUES
       ======================================================== */

    div[data-testid="stMetricValue"] {{
        color: {TERRACOTTA} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricValue"] > div {{
        color: {TERRACOTTA} !important;
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
       INFO BOX
       ======================================================== */

    div[data-testid="stAlert"] {{
        color: {ESPRESSO} !important;
    }}

    div[data-testid="stAlert"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       CODE TEXT INSIDE CARDS
       ======================================================== */

    code {{
        color: {TERRACOTTA} !important;
        background-color: {SAND} !important;
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
# CHECK DATA
# ============================================================

if not has_data():

    st.markdown(
        '<div class="card">No data has been loaded yet. Run '
        '<code>python scripts/run_pipeline.py --reset</code> from the project root, '
        'then reopen this page.</div>',
        unsafe_allow_html=True,
    )

    st.stop()


# ============================================================
# LOAD DATA
# ============================================================

sessions_pd, journeys, merged, transitions = load_pipeline_data()

kpis = compute_kpis(journeys, sessions_pd)


# ============================================================
# SESSION SUMMARY
# ============================================================

st.markdown(
    f'<div class="subtext" style="margin-top:-1rem;">'
    f'Analysis of {kpis["total_sessions"]:,} anonymized sessions'
    f'</div>',
    unsafe_allow_html=True,
)


# ============================================================
# KPI METRICS
# ============================================================

c1, c2, c3, c4 = st.columns(4)

c1.metric(
    "Total sessions",
    f"{kpis['total_sessions']:,}",
)

c2.metric(
    "Conversion rate",
    f"{kpis['conversion_rate']}%",
)

c3.metric(
    "Abandonment rate",
    f"{kpis['abandonment_rate']}%",
)

c4.metric(
    "Avg. journey duration",
    f"{kpis['avg_duration']:.0f}s",
)


c5, c6, c7 = st.columns(3)

c5.metric(
    "Avg. journey length",
    f"{kpis['avg_length']} pages",
)

c6.metric(
    "Top entry page",
    kpis["top_entry"],
)

c7.metric(
    "Top exit page",
    kpis["top_exit"],
)


# ============================================================
# WHERE SESSIONS ARE BEING LOST
# ============================================================

st.markdown("### Where sessions are being lost")

dropoff = dropoff_by_stage(journeys)

col_a, col_b = st.columns([2, 1])


# ============================================================
# DROPOFF CHART
# ============================================================

with col_a:

    if not dropoff.empty:

        fig = px.bar(
            dropoff,
            x="stage",
            y="sessions",
            text="share_pct",
            labels={
                "stage": "Abandonment stage",
                "sessions": "Sessions",
            },
        )

        fig.update_traces(
            texttemplate="%{text}%",
            textposition="outside",
            marker=dict(
                color=TERRACOTTA,
            ),
            textfont=dict(
                color=ESPRESSO,
            ),
        )

        # IMPORTANT:
        # plotly_layout_defaults() may already contain font,
        # so modify the returned dictionary rather than passing
        # another font argument to update_layout().

        chart_layout = plotly_layout_defaults()

        chart_layout["font"] = dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
        )

        chart_layout["paper_bgcolor"] = OFFWHITE
        chart_layout["plot_bgcolor"] = OFFWHITE

        chart_layout["xaxis"] = dict(
            title=dict(
                text="Abandonment stage",
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
            zeroline=False,
        )

        chart_layout["yaxis"] = dict(
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
            zeroline=False,
            gridcolor=TAUPE,
        )

        fig.update_layout(
            **chart_layout
        )

        st.plotly_chart(
            fig,
            width="stretch",
        )

    else:

        st.info(
            "No abandonment recorded in the current dataset."
        )


# ============================================================
# TOP INSIGHT
# ============================================================

with col_b:

    st.markdown(
        '<div class="card">',
        unsafe_allow_html=True,
    )

    st.markdown("**Top insight**")

    if not dropoff.empty:

        top = dropoff.iloc[0]

        st.write(
            f"The largest share of non-converting sessions abandon at the "
            f"**{top['stage']}** stage ({top['share_pct']}% of abandonments). "
            f"See the Causal Analysis page to check whether related friction "
            f"factors actually influence this."
        )

    else:

        st.write(
            "Not enough abandonment data yet."
        )

    st.markdown(
        "</div>",
        unsafe_allow_html=True,
    )


# ============================================================
# TOP RECOMMENDATION
# ============================================================

st.markdown("### Top recommendation")

recs_df = database.read_table("recommendations")


if not recs_df.empty:

    top_rec = recs_df.sort_values(
        "recommendation_score",
        ascending=False,
    ).iloc[0]

    st.markdown(
        f'<div class="card">'
        f'<span class="eyebrow">Recommended intervention</span>'
        f'<div class="headline" style="font-size:1.4rem;">'
        f'{top_rec["intervention"]}'
        f'</div>'
        f'<p style="color:{ESPRESSO} !important; opacity:1 !important;">'
        f'{top_rec["explanation"]}'
        f'</p>'
        f'<b>Recommendation score:</b> '
        f'{top_rec["recommendation_score"]}/10 '
        f'&nbsp;&middot;&nbsp; '
        f'<b>Confidence:</b> '
        f'{top_rec["confidence"]}'
        f'</div>',
        unsafe_allow_html=True,
    )

else:

    st.info(
        "No recommendations computed yet. Run "
        "`python scripts/run_pipeline.py` to generate them, "
        "or visit the Recommendations page."
    )


# ============================================================
# FOOTER
# ============================================================

project_footer()