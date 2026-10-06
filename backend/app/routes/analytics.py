from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.models.models import Event, Session as JourneySession, Journey

router = APIRouter(
    prefix="/api/analytics",
    tags=["analytics"]
)


# =========================================================
# OVERALL ANALYTICS
# =========================================================

@router.get("/overview")
def overview(db: Session = Depends(get_db)):

    sessions = db.query(JourneySession).all()
    journeys = db.query(Journey).all()

    total_sessions = len(sessions)

    converted_sessions = sum(
        1 for session in sessions
        if session.converted
    )

    conversion_rate = (
        converted_sessions / total_sessions * 100
        if total_sessions
        else 0
    )

    average_journey_length = (
        sum(j.journey_length for j in journeys) / len(journeys)
        if journeys
        else 0
    )

    average_duration = (
        sum(j.duration_seconds for j in journeys) / len(journeys)
        if journeys
        else 0
    )

    abandonment_rate = (
        (total_sessions - converted_sessions)
        / total_sessions
        * 100
        if total_sessions
        else 0
    )

    return {
        "total_sessions": total_sessions,

        "conversion_rate": round(
            conversion_rate,
            2
        ),

        "avg_journey_length": round(
            average_journey_length,
            2
        ),

        "avg_journey_duration": round(
            average_duration,
            2
        ),

        "abandonment_rate": round(
            abandonment_rate,
            2
        ),

        "event_count": db.query(Event).count(),

        "journey_count": len(journeys)
    }


# =========================================================
# ALL JOURNEYS
# =========================================================

@router.get("/journeys")
def journeys(
    db: Session = Depends(get_db)
):

    return (
        db.query(Journey)
        .order_by(Journey.id.desc())
        .limit(100)
        .all()
    )


# =========================================================
# UNIQUE USERS
# =========================================================

@router.get("/users")
def users(
    db: Session = Depends(get_db)
):

    rows = (
        db.query(
            JourneySession.anonymous_user_id
        )
        .distinct()
        .all()
    )

    return [
        {
            "user_id": row[0]
        }
        for row in rows
    ]


# =========================================================
# ONE USER'S COMPLETE JOURNEY
# =========================================================

@router.get("/users/{user_id}")
def user_journey(
    user_id: str,
    db: Session = Depends(get_db)
):

    sessions = (
        db.query(JourneySession)
        .filter(
            JourneySession.anonymous_user_id == user_id
        )
        .order_by(
            JourneySession.start_time
        )
        .all()
    )

    user_sessions = []

    for session in sessions:

        journey = (
            db.query(Journey)
            .filter(
                Journey.session_id == session.session_id
            )
            .first()
        )

        events = (
            db.query(Event)
            .filter(
                Event.session_id == session.session_id
            )
            .order_by(
                Event.sequence_number
            )
            .all()
        )

        event_records = []

        for event in events:

            event_records.append({
                "sequence": event.sequence_number,
                "event": event.event_name,
                "page": event.page,
                "product_id": event.product_id,
                "timestamp": event.timestamp,
                "metadata": event.metadata_json
            })

        user_sessions.append({

            "session_id": session.session_id,

            "start_time": session.start_time,

            "end_time": session.end_time,

            "converted": session.converted,

            "event_count": session.event_count,

            "journey": (
                journey.sequence
                if journey
                else []
            ),

            "journey_length": (
                journey.journey_length
                if journey
                else 0
            ),

            "duration_seconds": (
                journey.duration_seconds
                if journey
                else 0
            ),

            "abandonment_stage": (
                journey.abandonment_stage
                if journey
                else None
            ),

            "events": event_records
        })

    return {

        "user_id": user_id,

        "sessions": user_sessions,

        "session_count": len(user_sessions),

        "total_events": sum(
            session["event_count"]
            for session in user_sessions
        ),

        "converted_sessions": sum(
            1
            for session in user_sessions
            if session["converted"]
        )
    }


# =========================================================
# RECOMPUTE JOURNEYS
# =========================================================

@router.post("/recompute")
def recompute(
    db: Session = Depends(get_db)
):

    from backend.app.services.analytics import rebuild

    count = rebuild(db)

    return {
        "status": "recomputed",
        "sessions": count
    }