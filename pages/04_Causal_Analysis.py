import plotly.graph_objects as go
import streamlit as st

from src import causal_analysis, database
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import page_header, plotly_layout_defaults, project_footer


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
    "Causal Analysis",
    "What appears to actually influence conversion?",
    "Backdoor-adjusted causal effect estimation via DoWhy, "
    "with confidence intervals and refutation checks",
)


# ============================================================
# PAGE STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GENERAL TEXT
       ======================================================== */

    .stMarkdown,
    .stMarkdown p,
    .stMarkdown span,
    .stMarkdown strong {
        color: #32180F !important;
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
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ========================================================
       SELECTBOX LABEL
       ======================================================== */

    div[data-testid="stSelectbox"] label {
        color: #32180F !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }


    /* ========================================================
       SELECTBOX
       ======================================================== */

    div[data-testid="stSelectbox"] [role="combobox"] {
        background-color: #FCFAF6 !important;
        color: #32180F !important;
        border: 1px solid #D8CFC3 !important;
        border-radius: 6px !important;
    }


    div[data-testid="stSelectbox"] [role="combobox"] * {
        color: #32180F !important;
    }


    /* ========================================================
       DROPDOWN OPTIONS
       ======================================================== */

    ul[role="listbox"] {
        background-color: #FCFAF6 !important;
    }


    li[role="option"] {
        background-color: #FCFAF6 !important;
        color: #32180F !important;
    }


    li[role="option"]:hover {
        background-color: #E9DED1 !important;
        color: #32180F !important;
    }


    /* ========================================================
       METRICS
       ======================================================== */

    div[data-testid="stMetric"] {
        background-color: #FCFAF6 !important;
        border: 1px solid #D8CFC3 !important;
        border-radius: 8px !important;
        padding: 16px !important;
    }


    div[data-testid="stMetricLabel"],
    div[data-testid="stMetricLabel"] p {
        color: #32180F !important;
        opacity: 1 !important;
    }


    div[data-testid="stMetricValue"],
    div[data-testid="stMetricValue"] div {
        color: #9B3F24 !important;
        opacity: 1 !important;
    }


    /* ========================================================
       CAPTIONS
       ======================================================== */

    div[data-testid="stCaptionContainer"] p {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ========================================================
       EXPANDER
       ======================================================== */

    div[data-testid="stExpander"] {
        background-color: #FCFAF6 !important;
        border: 1px solid #D8CFC3 !important;
        border-radius: 8px !important;
    }


    div[data-testid="stExpander"] summary {
        color: #32180F !important;
    }


    div[data-testid="stExpander"] summary span {
        color: #32180F !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #D8CFC3 !important;
    }


    /* ========================================================
       ALERTS
       ======================================================== */

    div[data-testid="stAlert"] {
        background-color: #F7F1E8 !important;
        border: 1px solid #D8CFC3 !important;
    }


    div[data-testid="stAlert"] p {
        color: #32180F !important;
        opacity: 1 !important;
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


if journeys.empty:

    st.info(
        "No journeys available for causal analysis."
    )

    st.stop()


# ============================================================
# PREPARE CAUSAL DATA
# ============================================================

causal_df = journeys.merge(
    sessions_pd,
    on="session_id",
    how="left",
)


# ============================================================
# CAUSAL QUESTION DROPDOWN
# ============================================================

st.markdown("### Causal question")

st.caption(
    "Choose a causal question to estimate how a specific "
    "behavioral factor is associated with conversion after "
    "adjusting for the stated confounder."
)


question_labels = {
    q["id"]: q["question"]
    for q in causal_analysis.CAUSAL_QUESTIONS
}


question_ids = list(question_labels.keys())


selected_id = st.selectbox(
    "Causal question",
    question_ids,
    format_func=lambda k: question_labels[k],
    key="causal_question_selector",
)


# ============================================================
# GET SELECTED QUESTION
# ============================================================

q = next(
    q
    for q in causal_analysis.CAUSAL_QUESTIONS
    if q["id"] == selected_id
)


# ============================================================
# SELECTED QUESTION DETAILS
# ============================================================

st.markdown(
    f"**Selected question:** {q['question']}"
)

st.markdown(
    f"**Treatment:** {q['treatment_label']}  \n"
    f"**Outcome:** conversion (purchase)  \n"
    f"**Confounders adjusted for:** "
    f"{', '.join(q['confounders'])}"
)


# ============================================================
# ASSUMED CAUSAL GRAPH
# ============================================================

with st.expander("Assumed causal graph"):

    st.markdown(
        f"**Confounder:** {q['confounders'][0]}"
    )

    st.caption(
        "This observed variable is treated as a confounder "
        "affecting both the treatment and the outcome."
    )

    st.markdown(
        f"**Treatment:** {q['treatment_label']}"
    )

    st.markdown(
        "**Outcome:** conversion (purchase)"
    )

    st.markdown(
        f"`{q['confounders'][0]}` "
        "→ "
        f"`{q['treatment_label']}` "
        "→ "
        "`conversion`"
    )


# ============================================================
# CAUSAL ANALYSIS
# ============================================================

result = causal_analysis.estimate_effect(
    causal_df,
    treatment_raw=q["treatment_raw"],
    outcome=q["outcome"],
    confounders=q["confounders"],
    treatment_label=q["treatment_label"],
    beneficial_direction=q.get(
        "beneficial_direction",
        "low",
    ),
)


# ============================================================
# INSUFFICIENT EVIDENCE
# ============================================================

if result.status == "insufficient_evidence":

    st.warning(
        "Insufficient evidence for reliable causal estimation."
    )

    st.markdown(
        f"**Details:** {result.message}"
    )


# ============================================================
# RESULTS
# ============================================================

else:

    # --------------------------------------------------------
    # METRICS
    # --------------------------------------------------------

    c1, c2, c3 = st.columns(3)

    with c1:

        st.metric(
            "Effect estimate",
            f"{result.effect_estimate * 100:+.2f} pts",
        )

    with c2:

        st.metric(
            "95% CI",
            f"[{result.ci_lower * 100:.2f}, "
            f"{result.ci_upper * 100:.2f}]",
        )

    with c3:

        st.metric(
            "Sample size",
            f"{result.sample_size:,}",
        )


    # --------------------------------------------------------
    # EFFECT GRAPH
    # --------------------------------------------------------

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=[
                result.effect_estimate * 100
            ],
            y=["Effect"],
            error_x=dict(
                type="data",
                symmetric=False,
                array=[
                    (
                        result.ci_upper
                        - result.effect_estimate
                    ) * 100
                ],
                arrayminus=[
                    (
                        result.effect_estimate
                        - result.ci_lower
                    ) * 100
                ],
            ),
            mode="markers",
            marker=dict(
                size=14,
                color=TERRACOTTA,
            ),
        )
    )


    # Zero-effect reference line
    fig.add_vline(
        x=0,
        line_dash="dash",
        line_color=TAUPE,
    )


    # --------------------------------------------------------
    # PLOTLY LAYOUT
    # --------------------------------------------------------

    causal_layout = plotly_layout_defaults()

    # Replace the existing font safely.
    causal_layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
    )

    causal_layout["xaxis"] = dict(
        title=dict(
            text=(
                "Effect on conversion probability "
                "(percentage points)"
            ),
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

    causal_layout["yaxis"] = dict(
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

    causal_layout["paper_bgcolor"] = OFFWHITE
    causal_layout["plot_bgcolor"] = OFFWHITE
    causal_layout["height"] = 260


    fig.update_layout(
        **causal_layout
    )


    st.plotly_chart(
        fig,
        width="stretch",
    )


    # --------------------------------------------------------
    # METHOD
    # --------------------------------------------------------

    st.markdown(
        f"**Method:** {result.method}"
    )


    # --------------------------------------------------------
    # ASSUMPTIONS
    # --------------------------------------------------------

    st.markdown(
        f"**Assumptions:** {result.assumptions}"
    )


    # --------------------------------------------------------
    # REFUTATION CHECK
    # --------------------------------------------------------

    if result.refutation_passed is not None:

        icon = (
            "✓"
            if result.refutation_passed
            else "!"
        )

        st.markdown(
            f"**Refutation check ({icon}):** "
            f"{result.refutation_detail}"
        )


    # --------------------------------------------------------
    # DISCLAIMER
    # --------------------------------------------------------

    st.caption(
        "Causal estimates depend on the data and assumptions "
        "of the causal model."
    )


    # --------------------------------------------------------
    # SAVE RESULT
    # --------------------------------------------------------

    database.write_causal_result(
        {
            "treatment": result.treatment,
            "outcome": result.outcome,
            "effect_estimate": result.effect_estimate,
            "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper,
            "method": result.method,
            "sample_size": result.sample_size,
            "assumptions": result.assumptions,
            "refutation_passed": result.refutation_passed,
        }
    )


# ============================================================
# FOOTER
# ============================================================

project_footer()