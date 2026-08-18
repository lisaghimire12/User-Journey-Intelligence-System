import streamlit as st

from src.config import settings
from src.privacy import MIN_AGGREGATION_GROUP_SIZE, PRIVACY_PRINCIPLES
from src.ui_theme import page_header, project_footer


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
    "Privacy Center",
    "How this system is designed to minimize privacy risk",
    "A data-minimization architecture — not a claim of legal compliance",
)


# ============================================================
# PAGE-SPECIFIC COLORS
# ============================================================

st.markdown(
    f"""
    <style>

    /* ========================================================
       GENERAL PAGE TEXT
       ======================================================== */

    .stMarkdown p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .stMarkdown li {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .stMarkdown strong {{
        color: {ESPRESSO} !important;
    }}

    /* ========================================================
       HEADINGS
       ======================================================== */

    h3 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    h4 {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       PRIVACY CARDS
       ======================================================== */

    .card-sand {{
        background-color: {SAND} !important;
        border: 1px solid {TAUPE} !important;
        color: {ESPRESSO} !important;
    }}

    .card-sand p,
    .card-sand b,
    .card-sand span {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    .card {{
        background-color: {OFFWHITE} !important;
        border: 1px solid {TAUPE} !important;
        color: {ESPRESSO} !important;
    }}

    .card b {{
        color: {TERRACOTTA} !important;
    }}

    .card p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       METRIC LABELS
       ======================================================== */

    div[data-testid="stMetricLabel"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricLabel"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       METRIC VALUES
       ======================================================== */

    div[data-testid="stMetricValue"] {{
        color: {TERRACOTTA} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stMetricValue"] > div {{
        color: {TERRACOTTA} !important;
    }}

    /* ========================================================
       CAPTIONS
       ======================================================== */

    div[data-testid="stCaptionContainer"] {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    div[data-testid="stCaptionContainer"] p {{
        color: {ESPRESSO} !important;
        opacity: 1 !important;
    }}

    /* ========================================================
       INLINE CODE
       ======================================================== */

    code {{
        color: {TERRACOTTA} !important;
        background-color: {SAND} !important;
        border: 1px solid {TAUPE} !important;
    }}

    /* ========================================================
       DIVIDERS
       ======================================================== */

    hr {{
        border-color: {TAUPE} !important;
    }}

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# PRIVACY INTRODUCTION
# ============================================================

st.markdown(
    '<div class="card-sand">'
    'This system follows privacy-aware and data-minimization design '
    'principles. It does not claim compliance with GDPR, the DPDP Act, or any specific '
    'regulation — those are legal determinations outside the scope of this prototype.'
    '</div>',
    unsafe_allow_html=True,
)


# ============================================================
# WHAT IS COLLECTED
# ============================================================

st.markdown("### What is collected")

st.markdown(
    "- Pseudonymous session and user tokens (e.g. `session_8F29A1`)\n"
    "- Page views, clicks, and navigation events\n"
    "- Dwell time and sequence position within a session\n"
    "- Coarse technical context: device type, platform, acquisition source"
)


# ============================================================
# WHAT IS NEVER COLLECTED
# ============================================================

st.markdown("### What is never collected")

st.markdown(
    "- Names, email addresses, or phone numbers\n"
    "- Physical addresses\n"
    "- Passwords or authentication credentials\n"
    "- Any other direct identifier"
)


# ============================================================
# HOW PSEUDONYMIZATION WORKS
# ============================================================

st.markdown("### How pseudonymization works")

st.write(
    "Every raw identifier is passed through a keyed one-way hash "
    "(HMAC-SHA256) before it is ever written to the database. The key "
    "(salt) is stored only in the local environment configuration, never "
    "in code. The resulting token cannot practically be reversed to "
    "recover the original identifier without that key, and the system "
    "never stores the raw identifier alongside it."
)


# ============================================================
# HOW DATA IS PROCESSED
# ============================================================

st.markdown("### How data is processed")

for title, body in PRIVACY_PRINCIPLES:

    st.markdown(
        f"""
        <div class="card">
            <b>{title}</b>
            <p>{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# CONFIGURATION
# ============================================================

st.markdown("### Configuration")

c1, c2 = st.columns(2)

with c1:
    st.metric(
        "Retention window",
        f"{settings.data_retention_days} days",
    )

with c2:
    st.metric(
        "Minimum reportable group size",
        f"{MIN_AGGREGATION_GROUP_SIZE} sessions",
    )


# ============================================================
# WHY PRIVACY MATTERS
# ============================================================

st.markdown("### Why privacy matters here")

st.write(
    "Behavioral data can reveal sensitive patterns about individuals "
    "even without a name attached. Minimizing what is collected, "
    "aggregating what is reported, and pseudonymizing every identifier "
    "reduces the risk that this analysis could ever be used to single "
    "out or profile a specific person, while still preserving enough "
    "signal to understand and improve the aggregate user experience."
)


# ============================================================
# FOOTER
# ============================================================

project_footer()