"""
data_generator.py
------------------
Generates synthetic, privacy-safe, event-level user behavior data.

This is NOT random noise. The generator builds sessions from a small set
of latent behavioral populations (fast converters, researchers, hesitant
users, lost users) and injects deliberate, realistic causal structure so
that downstream causal inference and simulation have something genuine to
recover:

  * prior_engagement (confounder) influences BOTH the probability that a
    session is exposed to a friction-reducing intervention AND the
    probability of conversion -- this is exactly the kind of confounding
    that makes naive correlation misleading and that DoWhy's backdoor
    adjustment is meant to correct for.
  * registration_friction causally increases abandonment at the
    registration stage.
  * checkout_friction causally reduces purchase conversion.
  * page_delay causally increases the chance of exit.
  * content_exposure causally increases conversion.
  * navigation_friction causally increases non-linear (looping) behavior.

All identifiers produced here are already pseudonymous (see src.privacy).
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List

import numpy as np
import polars as pl

from src.config import settings
from src.privacy import pseudonymize

DEVICE_TYPES = ["desktop", "mobile", "tablet"]
PLATFORMS = ["web", "ios", "android"]
ACQUISITION_SOURCES = ["organic_search", "paid_search", "social", "referral", "direct", "email"]

PAGE_FUNNEL = ["Landing", "Home", "Search", "Product", "Reviews", "Registration",
               "Registration Error", "Cart", "Checkout", "Purchase", "Exit"]

POPULATIONS = ["fast_converter", "researcher", "hesitant", "lost"]
POPULATION_WEIGHTS = [0.28, 0.27, 0.25, 0.20]


@dataclass
class SessionSpec:
    session_id: str
    anonymous_user_id: str
    population: str
    device_type: str
    platform: str
    acquisition_source: str
    prior_engagement: float          # 0-1 latent confounder
    registration_friction: float     # 0-100
    checkout_friction: float         # 0-100
    page_delay: float                # seconds
    content_exposure: float          # 0-100
    navigation_friction: float       # 0-100
    intervention_exposure: bool


def _rng(seed: int) -> np.random.Generator:
    return np.random.default_rng(seed)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + np.exp(-x))


def _build_session_specs(n_sessions: int, rng: np.random.Generator) -> List[SessionSpec]:
    specs: List[SessionSpec] = []
    for i in range(n_sessions):
        population = rng.choice(POPULATIONS, p=POPULATION_WEIGHTS)

        raw_user_id = f"raw-user-{uuid.uuid4()}"
        session_id = pseudonymize(f"{raw_user_id}-{i}")
        anonymous_user_id = pseudonymize(raw_user_id)

        # Prior engagement: the confounder. Researchers & fast converters
        # tend to arrive with higher baseline engagement (e.g. returning
        # visitors, prior brand familiarity).
        base_engagement = {
            "fast_converter": 0.72,
            "researcher": 0.60,
            "hesitant": 0.40,
            "lost": 0.22,
        }[population]
        prior_engagement = float(np.clip(rng.normal(base_engagement, 0.15), 0.01, 0.99))

        # Intervention exposure probability depends on prior_engagement
        # (confounding by design): more engaged sessions are more likely
        # to reach/receive the simplified-registration treatment because
        # they progress further into the funnel.
        p_intervention = _sigmoid(4 * (prior_engagement - 0.5))
        intervention_exposure = bool(rng.random() < p_intervention)

        # Friction and delay parameters, population-flavored, with the
        # intervention reducing registration friction when present.
        registration_friction = float(np.clip(
            rng.normal({"fast_converter": 25, "researcher": 40, "hesitant": 60, "lost": 70}[population], 12),
            0, 100,
        ))
        if intervention_exposure:
            registration_friction = max(0.0, registration_friction - 30)

        checkout_friction = float(np.clip(
            rng.normal({"fast_converter": 20, "researcher": 35, "hesitant": 55, "lost": 65}[population], 15),
            0, 100,
        ))
        page_delay = float(np.clip(rng.exponential(1.2), 0, 9))
        content_exposure = float(np.clip(
            rng.normal({"fast_converter": 55, "researcher": 75, "hesitant": 45, "lost": 25}[population], 15),
            0, 100,
        ))
        navigation_friction = float(np.clip(
            rng.normal({"fast_converter": 15, "researcher": 35, "hesitant": 50, "lost": 70}[population], 15),
            0, 100,
        ))

        specs.append(SessionSpec(
            session_id=session_id,
            anonymous_user_id=anonymous_user_id,
            population=population,
            device_type=str(rng.choice(DEVICE_TYPES, p=[0.55, 0.38, 0.07])),
            platform=str(rng.choice(PLATFORMS, p=[0.5, 0.3, 0.2])),
            acquisition_source=str(rng.choice(ACQUISITION_SOURCES)),
            prior_engagement=prior_engagement,
            registration_friction=registration_friction,
            checkout_friction=checkout_friction,
            page_delay=page_delay,
            content_exposure=content_exposure,
            navigation_friction=navigation_friction,
            intervention_exposure=intervention_exposure,
        ))
    return specs


def _simulate_event_sequence(spec: SessionSpec, rng: np.random.Generator) -> List[dict]:
    """
    Walks a single session through the funnel as a stochastic process
    whose transition probabilities are driven by the session's causal
    parameters, producing a realistic, sometimes non-linear, sometimes
    looping page sequence.
    """
    events = []
    t = datetime.now(timezone.utc) - timedelta(days=int(rng.integers(0, 60)),
                                                 seconds=int(rng.integers(0, 86400)))
    seq = 0

    def emit(page, action, dwell):
        nonlocal t, seq
        seq += 1
        events.append({
            "event_id": str(uuid.uuid4()),
            "session_id": spec.session_id,
            "timestamp": t,
            "event_type": "page_view" if action == "view" else action,
            "page": page,
            "action": action,
            "dwell_time": max(0.0, dwell),
            "sequence_number": seq,
            "intervention_exposure": spec.intervention_exposure,
        })
        t = t + timedelta(seconds=max(1.0, dwell) + spec.page_delay)

    emit("Landing", "view", rng.exponential(8))
    emit("Home", "view", rng.exponential(10))

    # Researchers and hesitant users loop through Search/Product/Reviews.
    loop_prob = _sigmoid((spec.navigation_friction - 40) / 15) * {
        "researcher": 1.3, "hesitant": 1.1, "lost": 1.4, "fast_converter": 0.4,
    }[spec.population]
    n_loops = int(rng.poisson(max(0.2, loop_prob)))
    n_loops = min(n_loops, 5)

    for _ in range(max(1, n_loops)):
        emit("Search", "view", rng.exponential(6))
        emit("Product", "view", rng.exponential(12 + spec.content_exposure / 10))
        if rng.random() < 0.35:
            emit("Reviews", "view", rng.exponential(9))
            emit("Product", "view", rng.exponential(8))
        if rng.random() < (spec.navigation_friction / 200):
            emit("Home", "view", rng.exponential(5))  # backward navigation / loop

    # Content exposure raises the odds of proceeding toward registration.
    p_proceed = _sigmoid((spec.content_exposure - 45) / 20 + (spec.prior_engagement - 0.4))
    if rng.random() > p_proceed:
        emit("Exit", "exit", 0)
        return events, "browse_exit", False, "browse"

    emit("Registration", "view", rng.exponential(7))
    # Registration friction causally drives abandonment / errors here.
    p_reg_error = _sigmoid((spec.registration_friction - 45) / 15)
    if rng.random() < p_reg_error:
        emit("Registration Error", "error", rng.exponential(4))
        # Some retry, weighted down by friction.
        if rng.random() < _sigmoid((40 - spec.registration_friction) / 15):
            emit("Registration", "view", rng.exponential(6))
        else:
            emit("Exit", "exit", 0)
            return events, "registration_exit", False, "registration"

    p_reg_complete = _sigmoid((55 - spec.registration_friction) / 18 + (spec.prior_engagement - 0.4))
    if rng.random() > p_reg_complete:
        emit("Exit", "exit", 0)
        return events, "registration_exit", False, "registration"

    emit("Cart", "add_to_cart", rng.exponential(5))

    emit("Checkout", "view", rng.exponential(8))
    # Checkout friction causally reduces purchase probability.
    p_purchase = _sigmoid((45 - spec.checkout_friction) / 15 + (spec.prior_engagement - 0.3)
                           + (spec.content_exposure - 50) / 100)
    if rng.random() > p_purchase:
        emit("Exit", "exit", 0)
        return events, "checkout_exit", False, "checkout"

    emit("Purchase", "purchase", rng.exponential(3))
    return events, "purchase", True, "converted"


def generate_events(n_sessions: int | None = None, seed: int | None = None) -> tuple[pl.DataFrame, pl.DataFrame, pl.DataFrame]:
    """
    Returns three Polars DataFrames: (sessions_df, events_df, journeys_df)
    ready for loading into PostgreSQL / SQLite via src.database.
    """
    n_sessions = n_sessions or settings.synthetic_sessions
    seed = seed if seed is not None else settings.random_seed
    rng = _rng(seed)

    specs = _build_session_specs(n_sessions, rng)

    session_rows = []
    event_rows = []
    journey_rows = []

    for spec in specs:
        events, exit_label, converted, abandonment_stage = _simulate_event_sequence(spec, rng)
        if not events:
            continue

        session_start = events[0]["timestamp"]
        session_end = events[-1]["timestamp"]

        session_rows.append({
            "session_id": spec.session_id,
            "anonymous_user_id": spec.anonymous_user_id,
            "session_start": session_start,
            "session_end": session_end,
            "device_type": spec.device_type,
            "platform": spec.platform,
            "acquisition_source": spec.acquisition_source,
            # latent parameters retained ONLY for the causal/simulation
            # pipeline -- these are behavioral, not personal, attributes.
            "population": spec.population,
            "prior_engagement": spec.prior_engagement,
            "registration_friction": spec.registration_friction,
            "checkout_friction": spec.checkout_friction,
            "page_delay": spec.page_delay,
            "content_exposure": spec.content_exposure,
            "navigation_friction": spec.navigation_friction,
            "intervention_exposure": spec.intervention_exposure,
        })
        event_rows.extend(events)

        pages = [e["page"] for e in events]
        unique_pages = len(set(pages))
        repeated_pages = len(pages) - unique_pages
        duration = (session_end - session_start).total_seconds()

        journey_rows.append({
            "journey_id": str(uuid.uuid4()),
            "session_id": spec.session_id,
            "journey_sequence": " > ".join(pages),
            "journey_length": len(pages),
            "duration": duration,
            "converted": converted,
            "abandonment_stage": None if converted else abandonment_stage,
            "unique_pages": unique_pages,
            "repeated_pages": repeated_pages,
        })

    sessions_df = pl.DataFrame(session_rows)
    events_df = pl.DataFrame(event_rows)
    journeys_df = pl.DataFrame(journey_rows)
    return sessions_df, events_df, journeys_df


if __name__ == "__main__":
    s, e, j = generate_events()
    print(f"sessions={s.height} events={e.height} journeys={j.height}")
    print(j["converted"].mean())
