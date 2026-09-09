"""
simulation_engine.py
---------------------
Answers "What could happen if we intervene?" via discrete-event
simulation (SimPy).

The simulation uses only factors supported by the real dataset:
    - checkout_friction
    - page_delay
    - content_exposure
    - navigation_friction

Registration has been removed because the real GA4 dataset does not
contain registration events.

Every run actually executes the SimPy environment -- no numbers here are
pre-computed or hard-coded. Results are explicitly labeled
Simulated/Estimated wherever displayed.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import simpy


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


@dataclass
class SimulationParams:
    checkout_friction: float = 40.0       # 0-100
    page_delay: float = 1.5               # seconds
    content_exposure: float = 50.0        # 0-100
    navigation_friction: float = 35.0     # 0-100
    n_sessions: int = 2000
    seed: int = 42


def _session_process(
    env: simpy.Environment,
    params: SimulationParams,
    rng: np.random.Generator,
    results: dict,
):
    """A single simulated session's journey through the funnel."""

    prior_engagement = float(
        np.clip(rng.normal(0.5, 0.18), 0.01, 0.99)
    )

    # ------------------------------------------------------------
    # BROWSE STAGE
    # ------------------------------------------------------------

    # Page delay slows the journey down.
    yield env.timeout(
        max(0.01, rng.exponential(1.0) + params.page_delay)
    )

    p_proceed = _sigmoid(
        (params.content_exposure - 45) / 20
        + (prior_engagement - 0.4)
    )

    if rng.random() > p_proceed:
        results["browse_exit"] += 1
        return

    # ------------------------------------------------------------
    # CHECKOUT STAGE
    # ------------------------------------------------------------

    yield env.timeout(
        max(0.01, rng.exponential(1.0) + params.page_delay)
    )

    p_purchase = _sigmoid(
        (45 - params.checkout_friction) / 15
        + (prior_engagement - 0.3)
        + (params.content_exposure - 50) / 100
        - (params.navigation_friction - 35) / 150
    )

    if rng.random() > p_purchase:
        results["checkout_exit"] += 1
        return

    # ------------------------------------------------------------
    # CONVERSION
    # ------------------------------------------------------------

    results["converted"] += 1


def run_simulation(params: SimulationParams) -> dict:
    """
    Executes a real SimPy discrete-event simulation and returns
    aggregate outcome counts + conversion rate + uncertainty.
    """

    rng = np.random.default_rng(params.seed)

    env = simpy.Environment()

    results = {
        "converted": 0,
        "checkout_exit": 0,
        "browse_exit": 0,
    }

    for _ in range(params.n_sessions):
        env.process(
            _session_process(
                env,
                params,
                rng,
                results,
            )
        )

    env.run()

    total = sum(results.values())

    conversion_rate = (
        results["converted"] / total * 100
        if total
        else 0.0
    )

    # Bootstrap uncertainty band on the conversion rate.
    if total > 0:
        boot_rng = np.random.default_rng(params.seed + 1)

        draws = (
            boot_rng.binomial(
                total,
                results["converted"] / total,
                size=500,
            )
            / total
            * 100
        )

        uncertainty = float(np.std(draws))

    else:
        uncertainty = 0.0

    return {
        "conversion_rate": round(conversion_rate, 2),
        "uncertainty": round(uncertainty, 2),
        "n_sessions": total,
        "converted": results["converted"],
        "checkout_exit": results["checkout_exit"],
        "browse_exit": results["browse_exit"],
    }


# ============================================================
# PREDEFINED SCENARIOS
# ============================================================

SCENARIOS = {

    "A - Current system": SimulationParams(
        checkout_friction=40,
        page_delay=1.5,
        content_exposure=50,
        navigation_friction=35,
    ),

    "B - Reduced checkout friction": SimulationParams(
        checkout_friction=15,
        page_delay=1.5,
        content_exposure=50,
        navigation_friction=35,
    ),

    "C - Reduced page delay": SimulationParams(
        checkout_friction=40,
        page_delay=0.3,
        content_exposure=50,
        navigation_friction=35,
    ),

    "D - Improved content exposure": SimulationParams(
        checkout_friction=40,
        page_delay=1.5,
        content_exposure=80,
        navigation_friction=35,
    ),

    "E - Reduced navigation friction": SimulationParams(
        checkout_friction=40,
        page_delay=1.5,
        content_exposure=50,
        navigation_friction=15,
    ),
}


def run_all_scenarios(
    n_sessions: int = 2000,
    seed: int = 42,
) -> dict:

    out = {}

    for i, (name, params) in enumerate(SCENARIOS.items()):

        p = SimulationParams(
            **{
                **params.__dict__,
                "n_sessions": n_sessions,
                "seed": seed + i,
            }
        )

        out[name] = run_simulation(p)

    return out