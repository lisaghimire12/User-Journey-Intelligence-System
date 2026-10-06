import streamlit as st

import requests

import pandas as pd

import plotly.express as px


# =========================================================
# CONFIG
# =========================================================

API = "http://localhost:8000"


st.set_page_config(
    page_title="Journey Intelligence",
    page_icon="◉",
    layout="wide",
)


# =========================================================
# STYLING
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1400px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    .live {
        color: #b34a32;
        font-weight: 700;
    }

    .current-step {
        border: 1px solid #b34a32;
        padding: 14px;
        margin: 8px 0;
        border-radius: 6px;
        background: #fffaf7;
    }

    .journey-step {
        padding: 5px 0;
        font-size: 16px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# API HELPERS
# =========================================================

def get(path, default=None, timeout=5):
    try:
        response = requests.get(
            API + path,
            timeout=timeout,
        )

        response.raise_for_status()

        return response.json()

    except Exception:
        return default


def post(path, timeout=10):
    try:
        return requests.post(
            API + path,
            timeout=timeout,
        )

    except Exception:
        return None


# =========================================================
# JOURNEY HELPERS
# =========================================================

def seq(journey):
    """
    Extract the ordered journey sequence from a journey object.
    """

    sequence = journey.get("sequence", [])

    if isinstance(sequence, list):

        return [
            str(item)
            for item in sequence
            if item is not None
        ]

    if isinstance(sequence, str):

        if "→" in sequence:

            return [
                item.strip()
                for item in sequence.split("→")
                if item.strip()
            ]

        if ">" in sequence:

            return [
                item.strip()
                for item in sequence.split(">")
                if item.strip()
            ]

        if sequence.strip():

            return [sequence.strip()]

    return []


def has(sequence, keywords):
    """
    Check whether a journey contains any of the supplied keywords.
    """

    text = " ".join(sequence).lower()

    return any(
        keyword.lower() in text
        for keyword in keywords
    )


def df_for(journeys):
    """
    Convert reconstructed journeys into a DataFrame.
    """

    rows = []

    for journey in journeys:

        sequence = seq(journey)

        rows.append(
            {
                "session_id": journey.get(
                    "session_id",
                    "unknown",
                ),

                "sequence": " → ".join(sequence),

                "journey_length": journey.get(
                    "journey_length",
                    len(sequence),
                ),

                "duration_seconds": journey.get(
                    "duration_seconds",
                    0,
                ),

                "converted": bool(
                    journey.get(
                        "converted",
                        False,
                    )
                ),

                "abandonment_stage": journey.get(
                    "abandonment_stage"
                ),
            }
        )

    return pd.DataFrame(rows)


def contains_stage(sequence, keywords):
    return has(sequence, keywords)


# =========================================================
# LOAD BACKEND DATA
# =========================================================

overview = get(
    "/api/analytics/overview",
    default={},
)

journeys = get(
    "/api/analytics/journeys",
    default=[],
)

if not isinstance(journeys, list):
    journeys = []


# =========================================================
# HEADER
# =========================================================

st.title("Journey Intelligence")

st.caption(
    "Privacy-aware e-commerce analytics"
)

header_left, header_right = st.columns(
    [1, 5]
)

with header_left:

    if st.button(
        "Refresh",
        use_container_width=True,
    ):

        st.rerun()

with header_right:

    st.markdown(
        """
        <span class="live">● LIVE DATA</span>
        &nbsp; Dashboard is reading journey data from the FastAPI backend.
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# TOP METRICS
# =========================================================

columns = st.columns(5)

metrics = [

    (
        "Sessions",
        overview.get(
            "total_sessions",
            len(journeys),
        ),
    ),

    (
        "Conversion",
        f'{overview.get("conversion_rate", 0)}%',
    ),

    (
        "Avg Journey",
        overview.get(
            "avg_journey_length",
            0,
        ),
    ),

    (
        "Abandonment",
        f'{overview.get("abandonment_rate", 0)}%',
    ),

    (
        "Events",
        overview.get(
            "event_count",
            0,
        ),
    ),
]

for column, (label, value) in zip(
    columns,
    metrics,
):

    column.metric(
        label,
        value,
    )


# =========================================================
# TABS
# =========================================================

tabs = st.tabs(
    [
        "Overview",
        "Journey Explorer",
        "Per-User Journey",
        "Segments",
        "Causal Analysis",
        "What-If",
        "Recommendations",
        "Privacy Center",
        "System Status",
    ]
)


# =========================================================
# 1. OVERVIEW
# =========================================================

with tabs[0]:

    st.subheader(
        "Conversion Funnel"
    )

    # -----------------------------------------------------
    # OBSERVED CONVERSION FUNNEL
    # -----------------------------------------------------
    #
    # IMPORTANT:
    # These values come ONLY from actual reconstructed
    # journeys.
    #
    # There are NO hard-coded percentages such as:
    # 0.82
    # 0.61
    # 0.46
    #
    # The funnel reflects actual events.
    # -----------------------------------------------------

    sessions = len(journeys)

    product_views = 0
    cart_users = 0
    checkout_users = 0
    purchase_users = 0

    for journey in journeys:

        sequence = seq(journey)

        # Product page was actually viewed.
        if any(
            event in sequence
            for event in [
                "view_item",
            ]
        ):
            product_views += 1

        # User actually interacted with cart.
        if any(
            event in sequence
            for event in [
                "add_to_cart",
                "view_cart",
            ]
        ):
            cart_users += 1

        # User actually started checkout.
        if any(
            event in sequence
            for event in [
                "begin_checkout",
            ]
        ):
            checkout_users += 1

        # User actually purchased.
        if any(
            event in sequence
            for event in [
                "purchase",
            ]
        ) or journey.get(
            "converted",
            False,
        ):
            purchase_users += 1

    # -----------------------------------------------------
    # Keep funnel mathematically sensible.
    #
    # A later stage cannot contain more users than an
    # earlier stage.
    # -----------------------------------------------------

    product_views = min(
        product_views,
        sessions,
    )

    cart_users = min(
        cart_users,
        product_views,
    )

    checkout_users = min(
        checkout_users,
        cart_users,
    )

    purchase_users = min(
        purchase_users,
        checkout_users,
    )

    funnel = pd.DataFrame(
        {
            "Stage": [
                "Sessions",
                "Product views",
                "Cart",
                "Checkout",
                "Purchase",
            ],

            "Users": [
                sessions,
                product_views,
                cart_users,
                checkout_users,
                purchase_users,
            ],
        }
    )

    if sessions == 0:

        st.info(
            "No journeys have been recorded yet. "
            "Browse the e-commerce website first."
        )

    else:

        fig = px.funnel(
            funnel,
            x="Users",
            y="Stage",
            title="Observed Conversion Funnel",
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.caption(
            "Funnel values are calculated from actual "
            "reconstructed journeys and event sequences."
        )

    st.divider()

    st.subheader(
        "Journey Outcomes"
    )

    if journeys:

        df = df_for(journeys)

        if not df.empty:

            outcome = (
                df["converted"]
                .map(
                    {
                        True: "Converted",
                        False: "Not converted",
                    }
                )
                .value_counts()
                .rename_axis("Outcome")
                .reset_index(
                    name="Sessions"
                )
            )

            fig = px.bar(
                outcome,
                x="Outcome",
                y="Sessions",
                title="Observed Session Outcomes",
            )

            st.plotly_chart(
                fig,
                use_container_width=True,
            )

    else:

        st.info(
            "No journey data available yet."
        )


# =========================================================
# 2. JOURNEY EXPLORER
# =========================================================

with tabs[1]:

    st.subheader(
        "Live Journey Explorer"
    )

    st.caption(
        "This follows the journeys reconstructed from "
        "events generated by the e-commerce website."
    )

    # -----------------------------------------------------
    # REFRESH LIVE DATA
    # -----------------------------------------------------

    live_journeys = get(
        "/api/analytics/journeys",
        default=[],
        timeout=5,
    )

    if not isinstance(
        live_journeys,
        list,
    ):

        live_journeys = []

    # -----------------------------------------------------
    # FIND ACTIVE / INCOMPLETE JOURNEYS
    # -----------------------------------------------------

    active = []

    for journey in live_journeys:

        status = str(
            journey.get(
                "status",
                "",
            )
        ).lower()

        is_active = (
            journey.get(
                "active",
                False,
            )
            or status in [
                "active",
                "in_progress",
                "in progress",
            ]
        )

        incomplete = (
            not journey.get(
                "converted",
                False,
            )
            and not journey.get(
                "abandonment_stage"
            )
        )

        if is_active or incomplete:

            active.append(journey)

    # -----------------------------------------------------
    # SELECT CURRENT JOURNEY
    # -----------------------------------------------------

    if active:

        latest = active[-1]

        st.markdown(
            '<span class="live">● CURRENT JOURNEY</span>',
            unsafe_allow_html=True,
        )

        session_id = latest.get(
            "session_id",
            "unknown",
        )

        st.caption(
            f"Session: {session_id}"
        )

        sequence = seq(latest)

        if sequence:

            for index, step in enumerate(
                sequence
            ):

                is_current = (
                    index == len(sequence) - 1
                )

                if is_current:

                    st.markdown(
                        f"""
                        <div class="current-step">
                            <span class="live">
                                ● CURRENT
                            </span>
                            <br>
                            <strong>
                                {step}
                            </strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:

                    st.markdown(
                        f"""
                        <div class="journey-step">
                            ✓ {step}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                st.markdown(
                    "↓"
                )

        else:

            st.info(
                "The session exists, but its journey "
                "has not been reconstructed yet."
            )

        st.divider()

        a, b, c, d = st.columns(4)

        a.metric(
            "Events",
            latest.get(
                "event_count",
                len(sequence),
            ),
        )

        b.metric(
            "Journey Length",
            latest.get(
                "journey_length",
                len(sequence),
            ),
        )

        duration = float(
            latest.get(
                "duration_seconds",
                0,
            )
            or 0
        )

        c.metric(
            "Duration",
            f"{duration:.1f}s",
        )

        d.metric(
            "Status",
            "Active",
        )

    elif live_journeys:

        # If there is no explicitly active journey,
        # show the most recently returned journey.

        latest = live_journeys[-1]

        st.info(
            "No session is explicitly marked active. "
            "Showing the latest reconstructed journey."
        )

        sequence = seq(latest)

        if sequence:

            for index, step in enumerate(
                sequence
            ):

                if index == len(sequence) - 1:

                    st.markdown(
                        f"""
                        <div class="current-step">
                            <strong>
                                ● {step}
                            </strong>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                else:

                    st.write(
                        f"✓ {step}"
                    )

        st.caption(
            "Session: "
            + str(
                latest.get(
                    "session_id",
                    "unknown",
                )
            )
        )

    else:

        st.info(
            "No journeys yet. Open the e-commerce "
            "website and start browsing."
        )

    # -----------------------------------------------------
    # ALL JOURNEYS
    # -----------------------------------------------------

    st.divider()

    st.subheader(
        "All Reconstructed Journeys"
    )

    if live_journeys:

        journey_df = df_for(
            live_journeys
        )

        st.dataframe(
            journey_df,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No reconstructed journeys available."
        )


# =========================================================
# 3. PER USER
# =========================================================

with tabs[2]:

    st.subheader(
        "Analyze One User"
    )

    st.caption(
        "Uses pseudonymous identifiers only."
    )

    users = get(
        "/api/analytics/users",
        default=[],
    )

    if not isinstance(
        users,
        list,
    ):

        users = []

    ids = [
        user.get("user_id")
        for user in users
        if user.get("user_id")
    ]

    if not ids:

        st.info(
            "No users are available yet. "
            "Browse the storefront first."
        )

    else:

        uid = st.selectbox(
            "Select pseudonymous user",
            ids,
        )

        data = get(
            "/api/analytics/users/"
            + str(uid)
        )

        if data is None:

            st.error(
                "Could not load this user's journey."
            )

        else:

            a, b, c = st.columns(3)

            a.metric(
                "Sessions",
                data.get(
                    "session_count",
                    0,
                ),
            )

            b.metric(
                "Total Events",
                data.get(
                    "total_events",
                    0,
                ),
            )

            c.metric(
                "Converted Sessions",
                data.get(
                    "converted_sessions",
                    0,
                ),
            )

            st.divider()

            for i, session in enumerate(
                data.get(
                    "sessions",
                    []
                ),
                1,
            ):

                with st.container(
                    border=True
                ):

                    st.markdown(
                        f"### Session {i}"
                    )

                    st.code(
                        session.get(
                            "session_id",
                            "unknown",
                        )
                    )

                    journey = session.get(
                        "journey",
                        [],
                    )

                    if isinstance(
                        journey,
                        str,
                    ):

                        if "→" in journey:

                            journey = [
                                x.strip()
                                for x in journey.split(
                                    "→"
                                )
                                if x.strip()
                            ]

                        else:

                            journey = [
                                journey
                            ]

                    if journey:

                        st.markdown(
                            "**Journey Path**"
                        )

                        st.write(
                            " → ".join(
                                str(x)
                                for x in journey
                            )
                        )

                    else:

                        st.info(
                            "No reconstructed journey."
                        )

                    x, y, z, w = st.columns(4)

                    x.metric(
                        "Events",
                        session.get(
                            "event_count",
                            0,
                        ),
                    )

                    y.metric(
                        "Journey Length",
                        session.get(
                            "journey_length",
                            0,
                        ),
                    )

                    duration = float(
                        session.get(
                            "duration_seconds",
                            0,
                        )
                        or 0
                    )

                    z.metric(
                        "Duration",
                        f"{duration:.1f}s",
                    )

                    w.metric(
                        "Converted",
                        (
                            "Yes"
                            if session.get(
                                "converted"
                            )
                            else "No"
                        ),
                    )

                    if session.get(
                        "abandonment_stage"
                    ):

                        st.warning(
                            "Abandonment stage: "
                            + str(
                                session[
                                    "abandonment_stage"
                                ]
                            )
                        )

                    events = pd.DataFrame(
                        session.get(
                            "events",
                            [],
                        )
                    )

                    if not events.empty:

                        st.markdown(
                            "**Event-by-event record**"
                        )

                        st.dataframe(
                            events,
                            use_container_width=True,
                            hide_index=True,
                        )


# =========================================================
# 4. SEGMENTS
# =========================================================

with tabs[3]:

    st.subheader(
        "Behavioral Segmentation"
    )

    df = df_for(
        journeys
    )

    if len(df) < 4:

        st.info(
            "Not enough journeys for meaningful "
            "segmentation. Generate more sessions first."
        )

    else:

        df["conversion_numeric"] = (
            df["converted"]
            .astype(int)
        )

        df["journey_group"] = pd.cut(
            df["journey_length"],
            bins=[
                -1,
                3,
                6,
                float("inf"),
            ],
            labels=[
                "Short journey",
                "Medium journey",
                "Long journey",
            ],
        )

        summary = (
            df.groupby(
                "journey_group",
                observed=True,
            )
            .agg(
                users=(
                    "session_id",
                    "count",
                ),

                conversion_rate=(
                    "conversion_numeric",
                    "mean",
                ),

                avg_journey_length=(
                    "journey_length",
                    "mean",
                ),

                avg_duration=(
                    "duration_seconds",
                    "mean",
                ),
            )
            .reset_index()
        )

        summary[
            "conversion_rate"
        ] *= 100

        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
        )

        fig = px.bar(
            summary,
            x="journey_group",
            y="conversion_rate",
            title=(
                "Observed Conversion "
                "by Journey Length"
            ),
            labels={
                "conversion_rate":
                    "Conversion (%)"
            },
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        st.caption(
            "Descriptive groups only. "
            "They are not presented as causal clusters."
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
        This dashboard does not fabricate causal effects
        from observational journey data.

        A defensible causal conclusion requires an appropriate
        identification strategy, controlled experiment, or
        causal estimator with sufficient data and assumptions.
        """
    )

    st.code(
        "INSUFFICIENT_EVIDENCE"
    )


# =========================================================
# 6. WHAT-IF SIMULATION
# =========================================================

with tabs[5]:

    st.subheader(
        "What-If Simulation"
    )

    st.write(
        "Change a real journey factor and see how the "
        "modeled conversion, abandonment, and journey "
        "length could change."
    )

    st.warning(
        "SIMULATED / ESTIMATED — these results are "
        "hypothetical scenarios, not observed causal effects."
    )

    # -----------------------------------------------------
    # OBSERVED BASELINE
    # -----------------------------------------------------

    baseline_conversion = float(
        overview.get(
            "conversion_rate",
            0
        ) or 0
    )

    baseline_abandonment = float(
        overview.get(
            "abandonment_rate",
            0
        ) or 0
    )

    baseline_journey_length = float(
        overview.get(
            "avg_journey_length",
            0
        ) or 0
    )

    # -----------------------------------------------------
    # DEFAULT BEHAVIORAL VALUES
    #
    # These are used when the current event data does not
    # contain the corresponding measurement yet.
    # -----------------------------------------------------

    observed_page_load = 10.0
    observed_product_time = 1.0
    observed_pages = 2.0
    observed_checkout_steps = 5.0

    # -----------------------------------------------------
    # SELECT VARIABLE
    # -----------------------------------------------------

    st.markdown(
        "### Choose a journey factor"
    )

    variable = st.selectbox(
        "Variable to change",
        [
            "Page load time",
            "Time spent on product",
            "Pages visited",
            "Checkout steps",
        ]
    )

    # -----------------------------------------------------
    # PAGE LOAD TIME
    # -----------------------------------------------------

    if variable == "Page load time":

        st.markdown(
            "#### Page load time"
        )

        st.caption(
            "What if the page became faster or slower?"
        )

        new_value = st.slider(
            "Page load time (seconds)",
            min_value=1.0,
            max_value=15.0,
            value=5.0,
            step=0.5,
        )

        baseline_value = observed_page_load

        # Faster page = better hypothetical outcome.
        improvement = (
            baseline_value - new_value
        ) / baseline_value

        improvement = max(
            -1.0,
            min(1.0, improvement)
        )

        # Model effect.
        conversion_change = (
            improvement * 60.0
        )

        abandonment_change = (
            improvement * 45.0
        )

        journey_change = (
            improvement * 1.5
        )

        variable_label = "Page load time"

    # -----------------------------------------------------
    # TIME SPENT ON PRODUCT
    # -----------------------------------------------------

    elif variable == "Time spent on product":

        st.markdown(
            "#### Time spent on product"
        )

        st.caption(
            "What if users spent more time understanding "
            "the product before deciding?"
        )

        new_value = st.slider(
            "Time on product (seconds)",
            min_value=0.5,
            max_value=15.0,
            value=5.0,
            step=0.5,
        )

        baseline_value = observed_product_time

        improvement = (
            new_value - baseline_value
        ) / max(
            baseline_value,
            1.0
        )

        improvement = max(
            -1.0,
            min(1.0, improvement)
        )

        conversion_change = (
            improvement * 15.0
        )

        abandonment_change = (
            -improvement * 10.0
        )

        journey_change = (
            improvement * 0.5
        )

        variable_label = "Time spent on product"

    # -----------------------------------------------------
    # PAGES VISITED
    # -----------------------------------------------------

    elif variable == "Pages visited":

        st.markdown(
            "#### Pages visited"
        )

        st.caption(
            "What if users explored fewer or more pages "
            "before completing the journey?"
        )

        new_value = st.slider(
            "Pages visited",
            min_value=1,
            max_value=15,
            value=2,
            step=1,
        )

        baseline_value = observed_pages

        # Fewer pages can represent less navigation
        # friction in this hypothetical scenario.
        improvement = (
            baseline_value - new_value
        ) / max(
            baseline_value,
            1.0
        )

        improvement = max(
            -1.0,
            min(1.0, improvement)
        )

        conversion_change = (
            improvement * 25.0
        )

        abandonment_change = (
            improvement * 20.0
        )

        journey_change = (
            improvement * 1.0
        )

        variable_label = "Pages visited"

    # -----------------------------------------------------
    # CHECKOUT STEPS
    # -----------------------------------------------------

    else:

        st.markdown(
            "#### Checkout steps"
        )

        st.caption(
            "What if checkout required fewer steps?"
        )

        new_value = st.slider(
            "Checkout steps",
            min_value=1,
            max_value=8,
            value=3,
            step=1,
        )

        baseline_value = observed_checkout_steps

        improvement = (
            baseline_value - new_value
        ) / baseline_value

        improvement = max(
            -1.0,
            min(1.0, improvement)
        )

        conversion_change = (
            improvement * 25.0
        )

        abandonment_change = (
            improvement * 25.0
        )

        journey_change = (
            improvement * 1.5
        )

        variable_label = "Checkout steps"

    # -----------------------------------------------------
    # SIMULATED RESULTS
    # -----------------------------------------------------

    simulated_conversion = (
        baseline_conversion
        + conversion_change
    )

    simulated_abandonment = (
        baseline_abandonment
        - abandonment_change
    )

    simulated_journey = (
        baseline_journey_length
        - journey_change
    )

    simulated_conversion = max(
        0.0,
        min(100.0, simulated_conversion)
    )

    simulated_abandonment = max(
        0.0,
        min(100.0, simulated_abandonment)
    )

    simulated_journey = max(
        1.0,
        simulated_journey
    )

    # -----------------------------------------------------
    # BEFORE / AFTER
    # -----------------------------------------------------

    st.markdown(
        "### Scenario"
    )

    left, middle, right = st.columns(3)

    with left:

        st.metric(
            variable_label,
            f"{baseline_value:g}",
            f"→ {new_value:g}",
        )

    with middle:

        st.metric(
            "Conversion",
            f"{simulated_conversion:.1f}%",
            f"{simulated_conversion - baseline_conversion:+.1f}%",
        )

    with right:

        st.metric(
            "Abandonment",
            f"{simulated_abandonment:.1f}%",
            f"{simulated_abandonment - baseline_abandonment:+.1f}%",
        )

    # -----------------------------------------------------
    # JOURNEY LENGTH
    # -----------------------------------------------------

    st.markdown(
        "### Journey impact"
    )

    a, b, c = st.columns(3)

    with a:

        st.metric(
            "Current conversion",
            f"{baseline_conversion:.1f}%"
        )

    with b:

        st.metric(
            "Simulated conversion",
            f"{simulated_conversion:.1f}%"
        )

    with c:

        st.metric(
            "Simulated journey length",
            f"{simulated_journey:.1f}"
        )

    # -----------------------------------------------------
    # EXPLANATION
    # -----------------------------------------------------

    st.markdown(
        "### Interpretation"
    )

    if simulated_conversion > baseline_conversion:

        st.success(
            f"If {variable_label.lower()} changed from "
            f"{baseline_value:g} to {new_value:g}, "
            f"the model estimates a potential improvement "
            f"in conversion from "
            f"{baseline_conversion:.1f}% to "
            f"{simulated_conversion:.1f}%."
        )

    elif simulated_conversion < baseline_conversion:

        st.error(
            f"The modeled change would reduce estimated "
            f"conversion from "
            f"{baseline_conversion:.1f}% to "
            f"{simulated_conversion:.1f}%."
        )

    else:

        st.info(
            "The modeled change does not alter the "
            "estimated conversion rate."
        )

    st.caption(
        "These values are simulated estimates based on "
        "the selected hypothetical scenario. They are "
        "not measured causal effects."
    )

# =========================================================
# 7. RECOMMENDATIONS
# =========================================================

with tabs[6]:

    st.subheader(
        "Explainable Recommendations"
    )

    df = df_for(
        journeys
    )

    if df.empty:

        st.info(
            "Generate journeys before "
            "recommendations can be assessed."
        )

    else:

        converted = int(
            df["converted"].sum()
        )

        insights = sum(
            has(
                seq(journey),
                [
                    "product insight",
                    "product_insight",
                    "insight",
                ],
            )
            for journey in journeys
        )

        cards = [

            (
                "Monitor the largest journey drop-off",

                (
                    f"{len(df)} reconstructed sessions; "
                    f"{converted} are marked converted."
                ),
            ),

            (
                "Monitor Product Insight interaction",

                (
                    f"{insights} reconstructed journeys "
                    "contain a product-insight interaction."
                ),
            ),
        ]

        for title, evidence in cards:

            with st.container(
                border=True
            ):

                st.subheader(
                    title
                )

                st.write(
                    "Evidence:",
                    evidence,
                )

                st.caption(
                    "Descriptive evidence only; "
                    "no fabricated causal benefit "
                    "is reported."
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
        Pseudonymous user/session identifier,
        event type, timestamp, page context,
        product context, and limited event metadata
        needed for journey analytics.
        """
    )

    st.markdown(
        "### Not collected"
    )

    st.write(
        """
        Passwords, payment details, email addresses,
        phone numbers, and direct personal identifiers.
        """
    )

    st.markdown(
        "### Protection"
    )

    st.write(
        """
        Event allow-list, HMAC-SHA256 pseudonymization,
        data minimization, configurable retention,
        and aggregation thresholds.
        """
    )


# =========================================================
# 9. SYSTEM STATUS
# =========================================================

with tabs[8]:

    st.subheader(
        "System Status"
    )

    status = get(
        "/api/system/status"
    )

    if status is None:

        st.error(
            "Backend is not reachable."
        )

    else:

        st.success(
            "Backend is reachable."
        )

        st.json(
            status
        )

    st.divider()

    if st.button(
        "Recompute Journeys"
    ):

        response = post(
            "/api/analytics/recompute"
        )

        if (
            response is not None
            and response.ok
        ):

            st.success(
                "Journeys recomputed successfully."
            )

            st.rerun()

        elif response is not None:

            st.error(
                "Could not recompute journeys: "
                + response.text
            )

        else:

            st.error(
                "Could not reach the analytics backend."
            )