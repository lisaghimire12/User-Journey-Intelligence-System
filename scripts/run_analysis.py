"""
run_analysis.py
------------------
Re-runs analytics/causal/simulation/recommendation stages against
whatever data is currently in the database, without regenerating it.
Useful after loading real (anonymized) event data instead of synthetic
data.

Usage:
    python scripts/run_analysis.py
"""
import _bootstrap  # noqa: F401

from src import database
from src.data_processing import clean_events, clean_sessions
from src.journey_reconstruction import reconstruct_journeys
from src.behavioral_analysis import compute_kpis
from src import causal_analysis
from src.recommendation_engine import build_recommendations
from src.explanation_engine import build_explanation


def main():
    raw_events = database.read_table("events")
    raw_sessions = database.read_table("sessions")

    if raw_events.empty:
        print("No events found in the database. Run scripts/generate_data.py first "
              "(or load real anonymized event data).")
        return

    events_pl = clean_events(raw_events)
    sessions_pl = clean_sessions(raw_sessions)
    reconstructed = reconstruct_journeys(events_pl)

    kpis = compute_kpis(reconstructed, sessions_pl.to_pandas())
    print(f"Sessions: {kpis['total_sessions']}  Conversion: {kpis['conversion_rate']}%")

    causal_df = reconstructed.merge(sessions_pl.to_pandas(), on="session_id", how="left")
    for q in causal_analysis.CAUSAL_QUESTIONS:
        result = causal_analysis.estimate_effect(
            causal_df, q["treatment_raw"], q["outcome"], q["confounders"],
            treatment_label=q["treatment_label"], beneficial_direction=q.get("beneficial_direction", "low"),
        )
        print(f"{q['question']}: {result.status} "
              + (f"effect={result.effect_estimate} CI=({result.ci_lower},{result.ci_upper})" if result.status == "ok" else result.message))

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

    print("\nRanked recommendations:")
    for r in recs:
        print(f"  {r.label}: score={r.recommendation_score}/10 confidence={r.confidence}")


if __name__ == "__main__":
    main()
