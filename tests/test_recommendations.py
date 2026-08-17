import pandas as pd

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
