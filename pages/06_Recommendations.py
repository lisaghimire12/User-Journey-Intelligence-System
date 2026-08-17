import streamlit as st

from src import database
from src.behavioral_analysis import compute_kpis, dropoff_by_stage
from src.explanation_engine import build_explanation, build_llm_summary
from src.pipeline_state import has_data, load_pipeline_data
from src.recommendation_engine import build_recommendations
from src.ui_theme import complexity_pill, page_header, project_footer

page_header(
    "Recommendations",
    "Which intervention should we prioritize?",
    "Interventions ranked using causal effects, simulation results, affected users, complexity, risk, and uncertainty",
)

if not has_data():
    st.info("No data loaded yet. Run `python scripts/run_pipeline.py --reset`.")
    st.stop()

sessions_pd, journeys, merged, transitions = load_pipeline_data()
if journeys.empty:
    st.info("No journeys available.")
    st.stop()

kpis = compute_kpis(journeys, sessions_pd)
dropoff = dropoff_by_stage(journeys)

with st.spinner("Computing recommendations (causal analysis + simulation)..."):
    scores = build_recommendations(journeys, sessions_pd, kpis["conversion_rate"])

records = []
for s in scores:
    explanation = build_explanation(s, dropoff)
    records.append({
        "intervention": s.label, "expected_benefit": s.causal_effect_pct or s.simulated_improvement_pct or 0.0,
        "evidence": s.evidence, "confidence": s.confidence, "complexity": s.complexity,
        "risk": s.risk, "recommendation_score": s.recommendation_score, "explanation": explanation,
    })
database.write_recommendations(records)

top = scores[0]
st.markdown("### Recommended intervention")
st.markdown(
    f'<div class="card">'
    f'<span class="eyebrow">Top ranked</span>'
    f'<div class="headline" style="font-size:1.6rem;">{top.label}</div>'
    f'<div style="display:flex; gap:2rem; margin: 0.6rem 0 0.8rem 0; flex-wrap:wrap;">'
    f'<div><b>{top.causal_effect_pct if top.causal_effect_pct is not None else "—"}%</b><br>'
    f'<span style="opacity:0.6;font-size:0.8rem;">Estimated causal effect</span></div>'
    f'<div><b>{top.simulated_improvement_pct if top.simulated_improvement_pct is not None else "—"}%</b><br>'
    f'<span style="opacity:0.6;font-size:0.8rem;">Simulated improvement</span></div>'
    f'<div><b>{top.affected_sessions_pct}%</b><br><span style="opacity:0.6;font-size:0.8rem;">Affected sessions</span></div>'
    f'<div>{complexity_pill(top.complexity)}<br><span style="opacity:0.6;font-size:0.8rem;">Complexity</span></div>'
    f'<div>{complexity_pill(top.risk)}<br><span style="opacity:0.6;font-size:0.8rem;">Risk</span></div>'
    f'<div><b>{top.confidence}</b><br><span style="opacity:0.6;font-size:0.8rem;">Confidence</span></div>'
    f'<div><b>{top.recommendation_score} / 10</b><br><span style="opacity:0.6;font-size:0.8rem;">Recommendation score</span></div>'
    f'</div></div>',
    unsafe_allow_html=True,
)

st.markdown("### Why is this recommended?")
det_explanation = build_explanation(top, dropoff)
st.write(det_explanation)

llm_summary = build_llm_summary(top, det_explanation)
if llm_summary:
    with st.expander("Plain-language management summary (LLM-generated, numbers unchanged)"):
        st.write(llm_summary)
else:
    st.caption("No LLM API key configured — showing the deterministic, evidence-based explanation above. "
               "The core system requires no LLM to function.")

st.markdown("### All ranked interventions")
for s in scores:
    with st.expander(f"{s.label}  —  score {s.recommendation_score}/10  ({s.confidence} confidence)"):
        cc1, cc2, cc3, cc4 = st.columns(4)
        cc1.metric("Causal effect", f"{s.causal_effect_pct}%" if s.causal_effect_pct is not None else "n/a")
        cc2.metric("Simulated improvement", f"{s.simulated_improvement_pct}%" if s.simulated_improvement_pct is not None else "n/a")
        cc3.metric("Affected sessions", f"{s.affected_sessions_pct}%")
        cc4.metric("Uncertainty", f"±{s.uncertainty} pts")
        st.markdown(f"{complexity_pill(s.complexity)} complexity &nbsp; {complexity_pill(s.risk)} risk", unsafe_allow_html=True)
        st.write(s.description)
        st.write(build_explanation(s, dropoff))
        if s.causal_status == "insufficient_evidence":
            st.caption("Insufficient evidence for a reliable causal estimate for this intervention.")

project_footer()
