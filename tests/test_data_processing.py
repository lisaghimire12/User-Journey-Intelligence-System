import pandas as pd

from src.data_processing import apply_filters


def test_apply_filters_device():
    df = pd.DataFrame({
        "device_type": ["desktop", "mobile", "desktop"],
        "platform": ["web", "web", "ios"],
        "acquisition_source": ["organic_search", "paid_search", "direct"],
        "converted": [True, False, True],
    })
    out = apply_filters(df, device=["desktop"])
    assert set(out["device_type"]) == {"desktop"}
    assert len(out) == 2


def test_apply_filters_converted_only():
    df = pd.DataFrame({
        "device_type": ["desktop", "mobile"],
        "platform": ["web", "web"],
        "acquisition_source": ["organic_search", "paid_search"],
        "converted": [True, False],
    })
    out = apply_filters(df, converted_only="converted")
    assert len(out) == 1
    assert out["converted"].iloc[0] is True or out["converted"].iloc[0] == True  # noqa: E712
