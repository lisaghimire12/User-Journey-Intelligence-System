import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.behavioral_analysis import journey_length_distribution
from src.data_processing import apply_filters
from src.journey_reconstruction import top_journeys
from src.pipeline_state import has_data, load_pipeline_data
from src.ui_theme import page_header, plotly_layout_defaults, project_footer

page_header(
    "Journey Explorer",
    "What paths do users actually take?",
    "Reconstructed, non-linear user journeys from raw event sequences",
)

if not has_data():
    st.info("No data loaded yet. Run `python scripts/run_pipeline.py --reset`.")
    st.stop()

sessions_pd, journeys, merged, transitions = load_pipeline_data()

with st.sidebar:
    st.markdown("**Filters**")
    device = st.multiselect("Device", sorted(sessions_pd["device_type"].dropna().unique()))
    platform = st.multiselect("Platform", sorted(sessions_pd["platform"].dropna().unique()))
    source = st.multiselect("Acquisition source", sorted(sessions_pd["acquisition_source"].dropna().unique()))
    conv_filter = st.radio("Conversion", ["all", "converted", "not_converted"], horizontal=False)

filtered_sessions = apply_filters(sessions_pd, device, platform, source, conv_filter)
filtered_journeys = journeys[journeys["session_id"].isin(filtered_sessions["session_id"])]

st.markdown("### Major transition flow (Sankey)")
if not transitions.empty:
    top_edges = transitions.head(25)
    nodes = list(pd.unique(top_edges[["source", "target"]].values.ravel()))
    node_index = {n: i for i, n in enumerate(nodes)}
    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=16, thickness=16,
            label=nodes,
            color="#9B3F24",
            line=dict(color="#D8CFC3", width=0.5),
        ),
        link=dict(
            source=[node_index[s] for s in top_edges["source"]],
            target=[node_index[t] for t in top_edges["target"]],
            value=top_edges["count"],
            color="rgba(155,63,36,0.25)",
        ),
    )])
    fig.update_layout(**plotly_layout_defaults(), height=420)
    st.plotly_chart(fig, width='stretch')
else:
    st.info("Not enough event data for a transition diagram yet.")

col1, col2 = st.columns(2)
with col1:
    st.markdown("### Top journeys")
    tj = top_journeys(filtered_journeys, n=10)
    if not tj.empty:
        st.dataframe(tj, width='stretch', hide_index=True)
    else:
        st.info("No journeys match the current filters.")

with col2:
    st.markdown("### Journey length distribution")
    dist = journey_length_distribution(filtered_journeys)
    if not dist.empty:
        fig2 = px.histogram(dist, x="journey_length", nbins=20,
                             labels={"journey_length": "Pages per journey"})
        fig2.update_layout(**plotly_layout_defaults())
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("No journeys to plot.")

st.markdown("### Drop-off by stage")
from src.behavioral_analysis import dropoff_by_stage
dropoff = dropoff_by_stage(filtered_journeys)
if not dropoff.empty:
    fig3 = px.bar(dropoff, x="stage", y="sessions", text="share_pct")
    fig3.update_traces(texttemplate="%{text}%", textposition="outside")
    fig3.update_layout(**plotly_layout_defaults())
    st.plotly_chart(fig3, width='stretch')

project_footer()
