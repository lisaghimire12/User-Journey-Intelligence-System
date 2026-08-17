import plotly.graph_objects as go
import streamlit as st

from src import causal_analysis, database
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import page_header, plotly_layout_defaults, project_footer

page_header(
    "Causal Analysis",
    "What appears to actually influence conversion?",
    "Backdoor-adjusted causal effect estimation via DoWhy, with confidence intervals and refutation checks",
)

if not has_data():
    st.info("No data loaded yet. Run `python scripts/run_pipeline.py --reset`.")
    st.stop()

sessions_pd, journeys, merged, transitions = load_pipeline_data()

if journeys.empty:
    st.info("No journeys available for causal analysis.")
    st.stop()

causal_df = journeys.merge(sessions_pd, on="session_id", how="left")

question_labels = {q["id"]: q["question"] for q in causal_analysis.CAUSAL_QUESTIONS}
selected_id = st.selectbox("Causal question", list(question_labels.keys()), format_func=lambda k: question_labels[k])
q = next(q for q in causal_analysis.CAUSAL_QUESTIONS if q["id"] == selected_id)

st.markdown(
    f'<div class="card-sand"><b>Treatment:</b> {q["treatment_label"]} &nbsp;&middot;&nbsp; '
    f'<b>Outcome:</b> conversion (purchase) &nbsp;&middot;&nbsp; '
    f'<b>Confounders adjusted for:</b> {", ".join(q["confounders"])}</div>',
    unsafe_allow_html=True,
)

with st.expander("Assumed causal graph"):
    st.markdown(
        f"""
        <div style="display:flex; align-items:center; justify-content:center; gap:0; padding: 1.5rem 0; font-size:0.85rem;">
          <div style="text-align:center;">
            <div class="card-sand" style="min-width:150px;">{q['confounders'][0]}</div>
          </div>
        </div>
        <div style="text-align:center; opacity:0.6; font-size:0.8rem; margin-top:-1.2rem;">
          confounds both the treatment and the outcome
        </div>
        <div style="display:flex; align-items:center; justify-content:center; gap:1.2rem; padding: 0.8rem 0;">
          <div class="card-sand" style="min-width:170px; text-align:center;">{q['treatment_label']}</div>
          <div style="font-size:1.4rem; color:#9B3F24;">&#8594;</div>
          <div class="card-sand" style="min-width:150px; text-align:center;">conversion</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

result = causal_analysis.estimate_effect(
    causal_df,
    treatment_raw=q["treatment_raw"],
    outcome=q["outcome"],
    confounders=q["confounders"],
    treatment_label=q["treatment_label"],
    beneficial_direction=q.get("beneficial_direction", "low"),
)

if result.status == "insufficient_evidence":
    st.markdown(
        f'<div class="card"><b>Insufficient evidence for reliable causal estimation.</b><br>'
        f'<span style="opacity:0.7;">{result.message}</span></div>',
        unsafe_allow_html=True,
    )
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Effect estimate", f"{result.effect_estimate * 100:+.2f} pts")
    c2.metric("95% CI", f"[{result.ci_lower*100:.2f}, {result.ci_upper*100:.2f}]")
    c3.metric("Sample size", f"{result.sample_size:,}")

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=[result.effect_estimate * 100], y=["Effect"],
        error_x=dict(type="data", symmetric=False,
                      array=[(result.ci_upper - result.effect_estimate) * 100],
                      arrayminus=[(result.effect_estimate - result.ci_lower) * 100]),
        mode="markers", marker=dict(size=14, color="#9B3F24"),
    ))
    fig.add_vline(x=0, line_dash="dash", line_color="#D8CFC3")
    fig.update_layout(**plotly_layout_defaults(), height=220,
                       xaxis_title="Effect on conversion probability (percentage points)")
    st.plotly_chart(fig, width='stretch')

    st.markdown("**Method:** " + result.method)
    st.markdown("**Assumptions:** " + result.assumptions)
    if result.refutation_passed is not None:
        icon = "✓" if result.refutation_passed else "!"
        st.markdown(f"**Refutation check ({icon}):** {result.refutation_detail}")

    st.caption("Causal estimates depend on the data and assumptions of the causal model.")

    database.write_causal_result({
        "treatment": result.treatment, "outcome": result.outcome,
        "effect_estimate": result.effect_estimate, "ci_lower": result.ci_lower,
        "ci_upper": result.ci_upper, "method": result.method,
        "sample_size": result.sample_size, "assumptions": result.assumptions,
        "refutation_passed": result.refutation_passed,
    })

project_footer()
