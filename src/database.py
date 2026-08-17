"""
database.py
-----------
Thin, explicit database access layer. Uses SQLAlchemy Core so the same
code path works against the documented production target (PostgreSQL,
via DATABASE_URL) and against a local SQLite file for zero-config
development/testing, without any change to calling code.

No ORM magic, no query building hidden behind decorators: every function
here does one clear thing.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from src.config import settings

_ENGINE: Engine | None = None


def get_engine() -> Engine:
    global _ENGINE
    if _ENGINE is None:
        connect_args = {}
        if settings.database_url.startswith("sqlite"):
            # Make sure the parent directory exists for file-based sqlite.
            db_path = settings.database_url.replace("sqlite:///", "")
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            connect_args = {"check_same_thread": False}
        _ENGINE = create_engine(settings.database_url, connect_args=connect_args, future=True)
    return _ENGINE


def is_postgres() -> bool:
    return settings.database_url.startswith("postgresql")


def init_schema() -> None:
    """
    Creates all tables. Uses sql/schema.sql when running against Postgres.
    For the SQLite dev fallback, uses lightweight equivalent DDL (SQLite
    does not support SERIAL/JSONB/TIMESTAMPTZ) so the project remains
    runnable out of the box for testing/demoing without a Postgres server.
    """
    engine = get_engine()
    if is_postgres():
        schema_path = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
        ddl = schema_path.read_text()
        with engine.begin() as conn:
            for statement in ddl.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))
    else:
        ddl = """
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY, anonymous_user_id TEXT, session_start TEXT,
            session_end TEXT, device_type TEXT, platform TEXT, acquisition_source TEXT,
            population TEXT, prior_engagement REAL, registration_friction REAL,
            checkout_friction REAL, page_delay REAL, content_exposure REAL,
            navigation_friction REAL, intervention_exposure INTEGER
        );
        CREATE TABLE IF NOT EXISTS events (
            event_id TEXT PRIMARY KEY, session_id TEXT, timestamp TEXT, event_type TEXT,
            page TEXT, action TEXT, dwell_time REAL, sequence_number INTEGER,
            intervention_exposure INTEGER
        );
        CREATE TABLE IF NOT EXISTS journeys (
            journey_id TEXT PRIMARY KEY, session_id TEXT, journey_sequence TEXT,
            journey_length INTEGER, duration REAL, converted INTEGER,
            abandonment_stage TEXT, unique_pages INTEGER, repeated_pages INTEGER
        );
        CREATE TABLE IF NOT EXISTS causal_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT, treatment TEXT, outcome TEXT,
            effect_estimate REAL, ci_lower REAL, ci_upper REAL, method TEXT,
            sample_size INTEGER, assumptions TEXT, refutation_passed INTEGER,
            computed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS simulations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, scenario_name TEXT, intervention TEXT,
            parameters TEXT, baseline_result REAL, simulated_result REAL,
            improvement REAL, uncertainty REAL, computed_at TEXT
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id INTEGER PRIMARY KEY AUTOINCREMENT, intervention TEXT, expected_benefit REAL,
            evidence TEXT, confidence TEXT, complexity TEXT, risk TEXT,
            recommendation_score REAL, explanation TEXT, computed_at TEXT
        );
        """
        with engine.begin() as conn:
            for statement in ddl.split(";"):
                statement = statement.strip()
                if statement:
                    conn.execute(text(statement))


def truncate_all() -> None:
    engine = get_engine()
    tables = ["events", "journeys", "sessions", "causal_results", "simulations", "recommendations"]
    with engine.begin() as conn:
        for t in tables:
            try:
                if is_postgres():
                    conn.execute(text(f"TRUNCATE TABLE {t} CASCADE"))
                else:
                    conn.execute(text(f"DELETE FROM {t}"))
            except Exception:
                pass


def write_dataframe(df: pd.DataFrame, table_name: str, if_exists: str = "append") -> int:
    if df is None or df.empty:
        return 0
    engine = get_engine()
    df.to_sql(table_name, engine, if_exists=if_exists, index=False, method="multi", chunksize=1000)
    return len(df)


def read_sql(query: str, params: dict | None = None) -> pd.DataFrame:
    engine = get_engine()
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn, params=params or {})


def read_table(table_name: str) -> pd.DataFrame:
    return read_sql(f"SELECT * FROM {table_name}")


def table_counts() -> dict:
    counts = {}
    for t in ["sessions", "events", "journeys", "causal_results", "simulations", "recommendations"]:
        try:
            df = read_sql(f"SELECT COUNT(*) AS n FROM {t}")
            counts[t] = int(df["n"].iloc[0])
        except Exception:
            counts[t] = 0
    return counts


def latest_event_timestamp():
    try:
        df = read_sql("SELECT MAX(timestamp) AS ts FROM events")
        return df["ts"].iloc[0]
    except Exception:
        return None


def write_recommendations(records: list[dict]) -> None:
    if not records:
        return
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM recommendations"))
        for r in records:
            conn.execute(
                text(
                    "INSERT INTO recommendations "
                    "(intervention, expected_benefit, evidence, confidence, complexity, risk, "
                    "recommendation_score, explanation, computed_at) VALUES "
                    "(:intervention, :expected_benefit, :evidence, :confidence, :complexity, :risk, "
                    ":recommendation_score, :explanation, :computed_at)"
                ),
                {
                    "intervention": r["intervention"],
                    "expected_benefit": r["expected_benefit"],
                    "evidence": json.dumps(r["evidence"]),
                    "confidence": r["confidence"],
                    "complexity": r["complexity"],
                    "risk": r["risk"],
                    "recommendation_score": r["recommendation_score"],
                    "explanation": r["explanation"],
                    "computed_at": pd.Timestamp.utcnow().isoformat(),
                },
            )


def write_causal_result(record: dict) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO causal_results "
                "(treatment, outcome, effect_estimate, ci_lower, ci_upper, method, sample_size, "
                "assumptions, refutation_passed, computed_at) VALUES "
                "(:treatment, :outcome, :effect_estimate, :ci_lower, :ci_upper, :method, :sample_size, "
                ":assumptions, :refutation_passed, :computed_at)"
            ),
            {**record, "computed_at": pd.Timestamp.utcnow().isoformat()},
        )


def write_simulation(record: dict) -> None:
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO simulations "
                "(scenario_name, intervention, parameters, baseline_result, simulated_result, "
                "improvement, uncertainty, computed_at) VALUES "
                "(:scenario_name, :intervention, :parameters, :baseline_result, :simulated_result, "
                ":improvement, :uncertainty, :computed_at)"
            ),
            {
                **record,
                "parameters": json.dumps(record.get("parameters", {})),
                "computed_at": pd.Timestamp.utcnow().isoformat(),
            },
        )
