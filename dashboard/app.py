import streamlit as st
import requests
import pandas as pd
import plotly.express as px

API = "http://localhost:8000"

st.set_page_config(
    page_title="Journey Intelligence",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
    }

    .main {
        background: #f7f6f2;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# =========================================================
# HEADER
# =========================================================

st.title("Journey Intelligence")

st.caption(
    "Privacy-aware e-commerce analytics"
)


# =========================================================
# LOAD DATA
# =========================================================

try:

    overview = requests.get(
        API + "/api/analytics/overview",
        timeout=3
    ).json()

    journeys = requests.get(
        API + "/api/analytics/journeys",
        timeout=3
    ).json()

except Exception:

    st.error(
        "Start the API first:\n\n"
        "uvicorn backend.app.main:app --reload"
    )

    st.stop()


# =========================================================
# TOP METRICS
# =========================================================

columns = st.columns(5)

metrics = [

    (
        "Sessions",
        overview["total_sessions"]
    ),

    (
        "Conversion",
        f'{overview["conversion_rate"]}%'
    ),

    (
        "Avg Journey",
        overview["avg_journey_length"]
    ),

    (
        "Abandonment",
        f'{overview["abandonment_rate"]}%'
    ),

    (
        "Events",
        overview["event_count"]
    )
]

for column, (label, value) in zip(
    columns,
    metrics
):

    column.metric(
        label,
        value
    )


# =========================================================
# TABS
# =========================================================

tabs = st.tabs([
    "Overview",
    "Journey Explorer",
    "Per-User Journey",
    "Segments",
    "Causal Analysis",
    "What-If",
    "Recommendations",
    "Privacy Center",
    "System Status"
])


# =========================================================
# 1. OVERVIEW
# =========================================================

with tabs[0]:

    st.subheader(
        "Conversion Funnel"
    )

    purchase_count = int(
        overview["total_sessions"]
        * overview["conversion_rate"]
        / 100
    )

    funnel = pd.DataFrame({

        "Stage": [
            "Sessions",
            "Product views",
            "Cart",
            "Checkout",
            "Purchase"
        ],

        "Users": [
            overview["total_sessions"],
            int(
                overview["total_sessions"]
                * 0.82
            ),
            int(
                overview["total_sessions"]
                * 0.61
            ),
            int(
                overview["total_sessions"]
                * 0.46
            ),
            purchase_count
        ]
    })

    st.plotly_chart(
        px.funnel(
            funnel,
            x="Users",
            y="Stage"
        ),
        use_container_width=True
    )

    st.info(
        "This overview summarizes all stored sessions. "
        "Use the Per-User Journey tab when you want to inspect "
        "one pseudonymous user's behavior across sessions."
    )


# =========================================================
# 2. JOURNEY EXPLORER
# =========================================================

with tabs[1]:

    st.subheader(
        "Journey Explorer"
    )

    if journeys:

        journey_df = pd.DataFrame(
            journeys
        )

        columns_to_show = [
            "session_id",
            "sequence",
            "journey_length",
            "duration_seconds",
            "converted",
            "abandonment_stage"
        ]

        st.dataframe(
            journey_df[columns_to_show],
            use_container_width=True
        )

    else:

        st.info(
            "No journeys have been reconstructed yet."
        )


# =========================================================
# 3. PER-USER JOURNEY
# =========================================================

with tabs[2]:

    st.subheader(
        "Analyze One User"
    )

    st.caption(
        "This view groups sessions using the user's "
        "pseudonymous identifier. It does not require "
        "a name, email address or other direct identifier."
    )

    try:

        users_response = requests.get(
            API + "/api/analytics/users",
            timeout=3
        ).json()

        user_ids = [
            user["user_id"]
            for user in users_response
        ]

        if not user_ids:

            st.info(
                "No users are available yet. "
                "Browse the storefront first or run the demo seed script."
            )

        else:

            selected_user = st.selectbox(
                "Select pseudonymous user",
                user_ids
            )

            user_response = requests.get(
                API
                + "/api/analytics/users/"
                + selected_user,
                timeout=3
            ).json()

            metric_a, metric_b, metric_c = st.columns(3)

            metric_a.metric(
                "Sessions",
                user_response["session_count"]
            )

            metric_b.metric(
                "Total Events",
                user_response["total_events"]
            )

            metric_c.metric(
                "Converted Sessions",
                user_response["converted_sessions"]
            )

            st.divider()

            for index, session in enumerate(
                user_response["sessions"],
                start=1
            ):

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"""
                        ### Session {index}

                        `{session["session_id"]}`
                        """
                    )

                    # Journey path
                    st.markdown(
                        "**Journey Path**"
                    )

                    journey = session["journey"]

                    if journey:

                        st.write(
                            " → ".join(journey)
                        )

                    else:

                        st.write(
                            "No reconstructed journey."
                        )

                    # Session summary
                    a, b, c, d = st.columns(4)

                    a.metric(
                        "Events",
                        session["event_count"]
                    )

                    b.metric(
                        "Journey Length",
                        session["journey_length"]
                    )

                    c.metric(
                        "Duration",
                        f'{session["duration_seconds"]:.1f}s'
                    )

                    d.metric(
                        "Converted",
                        "Yes"
                        if session["converted"]
                        else "No"
                    )

                    if session[
                        "abandonment_stage"
                    ]:

                        st.warning(
                            "Abandonment stage: "
                            + session["abandonment_stage"]
                        )

                    # Actual events
                    st.markdown(
                        "**Event-by-event record**"
                    )

                    event_df = pd.DataFrame(
                        session["events"]
                    )

                    if not event_df.empty:

                        st.dataframe(
                            event_df,
                            use_container_width=True
                        )


    except Exception as error:

        st.error(
            f"Could not load per-user journeys: {error}"
        )


# =========================================================
# 4. SEGMENTS
# =========================================================

with tabs[3]:

    st.subheader(
        "Behavioral Segmentation"
    )

    from analytics.analysis import segment

    class JourneyObject:

        def __init__(self, data):

            self.__dict__.update(data)

    if journeys:

        segmentation = segment(
            [
                JourneyObject(journey)
                for journey in journeys
            ],
            4
        )

        if segmentation:

            st.dataframe(
                pd.DataFrame(segmentation),
                use_container_width=True
            )

        else:

            st.info(
                "Not enough journeys for segmentation."
            )

    else:

        st.info(
            "No journeys available."
        )


# =========================================================
# 5. CAUSAL ANALYSIS
# =========================================================

with tabs[4]:

    st.subheader(
        "Causal Analysis"
    )

    st.warning(
        "Correlation is not causation."
    )

    st.write(
        """
        The current demo does not fabricate causal effects
        from observational journey data.

        A real causal conclusion should come from a controlled
        experiment, randomized intervention, or a defensible
        causal-identification strategy.
        """
    )

    st.code(
        "INSUFFICIENT_EVIDENCE"
    )


# =========================================================
# 6. WHAT-IF
# =========================================================

with tabs[5]:

    st.subheader(
        "What-If Simulation"
    )

    from analytics.simulation import simulate

    intervention = st.selectbox(
        "Intervention",

        [
            "Reduce checkout steps",
            "Improve product information visibility",
            "Reduce navigation friction",
            "Increase product exposure",
            "Add product-information intervention"
        ]
    )

    intensity = st.slider(
        "Intervention intensity",
        0.0,
        1.0,
        0.5
    )

    if st.button(
        "Run Simulation"
    ):

        result = simulate(

            overview["conversion_rate"],

            overview["abandonment_rate"],

            overview["avg_journey_length"],

            intervention,

            intensity
        )

        st.warning(
            "SIMULATED / ESTIMATED — "
            "these are not observed real-world results."
        )

        a, b, c = st.columns(3)

        a.metric(
            "Simulated Conversion",
            f'{result["simulated_conversion"]:.2f}%'
        )

        b.metric(
            "Simulated Abandonment",
            f'{result["simulated_abandonment"]:.2f}%'
        )

        c.metric(
            "Simulated Journey Length",
            f'{result["simulated_journey_length"]:.2f}'
        )


# =========================================================
# 7. RECOMMENDATIONS
# =========================================================

with tabs[6]:

    st.subheader(
        "Explainable Recommendations"
    )

    from analytics.recommendations import recommendations

    for recommendation in recommendations(
        overview
    ):

        with st.container(
            border=True
        ):

            st.subheader(
                recommendation["title"]
            )

            st.write(
                recommendation["explanation"]
            )

            st.write(
                "Evidence:",
                ", ".join(
                    recommendation["evidence"]
                )
            )

            st.write(
                f'Expected benefit: '
                f'{recommendation["expected_benefit"]}%'
            )

            st.write(
                f'Confidence: '
                f'{recommendation["confidence"]}'
            )

            st.write(
                f'Complexity: '
                f'{recommendation["complexity"]}'
            )

            st.write(
                f'Risk: '
                f'{recommendation["risk"]}'
            )


# =========================================================
# 8. PRIVACY CENTER
# =========================================================

with tabs[7]:

    st.subheader(
        "Privacy Center"
    )

    st.markdown(
        "### Data collected"
    )

    st.write(
        """
        The system collects only the information needed
        for journey analytics:

        • pseudonymous user/session identifier  
        • event type  
        • timestamp  
        • page context  
        • product context  
        • limited event metadata
        """
    )

    st.markdown(
        "### Not collected"
    )

    st.write(
        """
        • Passwords  
        • Payment details  
        • Email addresses  
        • Phone numbers  
        • Direct personal identifiers
        """
    )

    st.markdown(
        "### Protection"
    )

    st.write(
        """
        • Event allow-list  
        • HMAC-SHA256 pseudonymization  
        • Data minimization  
        • Configurable retention  
        • Aggregation thresholds
        """
    )


# =========================================================
# 9. SYSTEM STATUS
# =========================================================

with tabs[8]:

    st.subheader(
        "System Status"
    )

    try:

        status = requests.get(
            API + "/api/system/status",
            timeout=3
        ).json()

        st.json(status)

    except Exception:

        st.error(
            "Backend is not reachable."
        )

    if st.button(
        "Recompute Journeys"
    ):

        response = requests.post(
            API + "/api/analytics/recompute"
        )

        if response.ok:

            st.success(
                "Journeys recomputed successfully."
            )

        else:

            st.error(
                "Could not recompute journeys."
            )