import pandas as pd
import streamlit as st

from src import database
from src.behavioral_analysis import compute_kpis, dropoff_by_stage
from src.config import PROJECT_TITLE
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import page_header, project_footer, plotly_layout_defaults
import plotly.express as px

page_header(
    "Research Prototype",
    "How are users moving through the platform?",
    PROJECT_TITLE,
)

if not has_data():
    st.markdown(
        '<div class="card">No data has been loaded yet. Run '
        '<code>python scripts/run_pipeline.py --reset</code> from the project root, '
        'then reopen this page.</div>',
        unsafe_allow_html=True,
    )
    st.stop()

sessions_pd, journeys, merged, transitions = load_pipeline_data()
kpis = compute_kpis(journeys, sessions_pd)

st.markdown(f'<div class="subtext" style="margin-top:-1rem;">Analysis of {kpis["total_sessions"]:,} anonymized sessions</div>', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Total sessions", f"{kpis['total_sessions']:,}")
c2.metric("Conversion rate", f"{kpis['conversion_rate']}%")
c3.metric("Abandonment rate", f"{kpis['abandonment_rate']}%")
c4.metric("Avg. journey duration", f"{kpis['avg_duration']:.0f}s")

c5, c6, c7 = st.columns(3)
c5.metric("Avg. journey length", f"{kpis['avg_length']} pages")
c6.metric("Top entry page", kpis["top_entry"])
c7.metric("Top exit page", kpis["top_exit"])

st.markdown("### Where sessions are being lost")
dropoff = dropoff_by_stage(journeys)
col_a, col_b = st.columns([2, 1])
with col_a:
    if not dropoff.empty:
        fig = px.bar(dropoff, x="stage", y="sessions", text="share_pct",
                     labels={"stage": "Abandonment stage", "sessions": "Sessions"})
        fig.update_traces(texttemplate="%{text}%", textposition="outside")
        fig.update_layout(**plotly_layout_defaults())
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No abandonment recorded in the current dataset.")
with col_b:
    st.markdown('<div class="card">', unsafe_allow_html=True)
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
        st.write("Not enough abandonment data yet.")
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("### Top recommendation")
recs_df = database.read_table("recommendations")
if not recs_df.empty:
    top_rec = recs_df.sort_values("recommendation_score", ascending=False).iloc[0]
    st.markdown(
        f'<div class="card"><span class="eyebrow">Recommended intervention</span>'
        f'<div class="headline" style="font-size:1.4rem;">{top_rec["intervention"]}</div>'
        f'<p style="opacity:0.75;">{top_rec["explanation"]}</p>'
        f'<b>Recommendation score:</b> {top_rec["recommendation_score"]}/10 &nbsp;&middot;&nbsp; '
        f'<b>Confidence:</b> {top_rec["confidence"]}</div>',
        unsafe_allow_html=True,
    )
else:
    st.info("No recommendations computed yet. Run `python scripts/run_pipeline.py` to generate them, "
            "or visit the Recommendations page.")

project_footer()
