"""
intervention_engine.py
------------------------
Defines the catalog of candidate interventions and computes, from real
session data, how many/what share of sessions each intervention would
plausibly affect (e.g. "simplify registration" only matters for sessions
that reach the registration stage).

Complexity and risk ratings are engineering judgments (documented here,
not computed from data) about how hard each change is to ship -- this is
made explicit rather than pretending they were "calculated".
"""

from __future__ import annotations

import pandas as pd

INTERVENTIONS = {
    "simplify_registration": {
        "label": "Simplify Registration",
        "description": "Reduce the number of required fields and steps in the registration form.",
        "causal_question_id": "registration_friction",
        "scenario_key": "B - Simplified registration",
        "complexity": "Low",
        "risk": "Low",
        "affected_stage_pages": ["Registration", "Registration Error"],
    },
    "reduce_checkout_steps": {
        "label": "Reduce Checkout Steps",
        "description": "Collapse checkout into fewer pages/steps and streamline payment entry.",
        "causal_question_id": "checkout_friction",
        "scenario_key": "C - Reduced checkout friction",
        "complexity": "Medium",
        "risk": "Medium",
        "affected_stage_pages": ["Checkout"],
    },
    "reduce_page_delay": {
        "label": "Reduce Page Delay",
        "description": "Improve page load / response latency across the funnel.",
        "causal_question_id": None,  # evaluated via simulation only
        "scenario_key": "D - Reduced page delay",
        "complexity": "Medium",
        "risk": "Low",
        "affected_stage_pages": ["Home", "Search", "Product", "Registration", "Checkout"],
    },
    "improve_content_exposure": {
        "label": "Improve Content Exposure",
        "description": "Surface more product information / reviews earlier in the journey.",
        "causal_question_id": "content_exposure",
        "scenario_key": "E - Improved content exposure",
        "complexity": "Medium",
        "risk": "Low",
        "affected_stage_pages": ["Product", "Reviews"],
    },
    "reduce_navigation_friction": {
        "label": "Reduce Navigation Friction",
        "description": "Simplify site navigation / search to cut down on backtracking loops.",
        "causal_question_id": "navigation_friction",
        "scenario_key": None,  # evaluated via causal analysis primarily
        "complexity": "High",
        "risk": "Medium",
        "affected_stage_pages": ["Search", "Product", "Home"],
    },
}


def affected_session_share(journeys_df: pd.DataFrame, stage_pages: list[str]) -> float:
    """
    Share of sessions whose journey_sequence touches at least one of the
    given stage pages -- i.e. sessions the intervention could plausibly
    have reached.
    """
    if journeys_df.empty or "journey_sequence" not in journeys_df.columns:
        return 0.0
    mask = journeys_df["journey_sequence"].apply(
        lambda seq: any(p in seq for p in stage_pages)
    )
    return round(float(mask.mean() * 100), 1)
