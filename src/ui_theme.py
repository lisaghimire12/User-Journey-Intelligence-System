"""
ui_theme.py
------------
Shared visual styling for every Streamlit page: warm editorial palette,
typography hierarchy, restrained card styling. Kept separate from
analytics code so UI concerns never leak into the data/analytics layers.
"""

from __future__ import annotations

import streamlit as st

from src.config import PALETTE, PROJECT_TITLE


def inject_theme():
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Source+Serif+4:wght@500;600&display=swap');

        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, sans-serif;
        }}

        .stApp {{
            background-color: {PALETTE['cream']};
        }}

        section[data-testid="stSidebar"] {{
            background-color: {PALETTE['offwhite']};
            border-right: 1px solid {PALETTE['taupe']};
        }}

        section[data-testid="stSidebar"] * {{
            color: {PALETTE['espresso']} !important;
        }}

        h1, h2, h3 {{
            color: {PALETTE['espresso']} !important;
            font-weight: 700 !important;
            letter-spacing: -0.01em;
        }}

        .eyebrow {{
            text-transform: uppercase;
            letter-spacing: 0.14em;
            font-size: 0.72rem;
            font-weight: 600;
            color: {PALETTE['rust']};
            margin-bottom: 0.25rem;
        }}

        .headline {{
            font-family: 'Source Serif 4', Georgia, serif;
            font-weight: 600;
            font-size: 2.1rem;
            color: {PALETTE['espresso']};
            line-height: 1.15;
            margin-bottom: 0.35rem;
        }}

        .subtext {{
            color: {PALETTE['espresso']};
            opacity: 0.65;
            font-size: 0.95rem;
            margin-bottom: 1.4rem;
        }}

        div[data-testid="stMetric"] {{
            background-color: {PALETTE['offwhite']};
            border: 1px solid {PALETTE['taupe']};
            border-radius: 6px;
            padding: 14px 16px 10px 16px;
        }}

        div[data-testid="stMetric"] label {{
            color: {PALETTE['espresso']} !important;
            opacity: 0.6;
        }}

        div[data-testid="stMetricValue"] {{
            color: {PALETTE['terracotta']} !important;
        }}

        .card {{
            background-color: {PALETTE['offwhite']};
            border: 1px solid {PALETTE['taupe']};
            border-radius: 6px;
            padding: 20px 22px;
            margin-bottom: 14px;
        }}

        .card-sand {{
            background-color: {PALETTE['sand']};
            border: 1px solid {PALETTE['taupe']};
            border-radius: 6px;
            padding: 16px 18px;
            margin-bottom: 12px;
        }}

        .pill {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 3px;
            font-size: 0.72rem;
            font-weight: 600;
            letter-spacing: 0.03em;
            text-transform: uppercase;
        }}

        .pill-low {{ background-color: #E4EFE2; color: #33632E; }}
        .pill-medium {{ background-color: #F4E7C8; color: #8A6412; }}
        .pill-high {{ background-color: #F0DAD3; color: #9B3F24; }}

        .stButton > button, .stDownloadButton > button {{
            background-color: {PALETTE['terracotta']};
            color: {PALETTE['white']};
            border: none;
            border-radius: 4px;
            font-weight: 600;
        }}
        .stButton > button:hover, .stDownloadButton > button:hover {{
            background-color: {PALETTE['rust']};
            color: {PALETTE['white']};
        }}

        hr {{
            border-color: {PALETTE['taupe']};
        }}

        [data-testid="stDataFrame"] {{
            border: 1px solid {PALETTE['taupe']};
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(eyebrow: str, headline: str, subtext: str):
    st.markdown(f'<div class="eyebrow">{eyebrow}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="headline">{headline}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="subtext">{subtext}</div>', unsafe_allow_html=True)


def project_footer():
    st.markdown(
        f'<div style="opacity:0.45; font-size:0.75rem; margin-top:2.5rem;">{PROJECT_TITLE} &middot; '
        f'research prototype &middot; synthetic data</div>',
        unsafe_allow_html=True,
    )


def complexity_pill(level: str) -> str:
    cls = {"Low": "pill-low", "Medium": "pill-medium", "High": "pill-high"}.get(level, "pill-medium")
    return f'<span class="pill {cls}">{level}</span>'


def plotly_layout_defaults() -> dict:
    return dict(
        paper_bgcolor=PALETTE["offwhite"],
        plot_bgcolor=PALETTE["offwhite"],
        font=dict(family="Inter, sans-serif", color=PALETTE["espresso"]),
        margin=dict(l=30, r=20, t=40, b=30),
        colorway=[PALETTE["terracotta"], PALETTE["rust"], PALETTE["espresso"],
                  PALETTE["taupe"], "#C97B4A", "#6E3A21"],
    )
