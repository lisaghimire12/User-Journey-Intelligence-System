"""
run_pipeline.py
-----------------
Runs the full pipeline end-to-end: init DB -> generate data -> process ->
reconstruct journeys -> behavioral analytics -> segmentation -> causal
analysis -> simulation -> recommendations. Mirrors the automation
described in the project spec so the Streamlit app never needs a manual
Power-BI-style export/import step.

Usage:
    python scripts/run_pipeline.py --sessions 6000 --reset
"""
import argparse
import _bootstrap  # noqa: F401

from src import database
from src.data_generator import generate_events
from src.data_processing import clean_events, clean_sessions
from src.journey_reconstruction import reconstruct_journeys
from src.behavioral_analysis import compute_kpis, engagement_score
from src.segmentation import compute_segments
from src import causal_analysis
from src.recommendation_engine import build_recommendations
from src.explanation_engine import build_explanation


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions", type=int, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--reset", action="store_true")
    args = parser.parse_args()

    print("[1/9] Initializing database schema ...")
    database.init_schema()
    if args.reset:
        database.truncate_all()

    print("[2/9] Generating synthetic events ...")
    sessions_df, events_df, journeys_df = generate_events(n_sessions=args.sessions, seed=args.seed)
    database.write_dataframe(sessions_df.to_pandas(), "sessions")
    database.write_dataframe(events_df.to_pandas(), "events")
    database.write_dataframe(journeys_df.to_pandas(), "journeys")

    print("[3/9] Reloading + cleaning from database ...")
    raw_events = database.read_table("events")
    raw_sessions = database.read_table("sessions")
    events_pl = clean_events(raw_events)
    sessions_pl = clean_sessions(raw_sessions)

    print("[4/9] Reconstructing journeys from raw events ...")
    reconstructed = reconstruct_journeys(events_pl)
    print(f"       {len(reconstructed)} journeys reconstructed")

    print("[5/9] Computing behavioral analytics ...")
    kpis = compute_kpis(reconstructed, sessions_pl.to_pandas())
    print(f"       Conversion rate: {kpis['conversion_rate']}%")

    print("[6/9] Computing behavioral segments ...")
    merged = engagement_score(sessions_pl.to_pandas(), reconstructed)
    assigned, summary = compute_segments(merged)
    print(f"       {len(summary)} segments identified" if not summary.empty else "       Not enough data for segmentation")

    print("[7/9] Running causal analysis on all predefined questions ...")
    causal_df = reconstructed.merge(sessions_pl.to_pandas(), on="session_id", how="left")
    for q in causal_analysis.CAUSAL_QUESTIONS:
        result = causal_analysis.estimate_effect(
            causal_df, q["treatment_raw"], q["outcome"], q["confounders"],
            treatment_label=q["treatment_label"], beneficial_direction=q.get("beneficial_direction", "low"),
        )
        database.write_causal_result({
            "treatment": result.treatment, "outcome": result.outcome,
            "effect_estimate": result.effect_estimate, "ci_lower": result.ci_lower,
            "ci_upper": result.ci_upper, "method": result.method,
            "sample_size": result.sample_size, "assumptions": result.assumptions,
            "refutation_passed": result.refutation_passed,
        })
        print(f"       {q['question']} -> {result.status}"
              + (f" (effect={result.effect_estimate})" if result.status == "ok" else ""))

    print("[8/9] Building automated recommendations ...")
    recs = build_recommendations(reconstructed, sessions_pl.to_pandas(), kpis["conversion_rate"])
    records = []
    for r in recs:
        explanation = build_explanation(r)
        records.append({
            "intervention": r.label, "expected_benefit": r.causal_effect_pct or r.simulated_improvement_pct or 0.0,
            "evidence": r.evidence, "confidence": r.confidence, "complexity": r.complexity,
            "risk": r.risk, "recommendation_score": r.recommendation_score, "explanation": explanation,
        })
    database.write_recommendations(records)
    print(f"       Top recommendation: {recs[0].label} (score {recs[0].recommendation_score}/10)")

    print("[9/9] Pipeline complete.")


if __name__ == "__main__":
    main()
