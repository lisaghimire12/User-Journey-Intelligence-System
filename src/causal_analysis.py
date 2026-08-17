"""
causal_analysis.py
-------------------
Answers "What appears to influence the outcome?" using DoWhy.

Design principles enforced here (see PROJECT SPEC section 19 -- "do not
fake causal results"):
  * No causal effect is ever hard-coded.
  * If the available sample / variance is insufficient to support an
    estimate, the function returns status="insufficient_evidence" and the
    UI must display that literally, not a number.
  * Every estimate is accompanied by a confidence interval, sample size,
    the assumed causal graph, and a refutation (placebo treatment) check.

Causal question modeled here (mirrors PROJECT SPEC section 18):
    Does reducing registration friction increase registration completion
    (proxied by full conversion through to purchase)?
Confounder handled explicitly: prior_engagement, which the generator
deliberately makes correlated with both treatment exposure and outcome
(see src/data_generator.py) -- exactly the situation backdoor adjustment
is meant to correct for.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, asdict

import numpy as np
import pandas as pd

MIN_SAMPLE_SIZE = 200
MIN_TREATMENT_VARIANCE = 0.02  # both arms need at least ~2% representation


@dataclass
class CausalResult:
    status: str  # "ok" | "insufficient_evidence" | "error"
    treatment: str
    outcome: str
    effect_estimate: float | None = None
    ci_lower: float | None = None
    ci_upper: float | None = None
    method: str = "dowhy_backdoor_linear_regression"
    sample_size: int = 0
    confounders: list | None = None
    assumptions: str = ""
    refutation_passed: bool | None = None
    refutation_detail: str = ""
    message: str = ""

    def to_dict(self):
        return asdict(self)


def _binarize_treatment(series: pd.Series, beneficial_direction: str = "low") -> pd.Series:
    """
    Binarizes a continuous score at its median for a clean treated-vs-
    control causal question. `beneficial_direction` says which side of
    the median counts as "treated" (i.e. receiving the improvement):
    "low" for friction-type variables (lower friction = treated), "high"
    for exposure-type variables (more exposure = treated).
    """
    median = series.median()
    if beneficial_direction == "low":
        return (series <= median).astype(int)
    return (series >= median).astype(int)


def estimate_effect(
    df: pd.DataFrame,
    treatment_raw: str,
    outcome: str,
    confounders: list[str],
    treatment_label: str | None = None,
    beneficial_direction: str = "low",
) -> CausalResult:
    treatment_label = treatment_label or treatment_raw

    required_cols = [treatment_raw, outcome] + confounders
    data = df.dropna(subset=[c for c in required_cols if c in df.columns]).copy()

    if data.empty or len(data) < MIN_SAMPLE_SIZE:
        return CausalResult(
            status="insufficient_evidence",
            treatment=treatment_label,
            outcome=outcome,
            sample_size=len(data),
            confounders=confounders,
            message=f"Insufficient evidence for reliable causal estimation "
                    f"(n={len(data)}, minimum required={MIN_SAMPLE_SIZE}).",
        )

    data["treatment_bin"] = _binarize_treatment(data[treatment_raw], beneficial_direction)
    treated_share = data["treatment_bin"].mean()
    if treated_share < MIN_TREATMENT_VARIANCE or treated_share > (1 - MIN_TREATMENT_VARIANCE):
        return CausalResult(
            status="insufficient_evidence",
            treatment=treatment_label,
            outcome=outcome,
            sample_size=len(data),
            confounders=confounders,
            message="Insufficient evidence for reliable causal estimation "
                    "(treatment and control groups are too imbalanced).",
        )

    data["outcome_num"] = data[outcome].astype(bool).astype(int)

    try:
        result = _estimate_with_dowhy(data, confounders)
    except Exception as exc:  # pragma: no cover - defensive fallback
        warnings.warn(f"DoWhy estimation failed, falling back to adjusted OLS: {exc}")
        result = _estimate_with_ols_fallback(data, confounders)

    effect, ci_lower, ci_upper, method = result

    refutation_passed, refutation_detail = _placebo_refutation(data, confounders, effect)

    direction_note = (
        "at or below the median counts as treated"
        if beneficial_direction == "low"
        else "at or above the median counts as treated"
    )
    assumptions = (
        f"Backdoor adjustment for observed confounder(s): {', '.join(confounders) or 'none'}. "
        f"Treatment binarized at the sample median of '{treatment_raw}' ({direction_note}). "
        f"Assumes no unobserved confounding beyond the listed variables and "
        f"correct functional form for the linear outcome model."
    )

    return CausalResult(
        status="ok",
        treatment=treatment_label,
        outcome=outcome,
        effect_estimate=round(float(effect), 4),
        ci_lower=round(float(ci_lower), 4),
        ci_upper=round(float(ci_upper), 4),
        method=method,
        sample_size=len(data),
        confounders=confounders,
        assumptions=assumptions,
        refutation_passed=refutation_passed,
        refutation_detail=refutation_detail,
        message="Causal estimates depend on the data and assumptions of the causal model.",
    )


def _estimate_with_dowhy(data: pd.DataFrame, confounders: list[str]):
    from dowhy import CausalModel

    model = CausalModel(
        data=data,
        treatment="treatment_bin",
        outcome="outcome_num",
        common_causes=confounders if confounders else None,
    )
    identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
    estimate = model.estimate_effect(
        identified_estimand,
        method_name="backdoor.linear_regression",
        confidence_intervals=True,
    )

    effect = float(estimate.value)
    try:
        ci = estimate.get_confidence_intervals()
        ci_lower, ci_upper = float(np.ravel(ci)[0]), float(np.ravel(ci)[1])
    except Exception:
        # Bootstrap a CI manually if DoWhy's built-in CI machinery is unavailable.
        ci_lower, ci_upper = _bootstrap_ci(data, confounders)

    return effect, ci_lower, ci_upper, "dowhy_backdoor_linear_regression"


def _estimate_with_ols_fallback(data: pd.DataFrame, confounders: list[str]):
    import statsmodels.formula.api as smf

    cols = ["treatment_bin"] + confounders
    formula_terms = " + ".join(cols)
    model = smf.ols(f"outcome_num ~ {formula_terms}", data=data).fit()
    effect = model.params["treatment_bin"]
    conf = model.conf_int().loc["treatment_bin"]
    return effect, conf[0], conf[1], "ols_adjusted_fallback"


def _bootstrap_ci(data: pd.DataFrame, confounders: list[str], n_boot: int = 300, seed: int = 42):
    import statsmodels.formula.api as smf

    rng = np.random.default_rng(seed)
    cols = ["treatment_bin"] + confounders
    formula_terms = " + ".join(cols)
    effects = []
    for _ in range(n_boot):
        sample = data.sample(frac=1.0, replace=True, random_state=int(rng.integers(0, 1_000_000)))
        try:
            model = smf.ols(f"outcome_num ~ {formula_terms}", data=sample).fit()
            effects.append(model.params["treatment_bin"])
        except Exception:
            continue
    if not effects:
        return -0.0, 0.0
    return float(np.percentile(effects, 2.5)), float(np.percentile(effects, 97.5))


def _placebo_refutation(data: pd.DataFrame, confounders: list[str], observed_effect: float, seed: int = 7):
    """
    A lightweight placebo-treatment refutation: replace the real treatment
    with a randomly permuted (fake) version and re-estimate. A robust
    causal claim should see the placebo effect collapse toward zero.
    """
    try:
        import statsmodels.formula.api as smf
        rng = np.random.default_rng(seed)
        shuffled = data.copy()
        shuffled["treatment_bin"] = rng.permutation(shuffled["treatment_bin"].values)
        cols = ["treatment_bin"] + confounders
        formula_terms = " + ".join(cols)
        model = smf.ols(f"outcome_num ~ {formula_terms}", data=shuffled).fit()
        placebo_effect = model.params["treatment_bin"]
        passed = abs(placebo_effect) < max(0.05, abs(observed_effect) * 0.4)
        detail = (
            f"Placebo (randomly permuted) treatment effect = {placebo_effect:.4f}, "
            f"compared to observed effect = {observed_effect:.4f}. "
            f"{'Refutation passed: placebo effect is small relative to the observed effect.' if passed else 'Refutation caution: placebo effect is not negligible.'}"
        )
        return bool(passed), detail
    except Exception as exc:  # pragma: no cover
        return None, f"Refutation check could not be run: {exc}"


# Predefined causal questions surfaced in the UI (PROJECT SPEC section 18/37)
CAUSAL_QUESTIONS = [
    {
        "id": "registration_friction",
        "question": "Does reducing registration friction increase conversion?",
        "treatment_raw": "registration_friction",
        "outcome": "converted",
        "confounders": ["prior_engagement"],
        "treatment_label": "Registration friction (low vs high)",
        "beneficial_direction": "low",
    },
    {
        "id": "checkout_friction",
        "question": "Does reducing checkout friction increase conversion?",
        "treatment_raw": "checkout_friction",
        "outcome": "converted",
        "confounders": ["prior_engagement"],
        "treatment_label": "Checkout friction (low vs high)",
        "beneficial_direction": "low",
    },
    {
        "id": "content_exposure",
        "question": "Does increased content exposure increase conversion?",
        "treatment_raw": "content_exposure",
        "outcome": "converted",
        "confounders": ["prior_engagement"],
        "treatment_label": "Content exposure (high vs low)",
        "beneficial_direction": "high",
    },
    {
        "id": "navigation_friction",
        "question": "Does reducing navigation friction increase conversion?",
        "treatment_raw": "navigation_friction",
        "outcome": "converted",
        "confounders": ["prior_engagement"],
        "treatment_label": "Navigation friction (low vs high)",
        "beneficial_direction": "low",
    },
]
