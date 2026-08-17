"""
behavioral_analysis.py
-----------------------
Computes the "What happened?" layer: KPIs, drop-off analysis, engagement
scoring, and journey-length distributions, all from real reconstructed
journeys and events -- nothing here is hard-coded.
"""

from __future__ import annotations

import pandas as pd


def compute_kpis(journeys_df: pd.DataFrame, sessions_df: pd.DataFrame) -> dict:
    if journeys_df.empty:
        return {
            "total_sessions": 0, "conversion_rate": 0.0, "abandonment_rate": 0.0,
            "avg_duration": 0.0, "avg_length": 0.0,
            "top_entry": "-", "top_exit": "-", "top_conversion_journey": "-",
        }

    total_sessions = journeys_df["session_id"].nunique()
    conversion_rate = journeys_df["converted"].astype(bool).mean() * 100
    abandonment_rate = 100 - conversion_rate
    avg_duration = journeys_df["duration"].mean()
    avg_length = journeys_df["journey_length"].mean()

    entry_col = "entry_page" if "entry_page" in journeys_df.columns else None
    exit_col = "exit_page" if "exit_page" in journeys_df.columns else None
    top_entry = journeys_df[entry_col].mode().iloc[0] if entry_col and not journeys_df.empty else "-"
    top_exit = journeys_df[exit_col].mode().iloc[0] if exit_col and not journeys_df.empty else "-"

    converted = journeys_df[journeys_df["converted"].astype(bool)]
    top_conversion_journey = (
        converted["journey_sequence"].mode().iloc[0] if not converted.empty else "-"
    )

    return {
        "total_sessions": int(total_sessions),
        "conversion_rate": round(float(conversion_rate), 2),
        "abandonment_rate": round(float(abandonment_rate), 2),
        "avg_duration": round(float(avg_duration), 1),
        "avg_length": round(float(avg_length), 1),
        "top_entry": top_entry,
        "top_exit": top_exit,
        "top_conversion_journey": top_conversion_journey,
    }


def dropoff_by_stage(journeys_df: pd.DataFrame) -> pd.DataFrame:
    if journeys_df.empty:
        return pd.DataFrame(columns=["stage", "sessions", "share_pct"])
    abandoned = journeys_df[~journeys_df["converted"].astype(bool)]
    if abandoned.empty:
        return pd.DataFrame(columns=["stage", "sessions", "share_pct"])
    counts = abandoned["abandonment_stage"].value_counts().reset_index()
    counts.columns = ["stage", "sessions"]
    counts["share_pct"] = (counts["sessions"] / counts["sessions"].sum() * 100).round(1)
    return counts.sort_values("sessions", ascending=False)


def journey_length_distribution(journeys_df: pd.DataFrame) -> pd.DataFrame:
    if journeys_df.empty:
        return pd.DataFrame(columns=["journey_length"])
    return journeys_df[["journey_length"]].copy()


def conversion_by_dimension(journeys_df: pd.DataFrame, sessions_df: pd.DataFrame, dimension: str) -> pd.DataFrame:
    if journeys_df.empty or sessions_df.empty or dimension not in sessions_df.columns:
        return pd.DataFrame(columns=[dimension, "conversion_rate", "sessions"])
    merged = journeys_df.merge(sessions_df[["session_id", dimension]], on="session_id", how="left")
    grouped = merged.groupby(dimension).agg(
        conversion_rate=("converted", "mean"),
        sessions=("session_id", "count"),
    ).reset_index()
    grouped["conversion_rate"] = (grouped["conversion_rate"] * 100).round(1)
    return grouped.sort_values("sessions", ascending=False)


def engagement_score(sessions_df: pd.DataFrame, journeys_df: pd.DataFrame) -> pd.DataFrame:
    """
    A simple, transparent, explainable engagement score in [0, 100]
    combining journey depth, dwell/duration, and repeat-visit behavior --
    used as an input feature for segmentation, not a black box.
    """
    if journeys_df.empty:
        return pd.DataFrame()
    merged = journeys_df.merge(sessions_df, on="session_id", how="left")
    length_norm = (merged["journey_length"] / merged["journey_length"].quantile(0.95)).clip(0, 1)
    duration_norm = (merged["duration"] / merged["duration"].quantile(0.95)).clip(0, 1)
    unique_norm = (merged["unique_pages"] / merged["unique_pages"].clip(lower=1).quantile(0.95)).clip(0, 1)
    merged["engagement_score"] = ((0.4 * length_norm + 0.35 * duration_norm + 0.25 * unique_norm) * 100).round(1)
    return merged
