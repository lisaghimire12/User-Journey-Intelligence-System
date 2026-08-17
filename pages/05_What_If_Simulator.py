import pandas as pd
import plotly.express as px
import streamlit as st

from src import database
from src.simulation_engine import SCENARIOS, SimulationParams, run_all_scenarios, run_simulation
from src.ui_theme import page_header, plotly_layout_defaults, project_footer

page_header(
    "What-If Simulator",
    "What could happen if we change something?",
    "Discrete-event simulation (SimPy) of the user funnel under adjustable parameters — every run is executed live",
)

st.markdown("### Build a scenario")
c1, c2, c3 = st.columns(3)
with c1:
    registration_friction = st.slider("Registration friction", 0, 100, 45)
    checkout_friction = st.slider("Checkout friction", 0, 100, 40)
with c2:
    page_delay = st.slider("Page delay (seconds)", 0.0, 10.0, 1.5, step=0.1)
    content_exposure = st.slider("Content exposure", 0, 100, 50)
with c3:
    navigation_friction = st.slider("Navigation friction", 0, 100, 35)
    n_sessions = st.select_slider("Simulated sessions", options=[500, 1000, 2000, 4000], value=2000)

run = st.button("Run simulation", type="primary")

baseline_params = SCENARIOS["A - Current system"]
baseline = run_simulation(SimulationParams(**{**baseline_params.__dict__, "n_sessions": n_sessions}))

if run:
    scenario_params = SimulationParams(
        registration_friction=registration_friction,
        checkout_friction=checkout_friction,
        page_delay=page_delay,
        content_exposure=content_exposure,
        navigation_friction=navigation_friction,
        n_sessions=n_sessions,
    )
    scenario = run_simulation(scenario_params)

    change = round(scenario["conversion_rate"] - baseline["conversion_rate"], 2)

    st.markdown("### Result")
    c1, c2, c3 = st.columns(3)
    c1.metric("Baseline (Simulated)", f"{baseline['conversion_rate']}%", help=f"±{baseline['uncertainty']} pts uncertainty")
    c2.metric("Scenario (Simulated)", f"{scenario['conversion_rate']}%", help=f"±{scenario['uncertainty']} pts uncertainty")
    c3.metric("Estimated change", f"{change:+.2f} pts")

    st.caption("All values above are Simulated / Estimated outputs of a discrete-event model, not a guarantee.")

    database.write_simulation({
        "scenario_name": "Custom scenario",
        "intervention": "custom",
        "parameters": scenario_params.__dict__,
        "baseline_result": baseline["conversion_rate"],
        "simulated_result": scenario["conversion_rate"],
        "improvement": change,
        "uncertainty": scenario["uncertainty"],
    })

    breakdown = pd.DataFrame([
        {"scenario": "Baseline", "outcome": "Converted", "sessions": baseline["converted"]},
        {"scenario": "Baseline", "outcome": "Registration exit", "sessions": baseline["registration_exit"]},
        {"scenario": "Baseline", "outcome": "Checkout exit", "sessions": baseline["checkout_exit"]},
        {"scenario": "Baseline", "outcome": "Browse exit", "sessions": baseline["browse_exit"]},
        {"scenario": "Scenario", "outcome": "Converted", "sessions": scenario["converted"]},
        {"scenario": "Scenario", "outcome": "Registration exit", "sessions": scenario["registration_exit"]},
        {"scenario": "Scenario", "outcome": "Checkout exit", "sessions": scenario["checkout_exit"]},
        {"scenario": "Scenario", "outcome": "Browse exit", "sessions": scenario["browse_exit"]},
    ])
    fig = px.bar(breakdown, x="scenario", y="sessions", color="outcome", barmode="stack")
    fig.update_layout(**plotly_layout_defaults())
    st.plotly_chart(fig, width='stretch')
else:
    st.info("Adjust parameters above and click **Run simulation**.")

st.markdown("### Predefined scenario comparison")
if st.button("Run all predefined scenarios"):
    results = run_all_scenarios(n_sessions=n_sessions)
    comp_df = pd.DataFrame([
        {"scenario": name, "conversion_rate": r["conversion_rate"], "uncertainty": r["uncertainty"]}
        for name, r in results.items()
    ])
    st.dataframe(comp_df, width='stretch', hide_index=True)
    fig2 = px.bar(comp_df, x="scenario", y="conversion_rate", error_y="uncertainty",
                   labels={"conversion_rate": "Simulated conversion rate (%)"})
    fig2.update_layout(**plotly_layout_defaults())
    st.plotly_chart(fig2, width='stretch')
    st.caption("Simulated / Estimated. Error bars show bootstrap uncertainty on the conversion rate.")

project_footer()
