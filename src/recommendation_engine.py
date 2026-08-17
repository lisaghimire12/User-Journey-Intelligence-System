"""
recommendation_engine.py
--------------------------
Answers "Which intervention should we prioritize?"

Combines, per intervention:
  * causal effect estimate (from src.causal_analysis), when available
  * simulated improvement (from src.simulation_engine), when available
  * affected session share (from src.intervention_engine)
  * complexity / risk (engineering judgment, documented)
  * uncertainty (from causal CI width and/or simulation bootstrap std)

into a single 0-10 recommendation_score using a transparent, documented
weighted formula -- not an opaque model and not an LLM.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src import causal_analysis, intervention_engine, simulation_engine

COMPLEXITY_PENALTY = {"Low": 0.0, "Medium": 1.2, "High": 2.4}
RISK_PENALTY = {"Low": 0.0, "Medium": 1.0, "High": 2.0}


@dataclass
class InterventionScore:
    key: str
    label: str
    description: str
    causal_effect_pct: float | None
    causal_status: str
    simulated_improvement_pct: float | None
    affected_sessions_pct: float
    complexity: str
    risk: str
    uncertainty: float
    confidence: str
    recommendation_score: float
    evidence: dict


def _confidence_from_uncertainty(uncertainty: float, causal_status: str, refutation_passed) -> str:
    if causal_status == "insufficient_evidence":
        return "Low"
    if uncertainty <= 2.0 and refutation_passed:
        return "High"
    if uncertainty <= 5.0:
        return "Moderate"
    return "Low"


def build_recommendations(
    journeys_df: pd.DataFrame,
    sessions_df: pd.DataFrame,
    baseline_conversion_pct: float,
    n_sim_sessions: int = 2000,
) -> list[InterventionScore]:
    scores: list[InterventionScore] = []

    # Merge session causal-parameter columns onto journeys once.
    merge_cols = ["session_id", "prior_engagement", "registration_friction",
                  "checkout_friction", "page_delay", "content_exposure",
                  "navigation_friction"]
    available_cols = [c for c in merge_cols if c in sessions_df.columns]
    causal_df = journeys_df.merge(sessions_df[available_cols], on="session_id", how="left") \
        if not journeys_df.empty else pd.DataFrame()

    causal_question_map = {q["id"]: q for q in causal_analysis.CAUSAL_QUESTIONS}

    for key, meta in intervention_engine.INTERVENTIONS.items():
        causal_effect_pct = None
        causal_status = "not_evaluated"
        uncertainty = 8.0  # default: high uncertainty when nothing was evaluated
        refutation_passed = None

        q_id = meta["causal_question_id"]
        if q_id and q_id in causal_question_map and not causal_df.empty:
            q = causal_question_map[q_id]
            result = causal_analysis.estimate_effect(
                causal_df,
                treatment_raw=q["treatment_raw"],
                outcome=q["outcome"],
                confounders=q["confounders"],
                treatment_label=q["treatment_label"],
                beneficial_direction=q.get("beneficial_direction", "low"),
            )
            causal_status = result.status
            if result.status == "ok":
                causal_effect_pct = round(result.effect_estimate * 100, 2)
                uncertainty = round((result.ci_upper - result.ci_lower) * 100 / 2, 2)
                refutation_passed = result.refutation_passed

        simulated_improvement_pct = None
        scenario_key = meta["scenario_key"]
        if scenario_key:
            baseline = simulation_engine.run_simulation(
                simulation_engine.SCENARIOS["A - Current system"].__class__(
                    **{**simulation_engine.SCENARIOS["A - Current system"].__dict__, "n_sessions": n_sim_sessions}
                )
            )
            scenario_params = simulation_engine.SCENARIOS[scenario_key]
            scenario_result = simulation_engine.run_simulation(
                scenario_params.__class__(**{**scenario_params.__dict__, "n_sessions": n_sim_sessions})
            )
            simulated_improvement_pct = round(scenario_result["conversion_rate"] - baseline["conversion_rate"], 2)
            uncertainty = min(uncertainty, scenario_result["uncertainty"]) if causal_effect_pct is not None else scenario_result["uncertainty"]

        affected_pct = intervention_engine.affected_session_share(journeys_df, meta["affected_stage_pages"])

        # --- Transparent weighted scoring formula ---------------------
        # benefit signal: prefer causal effect when available (more
        # rigorous), otherwise fall back to simulated improvement.
        benefit_signal = causal_effect_pct if causal_effect_pct is not None else simulated_improvement_pct
        benefit_signal = benefit_signal if benefit_signal is not None else 0.0
        benefit_signal = max(0.0, benefit_signal)  # never reward a negative/harmful effect

        affected_weight = affected_pct / 100.0

        # Soft-cap the benefit contribution at a documented reference
        # ceiling (30 percentage points) so a single very large effect
        # can't automatically saturate the score, then blend in how many
        # sessions the change would actually reach.
        BENEFIT_REFERENCE_CEILING = 30.0
        BASE_SCORE = 1.5
        benefit_component = min(benefit_signal, BENEFIT_REFERENCE_CEILING) / BENEFIT_REFERENCE_CEILING * 6.5
        affected_component = affected_weight * 2.0

        penalty = COMPLEXITY_PENALTY[meta["complexity"]] + RISK_PENALTY[meta["risk"]] + (uncertainty * 0.15)
        score_0_10 = np.clip(BASE_SCORE + benefit_component + affected_component - penalty, 0, 10)

        confidence = _confidence_from_uncertainty(uncertainty, causal_status, refutation_passed)

        evidence = {
            "causal_effect_pct": causal_effect_pct,
            "causal_status": causal_status,
            "refutation_passed": refutation_passed,
            "simulated_improvement_pct": simulated_improvement_pct,
            "affected_sessions_pct": affected_pct,
            "uncertainty_pct_points": round(uncertainty, 2),
            "baseline_conversion_pct": baseline_conversion_pct,
        }

        scores.append(InterventionScore(
            key=key,
            label=meta["label"],
            description=meta["description"],
            causal_effect_pct=causal_effect_pct,
            causal_status=causal_status,
            simulated_improvement_pct=simulated_improvement_pct,
            affected_sessions_pct=affected_pct,
            complexity=meta["complexity"],
            risk=meta["risk"],
            uncertainty=round(uncertainty, 2),
            confidence=confidence,
            recommendation_score=round(float(score_0_10), 2),
            evidence=evidence,
        ))

    return sorted(scores, key=lambda s: s.recommendation_score, reverse=True)
