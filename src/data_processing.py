"""
data_processing.py
-------------------
Cleans and type-normalizes raw event/session data pulled from the
database, using Polars for the heavier transformations and returning
pandas DataFrames at the boundary (Streamlit + Plotly ecosystem expects
pandas).
"""

from __future__ import annotations

import pandas as pd
import polars as pl

from src import database


def load_raw_events() -> pd.DataFrame:
    return database.read_table("events")


def load_raw_sessions() -> pd.DataFrame:
    return database.read_table("sessions")


def load_raw_journeys() -> pd.DataFrame:
    return database.read_table("journeys")


def clean_events(events_df: pd.DataFrame) -> pl.DataFrame:
    """Type-normalize and sort the events table using Polars."""
    if events_df.empty:
        return pl.DataFrame()
    pdf = pl.from_pandas(events_df)
    pdf = pdf.with_columns([
        pl.col("timestamp").str.to_datetime(strict=False) if pdf.schema["timestamp"] == pl.Utf8 else pl.col("timestamp"),
        pl.col("dwell_time").cast(pl.Float64, strict=False),
        pl.col("sequence_number").cast(pl.Int64, strict=False),
    ])
    pdf = pdf.sort(["session_id", "sequence_number"])
    return pdf


def clean_sessions(sessions_df: pd.DataFrame) -> pl.DataFrame:
    if sessions_df.empty:
        return pl.DataFrame()
    pdf = pl.from_pandas(sessions_df)
    for col in ["session_start", "session_end"]:
        if col in pdf.columns and pdf.schema[col] == pl.Utf8:
            pdf = pdf.with_columns(pl.col(col).str.to_datetime(strict=False))
    if "intervention_exposure" in pdf.columns:
        pdf = pdf.with_columns(pl.col("intervention_exposure").cast(pl.Boolean, strict=False))
    return pdf


def apply_filters(
    df: pd.DataFrame,
    device: list[str] | None = None,
    platform: list[str] | None = None,
    source: list[str] | None = None,
    converted_only: str = "all",
) -> pd.DataFrame:
    """Generic filter application shared across dashboard pages."""
    out = df.copy()
    if device:
        out = out[out["device_type"].isin(device)]
    if platform:
        out = out[out["platform"].isin(platform)]
    if source:
        out = out[out["acquisition_source"].isin(source)]
    if converted_only == "converted" and "converted" in out.columns:
        out = out[out["converted"].astype(bool)]
    elif converted_only == "not_converted" and "converted" in out.columns:
        out = out[~out["converted"].astype(bool)]
    return out
