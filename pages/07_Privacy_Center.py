import streamlit as st

from src.config import settings
from src.privacy import MIN_AGGREGATION_GROUP_SIZE, PRIVACY_PRINCIPLES
from src.ui_theme import page_header, project_footer

page_header(
    "Privacy Center",
    "How this system is designed to minimize privacy risk",
    "A data-minimization architecture — not a claim of legal compliance",
)

st.markdown(
    '<div class="card-sand">This system follows privacy-aware and data-minimization design '
    'principles. It does not claim compliance with GDPR, the DPDP Act, or any other specific '
    'regulation — those are legal determinations outside the scope of this prototype.</div>',
    unsafe_allow_html=True,
)

st.markdown("### What is collected")
st.markdown(
    "- Pseudonymous session and user tokens (e.g. `session_8F29A1`)\n"
    "- Page views, clicks, and navigation events\n"
    "- Dwell time and sequence position within a session\n"
    "- Coarse technical context: device type, platform, acquisition source\n"
)

st.markdown("### What is never collected")
st.markdown(
    "- Names, email addresses, or phone numbers\n"
    "- Physical addresses\n"
    "- Passwords or authentication credentials\n"
    "- Any other direct identifier\n"
)

st.markdown("### How pseudonymization works")
st.write(
    "Every raw identifier is passed through a keyed one-way hash (HMAC-SHA256) before it is "
    "ever written to the database. The key (salt) is stored only in the local environment "
    "configuration, never in code. The resulting token cannot practically be reversed to "
    "recover the original identifier without that key, and the system never stores the raw "
    "identifier alongside it."
)

st.markdown("### How data is processed")
for title, body in PRIVACY_PRINCIPLES:
    st.markdown(f'<div class="card"><b>{title}</b><p style="opacity:0.75; margin-bottom:0;">{body}</p></div>',
                unsafe_allow_html=True)

st.markdown("### Configuration")
c1, c2 = st.columns(2)
c1.metric("Retention window", f"{settings.data_retention_days} days")
c2.metric("Minimum reportable group size", f"{MIN_AGGREGATION_GROUP_SIZE} sessions")

st.markdown("### Why privacy matters here")
st.write(
    "Behavioral data can reveal sensitive patterns about individuals even without a name "
    "attached. Minimizing what is collected, aggregating what is reported, and pseudonymizing "
    "every identifier reduces the risk that this analysis could ever be used to single out or "
    "profile a specific person, while still preserving enough signal to understand and improve "
    "the aggregate user experience."
)

project_footer()
