import pandas as pd

from src import causal_analysis, intervention_engine, simulation_engine
from src.intervention_engine import affected_session_share


def test_affected_session_share_basic():
    df = pd.DataFrame({
        "journey_sequence": [
            "Home > Registration > Exit",
            "Home > Product > Exit",
            "Home > Registration > Cart > Checkout > Purchase",
        ]
    })
    share = affected_session_share(df, ["Registration"])
    assert share == round(2 / 3 * 100, 1)


def test_affected_session_share_empty():
    df = pd.DataFrame(columns=["journey_sequence"])
    assert affected_session_share(df, ["Registration"]) == 0.0


def test_causal_estimate_reports_missing_required_column():
    result = causal_analysis.estimate_effect(
        pd.DataFrame({"converted": [True], "prior_engagement": [0.5]}),
        treatment_raw="registration_friction",
        outcome="converted",
        confounders=["prior_engagement"],
    )

    assert result.status == "insufficient_evidence"
    assert "registration_friction" in result.message


def test_intervention_scenario_references_are_valid():
    scenario_keys = [
        meta["scenario_key"]
        for meta in intervention_engine.INTERVENTIONS.values()
        if meta["scenario_key"]
    ]

    assert set(scenario_keys) <= set(simulation_engine.SCENARIOS)
