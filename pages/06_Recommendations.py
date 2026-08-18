import streamlit as st

from src import database
from src.behavioral_analysis import compute_kpis, dropoff_by_stage
from src.explanation_engine import build_explanation, build_llm_summary
from src.pipeline_state import has_data, load_pipeline_data
from src.recommendation_engine import build_recommendations
from src.ui_theme import complexity_pill, page_header, project_footer


# ============================================================
# COLOR PALETTE
# ============================================================

ESPRESSO = "#32180F"
DARK_RED = "#95271D"
MUTED_RED = "#B34A44"

CREAM = "#F7F1E8"
OFFWHITE = "#FCFAF6"
TAUPE = "#D8CFC3"
SAND = "#E9DED1"

WHITE = "#FFFFFF"


# ============================================================
# PAGE HEADER
# ============================================================

page_header(
    "Recommendations",
    "Which intervention should we prioritize?",
    "Interventions ranked using causal effects, simulation results, "
    "affected users, complexity, risk, and uncertainty",
)


# ============================================================
# PAGE-SPECIFIC CSS
# ============================================================

recommendation_css = """
<style>

    /* ========================================================
       GENERAL PAGE TEXT
       ======================================================== */

    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown div,
    .stMarkdown strong,
    .stMarkdown b {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       HEADINGS
       ======================================================== */

    h1,
    h2,
    h3,
    h4,
    h5,
    h6 {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       CAPTIONS
       ======================================================== */

    div[data-testid="stCaptionContainer"] p {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       EXPANDERS
       ======================================================== */

    div[data-testid="stExpander"] {
        background-color: __OFFWHITE__ !important;
        border: 1px solid __TAUPE__ !important;
        border-radius: 8px !important;
    }

    div[data-testid="stExpander"] summary {
        color: __ESPRESSO__ !important;
    }

    div[data-testid="stExpander"] summary p,
    div[data-testid="stExpander"] summary span {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }


    /* ========================================================
       METRIC LABELS
       ======================================================== */

    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       METRIC VALUES
       ======================================================== */

    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: __DARK_RED__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       METRIC SECONDARY TEXT
       ======================================================== */

    div[data-testid="stMetricDelta"] {
        color: __MUTED_RED__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       INFO / WARNING BOXES
       ======================================================== */

    div[data-testid="stAlert"] {
        background-color: __CREAM__ !important;
        border: 1px solid __TAUPE__ !important;
    }

    div[data-testid="stAlert"] p,
    div[data-testid="stAlert"] span {
        color: __ESPRESSO__ !important;
        opacity: 1 !important;
    }


    /* ========================================================
       DIVIDERS
       ======================================================== */

    hr {
        border-color: __TAUPE__ !important;
    }


    /* ========================================================
       LINKS
       ======================================================== */

    a {
        color: __DARK_RED__ !important;
    }


    /* ========================================================
       RECOMMENDATION CARD
       ======================================================== */

    .recommendation-card {
        background-color: __OFFWHITE__;
        border: 1px solid __TAUPE__;
        border-radius: 10px;
        padding: 1.5rem;
        color: __ESPRESSO__;
    }


    /* ========================================================
       TOP RANKED LABEL
       ======================================================== */

    .recommendation-eyebrow {
        color: __DARK_RED__ !important;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        font-size: 0.75rem;
        font-weight: 700;
        margin-bottom: 0.4rem;
    }


    /* ========================================================
       RECOMMENDATION HEADLINE
       ======================================================== */

    .recommendation-headline {
        color: __ESPRESSO__ !important;
        font-size: 1.6rem;
        font-weight: 700;
        margin-bottom: 1rem;
    }


    /* ========================================================
       RECOMMENDATION STATS
       ======================================================== */

    .recommendation-stats {
        display: flex;
        gap: 2rem;
        margin: 0.6rem 0 0.8rem 0;
        flex-wrap: wrap;
    }


    .recommendation-stat {
        color: __ESPRESSO__ !important;
    }


    /* ========================================================
       RECOMMENDATION VALUES
       ======================================================== */

    .recommendation-value {
        color: __DARK_RED__ !important;
        font-size: 1.15rem;
        font-weight: 700;
    }


    /* ========================================================
       RECOMMENDATION LABELS
       ======================================================== */

    .recommendation-label {
        color: __ESPRESSO__ !important;
        font-size: 0.8rem;
        margin-top: 3px;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    div.stButton > button {
        background-color: __DARK_RED__ !important;
        color: __WHITE__ !important;
        border: 1px solid __DARK_RED__ !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }

    div.stButton > button:hover {
        background-color: __MUTED_RED__ !important;
        border-color: __MUTED_RED__ !important;
        color: __WHITE__ !important;
    }
    
/* ========================================================
   LOADING SPINNER
   ======================================================== */

div[data-testid="stSpinner"] {
    color: #32180F !important;
}

div[data-testid="stSpinner"] p {
    color: #32180F !important;
    opacity: 1 !important;
    font-weight: 500 !important;
}

/* Actual spinning circle */
div[data-testid="stSpinner"] div {
    border-color: #95271D !important;
    border-right-color: transparent !important;
}

/* If Streamlit uses an SVG spinner */
div[data-testid="stSpinner"] svg {
    color: #95271D !important;
    stroke: #95271D !important;
}

</style>
"""


# ============================================================
# SAFELY INSERT PALETTE COLORS
# ============================================================

recommendation_css = (
    recommendation_css
    .replace("__ESPRESSO__", ESPRESSO)
    .replace("__DARK_RED__", DARK_RED)
    .replace("__MUTED_RED__", MUTED_RED)
    .replace("__CREAM__", CREAM)
    .replace("__OFFWHITE__", OFFWHITE)
    .replace("__TAUPE__", TAUPE)
    .replace("__SAND__", SAND)
    .replace("__WHITE__", WHITE)
)

st.markdown(
    recommendation_css,
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


if journeys.empty:
    st.info("No journeys available.")
    st.stop()


# ============================================================
# COMPUTE KPIs
# ============================================================

kpis = compute_kpis(
    journeys,
    sessions_pd,
)

dropoff = dropoff_by_stage(
    journeys
)


# ============================================================
# BUILD RECOMMENDATIONS
# ============================================================

with st.spinner(
    "Computing recommendations "
    "(causal analysis + simulation)..."
):

    scores = build_recommendations(
        journeys,
        sessions_pd,
        kpis["conversion_rate"],
    )


# ============================================================
# SAVE RECOMMENDATIONS
# ============================================================

records = []

for s in scores:

    explanation = build_explanation(
        s,
        dropoff,
    )

    records.append(
        {
            "intervention": s.label,
            "expected_benefit": (
                s.causal_effect_pct
                or s.simulated_improvement_pct
                or 0.0
            ),
            "evidence": s.evidence,
            "confidence": s.confidence,
            "complexity": s.complexity,
            "risk": s.risk,
            "recommendation_score": s.recommendation_score,
            "explanation": explanation,
        }
    )


database.write_recommendations(records)


# ============================================================
# TOP RECOMMENDATION
# ============================================================

top = scores[0]

st.markdown(
    "### Recommended intervention"
)


# ============================================================
# TOP RECOMMENDATION CARD
# ============================================================

causal_effect = (
    top.causal_effect_pct
    if top.causal_effect_pct is not None
    else "—"
)

simulated_improvement = (
    top.simulated_improvement_pct
    if top.simulated_improvement_pct is not None
    else "—"
)


# IMPORTANT:
# The HTML tags start at the beginning of the lines.
# This prevents Streamlit from treating the HTML as a
# Markdown code block.

recommendation_card = f"""
<div class="recommendation-card">
<div class="recommendation-eyebrow">Top ranked</div>

<div class="recommendation-headline">{top.label}</div>

<div class="recommendation-stats">

<div class="recommendation-stat">
<div class="recommendation-value">{causal_effect}%</div>
<div class="recommendation-label">Estimated causal effect</div>
</div>

<div class="recommendation-stat">
<div class="recommendation-value">{simulated_improvement}%</div>
<div class="recommendation-label">Simulated improvement</div>
</div>

<div class="recommendation-stat">
<div class="recommendation-value">{top.affected_sessions_pct}%</div>
<div class="recommendation-label">Affected sessions</div>
</div>

<div class="recommendation-stat">
{complexity_pill(top.complexity)}
<div class="recommendation-label">Complexity</div>
</div>

<div class="recommendation-stat">
{complexity_pill(top.risk)}
<div class="recommendation-label">Risk</div>
</div>

<div class="recommendation-stat">
<div class="recommendation-value">{top.confidence}</div>
<div class="recommendation-label">Confidence</div>
</div>

<div class="recommendation-stat">
<div class="recommendation-value">
{top.recommendation_score} / 10
</div>
<div class="recommendation-label">Recommendation score</div>
</div>

</div>
</div>
"""


st.markdown(
    recommendation_card,
    unsafe_allow_html=True,
)


# ============================================================
# WHY IS THIS RECOMMENDED?
# ============================================================

st.markdown(
    "### Why is this recommended?"
)

det_explanation = build_explanation(
    top,
    dropoff,
)

st.write(
    det_explanation
)


# ============================================================
# LLM SUMMARY
# ============================================================

llm_summary = build_llm_summary(
    top,
    det_explanation,
)

if llm_summary:

    with st.expander(
        "Plain-language management summary "
        "(LLM-generated, numbers unchanged)"
    ):

        st.write(
            llm_summary
        )

else:

    st.caption(
        "No LLM API key configured — showing the "
        "deterministic, evidence-based explanation above. "
        "The core system requires no LLM to function."
    )


# ============================================================
# ALL RANKED INTERVENTIONS
# ============================================================

st.markdown(
    "### All ranked interventions"
)


for s in scores:

    with st.expander(
        f"{s.label}  —  "
        f"score {s.recommendation_score}/10  "
        f"({s.confidence} confidence)"
    ):

        cc1, cc2, cc3, cc4 = st.columns(4)


        # ----------------------------------------------------
        # CAUSAL EFFECT
        # ----------------------------------------------------

        with cc1:

            st.metric(
                "Causal effect",
                (
                    f"{s.causal_effect_pct}%"
                    if s.causal_effect_pct is not None
                    else "n/a"
                ),
            )


        # ----------------------------------------------------
        # SIMULATED IMPROVEMENT
        # ----------------------------------------------------

        with cc2:

            st.metric(
                "Simulated improvement",
                (
                    f"{s.simulated_improvement_pct}%"
                    if s.simulated_improvement_pct is not None
                    else "n/a"
                ),
            )


        # ----------------------------------------------------
        # AFFECTED SESSIONS
        # ----------------------------------------------------

        with cc3:

            st.metric(
                "Affected sessions",
                f"{s.affected_sessions_pct}%",
            )


        # ----------------------------------------------------
        # UNCERTAINTY
        # ----------------------------------------------------

        with cc4:

            st.metric(
                "Uncertainty",
                f"±{s.uncertainty} pts",
            )


        # ----------------------------------------------------
        # COMPLEXITY + RISK
        # ----------------------------------------------------

        st.markdown(
            f"""
<div style="color:{ESPRESSO}; margin:0.6rem 0;">
{complexity_pill(s.complexity)}
<span style="color:{ESPRESSO}; margin:0 0.4rem;">
complexity
</span>

&nbsp;

{complexity_pill(s.risk)}
<span style="color:{ESPRESSO}; margin-left:0.4rem;">
risk
</span>
</div>
""",
            unsafe_allow_html=True,
        )


        # ----------------------------------------------------
        # DESCRIPTION
        # ----------------------------------------------------

        st.write(
            s.description
        )


        # ----------------------------------------------------
        # EXPLANATION
        # ----------------------------------------------------

        st.write(
            build_explanation(
                s,
                dropoff,
            )
        )


        # ----------------------------------------------------
        # INSUFFICIENT EVIDENCE
        # ----------------------------------------------------

        if s.causal_status == "insufficient_evidence":

            st.caption(
                "Insufficient evidence for a reliable "
                "causal estimate for this intervention."
            )


# ============================================================
# FOOTER
# ============================================================

project_footer()