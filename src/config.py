"""
config.py
---------
Central configuration for the project. Loads values from environment
variables (via .env) and exposes typed, documented settings. Nothing in
this module is a secret -- the actual credentials live only in the
user's local .env file, which is git-ignored.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

# Load .env if present. Safe to call even if the file doesn't exist.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")


def _get_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _get_int(name: str, default: int) -> int:
    val = os.getenv(name)
    if val is None or val == "":
        return default
    try:
        return int(val)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    # --- Database -----------------------------------------------------
    # Falls back to a local SQLite file if DATABASE_URL is not provided.
    # This keeps the project runnable for evaluation/testing without a
    # live PostgreSQL server, while the documented production target is
    # PostgreSQL (see README).
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL",
            f"sqlite:///{PROJECT_ROOT / 'data' / 'local_dev.db'}",
        )
    )

    # --- Privacy / data minimization -----------------------------------
    # Number of days behavioral event data is retained before it is
    # eligible for purge. This is a configurable knob, not a legal claim.
    data_retention_days: int = field(default_factory=lambda: _get_int("DATA_RETENTION_DAYS", 90))
    pseudonymization_salt: str = field(
        default_factory=lambda: os.getenv("PSEUDONYMIZATION_SALT", "change-me-in-.env")
    )

    # --- Optional LLM ----------------------------------------------------
    # The system is fully functional without this. It is only used, when
    # present, to turn already-computed structured results into plain
    # language summaries. It never invents numbers.
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    anthropic_api_key: str = field(default_factory=lambda: os.getenv("ANTHROPIC_API_KEY", ""))

    # --- Synthetic data generation ---------------------------------------
    synthetic_sessions: int = field(default_factory=lambda: _get_int("SYNTHETIC_SESSIONS", 6000))
    random_seed: int = field(default_factory=lambda: _get_int("RANDOM_SEED", 42))

    # --- App behavior ------------------------------------------------------
    cache_ttl_seconds: int = field(default_factory=lambda: _get_int("CACHE_TTL_SECONDS", 300))
    auto_refresh_enabled: bool = field(default_factory=lambda: _get_bool("AUTO_REFRESH_ENABLED", True))


settings = Settings()

# Color palette -- single source of truth for the whole UI so pages and
# Plotly charts stay visually consistent.
PALETTE = {
    "terracotta": "#9B3F24",
    "rust": "#A84A2A",
    "espresso": "#32180F",
    "cream": "#F7F1E8",
    "offwhite": "#FCFAF6",
    "taupe": "#D8CFC3",
    "sand": "#E9DED1",
    "white": "#FFFFFF",
}

PROJECT_TITLE = "Causal and Simulation-Based Analysis of Digital User Behavior"
