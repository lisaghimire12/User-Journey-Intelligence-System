"""
simulation_engine.py
---------------------
Answers "What could happen if we intervene?" via discrete-event
simulation (SimPy). Each simulated session is a SimPy process that walks
the same funnel logic as the synthetic data generator, but driven by
user-adjustable parameters instead of the fixed population definitions.

Every run actually executes the SimPy environment -- no numbers here are
pre-computed or hard-coded. Results are explicitly labeled
Simulated/Estimated wherever displayed (see the Streamlit pages).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import simpy


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class SimulationParams:
    registration_friction: float = 45.0   # 0-100
    checkout_friction: float = 40.0        # 0-100
    page_delay: float = 1.5                # seconds
    content_exposure: float = 50.0         # 0-100
    navigation_friction: float = 35.0      # 0-100
    n_sessions: int = 2000
    seed: int = 42


def _session_process(env: simpy.Environment, params: SimulationParams, rng: np.random.Generator, results: dict):
    """A single simulated session's journey through the funnel."""
    prior_engagement = float(np.clip(rng.normal(0.5, 0.18), 0.01, 0.99))

    # page delay slows every step down (models latency/friction cost)
    yield env.timeout(max(0.01, rng.exponential(1.0) + params.page_delay))

    p_proceed = _sigmoid((params.content_exposure - 45) / 20 + (prior_engagement - 0.4))
    if rng.random() > p_proceed:
        results["browse_exit"] += 1
        return

    yield env.timeout(max(0.01, rng.exponential(1.0) + params.page_delay))
    p_reg_error = _sigmoid((params.registration_friction - 45) / 15)
    if rng.random() < p_reg_error:
        yield env.timeout(max(0.01, rng.exponential(0.5)))
        if rng.random() > _sigmoid((40 - params.registration_friction) / 15):
            results["registration_exit"] += 1
            return

    p_reg_complete = _sigmoid((55 - params.registration_friction) / 18 + (prior_engagement - 0.4))
    if rng.random() > p_reg_complete:
        results["registration_exit"] += 1
        return

    yield env.timeout(max(0.01, rng.exponential(1.0) + params.page_delay))
    p_purchase = _sigmoid(
        (45 - params.checkout_friction) / 15 + (prior_engagement - 0.3)
        + (params.content_exposure - 50) / 100
        - (params.navigation_friction - 35) / 150
    )
    if rng.random() > p_purchase:
        results["checkout_exit"] += 1
        return

    results["converted"] += 1


def run_simulation(params: SimulationParams) -> dict:
    """Executes a real SimPy discrete-event simulation and returns
    aggregate outcome counts + conversion rate + a bootstrap uncertainty
    band around the conversion rate."""
    rng = np.random.default_rng(params.seed)
    env = simpy.Environment()
    results = {"converted": 0, "registration_exit": 0, "checkout_exit": 0, "browse_exit": 0}

    for _ in range(params.n_sessions):
        env.process(_session_process(env, params, rng, results))
    env.run()

    total = sum(results.values())
    conversion_rate = (results["converted"] / total * 100) if total else 0.0

    # Bootstrap uncertainty band on the conversion rate using a binomial
    # resampling of the realized outcome, so the UI can show an honest
    # +/- range rather than a bare point estimate.
    if total > 0:
        boot_rng = np.random.default_rng(params.seed + 1)
        draws = boot_rng.binomial(total, results["converted"] / total, size=500) / total * 100
        uncertainty = float(np.std(draws))
    else:
        uncertainty = 0.0

    return {
        "conversion_rate": round(conversion_rate, 2),
        "uncertainty": round(uncertainty, 2),
        "n_sessions": total,
        "converted": results["converted"],
        "registration_exit": results["registration_exit"],
        "checkout_exit": results["checkout_exit"],
        "browse_exit": results["browse_exit"],
    }


# Predefined scenarios (PROJECT SPEC section 22)
SCENARIOS = {
    "A - Current system": SimulationParams(
        registration_friction=45, checkout_friction=40, page_delay=1.5,
        content_exposure=50, navigation_friction=35,
    ),
    "B - Simplified registration": SimulationParams(
        registration_friction=15, checkout_friction=40, page_delay=1.5,
        content_exposure=50, navigation_friction=35,
    ),
    "C - Reduced checkout friction": SimulationParams(
        registration_friction=45, checkout_friction=15, page_delay=1.5,
        content_exposure=50, navigation_friction=35,
    ),
    "D - Reduced page delay": SimulationParams(
        registration_friction=45, checkout_friction=40, page_delay=0.3,
        content_exposure=50, navigation_friction=35,
    ),
    "E - Improved content exposure": SimulationParams(
        registration_friction=45, checkout_friction=40, page_delay=1.5,
        content_exposure=80, navigation_friction=35,
    ),
}


def run_all_scenarios(n_sessions: int = 2000, seed: int = 42) -> dict:
    out = {}
    for i, (name, params) in enumerate(SCENARIOS.items()):
        p = SimulationParams(**{**params.__dict__, "n_sessions": n_sessions, "seed": seed + i})
        out[name] = run_simulation(p)
    return out
