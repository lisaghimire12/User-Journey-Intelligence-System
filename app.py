"""
app.py
-------
Application entry point. Configures the page, injects the shared warm
editorial theme, and wires up navigation. Individual pages live under
pages/ and contain their own logic; this file is intentionally thin.
"""

import streamlit as st

from src.config import PROJECT_TITLE
from src.ui_theme import inject_theme

st.set_page_config(
    page_title=PROJECT_TITLE,
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()

pages = [
    st.Page("pages/01_Overview.py", title="Overview", default=True),
    st.Page("pages/02_Journey_Explorer.py", title="Journey Explorer"),
    st.Page("pages/03_Behavioral_Segments.py", title="Behavioral Segments"),
    st.Page("pages/04_Causal_Analysis.py", title="Causal Analysis"),
    st.Page("pages/05_What_If_Simulator.py", title="What-If Simulator"),
    st.Page("pages/06_Recommendations.py", title="Recommendations"),
    st.Page("pages/07_Privacy_Center.py", title="Privacy Center"),
    st.Page("pages/08_System_Status.py", title="System Status"),
]

nav = st.navigation(pages, position="sidebar")
nav.run()
