"""
segmentation.py
----------------
Derives interpretable behavioral segments using unsupervised clustering
(K-Means, scikit-learn) over real journey/session features, then labels
each resulting cluster based on its own statistical profile rather than
forcing a pre-baked label onto arbitrary data.

Candidate archetypes referenced only as *possible* labels, chosen by
comparing each cluster's measured conversion rate, journey length, and
loop/duration behavior against the others:
    Fast Converters, Researchers, Hesitant Users, Lost Users
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from src.privacy import MIN_AGGREGATION_GROUP_SIZE

FEATURES = ["journey_length", "duration", "unique_pages", "repeated_pages", "engagement_score"]


def _label_cluster(profile: pd.Series, global_conv: float, global_len: float) -> str:
    conv = profile["converted"]
    length = profile["journey_length"]
    repeats = profile["repeated_pages"]

    if conv >= global_conv and length <= global_len:
        return "Fast Converters"
    if length > global_len and repeats >= profile.get("repeated_pages", 0):
        if conv >= global_conv * 0.6:
            return "Researchers"
        return "Hesitant Users"
    if conv < global_conv * 0.5:
        return "Lost Users"
    return "Hesitant Users"


def compute_segments(merged_df: pd.DataFrame, n_clusters: int = 4, random_state: int = 42) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    merged_df must contain journey + engagement columns (see
    behavioral_analysis.engagement_score output).

    Returns (assigned_df, segment_summary_df).
    """
    if merged_df.empty or len(merged_df) < n_clusters * MIN_AGGREGATION_GROUP_SIZE:
        return pd.DataFrame(), pd.DataFrame()

    df = merged_df.dropna(subset=FEATURES).copy()
    if df.empty:
        return pd.DataFrame(), pd.DataFrame()

    X = df[FEATURES].values
    X_scaled = StandardScaler().fit_transform(X)

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df["cluster"] = model.fit_predict(X_scaled)

    global_conv = df["converted"].astype(bool).mean()
    global_len = df["journey_length"].mean()

    cluster_profiles = df.groupby("cluster").agg(
        journey_length=("journey_length", "mean"),
        duration=("duration", "mean"),
        repeated_pages=("repeated_pages", "mean"),
        converted=("converted", "mean"),
        sessions=("session_id", "count"),
    )

    labels = {}
    used_labels = set()
    for cluster_id, profile in cluster_profiles.iterrows():
        label = _label_cluster(profile, global_conv, global_len)
        # avoid duplicate labels across clusters by falling back to a
        # numbered variant if the primary label is already taken
        base_label = label
        i = 2
        while label in used_labels:
            label = f"{base_label} ({i})"
            i += 1
        used_labels.add(label)
        labels[cluster_id] = label

    df["segment"] = df["cluster"].map(labels)

    common_paths = (
        df.groupby("segment")["journey_sequence"].agg(lambda s: s.mode().iloc[0] if not s.mode().empty else "-")
    )

    summary = df.groupby("segment").agg(
        segment_size=("session_id", "count"),
        conversion_rate=("converted", "mean"),
        avg_duration=("duration", "mean"),
        avg_journey_length=("journey_length", "mean"),
        avg_engagement=("engagement_score", "mean"),
    ).reset_index()
    summary["conversion_rate"] = (summary["conversion_rate"] * 100).round(1)
    summary["avg_duration"] = summary["avg_duration"].round(1)
    summary["avg_journey_length"] = summary["avg_journey_length"].round(1)
    summary["avg_engagement"] = summary["avg_engagement"].round(1)
    summary["common_path"] = summary["segment"].map(common_paths)
    summary["reportable"] = summary["segment_size"] >= MIN_AGGREGATION_GROUP_SIZE

    return df, summary.sort_values("segment_size", ascending=False)
