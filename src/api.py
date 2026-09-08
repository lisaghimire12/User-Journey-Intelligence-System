"""FastAPI application for privacy-aware live event ingestion."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import text
from src import database
from src.event_mapping import SESSION_GAP_MINUTES, map_live_event
from src.privacy import minimize_event, minimize_session, pseudonymize
from src.config import settings


class LiveEvent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    raw_user_id: str = Field(min_length=1)
    raw_session_id: str | None = Field(default=None, min_length=1)
    event_name: str = Field(min_length=1)
    page_url: str = Field(min_length=1)
    product_id: str | None = Field(default=None, min_length=1)
    timestamp: datetime | None = None


app = FastAPI(title="User Journey Intelligence Live Ingestion API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def _utc_timestamp(value: datetime | None) -> datetime:
    timestamp = value or datetime.now(timezone.utc)
    if timestamp.tzinfo is None:
        return timestamp.replace(tzinfo=timezone.utc)
    return timestamp.astimezone(timezone.utc)


def _most_recent_event(user_id: str) -> dict | None:
    result = database.read_sql(
        """
        SELECT e.session_id, e.timestamp, e.sequence_number
        FROM events e
        JOIN sessions s ON s.session_id = e.session_id
        WHERE s.anonymous_user_id = :anonymous_user_id
        ORDER BY e.timestamp DESC
        LIMIT 1
        """,
        {"anonymous_user_id": user_id},
    )
    if result.empty:
        return None
    return result.iloc[0].to_dict()


def _timestamp(value: object) -> datetime:
    parsed = pd.to_datetime(value, utc=True)
    return parsed.to_pydatetime()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/events", status_code=201)
def ingest_event(payload: LiveEvent) -> dict[str, str]:
    try:
        mapping = map_live_event(payload.event_name)
    except KeyError:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported event_name: {payload.event_name}",
        ) from None

    timestamp = _utc_timestamp(payload.timestamp)
    anonymous_user_id = pseudonymize(payload.raw_user_id)
    recent = _most_recent_event(anonymous_user_id)

    if recent is not None:
        recent_timestamp = _timestamp(recent["timestamp"])
        gap_minutes = (timestamp - recent_timestamp).total_seconds() / 60
    else:
        gap_minutes = None

    if recent is not None and gap_minutes is not None and gap_minutes < SESSION_GAP_MINUTES:
        session_id = str(recent["session_id"])
        sequence_number = int(recent["sequence_number"]) + 1
        session_exists = True
    else:
        session_seed = f"{payload.raw_session_id or payload.raw_user_id}:{timestamp.isoformat()}"
        session_id = pseudonymize(session_seed)
        sequence_number = 1
        session_exists = False

    event_record = minimize_event(
        {
            "event_id": str(uuid.uuid4()),
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "event_type": mapping["event_type"],
            "page": mapping["page"],
            "action": mapping["action"],
            "sequence_number": sequence_number,
            "intervention_exposure": False,
        }
    )

    if not session_exists:
        session_record = minimize_session(
            {
                "session_id": session_id,
                "anonymous_user_id": anonymous_user_id,
                "session_start": timestamp.isoformat(),
                "session_end": timestamp.isoformat(),
                "device_type": "unknown",
                "platform": "live_web",
                "acquisition_source": "live_site",
            }
        )
        database.write_dataframe(pd.DataFrame([session_record]), "sessions")
    else:
        engine = database.get_engine()
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE sessions SET session_end = :session_end WHERE session_id = :session_id"),
                {"session_end": timestamp.isoformat(), "session_id": session_id},
            )

    database.write_dataframe(pd.DataFrame([event_record]), "events")
    return {"status": "accepted", "session_id": session_id, "event_id": event_record["event_id"]}