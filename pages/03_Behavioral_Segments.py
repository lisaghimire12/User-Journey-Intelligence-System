import plotly.express as px
import streamlit as st

from src.pipeline_state import has_data, load_pipeline_data
from src.segmentation import compute_segments
from src.ui_theme import page_header, plotly_layout_defaults, project_footer

page_header(
    "Behavioral Segments",
    "Which distinct behavioral groups exist in the data?",
    "Segments are derived from K-Means clustering over journey features, then labeled by their own statistical profile",
)

if not has_data():
    st.info("No data loaded yet. Run `python scripts/run_pipeline.py --reset`.")
    st.stop()

sessions_pd, journeys, merged, transitions = load_pipeline_data()

if merged.empty:
    st.info("Not enough data to compute engagement scores yet.")
    st.stop()

n_clusters = st.slider("Number of segments", min_value=2, max_value=6, value=4)
assigned, summary = compute_segments(merged, n_clusters=n_clusters)

if summary.empty:
    st.warning("Not enough sessions to form statistically reportable segments "
               "(each segment must contain at least 5 sessions).")
    st.stop()

col1, col2 = st.columns([1, 1])
with col1:
    fig = px.pie(summary, names="segment", values="segment_size", hole=0.45)
    fig.update_layout(**plotly_layout_defaults())
    st.plotly_chart(fig, width='stretch')
with col2:
    fig2 = px.bar(summary.sort_values("conversion_rate"), x="conversion_rate", y="segment",
                   orientation="h", labels={"conversion_rate": "Conversion rate (%)", "segment": ""})
    fig2.update_layout(**plotly_layout_defaults())
    st.plotly_chart(fig2, width='stretch')

st.markdown("### Segment profiles")
for _, row in summary.iterrows():
    st.markdown(
        f'<div class="card">'
        f'<span class="eyebrow">{row["segment"]}</span>'
        f'<div style="display:flex; gap:2.2rem; margin:0.4rem 0 0.6rem 0; flex-wrap:wrap;">'
        f'<div><b>{int(row["segment_size"])}</b><br><span style="opacity:0.6;font-size:0.8rem;">sessions</span></div>'
        f'<div><b>{row["conversion_rate"]}%</b><br><span style="opacity:0.6;font-size:0.8rem;">conversion</span></div>'
        f'<div><b>{row["avg_journey_length"]}</b><br><span style="opacity:0.6;font-size:0.8rem;">avg. pages</span></div>'
        f'<div><b>{row["avg_duration"]:.0f}s</b><br><span style="opacity:0.6;font-size:0.8rem;">avg. duration</span></div>'
        f'<div><b>{row["avg_engagement"]}</b><br><span style="opacity:0.6;font-size:0.8rem;">engagement score</span></div>'
        f'</div>'
        f'<span style="opacity:0.65; font-size:0.85rem;">Common path: {row["common_path"]}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

project_footer()
