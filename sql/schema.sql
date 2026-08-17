-- schema.sql
-- Postgres schema for the Causal and Simulation-Based Analysis of
-- Digital User Behavior project.
--
-- Notes on privacy-by-design:
--   * No direct-identifier columns (name/email/phone/address) exist
--     anywhere in this schema.
--   * anonymous_user_id / session_id are pseudonymous tokens produced by
--     src/privacy.py, never raw account identifiers.

CREATE TABLE IF NOT EXISTS sessions (
    session_id              VARCHAR(64) PRIMARY KEY,
    anonymous_user_id       VARCHAR(64) NOT NULL,
    session_start           TIMESTAMPTZ NOT NULL,
    session_end             TIMESTAMPTZ NOT NULL,
    device_type             VARCHAR(32) NOT NULL,
    platform                VARCHAR(32) NOT NULL,
    acquisition_source      VARCHAR(64) NOT NULL,
    population              VARCHAR(32),
    prior_engagement        DOUBLE PRECISION,
    registration_friction   DOUBLE PRECISION,
    checkout_friction       DOUBLE PRECISION,
    page_delay              DOUBLE PRECISION,
    content_exposure        DOUBLE PRECISION,
    navigation_friction     DOUBLE PRECISION,
    intervention_exposure   BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_sessions_start ON sessions (session_start);
CREATE INDEX IF NOT EXISTS idx_sessions_device ON sessions (device_type);

CREATE TABLE IF NOT EXISTS events (
    event_id                VARCHAR(64) PRIMARY KEY,
    session_id               VARCHAR(64) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    timestamp                TIMESTAMPTZ NOT NULL,
    event_type               VARCHAR(32) NOT NULL,
    page                     VARCHAR(64) NOT NULL,
    action                   VARCHAR(32) NOT NULL,
    dwell_time                DOUBLE PRECISION,
    sequence_number           INTEGER NOT NULL,
    intervention_exposure    BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_events_session ON events (session_id);
CREATE INDEX IF NOT EXISTS idx_events_page ON events (page);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON events (timestamp);

CREATE TABLE IF NOT EXISTS journeys (
    journey_id               VARCHAR(64) PRIMARY KEY,
    session_id                VARCHAR(64) NOT NULL REFERENCES sessions(session_id) ON DELETE CASCADE,
    journey_sequence          TEXT NOT NULL,
    journey_length             INTEGER NOT NULL,
    duration                  DOUBLE PRECISION NOT NULL,
    converted                 BOOLEAN NOT NULL,
    abandonment_stage         VARCHAR(32),
    unique_pages               INTEGER,
    repeated_pages             INTEGER
);

CREATE INDEX IF NOT EXISTS idx_journeys_session ON journeys (session_id);
CREATE INDEX IF NOT EXISTS idx_journeys_converted ON journeys (converted);

CREATE TABLE IF NOT EXISTS causal_results (
    id                        SERIAL PRIMARY KEY,
    treatment                 VARCHAR(64) NOT NULL,
    outcome                    VARCHAR(64) NOT NULL,
    effect_estimate             DOUBLE PRECISION,
    ci_lower                   DOUBLE PRECISION,
    ci_upper                   DOUBLE PRECISION,
    method                     VARCHAR(64),
    sample_size                 INTEGER,
    assumptions                TEXT,
    refutation_passed          BOOLEAN,
    computed_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS simulations (
    id                        SERIAL PRIMARY KEY,
    scenario_name              VARCHAR(128) NOT NULL,
    intervention                VARCHAR(64) NOT NULL,
    parameters                  JSONB,
    baseline_result              DOUBLE PRECISION,
    simulated_result             DOUBLE PRECISION,
    improvement                 DOUBLE PRECISION,
    uncertainty                 DOUBLE PRECISION,
    computed_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS recommendations (
    id                        SERIAL PRIMARY KEY,
    intervention                VARCHAR(64) NOT NULL,
    expected_benefit             DOUBLE PRECISION,
    evidence                    JSONB,
    confidence                  VARCHAR(16),
    complexity                  VARCHAR(16),
    risk                       VARCHAR(16),
    recommendation_score         DOUBLE PRECISION,
    explanation                 TEXT,
    computed_at                TIMESTAMPTZ NOT NULL DEFAULT now()
);
