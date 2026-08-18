import pandas as pd
import plotly.express as px
import streamlit as st

from src import database
from src.simulation_engine import (
    SCENARIOS,
    SimulationParams,
    run_all_scenarios,
    run_simulation,
)
from src.ui_theme import (
    page_header,
    plotly_layout_defaults,
    project_footer,
)


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
    "What-If Simulator",
    "What could happen if we change something?",
    "Discrete-event simulation (SimPy) of the user funnel "
    "under adjustable parameters — every run is executed live",
)


# ============================================================
# PAGE-SPECIFIC COLOR STYLING
# ============================================================

st.markdown(
    """
    <style>

    /* ========================================================
       GENERAL PAGE TEXT
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
       SLIDER LABEL
       ======================================================== */

    div[data-testid="stSlider"] label {
        color: #32180F !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }


    /* ========================================================
       SLIDER VALUE
       ======================================================== */

    div[data-testid="stSlider"]
    [data-testid="stThumbValue"] {
        color: #95271D !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }


    /* ========================================================
       SLIDER MIN / MAX VALUES
       ======================================================== */

    div[data-testid="stSlider"]
    [data-testid="stTickBarMin"],
    div[data-testid="stSlider"]
    [data-testid="stTickBarMax"] {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ========================================================
       ACTUAL STREAMLIT SLIDER
       ======================================================== */

    div[data-testid="stSlider"] [data-baseweb="slider"] {
        width: 100%;
    }


    /* Slider thumb */
    div[data-testid="stSlider"]
    [data-baseweb="slider"]
    [role="slider"] {
        background-color: #95271D !important;
        border: 2px solid #95271D !important;
        box-shadow: none !important;
    }


    /* Slider thumb when focused */
    div[data-testid="stSlider"]
    [data-baseweb="slider"]
    [role="slider"]:focus {
        background-color: #95271D !important;
        border-color: #95271D !important;
        box-shadow: 0 0 0 2px rgba(149, 39, 29, 0.18) !important;
    }


    /* Slider filled track */
    div[data-testid="stSlider"]
    [data-baseweb="slider"] > div > div {
        background-color: #95271D !important;
    }


    /* Additional BaseWeb track override */
    div[data-testid="stSlider"]
    [data-baseweb="slider"]
    div[style*="background"] {
        background-color: #95271D !important;
    }


    /* ========================================================
       SELECT SLIDER
       ======================================================== */

    div[data-testid="stSelectSlider"] label {
        color: #32180F !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }


    div[data-testid="stSelectSlider"]
    [data-testid="stThumbValue"] {
        color: #95271D !important;
        font-weight: 700 !important;
    }


    /* ========================================================
       BUTTONS
       ======================================================== */

    div.stButton > button {
        background-color: #95271D !important;
        color: #FFFFFF !important;
        border: 1px solid #95271D !important;
        border-radius: 6px !important;
        font-weight: 600 !important;
    }


    div.stButton > button:hover {
        background-color: #B34A44 !important;
        color: #FFFFFF !important;
        border-color: #B34A44 !important;
    }


    /* ========================================================
       METRIC CARDS
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
        color: #95271D !important;
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
       INFO MESSAGE
       ======================================================== */

    div[data-testid="stAlert"] {
        background-color: #F7F1E8 !important;
        border: 1px solid #D8CFC3 !important;
    }


    div[data-testid="stAlert"] p {
        color: #32180F !important;
        opacity: 1 !important;
    }


    /* ========================================================
       DATAFRAME
       ======================================================== */

    div[data-testid="stDataFrame"] {
        border: 1px solid #D8CFC3 !important;
    }


    /* ========================================================
       DIVIDER
       ======================================================== */

    hr {
        border-color: #D8CFC3 !important;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# BUILD A SCENARIO
# ============================================================

st.markdown("### Build a scenario")


c1, c2, c3 = st.columns(3)


with c1:

    registration_friction = st.slider(
        "Registration friction",
        0,
        100,
        45,
    )

    checkout_friction = st.slider(
        "Checkout friction",
        0,
        100,
        40,
    )


with c2:

    page_delay = st.slider(
        "Page delay (seconds)",
        0.0,
        10.0,
        1.5,
        step=0.1,
    )

    content_exposure = st.slider(
        "Content exposure",
        0,
        100,
        50,
    )


with c3:

    navigation_friction = st.slider(
        "Navigation friction",
        0,
        100,
        35,
    )

    n_sessions = st.select_slider(
        "Simulated sessions",
        options=[
            500,
            1000,
            2000,
            4000,
        ],
        value=2000,
    )


# ============================================================
# RUN SIMULATION BUTTON
# ============================================================

run = st.button(
    "Run simulation",
    type="primary",
)


# ============================================================
# BASELINE
# ============================================================

baseline_params = SCENARIOS["A - Current system"]

baseline = run_simulation(
    SimulationParams(
        **{
            **baseline_params.__dict__,
            "n_sessions": n_sessions,
        }
    )
)


# ============================================================
# CUSTOM SCENARIO
# ============================================================

if run:

    scenario_params = SimulationParams(
        registration_friction=registration_friction,
        checkout_friction=checkout_friction,
        page_delay=page_delay,
        content_exposure=content_exposure,
        navigation_friction=navigation_friction,
        n_sessions=n_sessions,
    )


    scenario = run_simulation(
        scenario_params
    )


    change = round(
        scenario["conversion_rate"]
        - baseline["conversion_rate"],
        2,
    )


    # ========================================================
    # RESULT
    # ========================================================

    st.markdown("### Result")


    c1, c2, c3 = st.columns(3)


    with c1:

        st.metric(
            "Baseline (Simulated)",
            f"{baseline['conversion_rate']}%",
            help=(
                f"±{baseline['uncertainty']} "
                "pts uncertainty"
            ),
        )


    with c2:

        st.metric(
            "Scenario (Simulated)",
            f"{scenario['conversion_rate']}%",
            help=(
                f"±{scenario['uncertainty']} "
                "pts uncertainty"
            ),
        )


    with c3:

        st.metric(
            "Estimated change",
            f"{change:+.2f} pts",
        )


    st.caption(
        "All values above are Simulated / Estimated "
        "outputs of a discrete-event model, not a guarantee."
    )


    # ========================================================
    # SAVE SIMULATION
    # ========================================================

    database.write_simulation(
        {
            "scenario_name": "Custom scenario",
            "intervention": "custom",
            "parameters": scenario_params.__dict__,
            "baseline_result": baseline["conversion_rate"],
            "simulated_result": scenario["conversion_rate"],
            "improvement": change,
            "uncertainty": scenario["uncertainty"],
        }
    )


    # ========================================================
    # BREAKDOWN DATA
    # ========================================================

    breakdown = pd.DataFrame(
        [
            {
                "scenario": "Baseline",
                "outcome": "Converted",
                "sessions": baseline["converted"],
            },
            {
                "scenario": "Baseline",
                "outcome": "Registration exit",
                "sessions": baseline["registration_exit"],
            },
            {
                "scenario": "Baseline",
                "outcome": "Checkout exit",
                "sessions": baseline["checkout_exit"],
            },
            {
                "scenario": "Baseline",
                "outcome": "Browse exit",
                "sessions": baseline["browse_exit"],
            },
            {
                "scenario": "Scenario",
                "outcome": "Converted",
                "sessions": scenario["converted"],
            },
            {
                "scenario": "Scenario",
                "outcome": "Registration exit",
                "sessions": scenario["registration_exit"],
            },
            {
                "scenario": "Scenario",
                "outcome": "Checkout exit",
                "sessions": scenario["checkout_exit"],
            },
            {
                "scenario": "Scenario",
                "outcome": "Browse exit",
                "sessions": scenario["browse_exit"],
            },
        ]
    )


    # ========================================================
    # BREAKDOWN CHART
    # ========================================================

    fig = px.bar(
        breakdown,
        x="scenario",
        y="sessions",
        color="outcome",
        barmode="stack",

        # YOUR PALETTE
        color_discrete_map={
            "Converted": DARK_RED,
            "Registration exit": MUTED_RED,
            "Checkout exit": TAUPE,
            "Browse exit": ESPRESSO,
        },
    )


    chart_layout = plotly_layout_defaults()


    # ========================================================
    # CHART FONT
    # ========================================================

    chart_layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
    )


    # ========================================================
    # CHART BACKGROUND
    # ========================================================

    chart_layout["paper_bgcolor"] = OFFWHITE
    chart_layout["plot_bgcolor"] = OFFWHITE


    # ========================================================
    # X AXIS
    # ========================================================

    chart_layout["xaxis"] = dict(
        title=dict(
            text="Scenario",
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
        gridcolor=SAND,
    )


    # ========================================================
    # Y AXIS
    # ========================================================

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
        gridcolor=SAND,
    )


    # ========================================================
    # LEGEND
    # ========================================================

    chart_layout["legend"] = dict(
        title=dict(
            text="Outcome",
            font=dict(
                color=ESPRESSO,
            ),
        ),
        font=dict(
            family="Inter, sans-serif",
            color=ESPRESSO,
            size=12,
        ),
    )


    fig.update_layout(
        **chart_layout
    )


    # Thin white separation between stacked sections
    fig.update_traces(
        marker_line=dict(
            color=WHITE,
            width=0.5,
        )
    )


    st.plotly_chart(
        fig,
        width="stretch",
    )


# ============================================================
# PREDEFINED SCENARIO COMPARISON
# ============================================================

st.markdown(
    "### Predefined scenario comparison"
)


if st.button(
    "Run all predefined scenarios"
):

    results = run_all_scenarios(
        n_sessions=n_sessions
    )


    comp_df = pd.DataFrame(
        [
            {
                "scenario": name,
                "conversion_rate": r["conversion_rate"],
                "uncertainty": r["uncertainty"],
            }
            for name, r in results.items()
        ]
    )


    st.dataframe(
        comp_df,
        width="stretch",
        hide_index=True,
    )


    # ========================================================
    # COMPARISON CHART
    # ========================================================

    fig2 = px.bar(
        comp_df,
        x="scenario",
        y="conversion_rate",
        error_y="uncertainty",
        labels={
            "conversion_rate":
                "Simulated conversion rate (%)"
        },
    )


    comparison_layout = plotly_layout_defaults()


    comparison_layout["font"] = dict(
        family="Inter, sans-serif",
        color=ESPRESSO,
    )


    comparison_layout["paper_bgcolor"] = OFFWHITE
    comparison_layout["plot_bgcolor"] = OFFWHITE


    comparison_layout["xaxis"] = dict(
        title=dict(
            text="Scenario",
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
        gridcolor=SAND,
    )


    comparison_layout["yaxis"] = dict(
        title=dict(
            text="Simulated conversion rate (%)",
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
        gridcolor=SAND,
    )


    fig2.update_layout(
        **comparison_layout
    )


    fig2.update_traces(
        marker=dict(
            color=MUTED_RED,
        ),
        marker_line=dict(
            color=WHITE,
            width=0.5,
        ),
    )


    st.plotly_chart(
        fig2,
        width="stretch",
    )


    st.caption(
        "Simulated / Estimated. Error bars show "
        "bootstrap uncertainty on the conversion rate."
    )


# ============================================================
# FOOTER
# ============================================================

project_footer()